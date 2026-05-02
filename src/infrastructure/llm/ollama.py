import re
from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from src.domain.models import RAGResult


class _StructuredRAGResponse(BaseModel):
    answer: str = Field(description="The detailed answer to the question or the generated notes.")
    source: Literal["Context", "Internal Knowledge", "Context & Internal Knowledge"] = Field(
        description="The source of the information."
    )


class OllamaRAGGenerator:
    def __init__(self, *, base_url: str, temperature: float = 0.7) -> None:
        self._base_url = base_url
        self._temperature = temperature
        self._parser = PydanticOutputParser(pydantic_object=_StructuredRAGResponse)

    def answer_question(self, *, context: str, question: str, model_name: str) -> RAGResult:
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

        response = self._invoke(
            prompt_template,
            model_name=model_name,
            variables={"context": context, "question": question},
        )
        return RAGResult(answer=response.answer, source=response.source)

    def generate_notes(self, *, context: str, topic: str, model_name: str) -> RAGResult:
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

        response = self._invoke(
            prompt_template,
            model_name=model_name,
            variables={"context": context, "topic": topic},
        )
        return RAGResult(answer=response.answer, source=response.source)

    def _invoke(self, prompt_template: str, *, model_name: str, variables: dict) -> _StructuredRAGResponse:
        llm = ChatOllama(
            model=model_name,
            temperature=self._temperature,
            format="json",
            base_url=self._base_url,
        )
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm | RunnableLambda(_clean_json_output) | self._parser

        return chain.invoke(
            {
                **variables,
                "format_instructions": self._parser.get_format_instructions(),
            }
        )


def _clean_json_output(ai_message) -> str:
    content = ai_message.content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```markdown\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
    return content

