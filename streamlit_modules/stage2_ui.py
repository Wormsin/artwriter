import streamlit as st
from streamlit_modules.api_calls import (
    find_facts, check_hypothesis, get_algorithms, fetch_file, APIError
)
from streamlit_modules.utils import show_default_text_editor  # Импорт общей функции редактора

def show_facts_ui():
    """UI для этапа поиска связей (Stage 2)."""
    st.header("⛓️ Поиск Связей (Stage 2)")
    st.success(f"Активный проект: {st.session_state.active_project_name}")
    st.write("Ищет неочевидные связи в исторических событиях, стоит гипотезы.")

    # Инициализация session_state для алгоритма
    if 'selected_algorithm' not in st.session_state:
        st.session_state.selected_algorithm = None

    algs = ["MAIN", "BLIND SPOTS"]
    st.session_state.selected_algorithm = st.radio(
    "Доступные опции:",
    algs,
    index=0,  # Выбран по умолчанию первый элемент
    key="bullet_selection")

    # Выбор алгоритма из списка
    if st.session_state.selected_algorithm:
        selected_algorithm = st.session_state.selected_algorithm
        # Выбор модели и запуск поиска
        selected_llm = st.selectbox("Модель LLM:", options=st.session_state.GEMINI_MODELS, key="search_model")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🚀 Запустить Поиск ({selected_algorithm})"):
                try:
                    with st.spinner(f"Поиск связей с {selected_algorithm}..."):
                        # facts_type на основе алгоритма (ALG_MAIN -> "main", ALG_BLIND -> "blind_spots")
                        facts_type = "main" if "MAIN" in selected_algorithm else "blind_spots"
                        result = find_facts(st.session_state.jwt_token, st.session_state.active_project_folder,
                                            st.session_state.active_project_id, selected_llm, facts_type)
                    st.success("✅ Факты найдены.")
                    st.json(result)
                except APIError as e:
                    st.error(f"❌ Ошибка поиска: {e.message}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
        with col2:
            if st.button("🔍 Проверить Факты"):
                try:
                    facts_type = "main" if "MAIN" in st.session_state.selected_algorithm else "blind_spots"
                    with st.spinner("Проверка фактов..."):
                        result = check_hypothesis(st.session_state.jwt_token, st.session_state.active_project_folder,
                                                  st.session_state.active_project_id, selected_llm, facts_type) 
                    st.success("✅ Факты проверены.")
                    st.json(result)
                except APIError as e:
                    st.error(f"❌ Ошибка проверки: {e.message}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")

    # Раздел редактирования и проверки (после поиска)
    st.divider()
    st.subheader("✏️ Редактирование и Проверка")
    
    if st.session_state.selected_algorithm:
        # Radio для RAW/CHECKED
        edit_mode = st.radio("Режим редактирования:", ["RAW (Сырые Факты)", "CHECKED (Проверенные Факты)"], key="edit_mode")
        
        # Определение stage_name на основе алгоритма и режима
        if "MAIN" in st.session_state.selected_algorithm:
            stage_name = "interesting_facts_main" if edit_mode == "RAW (Сырые Факты)" else "check_facts_main"
        else:
            stage_name = "interesting_facts_blind" if edit_mode == "RAW (Сырые Факты)" else "check_facts_blind"
        
        
        if st.session_state.file_content_editing is None:
            if st.button("Редактировать Файл"):
                    file_data = fetch_file(st.session_state.jwt_token, stage_name, st.session_state.active_project_id,
                                        st.session_state.active_project_folder)
                    if file_data:
                        st.session_state.file_content_editing = file_data.get("content", "")
                        st.rerun()
                    else:
                        st.warning("Файл не найден. Сначала найдите факты.")
        else:
            show_default_text_editor(
                stage_name=stage_name,
                project_id=st.session_state.active_project_id,
                folder_path=st.session_state.active_project_folder,
                jwt_token=st.session_state.jwt_token
            )  
    else:
        st.info("Сначала выберите алгоритм.")