# streamlit_modules/api_calls.py
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

# --- 1. СОЗДАНИЕ ПРОЕКТА ---
def create_project(jwt_token: str, topic_name: str) -> Dict:
    payload = {"topic_name": topic_name}
    headers = get_protected_headers(jwt_token)

    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/data/projects/create", 
            json=payload, 
            headers=headers
        )
        
        # Если статус 4xx/5xx, поднимаем исключение APIError
        if response.status_code >= 400:
            detail = response.json()
            # Особая обработка 401 для удобства в UI
            if response.status_code == 401:
                 raise APIError(401, "Недействительный или просроченный токен.", detail)
            
            raise APIError(response.status_code, "Ошибка при создании проекта.", detail)
        
        # Если статус 2xx, возвращаем результат
        return response.json()

    except requests.exceptions.ConnectionError:
        # Для ошибок соединения поднимаем стандартное исключение
        raise ConnectionError("Не удалось подключиться к серверу API.")


# --- 2. ПОЛУЧЕНИЕ ПРОЕКТОВ ---
@st.cache_data(ttl=600)
def get_user_projects(jwt_token: str) -> List[Dict]:
    PROJECTS_URL = f"{FASTAPI_BASE_URL}/data/myprojects" # Исправил /data/myprojects на /data/projects/my
    headers = get_protected_headers(jwt_token)

    try:
        response = requests.get(PROJECTS_URL, headers=headers)
        
        if response.status_code >= 400:
            detail = response.json()
            if response.status_code == 401:
                 raise APIError(401, "Сессия истекла. Требуется повторный вход.", detail)
            
            raise APIError(response.status_code, "Ошибка при загрузке проектов.", detail)
            
        return response.json()
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу API.")

def share_project_access(jwt_token: str, project_id: int, target_username: str, permission_level: str):
    payload = {"project_id": project_id, "target_username":target_username, "permission_level":permission_level}
    headers = get_protected_headers(jwt_token)
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/data/projects/share", 
            json=payload, 
            headers=headers
        )
        if response.status_code >= 400:
            detail = response.json()
            # Особая обработка 401 для удобства в UI
            if response.status_code == 401:
                 raise APIError(401, "Недействительный или просроченный токен.", detail)
            
            raise APIError(response.status_code, "Ошибка при создании проекта.", detail)
        
        # Если статус 2xx, возвращаем результат
        return response.json()

    except requests.exceptions.ConnectionError:
        # Для ошибок соединения поднимаем стандартное исключение
        raise ConnectionError("Не удалось подключиться к серверу API.")




def expand_db(jwt_token: str, folder_path: str, project_id:int):
    payload = {
        "folder_path": folder_path
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/expand", json=payload, headers=headers)
        response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        raise
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        raise
    except Exception as e:
        st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        raise

def search_facts(jwt_token: str, folder_path: str,  project_id:int):
    payload = {
        "folder_path": folder_path
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/search", json=payload, headers=headers)
        response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        raise
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        raise
    except Exception as e:
        st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        raise

def check_facts(jwt_token: str, folder_path: str,  project_id:int):
    payload = {
        "folder_path": folder_path,
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/workflow/{project_id}/facts/check", json=payload, headers=headers)
        response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        raise
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        raise
    except Exception as e:
        st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        raise

def generate_structure(jwt_token: str, folder_path: str,  project_id:int, num_series: int):
    payload = {
        "folder_path": folder_path,
        "num_series": num_series
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/workflow/{project_id}/scenario/structure", json=payload, headers=headers)
        response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        raise
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        raise
    except Exception as e:
        st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        raise

def write_scenario(jwt_token: str, folder_path: str,  project_id:int, max_output_tokens: int):
    payload = {
        "folder_path": folder_path,
        "max_output_tokens": max_output_tokens
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json" 
    }
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/workflow/{project_id}/scenario", json=payload, headers=headers)
        response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        raise
    except requests.exceptions.ConnectionError:
        st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        raise
    except Exception as e:
        st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        raise


def upload_reports_to_api(jwt_token: str, project_id: int, folder_path:str, uploaded_files: List) -> Dict:
    headers = {
        "Authorization": f"Bearer {jwt_token}",
    }

    files_to_send = []
    for f in uploaded_files:
        files_to_send.append(('files', (f.name, f.getvalue(), f.type)))

    data = {"folder_path": folder_path}

    try:
        # requests автоматически обрабатывает 'data' и 'files' как multipart/form-data
        response = requests.post(f"{FASTAPI_BASE_URL}/data/projects/{project_id}/upload-reports", headers=headers, data = data, files=files_to_send)
        
        if response.status_code >= 400:
            detail = response.json()
            if response.status_code == 401:
                 raise APIError(401, "Сессия истекла. Требуется повторный вход.", detail)
            
            raise APIError(response.status_code, "Ошибка при загрузке файлов.", detail)
        
        return response.json()

    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу API.")