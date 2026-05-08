import re
from typing import Literal

from pydantic import BaseModel, Field


class StructuredRAGResponse(BaseModel):
    answer: str = Field(description="The detailed answer to the question or the generated notes.")
    source: Literal["Context", "Internal Knowledge", "Context & Internal Knowledge"] = Field(
        description="The source of the information."
    )


ANSWER_PROMPT_TEMPLATE = """You are a helpful assistant answering questions about a YouTube video.

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


NOTES_PROMPT_TEMPLATE = """You are a helpful assistant generating notes on a YouTube video.

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


def clean_json_output(ai_message) -> str:
    content = ai_message.content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```markdown\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"^```\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
    return content
