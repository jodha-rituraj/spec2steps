from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()

def get_llm(api_key=None):
    """
    Get LLM instance with optional API key.
    Falls back to environment variable if no key provided.
    Raises error if neither is available.
    
    Args:
        api_key (str, optional): GROQ API key. If None, uses environment variable.
    
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
    
    return ChatGroq(
        api_key=groq_api_key,
        model="openai/gpt-oss-20b",
        temperature=0.1,
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