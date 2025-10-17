# streamlit_modules/main_ui.py
import streamlit as st
from streamlit_modules.api_calls import (
    get_user_projects, create_project, expand_db, search_facts, 
    check_facts, generate_structure, write_scenario, APIError,share_project_access, upload_reports_to_api
)

GEMINI_MODELS = [
    "gemini-2.5-flash", 
    "gemini-2.5-pro", 
    "gemini-2.5-flash-lite",
    "gemini-2.5-nano"
]


def show_main_app():
    is_project_active = st.session_state.active_project_folder is not None
    
    st.header("Выбор или Создание Проекта")
    tab01, tab02 = st.tabs([
        "🔮 Создание нового проекта", 
        "⚰️ Выбор существующего проекта"
    ])
    
    # --- ТАБ 1: СОЗДАНИЕ ПРОЕКТА ---
    with tab01:
        topic_name = st.text_input("Название темы/проекта (topic_name):", value="Морские_Торговые_Пути_1917-1970")
        if st.button("Создать Проект", key='btn1_init'):
            if not st.session_state.get('jwt_token'):
                 st.error("Отсутствует токен. Пожалуйста, выполните вход.")
                 return
            try:
                with st.spinner(f'Создаю проект "{topic_name}"...'):
                    project_data = create_project(st.session_state.jwt_token, topic_name)
    
                # Успешный результат и обновление состояния
                st.session_state.active_project_folder = project_data["file_path"]
                st.session_state.active_project_name = topic_name
                st.session_state.active_project_id = project_data["project_id"]
                st.success(f"🦇 Проект '{topic_name}' успешно инициализирован.")
                st.json(project_data) # Показать ответ от FastAPI
                
            except APIError as e:
                # Обработка API ошибок (4xx, 5xx)
                st.error(f"🩸 Ошибка API ({e.status_code}): {e.message}")
                # Если 401, сбрасываем состояние
                if e.status_code == 401:
                     st.session_state.authenticated = False
                     st.session_state.jwt_token = None
                     st.rerun()
            except ConnectionError:
                 st.error("🩸 Ошибка соединения: Сервер FastAPI недоступен.")
            except Exception as e:
                 st.error(f"🩸 Произошла неизвестная ошибка: {e}")

    # --- ТАБ 2: ВЫБОР ПРОЕКТА ---
    with tab02:
        projects_list = None
        try:
            projects_list = get_user_projects(st.session_state.jwt_token)
             
        except APIError as e:
            st.error(f"🩸 Ошибка загрузки проектов ({e.status_code}): {e.message}")
            if e.status_code == 401:
                st.session_state.authenticated = False
                st.session_state.jwt_token = None
                st.rerun()
            return # Прекращаем выполнение, так как список пуст
        except ConnectionError:
            st.error("🩸 Ошибка соединения: Сервер FastAPI недоступен.")
            return
        
        # Логика отображения списка (только если projects_list успешно получен)
        if projects_list:
            if not projects_list:
                st.info("У вас пока нет ни одного проекта. Создайте новый!")
                return
            project_names_to_ids_folder = {p['topic_name']: [p['project_id'], p["file_path"]]  for p in projects_list}
            project_names = list(project_names_to_ids_folder.keys())
            
            st.markdown("### 🕸️ Выберите Активный Проект")
            selected_name = st.selectbox(
                "Доступные проекты:",
                project_names,
                index=0,
                key="project_selector"
            )
            
            if selected_name:
                selected_id = project_names_to_ids_folder[selected_name][0]
                st.session_state.active_project_folder = project_names_to_ids_folder[selected_name][1]
                st.session_state.active_project_name = selected_name
                st.session_state.active_project_id = selected_id # Обновляем состояние
            else:
                 st.session_state.active_project_folder = None
                 st.session_state.active_project_id = None
                 st.session_state.active_project_name = ""

            active_project_id = st.session_state.get('active_project_id')
            #active_project_folder = st.session_state.get('active_project_folder')
            
            if active_project_id:
                
                # --- ФОРМА РАСШАРИВАНИЯ ПРОЕКТА ---
                st.markdown(f"#### Расшарить доступ к проекту 🖤{st.session_state.active_project_name}🖤")
                
                with st.form("share_project_form", clear_on_submit=True):
                    user_name = st.text_input(
                        "Имя Пользователя, которому предоставляется доступ:",
                        key="share_user_name_input"
                    )
                    
                    # 2. Уровень доступа
                    permission_level = st.selectbox(
                        "Уровень доступа:",
                        ["READ", "WRITE"],
                        key="permission_level_select"
                    )
                    
                    share_button = st.form_submit_button("Предоставить Доступ")
                
                    if share_button:
                        try:
                            with st.spinner(f"Предоставляю доступ пользователю {user_name}..."):
                                # Вызов API, который обрабатывает ошибки
                                result = share_project_access(
                                    st.session_state.jwt_token,
                                    active_project_id,
                                    user_name,
                                    permission_level
                                )
                            
                            st.success(f"🦇 Доступ '{permission_level}' успешно предоставлен пользователю с ID: {user_name}.")
                            st.json(result)
                            
                        except APIError as e:
                            st.error(f"🩸 Ошибка: {e.message}")
                            if e.status_code == 401:
                                # Сброс сессии, если токен просрочен
                                st.session_state.authenticated = False
                                st.session_state.jwt_token = None
                                st.rerun()
                        except ConnectionError:
                            st.error("🩸 Ошибка соединения: Сервер FastAPI недоступен.")
                        except ValueError as e:
                            st.error(f"🩸 Ошибка данных: {e}")
            
            else:
                st.info("Сначала выберите проект из списка или создайте новый, чтобы расшарить его.")
     
    st.markdown("---")

    if is_project_active:
        st.header("Этапы создания сценария")
        st.success(f"Активный проект: {st.session_state.active_project_name}")
        
        tab2, tab3, tab4, tab5 = st.tabs([
            "🪬 Расширение БД", 
            "⛓️ Поиск Связей", 
            "🦴 Структура Сценария", 
            "🚬 Написание Сценария"
        ])

        # --- Вкладка 2: Расширение БД ---
        with tab2:
            #st.header("Расширение Базы Данных")
            st.write("Добавляет дополнительную информацию в базу знаний проекта.")

            uploaded_files = st.file_uploader(
                "Выберите один или несколько файлов для загрузки", 
                type=['pdf', 'txt'], 
                accept_multiple_files=True 
                )
            if uploaded_files: # Теперь это список!
                if st.button(f"Загрузить {len(uploaded_files)} файл(ов) в проект"):
                    try:
                        with st.spinner(f"Загрузка {len(uploaded_files)} файлов..."):
                            # Вызов новой функции API
                            result = upload_reports_to_api(
                                st.session_state.jwt_token,
                                st.session_state.active_project_id,
                                st.session_state.active_project_folder,
                                uploaded_files # Передаем список
                            )
                        
                        st.success(f"🦇 Загрузка завершена! Успешно сохранено файлов: {len(result.get('results', []))}.")
                        st.json(result)
                    except Exception:
                        pass  # Errors handled in api_calls
            
            selected_llm_name = st.selectbox(
            "Выберите модель Gemini для генерации сценария:",
            options=GEMINI_MODELS,
            index=0,
            key="btn2_model"
            )
            if st.button("Расширить БД", key='btn2'):
                try:
                    with st.spinner(f'Собираю данные для проекта "{st.session_state.active_project_name}"...'):
                        result = expand_db(st.session_state.jwt_token, 
                                           st.session_state.active_project_folder,
                                           st.session_state.active_project_id,
                                           selected_llm_name
                                           )
                        # Обработка успешного ответа
                        st.success(f"🦇 Данные успешно собраны.")
                        st.json(result) # Показать ответ от FastAPI
                except Exception:
                    pass  # Errors handled in api_calls

        # --- Вкладка 3: Поиск Фактов ---
        with tab3:
            #st.header("Поиск Фактов")
            st.write("Ищет неочевидные связи в исторических событиях, стоит гепотезы.")
            selected_llm_name = st.selectbox(
            "Выберите модель Gemini для генерации сценария:",
            options=GEMINI_MODELS,
            index=0,
            key="btn3_model"
            )
            topic_folder = st.session_state.active_project_folder
            if st.button("Найти Факты", key='btn3'):
                try:
                    with st.spinner(f'Ищу факты "{topic_folder}"...'):
                        result = search_facts(st.session_state.jwt_token, 
                                              topic_folder, 
                                              st.session_state.active_project_id,
                                              selected_llm_name)
                        # Обработка успешного ответа
                        st.success(f"🦇 Факты успешно найдены.")
                        st.json(result) # Показать ответ от FastAPI
                except Exception:
                    pass  # Errors handled in api_calls
            
            selected_llm_name = st.selectbox(
            "Выберите модель Gemini для генерации сценария:",
            options=GEMINI_MODELS,
            index=0,
            key="btn4_model"
            )
            if st.button("Проверить Факты", key='btn4'):
                try:
                    with st.spinner(f'Проверяю факты "{topic_folder}"...'):
                        result = check_facts(st.session_state.jwt_token, 
                                             topic_folder, 
                                             st.session_state.active_project_id,
                                             selected_llm_name)
                        # Обработка успешного ответа
                        st.success(f"🦇 Факты успешно проверены.")
                        st.json(result) # Показать ответ от FastAPI
                except Exception:
                    pass  # Errors handled in api_calls

    
        # --- Вкладка 4: Структура Сценария ---
        with tab4:
            #st.header("Написание Структуры Сценария")
            st.write("Генерирует структуру сценария.")
            
            selected_llm_name = st.selectbox(
            "Выберите модель Gemini для генерации сценария:",
            options=GEMINI_MODELS,
            index=0,
            key="btn5_model"
            )
            num_acts = st.number_input("Количесво серий:", min_value=1, step=1, format="%d" )
            if st.button("Сгенерировать Структуру", key='btn5'):
                try:
                    with st.spinner(f'Создаю структуру "{st.session_state.active_project_name}"...'):
                        result = generate_structure(st.session_state.jwt_token, st.session_state.active_project_folder, 
                                                    st.session_state.active_project_id, num_acts, selected_llm_name)
                        # Обработка успешного ответа
                        st.success(f"🦇 Структура успешно создана.")
                        st.json(result) # Показать ответ от FastAPI
                except Exception:
                    pass  # Errors handled in api_calls

        # --- Вкладка 5: Написание Сценария ---
        with tab5:
            #st.header("Написание Сценария")
            st.write("Генерирует полный сценарий.")
            selected_llm_name = st.selectbox(
            "Выберите модель Gemini для генерации сценария:",
            options=GEMINI_MODELS,
            index=0,
            key="btn6_model"
            )
            temperature = st.slider("Макс. Токенов для вывода:", min_value=0.6, max_value=0.9, value=0.7, key='tokens5', step=0.05)
            if st.button("Написать Сценарий", key='btn6'):
                try:
                    with st.spinner(f'Пишу сценарий "{st.session_state.active_project_name}"...'):
                        result = write_scenario(st.session_state.jwt_token, st.session_state.active_project_folder, 
                                                st.session_state.active_project_id, 
                                                temperature, selected_llm_name)
                        # Обработка успешного ответа
                        st.success(f"🦇 Сценарий успешно написан.")
                        st.json(result) # Показать ответ от FastAPI
                except Exception:
                    pass  # Errors handled in api_calls