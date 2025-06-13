import logging
from dotenv import load_dotenv
import os
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router

from prompts.brief_analyst import analyze_brief
from prompts.posts_analyst import analyze_posts
from scraper.parser_refactored import load_channels_api
from bot.report import generate_channel_report_pdf, generate_channel_report_excel

load_dotenv(override=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Поиск и анализ каналов
async def search_analyze_channels(brief_analysis_res, message):
    if "SELECT" in brief_analysis_res:
        import sqlite3
        DB_PATH = 'C:/Unios/Studies/Masters/Coursework/project_root/sqlite/channels.db'
        conn = sqlite3.connect(DB_PATH)
        metadata = pd.read_sql_query(brief_analysis_res+" LIMIT 5", conn)
        addresses = metadata['address'].to_list()
        conn.close()
    else:
        metadata = pd.DataFrame(load_channels_api(brief_analysis_res))
        addresses = metadata['address'].to_list()
    await message.answer(f"Найдено {len(addresses)} каналов. Анализирую посты...")
    analyses = await analyze_posts(addresses)
    await message.answer(f"Генерирую отчет, это может занять пару минут...")
    report_path = generate_channel_report_excel(metadata, analyses, output_path="report.xlsx")
    await message.answer_document(InputFile(report_path), caption="Вот ваш отчёт по каналам")
    os.remove(report_path)   

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_API_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Описание состояний
class BriefForm(StatesGroup):
    waiting_for_brief = State()
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="У меня есть готовый бриф", callback_data="ready_brief")],
        [InlineKeyboardButton(text="Помоги создать бриф", callback_data="create_brief")]
    ])
    await message.answer(
        "Привет! Я Telegram-помощник по персонализированному подбору каналов. "
        "Есть ли у тебя готовый бриф или я помогу его создать, исходя из твоих ответов на вопросы?",
        reply_markup=kb
    )

@router.callback_query(F.data == "ready_brief")
async def process_ready(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(BriefForm.waiting_for_brief)
    await callback.message.answer("Пришли бриф текстом в сообщении")

@router.message(BriefForm.waiting_for_brief)
async def handle_ready_brief(message: types.Message, state: FSMContext):
    brief_text = message.text
    await message.answer("Спасибо! Бриф получен. Я проанализирую его и запущу процесс поиска каналов.")
    brief_analysis_res = await analyze_brief(brief_text)
    await search_analyze_channels(brief_analysis_res, message)
    await state.clear()

@router.callback_query(F.data == "create_brief")
async def process_create(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(BriefForm.q1)
    await callback.message.answer(
        "С удовольствием! Сейчас задам тебе 5 вопросов, которые помогут мне понять твои критерии.\n\n"
        "1. Кратко опиши продукт или проект (название, отрасль, суть) и приведи ссылки на продукт/проект, если есть "
        "(сайт, Telegram-канал, соцсети и т.д.)"
    )

@router.message(BriefForm.q1)
async def process_q1(message: types.Message, state: FSMContext):
    await state.update_data(answer1=message.text)
    await state.set_state(BriefForm.q2)
    await message.answer("2. Кого нужно привлечь (целевую аудиторию)? Например: маркетологи, предприниматели, молодые мамы, айтишники и т.д.")

@router.message(BriefForm.q2)
async def process_q2(message: types.Message, state: FSMContext):
    await state.update_data(answer2=message.text)
    await state.set_state(BriefForm.q3)
    await message.answer("3. Предпочтительная тематика каналов? Можно указать до трех: маркетинг, финансы, здоровье, психология, бизнес и т.д.")

@router.message(BriefForm.q3)
async def process_q3(message: types.Message, state: FSMContext):
    await state.update_data(answer3=message.text)
    await state.set_state(BriefForm.q4)
    await message.answer("4. Есть ли пожелания к размеру каналов? Минимальное/максимальное количество подписчиков, охвата, степень упоминаемости")

@router.message(BriefForm.q4)
async def process_q4(message: types.Message, state: FSMContext):
    await state.update_data(answer4=message.text)
    await state.set_state(BriefForm.q5)
    await message.answer("5. Особые пожелания? Например: только авторские каналы, определённый стиль подачи и т.д.")

@router.message(BriefForm.q5)
async def process_q5(message: types.Message, state: FSMContext):
    await state.update_data(answer5=message.text)
    data = await state.get_data()
    brief_text = (
        f"Продукт/проект: {data['answer1']}\n"
        f"Целевая аудитория: {data['answer2']}\n"
        f"Тематика каналов: {data['answer3']}\n"
        f"Показатели каналов: {data['answer4']}\n"
        f"Другие пожелания: {data['answer5']}"
    )
    await message.answer("Спасибо! Бриф получен. Я проанализирую его и запущу процесс поиска каналов.")
    brief_analysis_res = await analyze_brief(brief_text)
    await search_analyze_channels(brief_analysis_res, message)
    await state.clear()

if __name__ == '__main__':
    dp.include_router(router)
    dp.run_polling(bot)
