import os
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from transcript import get_youtube_transcript
from logger import setup_logger
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field 
from langchain_core.runnables import RunnableLambda
from typing import Literal
import re
from dotenv import load_dotenv

load_dotenv()

class RAGResponse(BaseModel):
    answer: str = Field(description="The detailed answer to the question or the generated notes.")
    source: Literal["Context", "Internal Knowledge", "Context & Internal Knowledge"] = Field(
        description="The source of the information. Use 'Context' if found in video, 'Internal Knowledge' if not."
    )

parser = PydanticOutputParser(pydantic_object=RAGResponse)

def clean_json_output(ai_message):
    """Refines the LLM output by removing markdown code blocks."""
    content = ai_message.content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```markdown\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
    return content

logger = setup_logger("rag_service", "logs/app.log")

class RAGService:
    def __init__(self, persist_directory: str = "db"):
        self.persist_directory = persist_directory
        # Initialize embeddings - assuming a default model for embeddings
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
        
        # Initialize ChromaDB persistent client
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

    def _get_llm(self, model_name: str):
        if "cloud" in model_name:
            host = "https://ollama.com/"
        else:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            
        return ChatOllama(model=model_name, temperature=0.7, format='json', base_url=host)

    def ingest_video(self, video_id: str):
        """
        Fetches transcript, splits it, and stores in ChromaDB.
        """
        try:
            # Check if video already exists (basic check, can be improved)
            # In Chroma, we can filter by metadata to see if we have docs for this video
            existing_docs = self.vector_store.get(where={"video_id": video_id})
            if existing_docs['ids']:
                logger.info(f"Video {video_id} already ingested. Skipping.")
                return

            transcript_text = get_youtube_transcript(video_id)
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.create_documents([transcript_text])
            
            # Add metadata to each document
            for doc in docs:
                doc.metadata = {"video_id": video_id}
                
            self.vector_store.add_documents(docs)
            logger.info(f"Successfully ingested video {video_id} with {len(docs)} chunks.")
            
        except Exception as e:
            logger.error(f"Error ingesting video {video_id}: {e}")
            raise e

    def ask_question(self, video_id: str, question: str, model_name: str = "mistral-large-3:675b-cloud"):
            """
            Queries the RAG system using Pydantic Parser for structured output.
            """
            try:
                # 1. Retrieval of relevant chunks
                retriever = self.vector_store.as_retriever(
                    search_type="mmr",
                    search_kwargs={"k": 5, "fetch_k": 20, "filter": {"video_id": video_id}}
                )
                
                relevant_docs = retriever.invoke(question)
                context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                if not context_text:
                    context_text = "No relevant video context found."

                # 2. Setup Pydantic Parser
                parser = PydanticOutputParser(pydantic_object=RAGResponse)

                # 3. Prompt with Format Instructions
                # We inject {format_instructions} which LangChain auto-generates from your Pydantic model
                prompt_template = """You are a helpful assistant answering questions about a YouTube video.
                
                Context from video transcript:
                {context}
                
                Question: {question}
                
                Instructions:
                1. Analyze the Context to see if it contains the answer to the Question.
                2. IF the Context contains the answer:
                - Answer strictly using the information provided.
                - Set "source" to "Context".
                3. IF the Context is empty, irrelevant, or does not contain the answer:
                - You MUST provide a helpful answer using your own internal knowledge.
                - In your answer text, you MUST start with: "This information is not covered in the video, but based on general knowledge..."
                - Set "source" to "Internal Knowledge".
                
                Format Instructions:
                {format_instructions}
                """
                
                llm = self._get_llm(model_name)
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                # 4. The Chain: Prompt -> LLM -> Parser
                # 4. The Chain: Prompt -> LLM -> Cleaner -> Parser
                chain = prompt | llm | RunnableLambda(clean_json_output) | parser
                
                # 5. Invoke (Returns a RAGResponse object, not a dict!)
                response = chain.invoke({
                    "context": context_text, 
                    "question": question,
                    "format_instructions": parser.get_format_instructions()
                })
                
                # Convert to dict for your API
                return response.dict()

            except Exception as e:
                logger.error(f"Error answering question for video {video_id}: {e}")
                # Fallback for API safety
                return {
                    "answer": "An error occurred while processing your request.",
                    "source": "Internal Knowledge",
                    "error": str(e)
                }

    def generate_notes(self, video_id: str, topic: str, model_name: str = "mistral-large-3:675b-cloud"):
        """
        Generates notes using Pydantic Parser.
        """
        try:
            retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 10, "fetch_k": 30, "filter": {"video_id": video_id}}
            )
             
            relevant_docs = retriever.invoke(topic)
            context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            parser = PydanticOutputParser(pydantic_object=RAGResponse)
            
            prompt_template = """You are a helpful assistant generating notes on a YouTube video.
            
            Context from video transcript:
            {context}
            
            Topic: {topic}
            
            Instructions:
            1. Generate comprehensive notes using the context.
            2. You are ENCOURAGED to add your own relevant knowledge.
            3. Clearly distinguish between video content and your additions.
            4. Create a captivating and engaging title for the topic at the beginning of the notes.
            
            Format Instructions:
            {format_instructions}
            """
            
            llm = self._get_llm(model_name)
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm | RunnableLambda(clean_json_output) | parser
            
            response = chain.invoke({
                "context": context_text, 
                "topic": topic,
                "format_instructions": parser.get_format_instructions()
            })
            
            return response.dict()

        except Exception as e:
            logger.error(f"Error generating notes for video {video_id}: {e}")
            raise e