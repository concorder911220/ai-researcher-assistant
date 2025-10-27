"""Document summarization service."""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..config import settings


def get_summarizer() -> ChatOpenAI:
    """
    Get the summarizer model.
    Always uses OpenAI for document summarization.
    """
    return ChatOpenAI(
        model="gpt-3.5-turbo",  # Use fast model for summarization
        temperature=0.3,  # Lower temperature for factual summaries
        openai_api_key=settings.openai_api_key,
    )


async def summarize_document(text: str) -> str:
    """
    Summarize a document.

    Args:
        text: Document text to summarize

    Returns:
        Document summary
    """
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant that creates concise, informative summaries of documents. "
                "Focus on key points, main ideas, and important details.",
            ),
            (
                "human",
                "Please provide a concise summary of the following document:\n\n{document}",
            ),
        ]
    )

    model = get_summarizer()
    chain = prompt_template | model

    # Truncate text if too long
    max_length = 8000
    if len(text) > max_length:
        text = text[:max_length] + "..."

    result = chain.invoke({"document": text})
    return result.content


