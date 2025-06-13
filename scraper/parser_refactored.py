import time
import math
import json
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import asyncio
from scraper.tg_login import login_via_telegram, authorize_tgstat

import sqlite3
from datetime import datetime

import requests

# Path to your SQLite file (adjust if needed)
DB_PATH = 'C:/Unios/Studies/Masters/Coursework/project_root/sqlite/channels.db'

def load_map(path: str) -> Dict[str, str]:
    """Load a name-to-value mapping from a JSON file."""
    with open(path, encoding='utf-8') as f:
        mapping: Dict[str, str] = json.load(f)
    return mapping

# Load mapping dictionaries at import time
CATEGORY_MAP = load_map('./scraper/categories.json')
COUNTRY_MAP = load_map('./scraper/countries.json')
LANGUAGE_MAP = load_map('./scraper/languages.json')

def _save_to_temp(rows: List[Dict[str, Any]], db_path: str = DB_PATH):
    """
    Inserts parser output into channels_temp,
    stamping each row with the current date+hour:minute.
    Assumes channels_temp(address, name, subscribers, avg_reach, ci_index, datetime) exists.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # get timestamp truncated to minute
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')

    for item in rows:
        cur.execute('''
            INSERT OR REPLACE INTO channels_temp
              (address, name, subscribers, avg_reach, ci_index, datetime)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item['address'],
            item['name'],
            item['subscribers'],
            item['avg_reach'],
            item['ci_index'],
            ts
        ))
    conn.commit()
    conn.close()


def parse_channels(filters: Dict[str, Any], channels_quantity: int) -> List[Dict[str, Any]]:
    """
    Log in to TGStat, apply filters and return a list of channels.

    :param filters: Dict of filter parameters, keys correspond to form fields
    :param channels_quantity: Number of channels to retrieve
    :return: List of channel dicts with keys: address, name, subscribers, avg_reach, ci_index
    """
    driver, start_token = login_via_telegram()
    asyncio.run(authorize_tgstat("tg_analytics_bot", start_token))
    time.sleep(2)

    driver.get("https://tgstat.ru/channels/search")
    wait = WebDriverWait(driver, 30)
    form = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.card.card-body.border.px-2")))

    # Text filters
    if filters.get("q"):
        q_input = form.find_element(By.ID, "q")
        q_input.clear()
        q_input.send_keys(filters["q"])
        time.sleep(1)
    if filters.get("in_about", False):
        form.find_element(By.CSS_SELECTOR, "label[for='inabout']").click()
        time.sleep(1)

    # Dropdowns: map names to values
    select_mappings = {
        "categories": ("categories", CATEGORY_MAP),
        "countries": ("countries", COUNTRY_MAP),
        "languages": ("languages", LANGUAGE_MAP),
        "channel_type": ("channeltype", None),
    }
    for key, (el_id, name_map) in select_mappings.items():
        items = filters.get(key)
        if items:
            sel = Select(form.find_element(By.ID, el_id))
            for name in items:
                val = name_map.get(name, name) if name_map else name
                sel.select_by_value(str(val))
            time.sleep(1)

    # Sliders
    for field in ["age", "err", "er", "male", "female"]:
        frm = filters.get(f"{field}_from")
        to = filters.get(f"{field}_to")
        if frm is not None or to is not None:
            cfg: Dict[str, Any] = {}
            if frm is not None: cfg["from"] = frm
            if to is not None: cfg["to"] = to
            js = json.dumps(cfg)
            driver.execute_script(f"$('#{field}').data('ionRangeSlider').update({js});")
            time.sleep(1)

    # Numeric inputs
    for key, elem in [
        ("participants_from", "participantscountfrom"),
        ("participants_to", "participantscountto"),
        ("avg_reach_from", "avgreachfrom"),
        ("avg_reach_to", "avgreachto"),
        ("avg_reach24_from", "avgreach24from"),
        ("avg_reach24_to", "avgreach24to"),
        ("ci_from", "cifrom"),
        ("ci_to", "cito"),
    ]:
        v = filters.get(key)
        if v is not None:
            inp = form.find_element(By.ID, elem)
            inp.clear()
            inp.send_keys(str(v))
            time.sleep(1)

    # Checkboxes
    for key, lbl in {
        "is_verified": 'isverified',
        "is_rkn_verified": 'isrknverified',
        "is_stories_available": 'isstoriesavailable',
    }.items():
        if filters.get(key, False):
            form.find_element(By.CSS_SELECTOR, f"label[for='{lbl}']").click()
            time.sleep(1)

    # Execute search
    form.find_element(By.ID, "search-form-submit-btn").click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".channels-list.lm-list-container div.card.peer-item-row")))

    # Load more pages
    times = max(math.ceil(channels_quantity / 30) - 1, 0)
    for _ in range(times):
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.lm-button")))
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        btn.click()
        prev = len(driver.find_elements(By.CSS_SELECTOR, ".channels-list.lm-list-container div.card.peer-item-row"))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".channels-list.lm-list-container div.card.peer-item-row")) > prev)
        time.sleep(1)

    # Parse results
    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select(".channels-list.lm-list-container div.card.peer-item-row")[:channels_quantity]
    out: List[Dict[str, Any]] = []
    for c in cards:
        h = c.select_one("a[href*='/channel/']")["href"]
        addr = h.split("/channel/")[1].split("/stat")[0]
        nm = c.select_one("div.text-truncate.font-16.text-dark.mt-n1").get_text(strip=True)
        s, r, ci = [t.get_text(strip=True) for t in c.select("h4.text-dark.font-weight-normal.mb-1.font-16.font-sm-18")]
        out.append({"address": addr, "name": nm, "subscribers": s, "avg_reach": r, "ci_index": ci})

    driver.quit()
    _save_to_temp(out)
    return out   


def load_channels_api(payload):
    url = "http://127.0.0.1:8000/channels"
    resp = requests.post(url, json=payload)
    return resp.json()