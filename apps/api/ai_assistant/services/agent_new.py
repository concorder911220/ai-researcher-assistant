"""Enhanced agent service with LangChain tools and OpenAI function calling."""
import json
import logging
from typing import Any, List, Dict

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool, StructuredTool
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from ..config import settings
from ..services.embeddings import get_embedding_model
from ..services.retriever_chat import hybrid_search_for_chat
from ..services.memory import (
    get_chat_summary,
    retrieve_memories,
)
from ..services.citations import extract_citations, format_chunk_source

logger = logging.getLogger(__name__)


# =====================
# TOOL IMPLEMENTATIONS
# =====================

def _search_web(query: str) -> str:
    """
    Search the web using SerpAPI.
    
    Args:
        query: Search query
    
    Returns:
        Formatted search results
    """
    if not settings.serpapi_api_key:
        return "Web search is not configured. Please provide SERPAPI_API_KEY."
    
    try:
        import serpapi
        
        params = {
            "q": query,
            "api_key": settings.serpapi_api_key,
            "engine": "google",
            "num": 5
        }
        
        # Log the request
        if settings.agent_verbose:
            print(f"   SerpAPI Request: query='{query}'")
        
        search = serpapi.search(params)
        results = search.as_dict()
        
        # Log response status
        if settings.agent_verbose:
            print(f"   SerpAPI Response: {len(results.get('organic_results', []))} results")
            if "error" in results:
                print(f"   SerpAPI Error: {results['error']}")
        
        # Check for errors
        if "error" in results:
            return f"Search error: {results['error']}"
        
        # Format results for LLM
        if "organic_results" in results and len(results["organic_results"]) > 0:
            formatted = []
            for i, result in enumerate(results["organic_results"][:5], 1):
                formatted.append(
                    f"{i}. {result.get('title', 'No title')}\n"
                    f"   URL: {result.get('link', '')}\n"
                    f"   Snippet: {result.get('snippet', 'No description')}"
                )
            return "\n\n".join(formatted)
        
        return "No results found for this query."
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        if settings.agent_verbose:
            print(f"   SerpAPI Exception: {error_msg}")
        return error_msg


# Pydantic schemas for tool arguments
class CalculatorInput(BaseModel):
    """Input for calculator tool."""
    query: str = Field(description="Mathematical expression to calculate (e.g., '2+2', '100*0.15', '(500+300)*2')")

class WebSearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="Search query to look up on the web")


class NewsSearchInput(BaseModel):
    """Input for news search tool."""
    topic: str = Field(description="News topic or keyword to search for (e.g., 'AI technology', 'climate change')")


def _calculate(query: str) -> str:
    """
    Evaluate a mathematical expression.
    
    Args:
        query: Math expression to evaluate (e.g. "2+2" or "(100*0.15)")
    
    Returns:
        Result or error message
    """
    try:
        # Clean the input
        expression = query.strip()
        
        # Safe eval with limited scope
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Expression contains invalid characters. Only numbers and operators (+, -, *, /, %, ()) allowed."
        
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"


def _search_news(topic: str) -> str:
    """
    Search Google News for latest articles on a topic.
    
    Args:
        topic: News topic to search for
    
    Returns:
        Formatted news results
    """
    if not settings.serpapi_api_key:
        return "News search is not configured. Please provide SERPAPI_API_KEY."
    
    try:
        import serpapi
        
        params = {
            "q": topic,
            "api_key": settings.serpapi_api_key,
            "engine": "google_news",
            "num": 5
        }
        
        # Log the request
        if settings.agent_verbose:
            print(f"   Google News Request: topic='{topic}'")
        
        search = serpapi.search(params)
        results = search.as_dict()
        
        # Log response status
        if settings.agent_verbose:
            print(f"   Google News Response: {len(results.get('news_results', []))} articles")
            if "error" in results:
                print(f"   Google News Error: {results['error']}")
        
        # Check for errors
        if "error" in results:
            return f"News search error: {results['error']}"
        
        # Format results for LLM
        if "news_results" in results and len(results["news_results"]) > 0:
            formatted = []
            for i, article in enumerate(results["news_results"][:5], 1):
                formatted.append(
                    f"{i}. {article.get('title', 'No title')}\n"
                    f"   Source: {article.get('source', {}).get('name', 'Unknown')}\n"
                    f"   Date: {article.get('date', 'Unknown')}\n"
                    f"   URL: {article.get('link', '')}\n"
                    f"   Snippet: {article.get('snippet', 'No description')}"
                )
            return "\n\n".join(formatted)
        
        return "No news articles found for this topic."
    except Exception as e:
        error_msg = f"News search failed: {str(e)}"
        if settings.agent_verbose:
            print(f"   Google News Exception: {error_msg}")
        return error_msg


