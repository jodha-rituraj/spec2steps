from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()

# GPT-OSS models support reasoning with include_reasoning and reasoning_effort
GPT_OSS_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
REASONING_EFFORTS = ["low", "medium", "high"]  # For GPT-OSS models

def get_llm(api_key=None, include_reasoning=True, reasoning_effort="medium"):
    """
    Get LLM instance with optional API key and reasoning support.
    Falls back to environment variable if no key provided.
    Raises error if neither is available.
    
    Args:
        api_key (str, optional): GROQ API key. If None, uses environment variable.
        include_reasoning (bool): If True, enables reasoning tokens in response.
            The reasoning will be in response.additional_kwargs['reasoning_content']
        reasoning_effort (str): Level of reasoning effort - "low", "medium", or "high".
            Higher effort = more reasoning tokens but better quality.
    
    Returns:
        ChatGroq: Configured LLM instance
    
    Raises:
        ValueError: If no API key is provided and none found in environment
    """
    # Try to get API key from parameter, then environment
    groq_api_key = api_key or os.getenv("GROQ_API_KEY")
    
    # Remove whitespace and check if valid
    if groq_api_key:
        groq_api_key = groq_api_key.strip()
    
    if not groq_api_key:
        raise ValueError(
            "❌ No GROQ API key found! Please either:\n"
            "1. Enter your API key in the sidebar, or\n"
            "2. Set GROQ_API_KEY in your .env file"
        )
    
    # Set environment variable for this session
    os.environ["GROQ_API_KEY"] = groq_api_key
    
    # Build ChatGroq with reasoning support for GPT-OSS models
    # Use reasoning_effort parameter (reasoning returned in additional_kwargs['reasoning_content'])
    if include_reasoning:
        return ChatGroq(
            api_key=groq_api_key,
            model="openai/gpt-oss-120b",
            temperature=0.6,  # Recommended for reasoning models
            reasoning_effort=reasoning_effort if reasoning_effort in REASONING_EFFORTS else "medium",
        )
    else:
        return ChatGroq(
            api_key=groq_api_key,
            model="openai/gpt-oss-120b",
            temperature=0.6,
        )

# Initialize default LLM (will use env variable if available)
try:
    llm = get_llm()
except ValueError:
    # Will be set when user provides API key
    llm = None

# Keep backward compatibility
os.environ["TOGETHER_API_KEY"] = os.getenv("TOGETHER_API_KEY", "")

llm_openai = ChatOpenAI(
    api_key=os.getenv("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
    model="openai/gpt-oss-20b",
    temperature=0.1,
) if os.getenv("TOGETHER_API_KEY") else None