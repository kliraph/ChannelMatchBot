import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs

from telethon import TelegramClient
from telethon.tl.functions.messages import (
    StartBotRequest,
)

from dotenv import load_dotenv
import os

def login_via_telegram():
    # 1. Launch undetected‐chromedriver
    options = uc.ChromeOptions()
    # (optional) run headless:
    options.add_argument("--headless=new")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    # 2. Go to TGStat login
    driver.get("https://tgstat.ru/login?redirect_uri=")

    telegram_btn = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "a.auth-btn")
    ))
    href = telegram_btn.get_attribute("href") # e.g. "https://t.me/tg_analytics_bot?start=ojORLfNWt3arfKLQV4HMmxrcN_cVzdru"

    u = urlparse(href)
    #bot_username = u.path.lstrip("/")           # "tg_analytics_bot"
    start_token  = parse_qs(u.query)["start"][0] # "ojORLfNWt3arfKLQV4HMmxrcN_cVzdru"

    telegram_btn.click()
    
    return driver, start_token

load_dotenv(override=True)

async def authorize_tgstat(bot_username: str, start_token: str):
    api_id   = int(os.getenv("tg_api_id"))       # get from https://my.telegram.org
    api_hash = os.getenv("tg_api_hash")

    client = TelegramClient("tgstat_session", api_id, api_hash)
    await client.start()

    # запускаем бота через MTProto-запрос
    await client(StartBotRequest(
        bot         = bot_username,
        peer        = bot_username,
        start_param = start_token
    ))
    await asyncio.sleep(2)
    # читаем новые сообщения из диалога с ботом
    async for msg in client.iter_messages(bot_username):
        if msg.buttons:
            await msg.click(text="Авторизоваться")
            print("Clicked ‘Авторизоваться’")
            break
        else:
            raise RuntimeError("Couldn’t find the ‘Авторизоваться’ button")
        
    await client.disconnect()
