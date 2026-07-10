from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import TypeVar, Type
import os
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv()

TModel = TypeVar("TModel", bound=BaseModel)

_MODEL_NAME = "gemini-3.1-flash-lite"


def get_structured_llm(
    schema: Type[TModel],
    temperature: float = 0.7,
    timeout_s: float = 240,
):
    """
    Returns a LangChain runnable that outputs a validated instance of `schema`.
    Centralizes model name, API key, retry, and structured-output config so
    every agent uses identical behavior.
    """
    llm = ChatGoogleGenerativeAI(
        model=_MODEL_NAME,
        temperature=temperature,
        google_api_key=os.environ.get("GEMINI_API_KEY"),
        timeout=timeout_s,
    )
    return llm.with_structured_output(schema).with_retry(
        retry_if_exception_type=(ResourceExhausted,),
        stop_after_attempt=5,
    )
