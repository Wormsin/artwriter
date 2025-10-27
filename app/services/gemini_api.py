import os
from google import genai
from google.genai import types
import pathlib
from dotenv import load_dotenv
import time
import random
from google.api_core.exceptions import ResourceExhausted
load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Set GEMINI_API_KEY environment variable")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash' 

def upload_files(file_paths):
    uploaded = []
    for path in file_paths:
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


def call_llm(prompt, files=None, model_name=MODEL_NAME, 
             web_search = False, thinking = True, temperature=1, max_output_tokens=10000):
    content = [prompt]
    tools = []
    thinking_budget = 1024
    if files:
        content.extend(files)
    if web_search:
        grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
        )
        tools = [grounding_tool]
    if not thinking:
        thinking_budget=0
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=tools,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
)
    max_retries = 5
    base_delay=5
    retries = 0
    while retries < max_retries:
        try:
            response = client.models.generate_content(
                model = model_name,
                contents = content,
                config=config,
            )
            return response.text
        except ResourceExhausted as e:
            # Перехватываем ошибку 429
            print(f"Ошибка 429: Лимит запросов исчерпан (Попытка {retries + 1}/{max_retries}).")
            
            if retries == max_retries - 1:
                print("Достигнут лимит попыток. Запрос не выполнен.")
                raise e
            # Расчет времени ожидания: base_delay * (2^retries) + (0-1 сек "джиттера")
            # "Джиттер" (случайная добавка) помогает избежать "стадного эффекта",
            # когда все клиенты повторяют запрос в одно и то же время.
            delay = (base_delay * (2 ** retries)) + random.uniform(0, 1)
            
            print(f"Ждем {delay:.2f} секунд перед следующей попыткой...")
            time.sleep(delay)
            
            # Увеличиваем счетчик попыток
            retries += 1
            
        except Exception as e:
            # Обработка других, не связанных с лимитами, ошибок
            print(f"Произошла непредвиденная ошибка: {e}")
            # При других ошибках (например, ошибка аутентификации) повторять нет смысла
            break

def structured_call_llm(prompt,structure, files=None, model_name=MODEL_NAME, temperature=0.7, max_output_tokens=4096):
    content = [prompt]
    if files:
        content.extend(files)
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_schema = structure,
        response_mime_type = 'application/json'
    )
    response = client.models.generate_content(
        model = model_name,
        contents = content,
        config=config,
    )
    if response.usage_metadata:
        # 2. Извлечение числа токенов для ОТВЕТА (выходные токены)
        output_tokens = response.usage_metadata.candidates_token_count
        # 3. Извлечение числа токенов для ПРОМПТА (входные токены)
        input_tokens = response.usage_metadata.prompt_token_count
        # 4. Извлечение общего числа токенов
        total_tokens = response.usage_metadata.total_token_count
        print(f"✅ Генерация завершена. Сгенерировано {len(response.text)} символов.")
        print("--- Использование токенов ---")
        print(f"Входных токенов (Промпт + Файлы): {input_tokens}")
        print(f"Выходных токенов (Ответ LLM): {output_tokens}")
        print(f"Всего токенов: {total_tokens}")
    else:
        print("ℹ️ Метаданные об использовании токенов не найдены в ответе.")
    return response