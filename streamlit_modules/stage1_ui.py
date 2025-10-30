import streamlit as st
from streamlit_modules.api_calls import expand_db, fetch_file, upload_reports_to_api, APIError
from streamlit_modules.utils import show_default_text_editor  # Импорт общей функции редактора

def show_expand_db_ui():
    """UI для этапа расширения БД (Stage 1)."""
    st.header("📊 Расширение Базы Данных (Stage 1)")
    
    # Загрузка файлов для отчета
    uploaded_files = st.file_uploader("Загрузите отчеты (PDF/TXT):", accept_multiple_files=True, type=["pdf", "txt"])
    if uploaded_files and st.button(f"Загрузить {len(uploaded_files)} файл(ов) в проект"):
        try:
            with st.spinner(f"Загрузка {len(uploaded_files)} файлов..."):
                result = upload_reports_to_api(
                    st.session_state.jwt_token,
                    st.session_state.active_project_id,
                    st.session_state.active_project_folder,
                    uploaded_files
                )
            st.success(f"✅ Файлы загружены. Успешно: {len([r for r in result.get('results', []) if r['status'] == 'success'])}")
            st.json(result)
        except APIError as e:
            st.error(f"❌ Ошибка загрузки: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")
    
    # Выбор модели и запуск workflow
    selected_llm = st.selectbox("Модель LLM:", options=st.session_state.GEMINI_MODELS, key="expand_model")
    if st.button("🚀 Расширить БД"):
        try:
            with st.spinner("Расширение БД..."):
                result = expand_db(st.session_state.jwt_token, st.session_state.active_project_folder,
                                   st.session_state.active_project_id, selected_llm)
            st.success("✅ БД расширена.")
            st.json(result)
        except APIError as e:
            st.error(f"❌ Ошибка: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")
    
    # Раздел редактирования (в самом низу)
    st.divider()
    st.subheader("✏️ Редактирование db_extension.txt")
    if st.button("Редактировать Файл"):
        file_data = fetch_file(st.session_state.jwt_token, "plus_facts", st.session_state.active_project_id,
                               st.session_state.active_project_folder)
        if file_data:
            show_default_text_editor(
                stage_name="plus_facts",
                file_data=file_data,
                project_id=st.session_state.active_project_id,
                folder_path=st.session_state.active_project_folder,
                jwt_token=st.session_state.jwt_token
            )
        else:
            st.warning("Файл не найден. Запустите расширение БД сначала.")