import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

# 1. Импорт модулей
from streamlit_modules.auth import show_auth_flow, handle_logout
from streamlit_modules.main_ui import show_main_app
from streamlit_modules.auth import handle_logout
from streamlit_modules.utils import handle_editing, show_edit_mode, return_to_main_page

# 2. Инициализация глобального состояния (должна быть самой первой)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'jwt_token' not in st.session_state:
    st.session_state.jwt_token = None
if 'active_project_id' not in st.session_state:
    st.session_state.active_project_id = None
if 'active_project_name' not in st.session_state:
    st.session_state.active_project_name = ""
if 'active_project_folder' not in st.session_state:
        st.session_state.active_project_folder = None
if 'current_stage_editing' not in st.session_state:
        st.session_state.current_stage_editing = None
if 'file_content_editing' not in st.session_state:
        st.session_state.file_content_editing = ""
if 'page' not in st.session_state:
        st.session_state.page = "main"


# --- ГЛАВНАЯ ЛОГИКА ---

def main():
    st.set_page_config(layout="wide")
    
    # Условное отображение
    if st.session_state.authenticated:
        st.title("📓 ARTwriter")

        with st.sidebar:
            st.button("🏰 Главная", on_click=return_to_main_page, type="secondary")
            st.button("📜 Редактировать", on_click=handle_editing, type="secondary")
            st.markdown("---")
            st.button("💀 Выйти", on_click=handle_logout, type="secondary")
        if st.session_state.page == "main":
            show_main_app()
        if st.session_state.page == "edit":
            if st.session_state.active_project_id:
                show_edit_mode()
            else:
                st.error("⚠️ **Ошибка доступа к редактированию.**")
                st.warning("Пожалуйста, **создайте** или **выберите** активный проект, прежде чем переходить в режим редактирования файлов.")
                st.session_state.page = "main" 
                st.experimental_rerun()
    else:
        # Если не авторизован: показываем формы входа/регистрации
        show_auth_flow()

if __name__ == "__main__":
    main()