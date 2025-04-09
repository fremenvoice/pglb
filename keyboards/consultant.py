from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_consultant_main_keyboard(extra_button=False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Утренняя подготовка", callback_data="consultant_morning_preparation")],
        [InlineKeyboardButton("Обязанности", callback_data="consultant_duties")],
        [InlineKeyboardButton("Вопросы оплаты", callback_data="consultant_payment")],
        [InlineKeyboardButton("ЧП и помощь", callback_data="consultant_emergency_help")],
        [InlineKeyboardButton("QR-сканнер", callback_data="consultant_qr_scanner")]
    ]
    
    if extra_button:
        keyboard.append([InlineKeyboardButton("🔁 На экран приветствия", callback_data="consultant_back_to_roles")])

    return InlineKeyboardMarkup(keyboard)
