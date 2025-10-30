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
    if 'algorithms_list' not in st.session_state:
        st.session_state.algorithms_list = []

    # Кнопка для получения списка алгоритмов
    if st.button("📋 Получить Список Алгоритмов"):
        try:
            with st.spinner("Загрузка алгоритмов..."):
                result = get_algorithms(st.session_state.jwt_token, st.session_state.active_project_id,
                                        st.session_state.active_project_folder)
            st.session_state.algorithms_list = result
            st.success("✅ Список алгоритмов загружен.")
            st.write("Доступные алгоритмы:", st.session_state.algorithms_list)
        except APIError as e:
            st.error(f"❌ Ошибка загрузки алгоритмов: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")

    # Выбор алгоритма из списка
    if st.session_state.algorithms_list:
        selected_algorithm = st.selectbox("Выберите алгоритм:", st.session_state.algorithms_list, key="alg_selector")
        st.session_state.selected_algorithm = selected_algorithm

        # Выбор модели и запуск поиска
        selected_llm = st.selectbox("Модель LLM:", options=st.session_state.GEMINI_MODELS, key="search_model")
        if st.button(f"🚀 Запустить Поиск ({selected_algorithm})"):
            try:
                with st.spinner(f"Поиск связей с {selected_algorithm}..."):
                    # facts_type на основе алгоритма (ALG_MAIN -> "main", ALG_BLIND -> "blind_spots")
                    facts_type = "main" if "MAIN" in selected_algorithm else "blind_spots"
                    result = find_facts(st.session_state.jwt_token, st.session_state.active_project_folder,
                                        st.session_state.active_project_id, selected_llm)
                st.success("✅ Факты найдены.")
                st.json(result)
            except APIError as e:
                st.error(f"❌ Ошибка поиска: {e.message}")
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
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Редактировать Файл"):
                try:
                    file_data = fetch_file(st.session_state.jwt_token, stage_name, st.session_state.active_project_id,
                                           st.session_state.active_project_folder)
                    if file_data:
                        show_default_text_editor(
                            stage_name=stage_name,
                            file_data=file_data,
                            project_id=st.session_state.active_project_id,
                            folder_path=st.session_state.active_project_folder,
                            jwt_token=st.session_state.jwt_token
                        )
                    else:
                        st.warning("Файл не найден. Запустите поиск сначала.")
                except APIError as e:
                    st.error(f"❌ Ошибка загрузки файла: {e.message}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
        
        with col2:
            if st.button("🔍 Проверить Факты"):
                try:
                    facts_type = "main" if "MAIN" in st.session_state.selected_algorithm else "blind_spots"
                    with st.spinner("Проверка фактов..."):
                        result = check_hypothesis(st.session_state.jwt_token, st.session_state.active_project_folder,
                                                  st.session_state.active_project_id, st.session_state.GEMINI_MODELS[0], facts_type)  # Default LLM
                    st.success("✅ Факты проверены.")
                    st.json(result)
                except APIError as e:
                    st.error(f"❌ Ошибка проверки: {e.message}")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
    else:
        st.info("Сначала выберите алгоритм.")