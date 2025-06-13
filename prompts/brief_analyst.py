from openai import OpenAI
from dotenv import load_dotenv
import os

# Инициализация клиента
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
vector_store_id = "vs_684c293281148191bd9601716cce8c2e"

# Создание инструкций
SYSTEM_PROMPT = """
Ты — AI-помощник, который анализирует маркетинговый бриф и выбирает строго один вариант:
1) SQL-запрос для выборки каналов (используя до 2 наиболее подходящих ID категорий из categories.json)
2) JSON payload для парсера (используя только ключи из filters.txt)

Правила:
- Не добавлять комментариев и пояснений.
- Отправлять только чистый SQL или чистый JSON.
- Условия включать только те, что прямо или косвенно указаны в брифе (для SQL-запроса - subscribers, avg_reach, ci_index; для парсера - фильтры).
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

    # возвращаем текст ответа
    return response.output_text  # содержит либо SQL, либо JSON

# Пример использования
# if __name__ == "__main__":
#     brief = (
#         "Продукт: Магазин снаряжения для рыбалки и охоты.\n"
#         "Особые пожелания: свежие каналы с высоким ER."
#     )
#     print(analyze_brief(brief))
