import streamlit as st
import requests
import os


FASTAPI_BASE_URL = os.environ.get('FASTAPI_SERVICE_URL')

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
            
        elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
            st.error("❌ Пользователь с таким логином уже существует.")
            
        else:
            st.error(f"Произошла ошибка при регистрации. Статус: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Ошибка подключения к API. Проверьте, запущен ли FastAPI.")

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

def handle_logout():
    st.session_state.authenticated = False
    st.session_state.jwt_token = None
    st.session_state.active_project_name = None
    st.session_state.active_project_id = None
    st.rerun()

def show_auth_flow():
    st.title("🔑 Авторизация")
    
    # Переключение между входом и регистрацией
    auth_mode = st.radio("Выберите действие:", ("Вход", "Регистрация"), horizontal=True)

    if auth_mode == "Вход":
        st.header("Вход в систему")
        
        with st.form("login_form"):
            login_username = st.text_input("Логин", key="login_user")
            login_password = st.text_input("Пароль", type="password", key="login_pass")
            submitted = st.form_submit_button("Войти")
            
            if submitted:
                handle_login(login_username, login_password)

    else:
        st.header("Регистрация")
        
        with st.form("register_form"):
            reg_username = st.text_input("Создайте Логин", key="reg_user")
            reg_password = st.text_input("Создайте Пароль", type="password", key="reg_pass")
            submitted = st.form_submit_button("Зарегистрироваться")
            
            if submitted:
                handle_register(reg_username, reg_password)