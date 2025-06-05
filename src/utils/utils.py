import asyncio
import base64
import functools
import logging
import os
import time
import json
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
import gradio as gr

from .llm import DeepSeekR1ChatOpenAI, DeepSeekR1ChatOllama

logger = logging.getLogger(__name__)

T = TypeVar('T')

PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "azure_openai": "Azure OpenAI",
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
    "google": "Google",
    "alibaba": "Alibaba",
    "moonshot": "MoonShot"
}

def extract_state_from_history(history):
    """
    Extract all current_state keys from the history dictionary and return as a list.
    
    Args:
        history (dict): A dictionary containing history data with model_output entries
        
    Returns:
        list: A list of all current_state dictionaries found in the history
    """
    states = []
    
    if not history or "history" not in history:
        return states
    
    for entry in history["history"]:
        if "model_output" in entry and "current_state" in entry["model_output"]:
            states.append(entry["model_output"]["current_state"])
    
    return states

def get_llm_model(provider: str, **kwargs):
    """
    获取LLM 模型
    :param provider: 模型类型
    :param kwargs:
    :return:
    """
    if provider not in ["ollama"]:
        env_var = f"{provider.upper()}_API_KEY"
        api_key = kwargs.get("api_key", "") or os.getenv(env_var, "")
        if not api_key:
            handle_api_key_error(provider, env_var)
        kwargs["api_key"] = api_key

    if provider == "anthropic":
        if not kwargs.get("base_url", ""):
            base_url = "https://api.anthropic.com"
        else:
            base_url = kwargs.get("base_url")

        return ChatAnthropic(
            model=kwargs.get("model_name", "claude-3-5-sonnet-20241022"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == 'mistral':
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai/v1")
        else:
            base_url = kwargs.get("base_url")
        if not kwargs.get("api_key", ""):
            api_key = os.getenv("MISTRAL_API_KEY", "")
        else:
            api_key = kwargs.get("api_key")

        return ChatMistralAI(
            model=kwargs.get("model_name", "mistral-large-latest"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "deepseek":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("DEEPSEEK_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")

        if kwargs.get("model_name", "deepseek-chat") == "deepseek-reasoner":
            return DeepSeekR1ChatOpenAI(
                model=kwargs.get("model_name", "deepseek-reasoner"),
                temperature=kwargs.get("temperature", 0.0),
                base_url=base_url,
                api_key=api_key,
            )
        else:
            return ChatOpenAI(
                model=kwargs.get("model_name", "deepseek-chat"),
                temperature=kwargs.get("temperature", 0.0),
                base_url=base_url,
                api_key=api_key,
            )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model_name", "gemini-2.0-flash-exp"),
            temperature=kwargs.get("temperature", 0.0),
            api_key=api_key,
        )
    elif provider == "ollama":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        else:
            base_url = kwargs.get("base_url")

        if "deepseek-r1" in kwargs.get("model_name", "qwen2.5:7b"):
            return DeepSeekR1ChatOllama(
                model=kwargs.get("model_name", "deepseek-r1:14b"),
                temperature=kwargs.get("temperature", 0.0),
                num_ctx=kwargs.get("num_ctx", 32000),
                base_url=base_url,
            )
        else:
            return ChatOllama(
                model=kwargs.get("model_name", "qwen2.5:7b"),
                temperature=kwargs.get("temperature", 0.0),
                num_ctx=kwargs.get("num_ctx", 32000),
                num_predict=kwargs.get("num_predict", 1024),
                base_url=base_url,
            )
    elif provider == "azure_openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")
        api_version = kwargs.get("api_version", "") or os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        return AzureChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            api_version=api_version,
            azure_endpoint=base_url,
            api_key=api_key,
        )
    elif provider == "alibaba":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("ALIBABA_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "qwen-plus"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )

    elif provider == "moonshot":
        return ChatOpenAI(
            model=kwargs.get("model_name", "moonshot-v1-32k-vision-preview"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=os.getenv("MOONSHOT_ENDPOINT"),
            api_key=os.getenv("MOONSHOT_API_KEY"),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# Predefined model names for common providers
model_names = {
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
    "openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "o3-mini"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "google": ["gemini-2.0-flash", "gemini-2.0-flash-thinking-exp", "gemini-1.5-flash-latest",
               "gemini-1.5-flash-8b-latest", "gemini-2.0-flash-thinking-exp-01-21", "gemini-2.0-pro-exp-02-05"],
    "ollama": ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b", "qwen2.5-coder:14b", "qwen2.5-coder:32b", "llama2:7b",
               "deepseek-r1:14b", "deepseek-r1:32b"],
    "azure_openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
    "mistral": ["mixtral-large-latest", "mistral-large-latest", "mistral-small-latest", "ministral-8b-latest"],
    "alibaba": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long"],
    "moonshot": ["moonshot-v1-32k-vision-preview", "moonshot-v1-8k-vision-preview"],
}


# Callback to update the model name dropdown based on the selected provider
def update_model_dropdown(llm_provider, api_key=None, base_url=None):
    """
    Update the model name dropdown with predefined models for the selected provider.
    """
    # Use API keys from .env if not provided
    if not api_key:
        api_key = os.getenv(f"{llm_provider.upper()}_API_KEY", "")
    if not base_url:
        base_url = os.getenv(f"{llm_provider.upper()}_BASE_URL", "")

    # Use predefined models for the selected provider
    if llm_provider in model_names:
        return gr.Dropdown(choices=model_names[llm_provider], value=model_names[llm_provider][0], interactive=True)
    else:
        return gr.Dropdown(choices=[], value="", interactive=True, allow_custom_value=True)


def handle_api_key_error(provider: str, env_var: str):
    """
    Handles the missing API key error by raising a gr.Error with a clear message.
    """
    provider_display = PROVIDER_DISPLAY_NAMES.get(provider, provider.upper())
    raise gr.Error(
        f"💥 {provider_display} API key not found! 🔑 Please set the "
        f"`{env_var}` environment variable or provide it in the UI."
    )


def encode_image(img_path):
    if not img_path:
        return None
    with open(img_path, "rb") as fin:
        image_data = base64.b64encode(fin.read()).decode("utf-8")
    return image_data


def get_latest_files(directory: str, file_types: list = ['.webm', '.zip']) -> Dict[str, Optional[str]]:
    """Get the latest recording and trace files"""
    latest_files: Dict[str, Optional[str]] = {ext: None for ext in file_types}

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return latest_files

    for file_type in file_types:
        try:
            matches = list(Path(directory).rglob(f"*{file_type}"))
            if matches:
                latest = max(matches, key=lambda p: p.stat().st_mtime)
                # Only return files that are complete (not being written)
                if time.time() - latest.stat().st_mtime > 1.0:
                    latest_files[file_type] = str(latest)
        except Exception as e:
            print(f"Error getting latest {file_type} file: {e}")

    return latest_files


async def capture_screenshot(browser_context):
    """Capture and encode a screenshot"""
    # Extract the Playwright browser instance
    playwright_browser = browser_context.browser.playwright_browser  # Ensure this is correct.

    # Check if the browser instance is valid and if an existing context can be reused
    if playwright_browser and playwright_browser.contexts:
        playwright_context = playwright_browser.contexts[0]
    else:
        return None

    # Access pages in the context
    pages = None
    if playwright_context:
        pages = playwright_context.pages

    # Use an existing page or create a new one if none exist
    if pages:
        active_page = pages[0]
        for page in pages:
            if page.url != "about:blank":
                active_page = page
    else:
        return None

    # Take screenshot
    try:
        screenshot = await active_page.screenshot(
            type='jpeg',
            quality=75,
            scale="css"
        )
        encoded = base64.b64encode(screenshot).decode('utf-8')
        return encoded
    except Exception as e:
        return None

class RetryError(Exception):
    """Exception raised when max retries are exceeded"""
    pass

def retry_async(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, 
               exceptions: tuple = (Exception,)) -> Callable:
    """
    Retry decorator for async functions.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay on each retry (default: 2.0)
        exceptions: Tuple of exception types to retry on (default: (Exception,))
    
    Usage:
        @retry_async(max_retries=3, delay=1.0)
        async def my_function():
            # function implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 because we want max_retries attempts after the first try
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts. Final error: {e}")
                        raise RetryError(f"Max retries ({max_retries}) exceeded") from e
                    
                    logger.warning(f"Function {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}: {e}")
                    logger.warning(traceback.format_exc())
                    logger.info(f"Retrying in {current_delay} seconds...")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise RetryError(f"Max retries ({max_retries}) exceeded") from last_exception
            
        return wrapper
    return decorator

def dump_llm_messages_pretty(messages: list[dict[str, str]]) -> str:
	"""
	Serialize a list of LLM messages to a JSON-like string,
	with multiline content strings preserved as per the specific format.
	"""
	output_list_lines = ["["]  # Start of the entire list

	for i, msg_dict in enumerate(messages):
		role_json = json.dumps(msg_dict["role"])

		# Each line of content_input prefixed with two spaces for final output
		content_input = msg_dict["content"]
		indented_content_block = "\n".join(["  " + line for line in content_input.splitlines()])

		# Build the string for a single message dictionary
		message_block_lines = [
			"  {",  # Message object indented by 2 spaces
			f"    \"role\": {role_json},",  # Role indented by 4 spaces
			f"    \"content\": \"\"\"\n{indented_content_block}\n    \"\"\"",  # Content block with specific indentation
			"  }"  # Closing brace of message object, indented by 2
		]

		if i < len(messages) - 1:
			message_block_lines[-1] += ","  # Add comma if not the last message

		output_list_lines.extend(message_block_lines)

	output_list_lines.append("]")  # End of the entire list
	return "\n".join(output_list_lines)

