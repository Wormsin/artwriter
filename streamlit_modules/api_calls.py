import streamlit as st
import requests
import os
from typing import Optional, List, Dict

FASTAPI_BASE_URL = os.environ.get('FASTAPI_SERVICE_URL')

class APIError(Exception):
    """Кастомное исключение для ошибок API."""
    def __init__(self, status_code: int, message: str, detail: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(self.message)

def get_protected_headers(jwt_token: str) -> Dict[str, str]:
    """Формирует заголовки с токеном."""
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }

def _handle_response(response: requests.Response, action: str) -> Dict:
    """Общий обработчик ответа: проверка статуса и возврат JSON или ошибка."""
    if response.status_code >= 400:
        try:
            detail = response.json()
            server_message = detail.get("detail", f"Ошибка при {action}.")
            if isinstance(server_message, str):
                error_message = server_message
            elif isinstance(server_message, list) and server_message:
                error_message = server_message[0].get("msg", f"Ошибка при {action}.")
            else:
                 error_message = f"Ошибка при {action}."
                 
        except ValueError:
            # Если ответ не JSON
            detail = {"error": response.text}
            error_message = response.text or f"Ошибка при {action}."
        
        if response.status_code == 401:
            raise APIError(401, "Сессия истекла. Требуется повторный вход.", detail)
        
        raise APIError(response.status_code, error_message, detail)
    
    try:
        return response.json()
    except ValueError:
        return {"status": "ok", "data": response.text}  # Для non-JSON, если нужно

def _make_request(method: str, url: str, jwt_token: str, payload: Optional[Dict] = None, files: Optional[List] = None) -> Dict:
    """Универсальный метод для запроса с обработкой ошибок."""
    headers = get_protected_headers(jwt_token)
    
    try:
        if method.upper() == "GET" and payload:
            # Для GET используем params вместо body
            response = requests.get(url, json=payload, headers=headers)
        elif files:
            # Multipart для файлов
            response = requests.post(url, data=payload if payload else {}, files=files, headers={k: v for k, v in headers.items() if k != "Content-Type"})
        else:
            response = requests.request(method, url, json=payload, headers=headers)
        
        return _handle_response(response, method.lower() + " " + url.split("/")[-1])
    
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу API.")
    except requests.exceptions.RequestException as e:
        raise APIError(500, f"Ошибка сети при запросе: {e}", None)

# --- 1. СОЗДАНИЕ ПРОЕКТА ---
def create_project(jwt_token: str, topic_name: str) -> Dict:
    """Создает новый проект."""
    payload = {"topic_name": topic_name}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/data/projects/create", jwt_token, payload)


# --- 2. ПОЛУЧЕНИЕ ПРОЕКТОВ ---
@st.cache_data(ttl=600)
def get_user_projects(jwt_token: str) -> List[Dict]:
    """Получает список доступных проектов пользователя."""
    return _make_request("GET", f"{FASTAPI_BASE_URL}/data/myprojects", jwt_token)

def share_project_access(jwt_token: str, project_id: int, target_username: str, permission_level: str) -> Dict:
    """Предоставляет доступ к проекту."""
    payload = {"project_id": project_id, "target_username": target_username, "permission_level": permission_level}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/data/projects/share", jwt_token, payload)

# --- 4. WORKFLOWS (LLM) ---
def expand_db(jwt_token: str, folder_path: str, project_id: int, llm_model: str) -> Dict:
    """Расширяет базу данных."""
    payload = {"folder_path": folder_path, "llm_model": llm_model}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/expand", jwt_token, payload)

def find_facts(jwt_token: str, folder_path: str, project_id: int, llm_model: str, facts_type:str) -> Dict:
    """Ищет факты и связи."""
    payload = {"folder_path": folder_path, "llm_model": llm_model, "search_type": facts_type}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/search", jwt_token, payload)

