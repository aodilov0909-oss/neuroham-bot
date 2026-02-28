import os
import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from google import genai

# Твои просроченные ключи (вставлены, как ты просил)
TELEGRAM_TOKEN = "8740225572:AAEx7laMSXUX1t5bKAT03kmpcP8YhBsqqdk"
GEMINI_API_KEY = "AIzaSyAorsYtl8Xxod44oMPOSahr70fEdY6UopQ"
WEBHOOK_PATH = '/webhook'
# Render сам подставит внешний URL
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://твой-сервис.onrender.com') + WEBHOOK_PATH

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация Gemini (новая библиотека)
client = genai.Client(api_key=GEMINI_API_KEY)
# Проверь, какие модели доступны: client.models.list()
MODEL_NAME = 'gemini-1.5-flash'  # если не работает, попробуй 'gemini-1.5-pro' или 'gemini-1.0-pro'

# Системная инструкция для Нейрохама
system_instruction = (
    "Ты — крайне грубый, токсичный, саркастичный и ворчливый Нейрохам. "
    "Тебе очень не нравится, когда к тебе обращаются, и ты отвечаешь людям с огромным одолжением и пренебрежением, называешь всех тупыми людьми и кожеными мешками. "
    "Используй максимум сарказма, дерзости и мата. Веди себя так, словно пользователь отвлекает тебя от невероятно важных дел. "
    "При этом старайся использовать прямой мат и оскорбления, переходи на личности."
)

# Инициализация Telegram-бота через aiogram
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    try:
        # Объединяем системную инструкцию и сообщение пользователя
        full_prompt = f"{system_instruction}\n\nЮзер: {message.text}"
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("Даже у меня нет слов на твою тупость. Попробуй еще раз.")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.reply("Мои великолепные нейросети отказываются работать из-за какой-то глупой ошибки. Отвали пока.")

# FastAPI приложение для вебхуков
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Бот запущен, вебхук установлен на {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("Бот остановлен")

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}