# =====================
# TOOL DEFINITIONS
# =====================

def create_agent_tools() -> List[Tool]:
    """
    Create LangChain tools for the agent.
    
    Returns:
        List of Tool objects
    """
    tools = []
    
    # Tool 1: Web Search
    if settings.enable_web_search and settings.serpapi_api_key:
        web_search_tool = StructuredTool.from_function(
            func=_search_web,
            name="web_search",
            description=(
                "Search the web for current information, facts, news, or data not available in the documents. "
                "Use this when the user asks about recent events, current data, or information not covered in uploaded documents."
            ),
            args_schema=WebSearchInput,
        )
        tools.append(web_search_tool)
    
    # Tool 2: Calculator
    if settings.enable_calculator:
        calculator_tool = StructuredTool.from_function(
            func=_calculate,
            name="calculator",
            description=(
                "Perform mathematical calculations. "
                "Use this when the user asks for computations, math problems, or numerical analysis. "
                "Examples: '2+2', '100*0.15', '(1500+2300)*0.15'"
            ),
            args_schema=CalculatorInput,
        )
        tools.append(calculator_tool)
    
    # Tool 3: News Search
    if settings.serpapi_api_key:  # Reuse SerpAPI key
        news_tool = StructuredTool.from_function(
            func=_search_news,
            name="news_search",
            description=(
                "Search Google News for the latest news articles on any topic. "
                "Use this when the user asks about recent news, current events, or trending topics. "
                "Examples: 'AI news', 'climate change updates', 'tech industry news'"
            ),
            args_schema=NewsSearchInput,
        )
        tools.append(news_tool)
    
    return tools


# =====================
# AGENT EXECUTION
# =====================

async def execute_tools(
    llm_with_tools: ChatOpenAI,
    messages: List,
    tools: List[Tool],
    max_iterations: int = 5
) -> tuple[str, List[Dict]]:
    """
    Execute tools based on LLM function calls.
    
    Args:
        llm_with_tools: LLM with tools bound
        messages: Conversation messages
        tools: Available tools
        max_iterations: Max tool calls
    
    Returns:
        Tuple of (final_response, tool_executions)
    """
    tool_map = {t.name: t for t in tools}
    tool_executions = []
    
    for iteration in range(max_iterations):
        # Get LLM response
        response = llm_with_tools.invoke(messages)
        
        # Check if LLM wants to use tools
        if not response.tool_calls:
            # No more tool calls, return final answer
            return response.content, tool_executions
        
        # Execute requested tools
        messages.append(response)
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if settings.agent_verbose:
                print(f"\n🔧 Tool Call: {tool_name}")
                print(f"   Args: {tool_args}")
            
            # Execute tool
            if tool_name in tool_map:
                try:
                    tool_output = tool_map[tool_name].func(**tool_args)
                    if settings.agent_verbose:
                        print(f"   Result: {tool_output[:200]}...")
                    
                    tool_executions.append({
                        "tool": tool_name,
                        "input": tool_args,
                        "output": tool_output
                    })
                    
                    # Add tool response to messages
                    messages.append(
                        ToolMessage(
                            content=tool_output,
                            tool_call_id=tool_call["id"]
                        )
                    )
                except Exception as e:
                    error_msg = f"Tool execution error: {str(e)}"
                    if settings.agent_verbose:
                        print(f"   Error: {error_msg}")
                    messages.append(
                        ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call["id"]
                        )
                    )
            else:
                messages.append(
                    ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_call["id"]
                    )
                )
    
    # Max iterations reached, get final response
    final_response = llm_with_tools.invoke(messages)
    return final_response.content, tool_executions


# =====================
# MAIN CHAT FUNCTION
# =====================

