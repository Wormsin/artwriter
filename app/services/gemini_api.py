import os
import logging
from google import genai
from google.genai import types
import pathlib
from dotenv import load_dotenv
import time
import random
from google.api_core.exceptions import ResourceExhausted


logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Set GEMINI_API_KEY environment variable")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash' 


def retry_on_rate_limit(func, *args, max_retries=3, **kwargs):
    """
    Общая функция для обработки ошибок с ретраями для 429.
    Вызывает функцию func с аргументами и возвращает её результат.
    При ошибке 429 выполняет ретраи с экспоненциальной задержкой.
    Если все ретраи исчерпаны, поднимает исключение.
    """
    retries = 0
    base_delay = 5
    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except ResourceExhausted as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Достигнут лимит попыток ({max_retries}). Запрос не выполнен.")
                raise e
            delay = (base_delay * (2 ** (retries - 1))) + random.uniform(0, 1)
            logger.warning(f"Ошибка 429: Лимит запросов исчерпан (Попытка {retries}/{max_retries}). Ждем {delay:.2f} секунд...")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Произошла непредвиденная ошибка: {e}")
            raise e


def upload_files(file_paths):
    uploaded = []
    for path in file_paths:
        path = str(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл не найден: {path}")
        if path.endswith('.txt'):
            mime_type = 'text/plain'
        elif path.endswith('.pdf') :
            mime_type = 'application/pdf'
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {path}. Только .txt или .pdf.")
        file = client.files.upload(file=path, config=dict(mime_type=mime_type))
        uploaded.append(file)
    return uploaded


def upload_small_file(file_path):
    file_path = str(file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    if file_path.endswith('.txt'):
        mime_type = 'text/plain'
    elif file_path.endswith('.pdf') :
        mime_type = 'application/pdf'
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_path}. Только .txt или .pdf.")
    
    filepath = pathlib.Path(file_path)
    file = types.Part.from_bytes(
        data=filepath.read_bytes(),
        mime_type=mime_type,
      )
    return [file]


def _generate_content(model_name, contents, config):
    """Внутренняя функция для генерации контента с обработкой токенов."""
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config,
    )
    if response.usage_metadata:
        total_tokens = response.usage_metadata.total_token_count
        logger.info(f"✅ Генерация завершена. Сгенерировано {len(response.text)} символов.")
        logger.info("--- Использование токенов ---")
        logger.info(f"Входных токенов (Промпт + Файлы): {response.usage_metadata.prompt_token_count}")
        logger.info(f"Выходных токенов (Ответ LLM): {response.usage_metadata.candidates_token_count}")
        logger.info(f"Всего токенов: {total_tokens}")
    else:
        logger.warning("ℹ️ Метаданные об использовании токенов не найдены в ответе.")
        total_tokens = None
    return response, total_tokens


def call_llm(prompt, files=None, model_name=MODEL_NAME, 
             web_search=False, thinking=True, temperature=1, max_output_tokens=10000):
    """
    Вызов LLM с возвратом статуса, ответа и токенов.
    Возвращает: (status: str, response: str or None, tokens: int or None)
    status: 'success' или 'error: description'
    """
    try:
        content = [prompt]
        tools = []
        thinking_budget = 1024 if thinking else 0
        if files:
            content.extend(files)
        if web_search:
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            tools = [grounding_tool]
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=tools,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
        )
        
        # Используем общую функцию ретраев
        response, total_tokens = retry_on_rate_limit(
            _generate_content, model_name, content, config
        )
        
        return "success", response.text, total_tokens
        
    except Exception as e:
        error_msg = f"Ошибка при вызове LLM: {str(e)}"
        logger.error(error_msg)
        return "error: " + error_msg, None, None


def structured_call_llm(prompt, structure, files=None, model_name=MODEL_NAME, temperature=0.7, max_output_tokens=4096):
    """
    Структурированный вызов LLM с возвратом статуса, ответа и токенов.
    Возвращает: (status: str, response: dict or None, tokens: int or None)
    response: распарсенный JSON или None
    """
    try:
        content = [prompt]
        if files:
            content.extend(files)
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_schema=structure,
            response_mime_type='application/json'
        )
        
        # Используем общую функцию ретраев
        response, total_tokens = retry_on_rate_limit(
            _generate_content, model_name, content, config
        )
        
        
        return "success", response, total_tokens
        
    except Exception as e:
        error_msg = f"Ошибка при структурированном вызове LLM: {str(e)}"
        logger.error(error_msg)
        return "error: " + error_msg, None, None