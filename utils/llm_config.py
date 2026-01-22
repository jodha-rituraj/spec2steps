from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()

# GPT-OSS models support reasoning with include_reasoning and reasoning_effort
GPT_OSS_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
REASONING_EFFORTS = ["low", "medium", "high"]  # For GPT-OSS models

def get_llm(provider="groq", api_key=None, endpoint=None, deployment_name=None, api_version=None, include_reasoning=True, reasoning_effort="medium"):
    """
    Get LLM instance with optional API key and reasoning support for multiple providers.
    
    Args:
        provider (str): LLM provider - "groq" or "azure"
        api_key (str, optional): API key. If None, uses environment variable.
        endpoint (str, optional): Azure OpenAI endpoint.
        deployment_name (str, optional): Azure OpenAI deployment name.
        api_version (str, optional): Azure OpenAI API version.
        include_reasoning (bool): Groq specific - if True, enables reasoning tokens.
        reasoning_effort (str): Groq specific - Level of reasoning effort.
    
    Returns:
        BaseChatModel: Configured LLM instance
    """
    if provider.lower() == "groq":
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
        
        if include_reasoning:
            return ChatGroq(
                api_key=groq_api_key,
                model="openai/gpt-oss-120b",
                temperature=0.6,
                reasoning_effort=reasoning_effort if reasoning_effort in REASONING_EFFORTS else "medium",
            )
        else:
            return ChatGroq(
                api_key=groq_api_key,
                model="openai/gpt-oss-120b",
                temperature=0.6,
            )
            
    elif provider.lower() == "azure":
        # Try to get params from parameters, then environment
        azure_api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        azure_api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        if not all([azure_api_key, azure_endpoint, azure_deployment]):
            missing = []
            if not azure_api_key: missing.append("API Key")
            if not azure_endpoint: missing.append("Endpoint")
            if not azure_deployment: missing.append("Deployment Name")
            
            raise ValueError(
                f"❌ Missing Azure OpenAI configuration: {', '.join(missing)}\n"
                "Please provide these in the sidebar or set environment variables."
            )
            
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint.strip(),
            openai_api_key=azure_api_key.strip(),
            azure_deployment=azure_deployment.strip(),
            openai_api_version=azure_api_version.strip(),
            temperature=0,
        )
    
    else:
        raise ValueError(f"❌ Unsupported provider: {provider}")

# Initialize default LLM (will use env variable if available)
try:
    # Try Groq first as default
    llm = get_llm(provider="groq")
except ValueError:
    try:
        # Try Azure if Groq fails and env vars exist
        llm = get_llm(provider="azure")
    except ValueError:
        llm = None

# Keep backward compatibility
os.environ["TOGETHER_API_KEY"] = os.getenv("TOGETHER_API_KEY", "")

llm_openai = ChatOpenAI(
    api_key=os.getenv("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
    model="openai/gpt-oss-20b",
    temperature=0.1,
) if os.getenv("TOGETHER_API_KEY") else None