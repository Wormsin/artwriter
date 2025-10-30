import streamlit as st
from streamlit_modules.api_calls import (
    create_scenario_structure, fetch_file, save_file, APIError
)
from streamlit_modules.utils import show_structure_editor  # Импорт специального редактора

def show_structure_ui():
    """UI для этапа структуры сценария (Stage 4)."""
    st.header("🦴 Структура Сценария (Stage 4)")
    st.success(f"Активный проект: {st.session_state.active_project_name}")
    st.write("Генерирует структуру сценария (серии и главы).")

    # Выбор модели и параметров
    selected_llm = st.selectbox("Модель LLM:", options=st.session_state.GEMINI_MODELS, key="struct_model")
    num_series = st.number_input("Количество серий:", min_value=1, max_value=10, value=3, step=1)

    if st.button("🚀 Сгенерировать Структуру"):
        try:
            with st.spinner("Генерация структуры..."):
                result = create_scenario_structure(st.session_state.jwt_token, st.session_state.active_project_folder,
                                                   st.session_state.active_project_id, num_series, selected_llm)
            st.success("✅ Структура сгенерирована.")
            st.json(result)
        except APIError as e:
            st.error(f"❌ Ошибка: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")

    # Раздел редактирования (в самом низу)
    st.divider()
    st.subheader("✏️ Редактирование script_structure.json")
    if st.button("Редактировать Структуру"):
        try:
            file_data = fetch_file(st.session_state.jwt_token, "structure", st.session_state.active_project_id,
                                   st.session_state.active_project_folder)
            if file_data:
                show_structure_editor(
                    stage_name="structure",
                    file_data=file_data,
                    project_id=st.session_state.active_project_id,
                    folder_path=st.session_state.active_project_folder,
                    jwt_token=st.session_state.jwt_token
                )
            else:
                st.warning("Структура не найдена. Сгенерируйте сначала.")
        except APIError as e:
            st.error(f"❌ Ошибка загрузки: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")