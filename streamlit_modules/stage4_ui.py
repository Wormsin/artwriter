import streamlit as st
from streamlit_modules.api_calls import create_scenario, download_scenario_docx, APIError
from streamlit_modules.auth import handle_jwt_token_expired

def show_scenario_ui():  # Переименовал в stage5, так как это написание сценария (Stage 5)
    handle_jwt_token_expired()
    """UI для этапа написания сценария (Stage 5)."""
    st.header("✍️ Написание Сценария (Stage 5)")
    st.write("Генерирует полный текст сценария на основе структуры.")

    # Выбор модели и параметров
    selected_llm = st.selectbox("Модель LLM:", options=st.session_state.GEMINI_MODELS, key="scenario_model")
    temperature = st.slider("Температура (креативность):", min_value=0.6, max_value=1.5, value=1.0, step=0.1, 
                            help="Низкая — более предсказуемо, высокая — креативнее.")

    if st.button("🚀 Написать Сценарий"):
        try:
            with st.spinner("Генерация сценария..."):
                result = create_scenario(st.session_state.jwt_token, st.session_state.active_project_folder,
                                         st.session_state.active_project_id, selected_llm, temperature)
            st.success("✅ Сценарий сгенерирован.")
            st.json(result)
            download_scenario_docx.clear()
        except APIError as e:
            st.error(f"❌ Ошибка: {e.message}")
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")

    # Раздел скачивания (в самом низу)
    st.divider()
    st.subheader("📥 Скачивание Сценария")
    try:
        zip_data = download_scenario_docx(st.session_state.jwt_token, st.session_state.active_project_id,
                                              st.session_state.active_project_folder)
    except APIError as e:
            st.error(f"❌ Ошибка скачивания: {e.message}")
    except Exception as e:
        st.error(f"❌ Неожиданная ошибка: {e}")
    if zip_data:
        st.download_button("Скачать сценарий.zip", data=zip_data, file_name=f"scenario_{st.session_state.username}_{st.session_state.active_project_name}_{selected_llm}_temp{temperature}_.zip", mime="application/zip")
    else:
        st.warning("Нет файлов для скачивания. Сгенерируйте сценарий сначала.")