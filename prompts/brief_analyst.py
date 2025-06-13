from openai import OpenAI

# Инициализация клиента Assistants API
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

# Загружаем статические файлы с категориями и фильтрами
#categories_file = client.files.create(
#     file=open("categories.json", "rb"),
#     purpose="search",
# )

# Создаём векторное хранилище для file_search
vector_store = client.vector_stores.create(name="ChannelBriefData")

# загружаем категории и фильтры как отдельные файлы для последующего поиска
with open("./prompts/categories.json", "rb") as f_cat:
    client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id,
        file=f_cat
    )  # используется default chunking :contentReference[oaicite:5]{index=5}

with open("./prompts/filters.json", "rb") as f_fil:
    client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id,
        file=f_fil
    )  # аналогично :contentReference[oaicite:6]{index=6}

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
def analyze_brief(brief_text: str) -> str:
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=SYSTEM_PROMPT,
        input=brief_text,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store.id],
            "max_num_results": 5
        }]
    )  # встроенный инструмент file_search в Responses API :contentReference[oaicite:8]{index=8}

    # возвращаем текст ответа
    return response.output_text  # содержит либо SQL, либо JSON

# Пример использования
if __name__ == "__main__":
    brief = (
        "Продукт: Магазин снаряжения для рыбалки и охоты.\n"
        "Особые пожелания: свежие каналы с высоким ER."
    )
    print(analyze_brief(brief))