def check_hypothesis(jwt_token: str, folder_path: str, project_id: int, llm_model: str, facts_type: str = "main") -> Dict:
    """Проверяет гипотезы."""
    payload = {"folder_path": folder_path, "llm_model": llm_model, "search_type": facts_type}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/check", jwt_token, payload) 

def create_scenario_structure(jwt_token: str, folder_path: str, project_id: int, num_series: int, llm_model: str) -> Dict:
    """Создает структуру сценария."""
    payload = {"folder_path": folder_path, "llm_model": llm_model, "num_series": num_series}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/workflow/{project_id}/scenario/structure", jwt_token, payload)

def create_scenario(jwt_token: str, folder_path: str, project_id: int, llm_model: str, temperature: float) -> Dict:
    """Создает текст сценария."""
    payload = {"folder_path": folder_path, "llm_model": llm_model, "temperature": temperature}
    return _make_request("POST", f"{FASTAPI_BASE_URL}/workflow/{project_id}/scenario", jwt_token, payload)



# --- 5. ЗАГРУЗКА ФАЙЛОВ ---
def upload_reports_to_api(jwt_token: str, project_id: int, folder_path: str, uploaded_files: List) -> Dict:
    """Загружает отчеты как multipart/form-data."""
    headers = {k: v for k, v in get_protected_headers(jwt_token).items() if k != "Content-Type"}  # Убираем Content-Type для multipart
    files_to_send = [('files', (f.name, f.getvalue(), f.type)) for f in uploaded_files]
    data = {"folder_path": folder_path}
    
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/data/projects/{project_id}/upload-reports",
            data=data,
            files=files_to_send,
            headers=headers
        )
        return _handle_response(response, "upload")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу API.")

# --- 6. РАБОТА С ФАЙЛАМИ ---
def fetch_file(jwt_token: str, stage_name: str, project_id: int, folder_path: str) -> Optional[Dict]:
    """Получает контент файла с сервера."""
    params = {"folder_path": folder_path}
    try:
        return _make_request("GET", f"{FASTAPI_BASE_URL}/files/{project_id}/{stage_name}", jwt_token, payload=params)
    except APIError as e:
        st.error(f"Ошибка при загрузке файла: {e}")
        return None

def save_file(jwt_token: str, stage_name: str, project_id: int, content: str, folder_path: str) -> Dict:
    """Сохраняет обновленный контент на сервере."""
    payload = {"folder_path": folder_path, "stage_name": stage_name, "content": content}
    result = _make_request("POST", f"{FASTAPI_BASE_URL}/files/update/{project_id}", jwt_token, payload)
    st.success("✅ Файл успешно сохранен на сервере!")
    return result


# --- 8. СКАЧИВАНИЕ АРХИВОВ ---
@st.cache_data(ttl=600)
def download_scenario_docx(jwt_token: str, project_id: int, folder_path: str) -> Optional[bytes]:
    """Скачивает ZIP с .docx файлами сценария."""
    params = {"folder_path": folder_path}
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/files/download/scenario/{project_id}",
            json=params,
            headers=get_protected_headers(jwt_token)
        )
        _handle_response(response, action="download zip")
        return response.content
    except APIError as e:
        st.error(f"Ошибка при скачивании файлов сценария: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка сети при скачивании: {e}")
        return None

@st.cache_data(ttl=600)
def download_lens_zip(jwt_token: str, project_id: int, folder_path: str) -> Optional[bytes]:
    """Скачивает ZIP файлов из LENS папки."""
    params = {"folder_path": folder_path}
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/files/download/lens/{project_id}",
            json=params,
            headers=get_protected_headers(jwt_token)
        )
        _handle_response(response, action="download lens zip")
        return response.content
    except APIError as e:
        st.error(f"Ошибка при скачивании LENS архива: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка сети при скачивании: {e}")
        return None
    

def delete_project(jwt_token: str, project_id: int) -> Dict:
    """Удаляет проект и его папку."""
    return _make_request("DELETE", f"{FASTAPI_BASE_URL}/files/project/{project_id}", jwt_token)