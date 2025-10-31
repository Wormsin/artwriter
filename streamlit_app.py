import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

# 1. Импорт модулей
from streamlit_modules.auth import show_auth_flow, handle_logout
from streamlit_modules.main_ui import show_main_app
from streamlit_modules.stage1_ui import show_expand_db_ui
from streamlit_modules.stage2_ui import show_facts_ui
from streamlit_modules.stage3_ui import show_structure_ui
from streamlit_modules.stage4_ui import show_scenario_ui

# 2. Инициализация глобального состояния (только используемые)
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
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "projects"  # Дефолт: проекты
if 'GEMINI_MODELS' not in st.session_state:
    st.session_state.GEMINI_MODELS = ["gemini-2.5-flash", 
    "gemini-2.5-pro", 
    "gemini-2.5-flash-lite",
    "gemini-2.5-nano"]
if "file_content_editing" not in st.session_state:
    st.session_state.file_content_editing = None
    

# --- ГЛАВНАЯ ЛОГИКА ---

def main():
    st.set_page_config(layout="wide")
    
    # Условное отображение
    if st.session_state.authenticated:
        st.title("📓 ARTwriter")

        # Sidebar с навигацией по этапам
        with st.sidebar:
            st.header("📋 Навигация")
            
            # Кнопка Главная (проекты)
            if st.button("🏠 Главная (Проекты)", key="nav_projects"):
                st.session_state.file_content_editing = None
                st.session_state.current_stage = "projects"
                st.rerun()
            
            st.markdown("---")
            st.header("Этапы Workflow")
            
            # Кнопки для этапов
            if st.button("📊 Этап 1: Расширение БД", key="nav_expand_db"):
                st.session_state.file_content_editing = None
                st.session_state.current_stage = "expand_db"
                st.rerun()
            
            if st.button("🔍 Этап 2: Поиск Связей", key="nav_facts_search"):
                st.session_state.file_content_editing = None
                st.session_state.current_stage = "facts_search"
                st.rerun()
            
            if st.button("📋 Этап 4: Структура Сценария", key="nav_structure"):
                st.session_state.file_content_editing = None
                st.session_state.current_stage = "structure"
                st.rerun()
            
            if st.button("✍️ Этап 5: Написание Сценария", key="nav_scenario"):
                st.session_state.file_content_editing = None
                st.session_state.current_stage = "scenario"
                st.rerun()
            
            st.markdown("---")
            st.button("💀 Выйти", on_click=handle_logout, type="secondary")
        
        # Вызов UI в зависимости от current_stage
        if st.session_state.current_stage == "projects":
            show_main_app()  # Показывает вкладки проектов/шаринга
        elif st.session_state.current_stage == "expand_db":
            show_expand_db_ui()
        elif st.session_state.current_stage == "facts_search":
            show_facts_ui()
        elif st.session_state.current_stage == "structure":
            show_structure_ui()
        elif st.session_state.current_stage == "scenario":
            show_scenario_ui()
        else:
            st.error("Неизвестный этап.")
            st.session_state.current_stage = "projects"
            st.rerun()
    else:
        # Если не авторизован: показываем формы входа/регистрации
        show_auth_flow()

if __name__ == "__main__":
    main()