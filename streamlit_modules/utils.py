import streamlit as st
import requests
import os
from streamlit_modules.api_calls import fetch_file, save_file

STAGE_BUTTONS = ["ДОП. ФАКТЫ", "НЕОЧЕВИДНЫЕ СВЯЗИ", "ПРОВЕРКА СВЯЗЕЙ", "СТРУКТУРА"]
EDITING_STAGES ={"ДОП. ФАКТЫ": "plus_facts", 
                 "НЕОЧЕВИДНЫЕ СВЯЗИ": "interesting_facts", 
                 "ПРОВЕРКА СВЯЗЕЙ": "check_facts", 
                 "СТРУКТУРА": "structure"}

def handle_editing():
    st.session_state.page = "edit"

def return_to_main_page():
    st.session_state.page = "main"
    st.session_state.file_content_editing = ""
    st.session_state.current_stage_editing = None


def show_edit_mode():
    """Основная страница редактирования файлов."""
    st.subheader("Редактирование Файлов Сценария")
    
    # Кнопки в несколько колонок
    cols = st.columns(len(STAGE_BUTTONS))
    for col, stage in zip(cols, STAGE_BUTTONS):
        if col.button(stage, use_container_width=True):
            st.session_state.current_stage_editing = EDITING_STAGES[stage]
            # Получаем контент при нажатии на кнопку
            file_data = fetch_file(stage_name=st.session_state.current_stage_editing, 
                                   jwt_token=st.session_state.jwt_token,
                                   project_id=st.session_state.active_project_id,
                                   folder_path=st.session_state.active_project_folder)
            if file_data:
                st.session_state.file_content_editing = file_data.get("content", "")
            else:
                st.session_state.file_content_editing = "" # На случай ошибки
            st.rerun() # Перезапуск для обновления интерфейса


    # --- Блок редактирования и сохранения ---
    if st.session_state.current_stage_editing:
        
        st.divider()
        st.success(f"Редактирование: {stage}")
        
        # Виджет для редактирования текста
        edited_content = st.text_area(
            "Редактируйте содержимое (TXT-файл)",
            value=st.session_state.file_content_editing,
            height=500,
            key=f"editor_area_{st.session_state.current_stage_editing}"
        )
        
        # Кнопка сохранения
        if st.button("💣 Сохранить Изменения", type="primary"):

            save_file(stage_name=st.session_state.current_stage_editing, 
                                   jwt_token=st.session_state.jwt_token,
                                   project_id=st.session_state.active_project_id,
                                   folder_path=st.session_state.active_project_folder,
                                   content=edited_content)
            # Обновляем состояние после сохранения, чтобы пользователь видел новый текст
            st.session_state.file_content_editing = edited_content