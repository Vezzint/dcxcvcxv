import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Импортируем логику из bot.py
from bot import dp, BOT_TOKEN, init_db

# Инициализируем бота (с новыми правилами aiogram 3.x)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске инициализируем БД (создаст файл, если его нет)
    try:
        await init_db()
    except Exception as e:
        print(f"Ошибка БД: {e}")
    
    # Устанавливаем вебхук
    webhook_url = "https://dcxcvcxv-git-main-dd-ser.vercel.app/api/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"Вебхук установлен на {webhook_url}")
    
    yield
    
    # При выключении удаляем вебхук и закрываем сессию
    await bot.delete_webhook()
    await bot.session.close()

# Создаем приложение FastAPI (Vercel ищет именно переменную app)
app = FastAPI(lifespan=lifespan)

# Эндпоинт, куда Telegram будет присылать сообщения
@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    try:
        # Получаем данные от Telegram
        update_data = await request.json()
        # Преобразуем в объект Update
        update = types.Update(**update_data)
        # Передаем диспетчеру aiogram
        await dp.feed_update(bot, update)
        return Response(status_code=200)
    except Exception as e:
        print(f"Ошибка при обработке вебхука: {e}")
        return Response(status_code=200) # Всегда отвечаем 200, чтобы Telegram не спамил

# Простой эндпоинт для проверки, что сервер жив
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is running"}

# Этот блок нужен только если ты захочешь запустить бота локально (python index.py)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
