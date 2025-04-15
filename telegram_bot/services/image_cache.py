import os
import logging
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

# Путь к директории с изображениями
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "domain", "img")

# Кеш картинок: {filename: FSInputFile}
_image_cache: dict[str, FSInputFile] = {}


async def preload_images():
    """
    Предзагружает изображения из IMG_DIR в кеш.
    """
    global _image_cache
    _image_cache = {}

    if not os.path.isdir(IMG_DIR):
        logger.warning(f"❌ Каталог изображений не найден: {IMG_DIR}")
        return

    for filename in os.listdir(IMG_DIR):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        filepath = os.path.join(IMG_DIR, filename)
        try:
            _image_cache[filename] = FSInputFile(filepath)
            logger.info(f"🖼️ Изображение загружено в кеш: {filename}")
        except Exception as e:
            logger.warning(f"❌ Ошибка при загрузке изображения {filename}: {e}")


def get_image(filename: str) -> FSInputFile | None:
    """
    Получает FSInputFile из кеша по имени файла.
    """
    image = _image_cache.get(filename)
    if image is None:
        logger.warning(f"⚠️ Изображение {filename} не найдено в кеше.")
    return image
