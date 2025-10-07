import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

FASTAPI_BASE_URL = os.environ.get('FASTAPI_SERVICE_URL')

st.set_page_config(layout="wide", page_title="Сценарист API UI")

st.title("🎬 ARTwriter")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛠️ 1. Инициализация Проекта", 
    "📚 2. Расширение БД", 
    "🔍 3. Поиск Фактов", 
    "📝 4. Структура Сценария", 
    "✍️ 5. Написание Сценария"
])

def call_api_endpoint(endpoint_name, payload):
    """Имитирует вызов API и возвращает заглушку-ответ."""
    st.info(f"Имитация POST-запроса к: {endpoint_name}")
    st.json(payload)
    return {"status": "success", "message": f"Функция {endpoint_name} выполнена с параметрами."}

# --- Вкладка 1: Инициализация Проекта ---
with tab1:
    #st.header("Инициализация Проекта")
    st.write("Создает базовую локальную структуру проекта.")
    
    topic_name = st.text_input("Название темы/проекта (topic_name):", value="Морские_Торговые_Пути_1917-1970")
    if st.button("Создать Локальный Проект", key='btn1_init'):
        payload = {"topic_name": topic_name}
        try:
            with st.spinner(f'Создаю проект "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/disk/local/project", json=payload)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Проект '{topic_name}' успешно инициализирован.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")


# --- Вкладка 2: Расширение БД ---
with tab2:
    #st.header("Расширение Базы Данных")
    st.write("Добавляет дополнительную информацию в базу знаний проекта.")

    web= st.checkbox("Enable web search", value=True)
    topic_name = "Морские_Торговые_Пути"
    if st.button("Расширить БД", key='btn2'):
        payload_2 = {
        "topic_name": topic_name,
        "use_websearch": web
    }
        try:
            with st.spinner(f'Собираю данные для проекта "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/workflow/facts/expand", json=payload_2)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Данные успешно собраны.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")


# --- Вкладка 3: Поиск Фактов ---
with tab3:
    #st.header("Поиск Фактов")
    st.write("Ищет неочевидные связи в исторических событиях, стоит гепотезы.")
    topic_name = "Морские_Торговые_Пути"
    payload_3 = {
        "topic_name": topic_name,
        }
    if st.button("Найти Факты", key='btn3'):
        try:
            with st.spinner(f'Ищу факты "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/workflow/facts/search", json=payload_3)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Факты успешно найдены.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")
    
    if st.button("Проверить Факты", key='btn4'):
        try:
            with st.spinner(f'Проверяю факты "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/workflow/facts/check", json=payload_3)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Факты успешно проверены.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")


# --- Вкладка 4: Структура Сценария ---
with tab4:
    #st.header("Написание Структуры Сценария")
    st.write("Генерирует структуру сценария.")
    
    num_acts = st.number_input("Количесво серий:", min_value=1, step=1, format="%d" )
    topic_name = "Морские_Торговые_Пути"
    payload_4 = {
        "topic_name": topic_name,
        "num_series": num_acts
    }

    if st.button("Сгенерировать Структуру", key='btn5'):
        try:
            with st.spinner(f'Создаю структуру "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/workflow/scenario/structure", json=payload_4)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Структура успешно создана.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        


# --- Вкладка 5: Написание Сценария ---
with tab5:
    #st.header("Написание Сценария")
    st.write("Генерирует полный сценарий.")
    
    topic_name = "Морские_Торговые_Пути"
    max_tokens = st.slider("Макс. Токенов для вывода:", min_value=500, max_value=30000, value=10000, key='tokens5', step=500)

    payload_5 = {
        "topic_name": topic_name,
        "max_output_tokens": max_tokens
    }

    if st.button("Написать Сценарий", key='btn6'):
        try:
            with st.spinner(f'Пишу сценарий "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/workflow/scenario", json=payload_5)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                # Обработка успешного ответа
                st.success(f"✅ Сценарий успешно написан.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")
        