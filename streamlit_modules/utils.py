from typing import Dict
import streamlit as st
from streamlit_modules.api_calls import save_file, APIError
import json
import uuid


def show_default_text_editor(stage_name: str, file_data: Dict, project_id: int, folder_path: str, jwt_token: str):
    """Общий текстовый редактор для этапов (TXT файлы)."""
    st.subheader(f"Редактирование: {stage_name}")
    
    edited_content = st.text_area(
        "Контент (TXT):",
        value=file_data.get("content", ""),
        height=500,
        key=f"editor_{stage_name}_{project_id}"  # Уникальный ключ
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить", type="primary", key=f"save_{stage_name}"):
            try:
                save_file(jwt_token, stage_name, project_id, edited_content, folder_path)
                st.success("✅ Изменения сохранены.")
                st.rerun()  # Обновляем, чтобы показать свежие данные
            except APIError as e:
                st.error(f"❌ Ошибка сохранения: {e.message}")
            except Exception as e:
                st.error(f"❌ Неожиданная ошибка: {e}")
    with col2:
        if st.button("🔙 Назад", key=f"back_{stage_name}"):
            # Логика возврата (очистка или переключение)
            if 'current_stage_editing' in st.session_state:
                del st.session_state.current_stage_editing
            st.rerun()

# --- Специальный редактор для JSON структуры (для Stage 4, если нужно) ---
def show_structure_editor(stage_name: str, file_data: Dict, project_id: int, folder_path: str, jwt_token: str):
    """Расширенный редактор для JSON-структуры сценария."""
    st.subheader(f"Редактирование JSON: {stage_name}")
    
    try:
        structure_data = json.loads(file_data.get("content", "{}"))
    except json.JSONDecodeError:
        structure_data = {}
    
    # Динамический редактор (серии/главы) — упрощенная версия
    new_data = []
    for idx, serie in enumerate(structure_data.get('content', [])):
        serie_key_prefix = f"serie_{idx}"
        new_serie_name = st.text_input(f"Название серии {serie.get('serie_number', idx+1)}:", 
                                       value=serie.get('serie_name', ''), key=f"{serie_key_prefix}_name")
        new_chapters_list = []
        for ch_idx, chapter in enumerate(serie.get('content', [])):
            chapter_key_prefix = f"{serie_key_prefix}_ch_{ch_idx}"
            new_chapter_name = st.text_input(f"Название главы {chapter.get('chapter_number', ch_idx+1)}:", 
                                             value=chapter.get('chapter_name', ''), key=f"{chapter_key_prefix}_name")
            new_chapter_desc = st.text_area("Описание главы", value=chapter.get('chapter_description', ''), 
                                            key=f"{chapter_key_prefix}_desc", height=100)
            
            st.button("➖ Удалить Главу", key=f"{chapter_key_prefix}_delete")
            new_chapters_list.append({
                "chapter_number": chapter.get('chapter_number'),
                "chapter_name": new_chapter_name,
                "chapter_description": new_chapter_desc
            })
        st.button("➕ Добавить Главу", key=f"{serie_key_prefix}_add_chap")
        new_data.append({
            "serie_number": serie.get('serie_number'),
            "serie_name": new_serie_name,
            "content": new_chapters_list
        })
    
    st.button("➕ Добавить Серию")
    st.divider()
    
    if st.button("💾 Сохранить Структуру", type="primary", key=f"save_struct_{project_id}"):
        final_json = json.dumps(new_data, indent=2, ensure_ascii=False)
        try:
            save_file(jwt_token, stage_name, project_id, final_json, folder_path)
            st.success("✅ Структура сохранена.")
            st.rerun()
        except APIError as e:
            st.error(f"❌ Ошибка: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")