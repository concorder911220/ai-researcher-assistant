"""Chunking service."""
from typing import Iterator

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Split text into chunks with overlap.

    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)
    return chunks


def chunk_document(text: str) -> Iterator[dict[str, str | int]]:
    """
    Chunk a document and yield chunks with metadata.

    Args:
        text: Document text

    Yields:
        Dictionary with 'content' and 'index' keys
    """
    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks):
        yield {"content": chunk, "index": i}


