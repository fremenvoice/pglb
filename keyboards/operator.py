from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_operator_main_keyboard(extra_button=False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Утренняя подготовка", callback_data="operator_morning_preparation")],
        [InlineKeyboardButton("Обязанности", callback_data="operator_duties")],
        [InlineKeyboardButton("Посетители и допуск", callback_data="operator_visitors")],
        [InlineKeyboardButton("ЧП и помощь", callback_data="operator_emergency_help")],
        [InlineKeyboardButton("Вопросы оплаты", callback_data="operator_payment")],
        [InlineKeyboardButton("ГОСТ 33807", callback_data="operator_gost")],
        [InlineKeyboardButton("QR-сканнер", callback_data="operator_qr_scanner")]
    ]
    
    if extra_button:
        keyboard.append([InlineKeyboardButton("🔁 На экран приветствия", callback_data="operator_back_to_roles")])

    return InlineKeyboardMarkup(keyboard)