async def chat_with_rag_agent(
    chat_id: str,
    message: str,
    system_prompt: str,
    personality: str | None = None,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4-turbo-preview",
    llm_temperature: float = 0.7,
    stream: bool = False,
):
    """
    Handle chat using LangChain tools with OpenAI function calling or Anthropic.
    
    Args:
        chat_id: Chat ID
        message: User message
        system_prompt: System prompt
        personality: Personality type
        llm_provider: LLM provider (openai, anthropic)
        llm_model: Model name
        llm_temperature: Temperature for generation
        stream: Whether to stream (fallback to direct LLM)
    
    Yields:
        Response dictionary or chunks
    """
    # Log agent initialization
    print(f"\n🔧 Agent Initialization")
    print(f"  Provider: {llm_provider.upper()}")
    print(f"  Model: {llm_model}")
    print(f"  Temperature: {llm_temperature}")
    print(f"  Stream: {stream}")
    
    logger.info(f"chat_with_rag_agent: provider={llm_provider}, model={llm_model}, stream={stream}")
    
    # Retrieve recent conversation history (last 10 messages)
    from ..db import get_db_session
    conversation_history = []
    try:
        with get_db_session() as cursor:
            cursor.execute(
                """
                SELECT role, content
                FROM messages
                WHERE chat_id = %(chat_id)s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                {"chat_id": chat_id}
            )
            results = cursor.fetchall()
            # Reverse to get chronological order (oldest first)
            conversation_history = [
                {"role": row["role"], "content": row["content"]} 
                for row in reversed(results)
            ]
            
        if conversation_history:
            print(f"📜 Retrieved {len(conversation_history)} previous messages")
    except Exception as e:
        logger.warning(f"Could not retrieve conversation history: {e}")
    
    # Get chat summary
    summary = None
    try:
        summary = await get_chat_summary(chat_id)
        if summary:
            summary_preview = summary[:100] + "..." if len(summary) > 100 else summary
            print(f"📝 Chat Summary: {summary_preview}\n")
    except Exception:
        pass
    
    # Generate query embedding
    embedding_model = get_embedding_model()
    query_embedding = embedding_model.embed_query(message)
    
    # Retrieve relevant chunks for context
    chunks = await hybrid_search_for_chat(
        query=message,
        query_embedding=query_embedding,
        chat_id=chat_id,
        top_k=settings.top_k_chunks,
    )
    
    # Format document context with detailed metadata
    context_parts = []
    if chunks:
        print(f"\n📄 Retrieved {len(chunks)} document chunks:")
    for i, chunk in enumerate(chunks):
        # Get metadata
        doc_name = chunk.get('title', 'Unknown Document')
        page = chunk.get('page', 'N/A')
        chunk_id = chunk.get('id', 'N/A')
        content_preview = chunk['content'][:80] + "..." if len(chunk['content']) > 80 else chunk['content']
        
        # Log chunk info
        print(f"  {i+1}. {doc_name}", end="")
        if page and page != 'N/A':
            print(f" (Page {page})", end="")
        print(f"\n     Preview: {content_preview}")
        
        # Format chunk with metadata
        chunk_header = f"[Source {i+1}: {doc_name}"
        if page and page != 'N/A':
            chunk_header += f" - Page {page}"
        chunk_header += "]"
        
        context_parts.append(f"{chunk_header}\n{chunk['content']}")
    
    context = "\n\n---\n\n".join(context_parts)
    if chunks:
        print()  # Empty line for readability
    
    # Retrieve memories
    memories = []
    try:
        memories = await retrieve_memories(chat_id, query_embedding)
        if memories:
            print(f"🧠 Retrieved {len(memories)} long-term memories:")
            for i, mem in enumerate(memories, 1):
                mem_preview = mem.get('content', '')[:60] + "..." if len(mem.get('content', '')) > 60 else mem.get('content', '')
                print(f"  {i}. [{mem.get('memory_type', 'unknown')}] {mem_preview}")
            print()  # Empty line
    except Exception:
        pass
    
    # Load personality prompts
    personality_prompt = ""
    print(f"Personality: {personality}")   
    if personality:
        try:
            with open(f"apps/api/ai_assistant/prompts/persona_{personality}.md") as f:
                personality_prompt = f.read()
        except FileNotFoundError:
            pass
    
    # Build system message
    system_parts = [system_prompt, personality_prompt]
    
    if context:
        system_parts.append(f"\n### Document Context:\n{context}")
    
    if summary:
        system_parts.append(f"\n### Conversation Summary:\n{summary}")
    
    if memories:
        memory_text = "\n".join([mem.get("content", "") for mem in memories])
        system_parts.append(f"\n### Relevant Memories:\n{memory_text}")
    
    full_system_prompt = "\n\n".join(filter(None, system_parts))
    
    # Create LLM based on provider
    if llm_provider == "anthropic":
        print(f"🎭 Initializing Anthropic Claude...")
        print(f"   Model: {llm_model}")
        print(f"   Temperature: {llm_temperature}")
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=llm_model,
                temperature=llm_temperature,
                anthropic_api_key=settings.anthropic_api_key,
            )
            print(f"✅ Anthropic Claude initialized successfully\n")
        except Exception as e:
            print(f"❌ Failed to initialize Anthropic: {e}")
            print(f"⚠️  Falling back to OpenAI...\n")
            llm_provider = "openai"  # Fallback
            llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=llm_temperature,
                openai_api_key=settings.openai_api_key,
            )
    else:
        print(f"🤖 Initializing OpenAI GPT...")
        print(f"   Model: {llm_model}")
        print(f"   Temperature: {llm_temperature}")
        llm = ChatOpenAI(
            model=llm_model,
            temperature=llm_temperature,
            openai_api_key=settings.openai_api_key,
        )
        print(f"✅ OpenAI GPT initialized successfully\n")
    
    # For streaming, bypass tools (agents don't stream well)
    if stream:
        # Build messages with conversation history
        messages = [("system", full_system_prompt)]
        
        # Add conversation history
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("assistant", msg["content"]))
        
        # Add current message
        messages.append(("human", message))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm
        
        async for chunk in chain.astream({}):
            if hasattr(chunk, 'content'):
                yield chunk
        return
    
    # Create tools and bind to LLM
    tools = create_agent_tools()
    
    if not tools:
        # No tools available, use direct LLM with conversation history
        messages = [("system", full_system_prompt)]
        
        # Add conversation history
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("assistant", msg["content"]))
        
        # Add current message
        messages.append(("human", message))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm
        result = chain.invoke({})
        
        yield {
            "content": result.content,
            "sources": [format_chunk_source(chunk) for chunk in chunks],
            "citations": extract_citations(result.content),
            "tool_calls": 0,
        }
        return
    
    # Bind tools to LLM (OpenAI function calling)
    llm_with_tools = llm.bind_tools(tools)
    
    # Prepare messages with conversation history
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    messages = [SystemMessage(content=full_system_prompt)]
    
    # Add conversation history
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    # Execute with tools
    try:
        final_content, tool_executions = await execute_tools(
            llm_with_tools,
            messages,
            tools,
            max_iterations=settings.agent_max_iterations
        )
        
        # Extract citations
        citations = extract_citations(final_content)
        
        # Format sources
        sources = []
        for i, chunk in enumerate(chunks):
            sources.append({
                **format_chunk_source(chunk),
                "citation_id": i + 1,
            })
        
        # Add tool results to sources
        for tool_exec in tool_executions:
            if tool_exec["tool"] == "web_search":
                sources.append({
                    "source_type": "web_search",
                    "tool": tool_exec["tool"],
                    "content": tool_exec["output"][:200],
                    "citation_id": len(sources) + 1,
                })
        
        # Log completion
        print(f"\n✨ Response Generated")
        print(f"   Provider: {llm_provider.upper()}")
        print(f"   Model: {llm_model}")
        print(f"   Tool Calls: {len(tool_executions)}")
        print(f"   Response Length: {len(final_content)} chars")
        print(f"   Context Used:")
        print(f"     • {len(chunks)} document chunks")
        print(f"     • {len(conversation_history)} conversation messages")
        print(f"     • {len(memories)} long-term memories")
        print(f"     • Chat summary: {'Yes' if summary else 'No'}")
        
        # Show tool calls if any
        if tool_executions:
            print(f"\n   🔧 Tool Calls Made:")
            for i, tool_exec in enumerate(tool_executions, 1):
                print(f"     {i}. {tool_exec.get('name', 'unknown')} → {tool_exec.get('result', 'N/A')[:60]}...")
        
        # Show response preview
        response_preview = final_content[:150] + "..." if len(final_content) > 150 else final_content
        print(f"\n   📝 Response Preview:")
        print(f"     {response_preview}")
        print()
        
        yield {
            "content": final_content,
            "sources": sources,
            "citations": citations,
            "tool_calls": len(tool_executions),
        }
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        # Fallback: return basic response without tools
        if settings.agent_verbose:
            print(f"Tool execution failed: {e}")
        
        yield {
            "content": f"I encountered an error with tools. Based on the documents: {context[:500]}",
            "sources": [format_chunk_source(chunk) for chunk in chunks],
            "citations": [],
            "tool_calls": 0,
        }
