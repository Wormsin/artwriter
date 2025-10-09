import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

FASTAPI_BASE_URL = os.environ.get('FASTAPI_SERVICE_URL')
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'jwt_token' not in st.session_state:
    st.session_state.jwt_token = None
if 'active_project_name' not in st.session_state:
    st.session_state.active_project_name = None


def show_login_form():
    st.title("🔑 Авторизация")
    
    # Переключение между входом и регистрацией
    auth_mode = st.radio("Выберите действие:", ("Вход", "Регистрация"), horizontal=True)

    if auth_mode == "Вход":
        # -----------------------------------
        # А. ФОРМА ВХОДА (Уже была)
        # -----------------------------------
        st.header("Вход в систему")
        
        with st.form("login_form"):
            login_username = st.text_input("Логин", key="login_user")
            login_password = st.text_input("Пароль", type="password", key="login_pass")
            submitted = st.form_submit_button("Войти")
            
            if submitted:
                handle_login(login_username, login_password)

    else:
        # -----------------------------------
        # Б. ФОРМА РЕГИСТРАЦИИ (Новая)
        # -----------------------------------
        st.header("Регистрация")
        
        with st.form("register_form"):
            reg_username = st.text_input("Создайте Логин", key="reg_user")
            reg_password = st.text_input("Создайте Пароль", type="password", key="reg_pass")
            submitted = st.form_submit_button("Зарегистрироваться")
            
            if submitted:
                handle_register(reg_username, reg_password)


# --- ФУНКЦИЯ ОБРАБОТКИ РЕГИСТРАЦИИ ---
def handle_register(username, password):
    if not username or not password:
        st.error("Пожалуйста, заполните оба поля.")
        return

    REGISTER_URL = f"{FASTAPI_BASE_URL}/users/users/register"
    
    # FastAPI ожидает JSON для ручки регистрации
    user_data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(REGISTER_URL, json=user_data)
        
        if response.status_code == 201:
            st.success("✅ Регистрация прошла успешно! Теперь Вы можете войти.")
            # st.rerun() # Не обязательно, но может вернуть пользователя на форму входа
            
        elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
            st.error("❌ Пользователь с таким логином уже существует.")
            
        else:
            st.error(f"Произошла ошибка при регистрации. Статус: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Ошибка подключения к API. Проверьте, запущен ли FastAPI.")

# --- ФУНКЦИЯ ОБРАБОТКИ ВХОДА (для чистоты кода) ---
def handle_login(username, password):
    TOKEN_URL = f"{FASTAPI_BASE_URL}/users/token"
    login_data = {"username": username, "password": password}
            
    try:
        response = requests.post(TOKEN_URL, data=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.jwt_token = token_data['access_token']
            st.session_state.authenticated = True
            st.success("Вход успешен! Загрузка функционала...")
            st.rerun() 
        else:
            st.error("Неверный логин или пароль.")
            st.session_state.authenticated = False
            
    except requests.exceptions.ConnectionError:
        st.error("Ошибка подключения к API. Убедитесь, что FastAPI запущен.")




if not st.session_state.authenticated:
    
    show_login_form()

else:
    is_project_active = st.session_state.active_project_name is not None

    st.set_page_config(layout="wide", page_title="Сценарист API UI")
    st.title("🎬 ARTwriter")

    st.header("🛠️ Шаг 1: Выбор или Создание Проекта")
    st.write("Создает базовую локальную структуру проекта.")

    topic_name = st.text_input("Название темы/проекта (topic_name):", value="Морские_Торговые_Пути_1917-1970")
    if st.button("Создать Локальный Проект", key='btn1_init'):
        payload = {"topic_name": topic_name}
        try:
            with st.spinner(f'Создаю проект "{topic_name}"...'):
                
                # Отправка POST-запроса
                response = requests.post(f"{FASTAPI_BASE_URL}/disk/local/project", json=payload)
                response.raise_for_status() # Вызовет ошибку для HTTP 4xx/5xx
                
                st.session_state.active_project_name = topic_name
                is_project_active = st.session_state.active_project_name is not None
                st.success(f"✅ Проект '{topic_name}' успешно инициализирован.")
                st.json(response.json()) # Показать ответ от FastAPI
                
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Ошибка HTTP: Проверьте логи FastAPI. {e}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Ошибка соединения: Убедитесь, что ваш FastAPI запущен и доступен.")
        except Exception as e:
            st.error(f"❌ Произошла непредвиденная ошибка: {e}")

    st.markdown("---")







    if is_project_active:
        st.success(f"Активный проект: {st.session_state.active_project_name}. Доступны следующие шаги.")
        
        tab2, tab3, tab4, tab5 = st.tabs([
            "📚 2. Расширение БД", 
            "🔍 3. Поиск Фактов", 
            "📝 4. Структура Сценария", 
            "✍️ 5. Написание Сценария"
        ])

        # --- Вкладка 2: Расширение БД ---
        with tab2:
            #st.header("Расширение Базы Данных")
            st.write("Добавляет дополнительную информацию в базу знаний проекта.")

            web= st.checkbox("Enable web search", value=True) 
            if st.button("Расширить БД", key='btn2'):
                payload_2 = {
                "topic_name": st.session_state.active_project_name ,
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
            payload_3 = {
                "topic_name": st.session_state.active_project_name ,
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
            payload_4 = {
                "topic_name": st.session_state.active_project_name ,
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
            
            max_tokens = st.slider("Макс. Токенов для вывода:", min_value=500, max_value=30000, value=10000, key='tokens5', step=500)

            payload_5 = {
                "topic_name": st.session_state.active_project_name ,
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
        