import streamlit as st
import requests
import os


FASTAPI_BASE_URL = os.environ.get('FASTAPI_SERVICE_URL')

def validate_credentials(username: str, password: str) -> bool:
    """Простая валидация: username не пустой, password >6 символов."""
    if not username or len(username) < 3:
        st.error("Логин должен содержать минимум 3 символа.")
        return False
    if not password or len(password) < 6:
        st.error("Пароль должен содержать минимум 6 символов.")
        return False
    return True


def handle_register(username: str, password: str) -> bool:
    """Обработка регистрации с улучшенной обработкой ошибок."""
    if not validate_credentials(username, password):
        return False

    REGISTER_URL = f"{FASTAPI_BASE_URL}/users/register"
    user_data = {"username": username, "password": password}

    with st.spinner("Регистрация..."):
        try:
            response = requests.post(REGISTER_URL, json=user_data, timeout=10)
            
            if response.status_code == 201:
                st.success("✅ Регистрация прошла успешно! Теперь Вы можете войти.")
                return True
            
            elif response.status_code == 400:
                detail = response.json().get("detail", "Неизвестная ошибка")
                if "already registered" in detail.lower():
                    st.error("❌ Пользователь с таким логином уже существует.")
                else:
                    st.error(f"❌ Ошибка регистрации: {detail}")
                return False
            
            else:
                st.error(f"❌ Неожиданная ошибка при регистрации. Статус: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            st.error("⚠️ Таймаут: Сервер не отвечает. Попробуйте позже.")
            return False
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Ошибка подключения к API. Проверьте, запущен ли FastAPI.")
            return False
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {str(e)}")
            return False

def handle_login(username: str, password: str) -> bool:
    """Обработка логина с улучшенной обработкой ошибок."""
    if not validate_credentials(username, password):
        return False

    TOKEN_URL = f"{FASTAPI_BASE_URL}/users/token"
    login_data = {"username": username, "password": password}

    with st.spinner("Вход в систему..."):
        try:
            response = requests.post(TOKEN_URL, data=login_data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.jwt_token = token_data['access_token']
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Вход успешен! Перезагрузка...")
                st.rerun()  # Перезагружаем для обновления UI
                return True
            
            elif response.status_code == 401:
                st.error("❌ Неверный логин или пароль. Попробуйте снова.")
                return False
            
            else:
                detail = response.json().get("detail", "Неизвестная ошибка")
                st.error(f"❌ Ошибка входа: {detail}")
                return False
                
        except requests.exceptions.Timeout:
            st.error("⚠️ Таймаут: Сервер не отвечает. Попробуйте позже.")
            return False
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Ошибка подключения к API. Убедитесь, что FastAPI запущен.")
            return False
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {str(e)}")
            return False

def handle_logout():
    st.session_state.clear()
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ Вы вышли из системы.")

def handle_jwt_token_expired():
    if not st.session_state.get('authenticated', False) or not st.session_state.get('jwt_token'):
        st.error("❌ Требуется авторизация. Перейдите на страницу входа.")
        st.stop()


def show_auth_flow():
    """Основной flow авторизации с переключением режимов."""
    st.title("🪦 Авторизация")
    
    # Проверяем, аутентифицирован ли уже пользователь
    if st.session_state.get('authenticated', False):
        st.success("👋 Вы уже авторизованы!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Обновить сессию"):
                st.rerun()
        with col2:
            if st.button("🚪 Выйти"):
                handle_logout()
        return  # Выходим, если уже logged in
    
    # Переключение между входом и регистрацией
    auth_mode = st.radio("Выберите режим:", ("Вход", "Регистрация"), horizontal=True, key="auth_mode", label_visibility='collapsed')
    

    if auth_mode == "Вход":
        st.header("🪤 Вход")
        
        with st.form("login_form", clear_on_submit=True):
            login_username = st.text_input("Логин", placeholder="Введите логин", key="login_user")
            login_password = st.text_input("Пароль", type="password", placeholder="Введите пароль", key="login_pass")
            submitted = st.form_submit_button("Войти", use_container_width=True)
            
            if submitted:
                handle_login(login_username, login_password)

    else:
        st.header("🩻 Регистрация")
        
        with st.form("register_form", clear_on_submit=True):
            reg_username = st.text_input("Создайте логин", placeholder="Минимум 3 символа", key="reg_user")
            reg_password = st.text_input("Создайте пароль", type="password", placeholder="Минимум 6 символов", key="reg_pass")
            submitted = st.form_submit_button("Зарегистрироваться", use_container_width=True)
            
            if submitted:
                handle_register(reg_username, reg_password)
