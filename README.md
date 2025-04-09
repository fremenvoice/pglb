Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

.venv\Scripts\Activate.ps1
#синхратаблиц и ролей
python -m telegram_bot.services.sheets_cache
