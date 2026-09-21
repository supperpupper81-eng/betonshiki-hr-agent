"""
Агент поиска бетонщиков.
Ищет кандидатов и присылает в @Kadrovik_ZHB_bot.
Запуск: 2 раза в день (09:00 и 20:00 по Томску).
"""

import asyncio
import logging
import sys
from datetime import datetime

from config import MAX_CANDIDATES_PER_RUN, BOT_TOKEN, CHAT_ID
from storage import init_db, already_sent, mark_as_sent, cleanup_old
from scraper_tg import scrape_telegram
from sender import send_candidate, send_error, send_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def run():
    logger.info("=== Запуск агента поиска бетонщиков ===")
    start = datetime.utcnow()

    init_db()
    cleanup_old(days=45)

    found = 0
    sent = 0

    try:
        candidates = scrape_telegram()
        found = len(candidates)

        unique = []
        seen = set()
        for item in candidates:
            key = (item.get("title", "")[:80], item.get("contacts", ""))
            if key not in seen:
                seen.add(key)
                unique.append(item)

        to_send = []
        for item in unique:
            if already_sent(item["title"], item["contacts"]):
                continue
            to_send.append(item)
            if len(to_send) >= MAX_CANDIDATES_PER_RUN:
                break

        logger.info(f"К отправке после фильтра: {len(to_send)}")

        for item in to_send:
            try:
                ok = await send_candidate(item)
                if ok:
                    mark_as_sent(item["title"], item["contacts"])
                    sent += 1
                    logger.info(f"Отправлен: {item['title'][:50]}...")
                await asyncio.sleep(1.2)
            except Exception as e:
                logger.error(f"Не удалось отправить: {e}")

        await send_report(found, sent)

    except Exception as e:
        logger.exception("Критическая ошибка агента")
        await send_error(str(e))

    duration = (datetime.utcnow() - start).total_seconds()
    logger.info(f"=== Готово. Найдено: {found}, отправлено: {sent}, время: {duration:.1f}с ===")


if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("ОШИБКА: не заданы BOT_TOKEN и CHAT_ID")
        sys.exit(1)
    asyncio.run(run())
