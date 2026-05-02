from langchain_text_splitters import RecursiveCharacterTextSplitter


class LangChainTextChunker:
    def __init__(self, *, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split(self, text: str) -> list[str]:
        return [document.page_content for document in self._splitter.create_documents([text])]

