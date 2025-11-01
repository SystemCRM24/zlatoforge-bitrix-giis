from loguru import logger
import sys
from src.core import settings


logger.remove()


debug_template = (
    "<level>{level:<7}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{message}"
)

# Основной логгер
logger.add(
    sys.stdout,
    level='DEBUG' if settings.DEBUG else 'INFO',
    format=debug_template,
    filter=lambda r: r['level'].no < logger.level('CRITICAL').no,
    enqueue=True
)
