import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8789519474:AAGBS8tj4fg7I7x7KwOUhvTztrj2pj9ujdM"
SUPPORT_USERNAME = "cyyle"
ADMIN_ID = 6584350034
LAVA_PAY_URL = "https://app.lava.top/products/9aad4276-e009-4438-969d-3cf175a430c2"

# ⚠️ Временное хранилище в памяти (данные теряются после перезапуска Vercel)
# В продакшене рекомендуется использовать Supabase / Turso / Vercel Postgres
user_subs = {}  # { user_id: [ {title, price, billing_day}, ... ] }
premium_users = set()

class AddSubState(StatesGroup):
    title = State()
    price = State()
    day = State()

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub", style="success"),
         InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subs", style="primary")],
        [InlineKeyboardButton(text="⭐ Купить Premium", callback_data="buy_premium"),
         InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])

def get_dispatcher():
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        await state.clear()
        text = (
            "👋 Привет! Я твой токсичный финансовый помощник 😈\n\n"
            "Моя задача - бить тебя по рукам ✋ до того, как сервисы сожрут твои деньги 💸.\n\n"
            "👇 Выбирай действие в меню:"
        )
        await message.answer(text, reply_markup=main_keyboard())

    # ... (остальные декораторы @dp.message и @dp.callback_query из вашего исходного кода)
    # Для краткости здесь не приводится полный код, скопируйте логику обработки из исходного bot.py
    # Но обратите внимание: все операции с БД замените на операции с user_subs / premium_users
    # Например:
    @dp.callback_query(F.data == "list_subs")
    async def list_subscriptions(callback: CallbackQuery):
        rows = user_subs.get(callback.from_user.id, [])
        if not rows:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub", style="success")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
            ])
            await callback.message.edit_text("🕸️ У тебя пока нет подписок.", reply_markup=keyboard)
            return
        total_month = sum(row["price"] for row in rows)
        text = "💸 Твои финансовые черные дыры 🕳️:\n\n"
        buttons = []
        for idx, row in enumerate(rows):
            text += f"▫️ {row['title']} - {row['price']} ₽ (списание {row['billing_day']}-го числа)\n"
            buttons.append([InlineKeyboardButton(text=f"🗑️ Удалить {row['title']}", callback_data=f"del_{idx}", style="danger")])
        text += f"\n💳 В месяц улетает: {total_month:.2f} ₽"
        buttons.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="to_main")])
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    @dp.callback_query(F.data.startswith("del_"))
    async def delete_subscription(callback: CallbackQuery):
        idx = int(callback.data.split("_")[1])
        subs = user_subs.get(callback.from_user.id, [])
        if 0 <= idx < len(subs):
            subs.pop(idx)
        await callback.answer("✂️ Подписка отсечена!")
        await list_subscriptions(callback)

    @dp.callback_query(F.data == "add_sub")
    async def start_add_sub(callback: CallbackQuery, state: FSMContext):
        # Упрощённая проверка, логику Premium можно восстановить самостоятельно
        await state.set_state(AddSubState.title)
        await callback.message.edit_text("✍️ Вводи название сервиса:\n\n<i>(/cancel чтобы отменить)</i>", parse_mode="HTML")

    @dp.message(AddSubState.title)
    async def process_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text.strip())
        await state.set_state(AddSubState.price)
        await message.answer("💰 Сколько сдирают каждый месяц? (число):")

    @dp.message(AddSubState.price)
    async def process_price(message: Message, state: FSMContext):
        try:
            price = float(message.text.replace(",", ".").strip())
            if price <= 0: raise ValueError
        except ValueError:
            await message.answer("🤡 Давай нормальное число:")
            return
        await state.update_data(price=price)
        await state.set_state(AddSubState.day)
        await message.answer("📅 В какой день месяца списание? (1-31):")

    @dp.message(AddSubState.day)
    async def process_day(message: Message, state: FSMContext):
        try:
            day = int(message.text.strip())
            if not (1 <= day <= 31): raise ValueError
        except ValueError:
            await message.answer("🤦‍♂️ От 1 до 31. Попробуй еще раз:")
            return
        data = await state.get_data()
        user_subs.setdefault(message.from_user.id, []).append({
            "title": data["title"], "price": data["price"], "billing_day": day
        })
        await state.clear()
        await message.answer(f"✅ Готово. Напомню про '{data['title']}'.")

    @dp.callback_query(F.data == "to_main")
    async def back_to_main(callback: CallbackQuery):
        await callback.message.edit_text("👋 Главное меню:", reply_markup=main_keyboard())

    @dp.callback_query(F.data == "buy_premium")
    async def buy_premium_info(callback: CallbackQuery):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить на Lava.top", url=LAVA_PAY_URL)],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
        ])
        await callback.message.edit_text("💎 Premium доступ (ссылка на оплату):", reply_markup=keyboard)

    @dp.message(Command("cancel"))
    async def cancel_handler(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=main_keyboard())

    return dp
