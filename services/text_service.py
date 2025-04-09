from pathlib import Path

TEXT_BLOCKS_DIR = Path("domain/text_blocks")

def get_text_block(name: str) -> str:
    path = TEXT_BLOCKS_DIR / name
    if not path.exists():
        return "⚠️ Блок не найден."
    return path.read_text(encoding="utf-8")

def render_text_block(name: str, **kwargs) -> str:
    """
    Возвращает текст с подстановкой переменных из блока Markdown.
    Пример: render_text_block("welcome.md", full_name="Иванов", role="operator")
    """
    text = get_text_block(name)
    return text.format(**kwargs)
