from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["TOGETHER_API_KEY"] = os.getenv("TOGETHER_API_KEY")

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
)

llm_openai = ChatOpenAI(
    api_key=os.getenv("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
    model="openai/gpt-oss-20b",
    temperature=0.1,
)