import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

# 1. Импорт модулей
from streamlit_modules.auth import show_auth_flow, handle_logout
from streamlit_modules.main_ui import show_main_app
from streamlit_modules.auth import handle_logout

# 2. Инициализация глобального состояния (должна быть самой первой)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'jwt_token' not in st.session_state:
    st.session_state.jwt_token = None
if 'active_project_id' not in st.session_state:
    st.session_state.active_project_id = None
if 'active_project_folder' not in st.session_state:
        st.session_state.active_project_folder = None


# --- ГЛАВНАЯ ЛОГИКА ---

def main():
    st.set_page_config(layout="wide")
    
    # Условное отображение
    if st.session_state.authenticated:
        st.title("🎬 ARTwriter")

        with st.sidebar:
            st.button("🚪 Выйти", on_click=handle_logout, type="secondary")
            st.markdown("---")
        show_main_app()
    else:
        # Если не авторизован: показываем формы входа/регистрации
        show_auth_flow()

if __name__ == "__main__":
    main()