import os
from google import genai
from google.genai import types
import pathlib
from dotenv import load_dotenv

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
             web_search = False, thinking = False, temperature=0.7):
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
        top_p=0.8,
        top_k=40,
        max_output_tokens=4096,
        tools=tools,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
)
    response = client.models.generate_content(
        model = model_name,
        contents = content,
        config=config,
    )
    return response.text

def structured_call_llm(prompt,structure, files=None, model_name=MODEL_NAME, temperature=0.7, max_output_tokens=4096):
    content = [prompt]
    if files:
        content.extend(files)
    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=0.8,
        top_k=40,
        max_output_tokens=4096,
        response_schema = structure,
        response_mime_type = 'application/json'
    )
    response = client.models.generate_content(
        model = model_name,
        contents = content,
        config=config,
    )
    return response