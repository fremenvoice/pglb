# telegram_bot/domain/menu_registry.py

menu_by_role = {
    "operator": [
        ("📋 Обязанности", "duties_operator.md"),
        ("🌅 Утренняя подготовка", "preparation_operator.md"),
        ("👥 Посетители и допуск", "visitors.md"),
        ("🚨 ЧП и помощь", "emergency.md"),
        ("💰 Вопросы оплаты", "payment.md"),
        ("📘 ГОСТ 33807", "gost.md"),
        ("🔍 QR-сканер", "qr_scanner.md")
    ],
    "consultant": [
        ("📋 Обязанности", "duties_consultant.md"),
        ("🌅 Утренняя подготовка", "preparation_consultant.md"),
        ("💰 Вопросы оплаты", "payment.md"),
        ("🚨 ЧП и помощь", "emergency.md"),
        ("🔍 QR-сканер", "qr_scanner.md")
    ],
    "admin": [
        ("Меню операторов", "menu_operator"),
        ("Меню консультантов", "menu_consultant"),
        ("Без роли", "menu_guest"),
        ("🔍 QR-сканер (админ)", "qr_scanner.md")
    ],
    "guest": [
        ("ℹ️ О парке", "about_park.md")
    ]
}
