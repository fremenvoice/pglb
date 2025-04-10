from aiogram.fsm.state import State, StatesGroup

class AdminMenuContextState(StatesGroup):
    role = State()
