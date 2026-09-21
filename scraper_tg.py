import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed

from config import CHANNELS, KEYWORDS_CANDIDATES, EXCLUDE_KEYWORDS, HOURS_LOOKBACK

logger = logging.getLogger(__name__)

# Признаки, что это ВАКАНСИЯ (работодатель), а не соискатель
VACANCY_SIGNS = [
    "требуется", "требуются", "нужен", "нужна", "нужны",
    "ищем", "ищет", "вакансия", "вакансии", "набор",
    "приглашаем", "требования", "обязанности",
    "зарплата", "з/п", "зп", "₽", "руб.", "рублей",
    "оформление", "трудоустройство", "график работы",
    "вахта", "предоставляется", "питание", "проживание",
    "от", "до", "тыс", "тысяч",
]


def is_candidate(text: str) -> bool:
    text_lower = text.lower()

    # Должно быть хоть одно слово про бетон/монолит/арматуру
    has_trade = any(kw in text_lower for kw in [
        "бетонщик", "бетонщики", "монолитчик", "монолитчики",
        "арматурщик", "арматурщики", "опалубщик", "монолит", "бетон"
    ])
    if not has_trade:
        return False

    # Если много признаков вакансии — это работодатель
    vacancy_hits = sum(1 for s in VACANCY_SIGNS if s in text_lower)
    if vacancy_hits >= 2:
        return False

    # Явные признаки соискателя
    seeker_signs = [
        "ищу работу", "ищу работу", "резюме", "готов выйти",
        "готов к работе", "рассмотрю предложения", "имею опыт",
        "опыт работы", "мой опыт", "работаю", "ищу вахту",
        "бригада ищет", "мы ищем работу", "свободны",
    ]
    if any(s in text_lower for s in seeker_signs):
        return True

    # Если есть телефон и мало признаков вакансии — оставляем как возможного кандидата
    has_phone = bool(re.search(r"\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text))
    if has_phone and vacancy_hits == 0:
        return True

    return False


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def fetch_channel_page(channel: str) -> str:
    url = f"https://t.me/s/{channel}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_phones(text: str) -> str:
    phones = re.findall(
        r"(\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})",
        text
    )
    unique = list(dict.fromkeys(phones))
    return ", ".join(unique) if unique else "смотреть в источнике"


def parse_messages(html: str, channel: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    cutoff = datetime.utcnow() - timedelta(hours=HOURS_LOOKBACK)

    for msg in soup.select("div.tgme_widget_message"):
        try:
            text_el = msg.select_one("div.tgme_widget_message_text")
            if not text_el:
                continue
            text = text_el.get_text(separator="\n", strip=True)
            if not is_candidate(text):
                continue

            date_el = msg.select_one("time")
            msg_date = datetime.utcnow()
            if date_el and date_el.get("datetime"):
                try:
                    msg_date = datetime.fromisoformat(
                        date_el["datetime"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except Exception:
                    pass
            if msg_date < cutoff:
                continue

            link_el = msg.select_one("a.tgme_widget_message_date")
            link = link_el["href"] if link_el else f"https://t.me/{channel}"

            contacts = extract_phones(text)
            title = text[:110].replace("\n", " ").strip()
            if len(text) > 110:
                title += "..."

            results.append({
                "title": title,
                "experience": "не указан",
                "city": "Россия / уточнять",
                "contacts": contacts,
                "source": link,
                "raw": text,
                "channel": channel,
            })
        except Exception as e:
            logger.warning(f"Ошибка парсинга в {channel}: {e}")
            continue

    return results


def scrape_telegram() -> List[Dict]:
    all_candidates = []
    logger.info("Парсинг каналов на соискателей...")

    for channel in CHANNELS:
        try:
            logger.info(f"  → {channel}")
            html = fetch_channel_page(channel)
            items = parse_messages(html, channel)
            logger.info(f"     кандидатов: {len(items)}")
            all_candidates.extend(items)
        except Exception as e:
            logger.error(f"Ошибка {channel}: {e}")

    logger.info(f"Всего сырых кандидатов: {len(all_candidates)}")
    return all_candidates
