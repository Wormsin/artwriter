import streamlit as st
import requests
import os
from streamlit_modules.api_calls import fetch_file, save_file
import json
import uuid

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
        stage_filename = st.session_state.current_stage_editing
        st.success(f"Редактирование: {stage_filename}")
        
        # --- ВЫБОР РЕЖИМА РЕДАКТИРОВАНИЯ ---
        if stage_filename == "structure":
            # Используем специальный редактор для JSON-структуры
            show_structure_editor(stage_filename)
        else:
            # Используем обычный текстовый редактор для других файлов
            show_default_text_editor()

def show_default_text_editor():
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



def show_structure_editor(stage_filename):
    """
    Отображает динамический UI для редактирования JSON-структуры сценария.
    """
    
    st.subheader(f"2. Редактирование (Структура Сценария): {stage_filename}")

    try:
        # 1. Загружаем и парсим JSON из session_state
        # Мы делаем это на каждом реране, чтобы UI всегда был актуальным
        data = json.loads(st.session_state.file_content_editing)
    except json.JSONDecodeError:
        st.error(f"Ошибка: Не удалось распознать JSON в файле '{stage_filename}'.")
        st.warning("Пожалуйста, исправьте файл вручную или очистите его.")
        # Показываем сырой текст для исправления
        show_default_text_editor(stage_filename)
        return

    # --- Callback-функции для изменения структуры ---
    # Эти функции модифицируют 'data', а затем сохраняют 
    # обновленную JSON-строку обратно в 'st.session_state.file_content_editing'.
    # Streamlit автоматически перезапустится, и UI обновится.

    def add_serie_callback():
        new_serie_num = max([s.get('serie_number', 0) for s in data], default=0) + 1
        data.append({
            "serie_number": new_serie_num,
            "serie_name": f"Новая Серия {new_serie_num}",
            "content": [],
            "serie_id": str(uuid.uuid4())
        })
        st.session_state.file_content_editing = json.dumps(data, indent=2, ensure_ascii=False)

    def delete_serie_callback(serie_id, serie_number):
        data[:] = [s for s in data if s.get('serie_id') != serie_id]
        # Переиндексация серий
        if len(data[:]) > 0:
            for idx, s in enumerate(data):
                s['serie_number'] = idx +1
        st.session_state.file_content_editing = json.dumps(data, indent=2, ensure_ascii=False)

    def add_chapter_callback(serie_id):
        for serie in data:
            if serie.get('serie_id') == serie_id:
                new_chap_num = max([c.get('chapter_number', 0) for c in serie['content']], default=0) + 1
                serie['content'].append({
                    "chapter_number": new_chap_num,
                    "chapter_name": f"Новая Глава {new_chap_num}",
                    "chapter_description": "Краткое описание новой главы...",
                    "chapter_id": str(uuid.uuid4())
                })
                break
        st.session_state.file_content_editing = json.dumps(data, indent=2, ensure_ascii=False)

    def delete_chapter_callback(serie_id, chapter_id):
        for serie in data:
            if serie.get('serie_id') == serie_id:
                serie['content'][:] = [c for c in serie['content'] if c.get('chapter_id') != chapter_id]
                if len(serie['content'][:]) > 0:
                    for indx, c in enumerate(serie['content']):
                            c['chapter_number'] = indx +1
                break
        st.session_state.file_content_editing = json.dumps(data, indent=2, ensure_ascii=False)

    # --- UI для Сохранения (Сбор данных) ---
    # Мы будем использовать виджеты для *сбора* данных, а не для их изменения в реальном времени.
    # При нажатии "Сохранить" мы соберем все данные из виджетов и создадим новый JSON.
    
    new_data = [] # Здесь будет собран обновленный JSON

    # --- Цикл рендеринга UI ---
    for i, serie in enumerate(data):
        serie_key_prefix = f"serie_{serie.get('serie_id')}"
        
        with st.expander(f"Серия {serie.get('serie_number', i)}: {serie.get('serie_name', 'Без имени')}", expanded=True):
            
            # Поле для редактирования названия серии
            new_serie_name = st.text_input(
                "Название серии", 
                value=serie.get('serie_name', ''), 
                key=f"{serie_key_prefix}_name"
            )
            
            # Кнопка удаления серии
            st.button(
                "❌ Удалить Серию", 
                key=f"{serie_key_prefix}_delete", 
                on_click=delete_serie_callback, 
                args=(serie.get('serie_id'), serie.get('serie_number'))
            )
            
            st.markdown("---")
            
            new_chapters_list = []
            
            # Цикл по главам внутри серии
            for j, chapter in enumerate(serie.get('content', [])):
                chapter_key_prefix = f"serie_{serie.get('serie_id')}_chap_{chapter.get('chapter_id')}"
                
                st.markdown(f"**Глава {chapter.get('chapter_number', j)}**")
                
                new_chapter_name = st.text_input(
                    "Название главы", 
                    value=chapter.get('chapter_name', ''), 
                    key=f"{chapter_key_prefix}_name"
                )
                
                new_chapter_desc = st.text_area(
                    "Описание главы", 
                    value=chapter.get('chapter_description', ''), 
                    key=f"{chapter_key_prefix}_desc",
                    height=100
                )
                
                st.button(
                    "➖ Удалить Главу", 
                    key=f"{chapter_key_prefix}_delete", 
                    on_click=delete_chapter_callback, 
                    args=(serie.get('serie_id'), chapter.get('chapter_id'))
                )
                st.markdown("---")
                
                # Собираем отредактированные данные главы
                new_chapters_list.append({
                    "chapter_id": chapter.get('chapter_id'),
                    "chapter_number": chapter.get('chapter_number'),
                    "chapter_name": new_chapter_name,
                    "chapter_description": new_chapter_desc
                })

            # Кнопка добавления главы в эту серию
            st.button(
                "➕ Добавить Главу", 
                key=f"{serie_key_prefix}_add_chap", 
                on_click=add_chapter_callback, 
                args=(serie.get('serie_id'),)
            )
            
            # Собираем отредактированные данные серии
            new_data.append({
                "serie_id": serie.get('serie_id'),
                "serie_number": serie.get('serie_number'),
                "serie_name": new_serie_name,
                "content": new_chapters_list
            })

    # Кнопка добавления новой серии
    st.button("➕ Добавить Серию", on_click=add_serie_callback)
    
    st.divider()

    # --- Кнопка Сохранения (Главная) ---
    if st.button("💣 Сохранить Всю Структуру", type="primary", key="save_structure"):
        
        try:
            # Преобразуем собранные данные (new_data) в JSON-строку
            final_json_string = json.dumps(new_data, indent=2, ensure_ascii=False)
            
            # Вызываем API сохранения
            save_file_wrapper(stage_filename, final_json_string)
            
            # Обновляем 'исходный' контент в session_state
            st.session_state.file_content_editing = final_json_string
            st.success("Структура сценария успешно сохранена на сервере!")
            st.rerun() # Перезапускаем, чтобы UI использовал 100% свежие данные
            
        except Exception as e:
            st.error(f"Ошибка при сборке или сохранении JSON: {e}")

# --- ОБЕРТКА ДЛЯ API-ВЫЗОВА SAVE ---
# (Чтобы не дублировать все аргументы)

def save_file_wrapper(stage_filename, content_to_save):
    """Вызывает save_file, используя данные из session_state."""
    save_file(
        stage_name=stage_filename, 
        jwt_token=st.session_state.jwt_token,
        project_id=st.session_state.active_project_id,
        folder_path=st.session_state.active_project_folder,
        content=content_to_save
    )