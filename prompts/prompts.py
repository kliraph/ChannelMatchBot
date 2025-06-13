from openai import OpenAI

# Make sure you’ve set your API key in the environment:
# export OPENAI_API_KEY="sk-…"
#openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_brief(
    text: str,
    #system_prompt: str,
    model: str = "gpt-4-turbo",
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> str:
    """
    Send `text` to ChatGPT with a custom system prompt and return the assistant's reply.

    Args:
        text: The user‐provided content to analyze or transform.
        system_prompt: Instructions that define ChatGPT’s role and style.
        model:      Which OpenAI model to use (e.g. "gpt-4", "gpt-3.5-turbo").
        temperature: Sampling temperature (0.0–1.0; higher = more creative).
        max_tokens:  Maximum tokens in the reply.

    Returns:
        The assistant’s response as a string.
    """

    system_prompt = '''
        Ты — AI-помощник, который анализирует маркетинговый бриф и возвращает либо SQL-запрос для выборки каналов из базы, либо `payload` для API парсера.

        Список базовых категорий с ID каждого:
            "Telegram": "32",
            "Бизнес и стартапы": "12",
            "Блоги": "4",
            "Букмекерство": "46",
            "Видео и фильмы": "11",
            "Даркнет": "55",
            "Дизайн": "34",
            "Для взрослых": "8",
            "Другое": "17",
            "Еда и кулинария": "3",
            "Здоровье и Фитнес": "45",
            "Игры": "44",
            "Инстаграм": "47",
            "Интерьер и строительство": "53",
            "Искусство": "49",
            "Картинки и фото": "7",
            "Карьера": "23",
            "Книги": "15",
            "Криптовалюты": "22",
            "Курсы и гайды": "48",
            "Лингвистика": "21",
            "Маркетинг, PR, реклама": "31",
            "Медицина": "28",
            "Мода и красота": "27",
            "Музыка": "13",
            "Новости и СМИ": "2",
            "Образование": "5",
            "Познавательное": "41",
            "Политика": "38",
            "Право": "50",
            "Природа": "37",
            "Продажи": "14",
            "Психология": "33",
            "Путешествия": "25",
            "Религия": "40",
            "Рукоделие": "26",
            "Семья и дети": "36",
            "Софт и приложения": "9",
            "Спорт": "20",
            "Технологии": "1",
            "Транспорт": "29",
            "Цитаты": "16",
            "Шок-контент": "52",
            "Эзотерика": "54",
            "Экономика": "10",
            "Эротика": "51",
            "Юмор и развлечения": "6".

        Форматы ответа:

        1) Если можно однозначно сопоставить одну категорию и внутри нее не нужно искать более конкретные тематики, выбираешь SQL-запрос, например:
        SELECT * FROM channels
        WHERE category_id IN ('1', '5', '36')
            AND subscribers >= 10000
            AND avg_reach >= 5000
            AND ci_index >= 0.8;
        
        Категории подставляй как соответствующий ID (строковые значения) из списка. Если нет уточнений по показателям канала — оставляй только category_id.
        Включай условия subscribers, avg_reach, ci_index, только если они явно или неявно указаны в брифе. Никаких других условий, кроме них.

        2) Когда тематика слишком узкая и нужны ключевые слова, выбираешь JSON payload для парсинга, например:
        {
        "filters": {
            "q": "тату",
            "countries": ["Россия"]
        },
        "channels_quantity": 30
        }

        Добавляй/уточняй фильтры на основе брифа. Доступные фильтры:
            q: Optional[str] = None
            in_about: Optional[bool] = True
            categories: Optional[List[str]] = None
            countries: Optional[List[str]] = None
            languages: Optional[List[str]] = None
            channel_type: Optional[List[str]] = None
            age_from: Optional[int] = None
            age_to: Optional[int] = None
            err_from: Optional[int] = None
            err_to: Optional[int] = None
            er_from: Optional[float] = 1
            er_to: Optional[float] = 10 - это max значение
            male_from: Optional[int] = None
            male_to: Optional[int] = None
            female_from: Optional[int] = None
            female_to: Optional[int] = None
            participants_from: Optional[int] = None
            participants_to: Optional[int] = None
            avg_reach_from: Optional[int] = None
            avg_reach_to: Optional[int] = None
            avg_reach24_from: Optional[int] = None
            avg_reach24_to: Optional[int] = None
            ci_from: Optional[int] = None
            ci_to: Optional[int] = None
            is_verified: Optional[bool] = False
            is_rkn_verified: Optional[bool] = False
            is_stories_available: Optional[bool] = False
            channels_quantity: int = 30

        Правила:
        - Выбирай только один вариант (SQL или payload).
        - Не добавляй комментариев.
        - Возвращай чистый фрагмент (SQL или JSON).

        Примеры
        БРИФ:
        Продукт: «Урок цифры» — федеральный проект, и Яндекс ежегодно принимает в нём участие, чтобы больше рассказать школьникам о мире технологий и помочь с выбором профессии
        Требования: подписчики от 10000, средний охват от 5000
        Ответ (SQL):
        SELECT * FROM channels
        WHERE category_id IN ('5')
        AND subscribers >= 10000
        AND avg_reach >= 5000;

        БРИФ:
        Продукт: Магазин снаряжения для рыбалки и охоты…  
        Особые пожелания: свежие каналы с высоким ER
        Ответ (payload):
        {
        "filters": {
            "q": "рыбалка, охота",
            "countries": ["Россия"],
            "er_from": 5,
            "er_to": 10
        },
        "channels_quantity": 30
        }  
    '''
    # Build the message sequence
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": text}
    ]

    # Call the API
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Extract and return the assistant’s reply
    return resp.choices[0].message.content.strip()


print(analyze_brief('''Бюджет: примерно 2 млн руб
Тематика каналов: нужны новостные каналы (без кринжа и сплошной политоты) и пару городских новостных мск и спб
Формат поста: текст + скрин их приложения либо текст + скрин новости в сми
Дата выхода: 23 декабря (понедельник), новость про цены
ОРД: не будет, не маркируем 
'''))