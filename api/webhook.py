import asyncio
from aiogram.types import Update
from your_bot_module import bot, dp  # импортируйте из вашего bot.py

async def handler(request):
    # Vercel Python runtime передаёт запрос как объект
    body = await request.json()
    update = Update.model_validate(body, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"statusCode": 200, "body": "ok"}
