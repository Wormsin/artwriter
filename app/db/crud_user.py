import logging
from requests import Session
from db.models import User
from datetime import datetime

logger = logging.getLogger(__name__)


# --- ФУНКЦИЯ ДЛЯ ОБНОВЛЕНИЯ ТОКЕНОВ (добавьте в отдельный crud_user.py или utils.py) ---
def update_user_token_usage(db: Session, user_id: int, tokens: int):
    """
    Обновляет использование токенов для пользователя за текущий месяц.
    Проверяет последнюю дату в token_usage: если текущий месяц != последнему ключу,
    добавляет новую запись. Иначе суммирует к существующей.
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.error(f"Пользователь {user_id} не найден для обновления токенов")
            raise ValueError(f"Пользователь {user_id} не найден")
        
        token_usage = user.token_usage or {}
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Получаем последний день из ключей (сортируем по дате)
        if token_usage:
            last_date = max(token_usage.keys())  # max по строке YYYY-MM-DD работает как дата
            # Если текущий день != последний, добавляем новую (день "истёк")
            if current_date != last_date:
                token_usage[current_date] = tokens
            else:
                token_usage[current_date] += tokens
        else:
            # Первый раз — новая запись
            token_usage[current_date] = tokens
        
        user.token_usage = token_usage
        db.commit()
        logger.info(f"Токены обновлены для {user_id}: +{tokens} за {current_date}. Итого: {token_usage[current_date]}")
        return user.token_usage
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления токенов для {user_id}: {e}")
        raise