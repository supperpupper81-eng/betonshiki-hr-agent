import logging
from telegram import Bot
from telegram.constants import ParseMode
from tenacity import retry, stop_after_attempt, wait_fixed
from config import BOT_TOKEN, CHAT_ID

logger = logging.getLogger(__name__)

def format_candidate(item: dict) -> str:
    return (
        f"👷 **{item.get('title', 'Кандидат (бетонщик/монолитчик)')}**\n"
        f"Опыт / город: {item.get('city', 'не указан')}\n"
        f"Контакты: {item.get('contacts', 'не указаны')}\n"
        f"Источник: {item.get('source', '')}"
    )

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def send_candidate(item: dict) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("BOT_TOKEN или CHAT_ID не заданы")
        return False
    bot = Bot(token=BOT_TOKEN)
    text = format_candidate(item)
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def send_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        return
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text[:4000])
    except Exception as e:
        logger.error(f"Не удалось отправить: {e}")

async def send_error(message: str):
    await send_message(f"⚠️ Ошибка агента:\n{message[:500]}")

async def send_report(found: int, sent: int):
    text = (
        f"📊 Отчёт агента (поиск бетонщиков):\n"
        f"Найдено кандидатов: {found}\n"
        f"Отправлено тебе: {sent}"
    )
    await send_message(text)
