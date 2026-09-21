import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

CHANNELS = [
    "stroiVLG",
    "Monolithici_RF",
    "SRO_rus",
    "stroy_podryad_chat",
    "monolitmos",
    "monolitchikii",
    "monolitchiki_moskvi",
    "rabota_tomskd",
    "v_tomske_rabotaa",
    "tomsx_rabotaz",
    "rabotav_tomsk",
    "Rabota_NSK_podrabotka",
    "nskrabotaru",
    "rabota1_nsk",
    "vakansiii_nsk",
    "rabota_tyumens",
    "Job_WorkFinder_bot",
]

KEYWORDS_CANDIDATES = [
    "бетонщик", "бетонщики", "монолитчик", "монолитчики",
    "арматурщик", "арматурщики", "опалубщик",
    "ищу работу", "ищу работу бетон", "резюме бетон",
    "готов выйти", "готов к работе", "бригада монолит",
    "монолит ищу", "бетон ищу работу", "работаю бетон",
    "опыт монолит", "опыт бетон", "вахта бетон",
]

EXCLUDE_KEYWORDS = [
    "требуется", "нужны", "ищем бригаду", "нужна бригада",
    "требуется бетонщик", "вакансия", "набор", "приглашаем",
    "объём работ", "м3", "м³", "тендер", "подряд",
]

MAX_CANDIDATES_PER_RUN = 12
HOURS_LOOKBACK = 48
