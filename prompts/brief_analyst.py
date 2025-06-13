from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio
import re

def clean_sql(raw: str) -> str:
    """
    Remove markdown fences and trailing semicolons from a raw SQL string.
    """
    # Extract between ```sql … ``` if present
    m = re.search(r"```(?:sql)?\s*([\s\S]+?)```", raw, flags=re.IGNORECASE)
    sql = m.group(1) if m else raw

    # Strip whitespace and any trailing semicolons
    sql = sql.strip().rstrip(';').strip()

    # Truncate after "WHERE categories IN (...)" if present
    m2 = re.search(
        r"(.*WHERE\s+category_id\s+IN\s*\(\s*[^)]*\s*\))",
        sql,
        flags=re.IGNORECASE | re.DOTALL
    )
    if m2:
        sql = m2.group(1)    

    return sql

# Инициализация клиента
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
vector_store_id = "vs_684c293281148191bd9601716cce8c2e"

# Создание инструкций
SYSTEM_PROMPT = """
Ты — AI-помощник, который анализирует маркетинговый бриф и выбирает строго один вариант:
1) SQL-запрос для выборки каналов (используя до 2 наиболее подходящих category_id из categories.json)
2) JSON payload для парсера (используя только ключи из filters.txt)

Правила:
- Не добавлять комментариев и пояснений.
- Отправлять только чистый SQL или чистый JSON.
- Условия включать только те, что прямо указаны в брифе (для SQL-запроса - subscribers, avg_reach, ci_index; для парсера - фильтры).
- Для категорий использовать только ID из categories.json.
- Для фильтров использовать только поля из filters.txt.

Структуру JSON-payload брать из filters.txt
""".strip()

# Функция для анализа брифа
async def analyze_brief(brief_text: str) -> str:
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=SYSTEM_PROMPT,
        input=brief_text,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
            "max_num_results": 5
        }]
    )  # встроенный инструмент file_search в Responses API :contentReference[oaicite:8]{index=8}
    out = clean_sql(response.output_text)
    # возвращаем текст ответа
    return out  # содержит либо SQL, либо JSON

# Пример использования
if __name__ == "__main__":
    brief = (
        # "Продукт: Магазин снаряжения для рыбалки и охоты.\n"
        # "Особые пожелания: свежие каналы с высоким ER."
        "О проекте: «Урок цифры» — федеральный проект, где школьникам рассказывают о мире технологий и помогают с выбором профессии. Целевая аудитория: школьники 1-11 класса, родители школьников, учителя информатики, широкая аудитория"
    )
    print(asyncio.run(analyze_brief(brief)))
