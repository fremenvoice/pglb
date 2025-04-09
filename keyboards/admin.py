from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_role_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📋 Меню операторов", callback_data="admin_select_operator"),
            InlineKeyboardButton("📋 Меню консультантов", callback_data="admin_select_consultant")
        ],
        [
            InlineKeyboardButton("🙋 Без роли", callback_data="admin_select_none")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_role_selection_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔁 На экран приветствия", callback_data="admin_back_to_roles")]
    ]
    return InlineKeyboardMarkup(keyboard)
