"""Document parsing service."""
from pathlib import Path

from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition


def parse_document(file_path: str) -> list[str]:
    """
    Parse a document into structured elements.

    Args:
        file_path: Path to the document file

    Returns:
        List of text chunks
    """
    path = Path(file_path)

    # Determine mime type based on extension
    mime_type_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }

    ext = path.suffix.lower()
    mime_type = mime_type_map.get(ext, "application/octet-stream")

    # Parse document
    elements = partition(
        filename=str(path),
        mime_type=mime_type,
        strategy="auto",
    )

    # Extract text from elements
    texts = [element.text for element in elements if hasattr(element, "text") and element.text.strip()]

    return texts


def parse_and_chunk(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Parse a document and chunk it.

    Args:
        file_path: Path to the document file
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    # First parse the document
    elements = parse_document(file_path)

    # Chunk the elements
    all_chunks = []
    current_chunk = ""

    for element in elements:
        if len(current_chunk) + len(element) < chunk_size:
            current_chunk += element + "\n\n"
        else:
            if current_chunk:
                all_chunks.append(current_chunk.strip())
            current_chunk = element + "\n\n"

    # Add the last chunk
    if current_chunk:
        all_chunks.append(current_chunk.strip())

    # Handle overlap
    overlapped_chunks = []
    for i, chunk in enumerate(all_chunks):
        if i == 0:
            overlapped_chunks.append(chunk)
        else:
            prev_chunk = all_chunks[i - 1]
            overlap_text = prev_chunk[-chunk_overlap:] if len(prev_chunk) > chunk_overlap else prev_chunk
            overlapped_chunks.append(f"{overlap_text}\n\n{chunk}")

    return overlapped_chunks


