from typing import Dict
import streamlit as st
from streamlit_modules.api_calls import save_file, APIError
import json
import uuid


def show_default_text_editor(stage_name: str, project_id: int, folder_path: str, jwt_token: str):
    """Общий текстовый редактор для этапов (TXT файлы)."""
    st.subheader(f"Редактирование: {stage_name}")
    
    edited_content = st.text_area(
        "Контент (TXT):",
        value=st.session_state.file_content_editing,
        height=500,
        key=f"editor_{stage_name}_{project_id}"  # Уникальный ключ
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить", type="primary", key=f"save_{stage_name}"):
            try:
                result = save_file(jwt_token, stage_name, project_id, edited_content, folder_path)
                st.success("✅ Изменения сохранены.")
                st.json(result)
                st.session_state.file_content_editing = edited_content
                st.rerun()
            except APIError as e:
                st.error(f"❌ Ошибка сохранения: {e.message}")
            except Exception as e:
                st.error(f"❌ Неожиданная ошибка: {e}")
    with col2:
        if st.button("🔙 Назад", key=f"back_{stage_name}"):
            # Логика возврата (очистка или переключение)
            st.session_state.file_content_editing = None
            st.rerun()

# --- Специальный редактор для JSON структуры (для Stage 4, если нужно) ---
def show_structure_editor(stage_name: str,  project_id: int, folder_path: str, jwt_token: str):
    """Расширенный редактор для JSON-структуры сценария."""
    st.subheader(f"Редактирование JSON: {stage_name}")
    
    try:
        data = json.loads(st.session_state.file_content_editing)
    except json.JSONDecodeError:
        st.error(f"Ошибка: Не удалось распознать JSON в файле.")
        st.warning("Пожалуйста, исправьте файл вручную или очистите его.")
        show_default_text_editor(stage_name,  project_id, folder_path, jwt_token)
        return
    
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

    col1, col2 = st.columns(2)
    # --- Кнопка Сохранения (Главная) ---
    with col1:
        if st.button("💣 Сохранить Всю Структуру", type="primary", key="save_structure"):
            
            try:
                # Преобразуем собранные данные (new_data) в JSON-строку
                final_json_string = json.dumps(new_data, indent=2, ensure_ascii=False)
                
                # Вызываем API сохранения
                save_file(jwt_token, stage_name, project_id, final_json_string, folder_path)
                
                # Обновляем 'исходный' контент в session_state
                st.session_state.file_content_editing = final_json_string
                st.success("Структура сценария успешно сохранена на сервере!")
                st.rerun() # Перезапускаем, чтобы UI использовал 100% свежие данные
                
            except Exception as e:
                st.error(f"Ошибка при сборке или сохранении JSON: {e}")
    
    with col2:
        if st.button("🔙 Назад", key=f"back_{stage_name}"):
            # Логика возврата (очистка или переключение)
            st.session_state.file_content_editing = None
            st.rerun()