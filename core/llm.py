import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI, ChatOpenAI

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
REASONING_EFFORTS = ("low", "medium", "high")
# Free tiers rate-limit by tokens per minute; the SDKs honour Retry-After between attempts.
MAX_RETRIES = 6


def get_llm(
    provider="groq",
    api_key=None,
    endpoint=None,
    deployment_name=None,
    api_version=None,
    include_reasoning=True,
    reasoning_effort="medium",
    model=None,
):
    provider = provider.lower()

    if provider == "groq":
        key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        if not key:
            raise ValueError("No Groq API key. Enter one in the sidebar or set GROQ_API_KEY.")
        kwargs = {"api_key": key, "model": GROQ_MODEL, "temperature": 0.6, "max_retries": MAX_RETRIES}
        if include_reasoning:
            kwargs["reasoning_effort"] = reasoning_effort if reasoning_effort in REASONING_EFFORTS else "medium"
        return ChatGroq(**kwargs)

    if provider == "openrouter":
        key = (api_key or os.getenv("OPENROUTER_API_KEY") or "").strip()
        if not key:
            raise ValueError("No OpenRouter API key. Enter one in the sidebar or set OPENROUTER_API_KEY.")
        return ChatOpenAI(
            api_key=key,
            base_url=OPENROUTER_URL,
            model=(model or os.getenv("OPENROUTER_MODEL") or OPENROUTER_MODEL).strip(),
            temperature=0.6,
            max_retries=MAX_RETRIES,
        )

    if provider == "azure":
        config = {
            "API key": api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment name": deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        }
        missing = [name for name, value in config.items() if not value]
        if missing:
            raise ValueError(f"Missing Azure OpenAI config: {', '.join(missing)}.")
        return AzureChatOpenAI(
            azure_endpoint=config["endpoint"].strip(),
            api_key=config["API key"].strip(),
            azure_deployment=config["deployment name"].strip(),
            api_version=(api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")).strip(),
            temperature=0,
            max_retries=MAX_RETRIES,
        )

    raise ValueError(f"Unsupported provider: {provider}")
