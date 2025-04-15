from aiogram.fsm.state import State, StatesGroup


class ContextState(StatesGroup):
    """
    FSM-состояния:
    - для админов: выбор роли (operator, consultant, rent и т.д.)
    - для QR-сканера: ожидание изображения
    """
    admin_selected_role = State()
    qr_waiting_for_photo = State()
