import streamlit as st
from streamlit_modules.api_calls import (
    get_user_projects, create_project, APIError, share_project_access
)


def show_main_app():
    # Проверка аутентификации
    if not st.session_state.get('authenticated', False) or not st.session_state.get('jwt_token'):
        st.error("❌ Требуется авторизация. Перейдите на страницу входа.")
        st.stop()
    
    
    st.header("Выбор или Создание Проекта")
    tab01, tab02 = st.tabs([
    "⚰️ Выбор существующего проекта",
        "🔮 Создание нового проекта" 
    ])
    
    # --- ТАБ 2: СОЗДАНИЕ ПРОЕКТА ---
    with tab02:
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
                #st.success(f"🦇 Проект '{topic_name}' успешно инициализирован.")
                #st.json(project_data) # Показать ответ от FastAPI
                projects_list = None
                get_user_projects.clear()
                st.rerun()
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

    # --- ТАБ 1: ВЫБОР ПРОЕКТА ---
    with tab01:
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
            project_names_to_ids_folder = {f"{p['topic_name']} {p['permission_level']}": [p['project_id'], p["file_path"], p['topic_name'], p['permission_level']]  for p in projects_list}
            projects_id = [p["project_id"] for p in projects_list]
            project_names_with_access = list(project_names_to_ids_folder.keys())

            active_project_id = st.session_state.get('active_project_id')

            current_project_index = 0
            if active_project_id and active_project_id in projects_id:
                current_project_index = projects_id.index(active_project_id)
        
            st.markdown("### 🕸️ Выберите Активный Проект")
            selected_box_name = st.selectbox(
                "Доступные проекты:",
                project_names_with_access,
                index=current_project_index,
                key="project_selector"
            )
            
            if selected_box_name:
                selected_id = project_names_to_ids_folder[selected_box_name][0]
                selected_folder = project_names_to_ids_folder[selected_box_name][1]
                selected_name = project_names_to_ids_folder[selected_box_name][2]
                
                if selected_id != active_project_id:
                    st.session_state.active_project_folder = selected_folder
                    st.session_state.active_project_name = selected_name
                    st.session_state.active_project_id = selected_id 
                    
                    st.rerun()
            else:
                 st.session_state.active_project_folder = None
                 st.session_state.active_project_id = None
                 st.session_state.active_project_name = ""


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
        else:
            st.info("У вас пока нет ни одного проекта.")
     
    st.markdown("---")