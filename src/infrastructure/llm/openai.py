from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.domain.models import RAGResult
from src.infrastructure.llm.common import ANSWER_PROMPT_TEMPLATE, NOTES_PROMPT_TEMPLATE, StructuredRAGResponse


class OpenAIRAGGenerator:
    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key

    def answer_question(self, *, context: str, question: str, model_name: str) -> RAGResult:
        response = self._invoke(
            ANSWER_PROMPT_TEMPLATE,
            model_name=model_name,
            variables={"context": context, "question": question},
        )
        return RAGResult(answer=response.answer, source=response.source)

    def generate_notes(self, *, context: str, topic: str, model_name: str) -> RAGResult:
        response = self._invoke(
            NOTES_PROMPT_TEMPLATE,
            model_name=model_name,
            variables={"context": context, "topic": topic},
        )
        return RAGResult(answer=response.answer, source=response.source)

    def _invoke(self, prompt_template: str, *, model_name: str, variables: dict) -> StructuredRAGResponse:
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required when using the OpenAI LLM provider.")

        llm = ChatOpenAI(model=model_name, api_key=self._api_key)
        structured_llm = llm.with_structured_output(StructuredRAGResponse, method="function_calling")
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | structured_llm

        return chain.invoke(
            {
                **variables,
                "format_instructions": "Return a structured response matching the requested schema.",
            }
        )
