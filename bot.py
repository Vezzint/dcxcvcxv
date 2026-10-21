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
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8789519474:AAGBS8tj4fg7I7x7KwOUhvTztrj2pj9ujdM"
SUPPORT_USERNAME = "cyyle"
ADMIN_ID = 6584350034
LAVA_PAY_URL = "https://app.lava.top/products/9aad4276-e009-4438-969d-3cf175a430c2"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class AddSubState(StatesGroup):
    title = State()
    price = State()
    day = State()

async def init_db():
    # Заглушка, чтобы Vercel не падал
    print("Vercel: база отключена")

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub"),
            InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subs")
        ],
        [
            InlineKeyboardButton(text="⭐ Купить Premium", callback_data="buy_premium"),
            InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "👋 Привет! Я твой токсичный финансовый помощник 😈\n\n"
        "Моя задача - бить тебя по рукам ✋ до того, как сервисы сожрут твои деньги 💸. "
        "Вноси свои подписки, а я позабочусь, чтобы ты перестал спонсировать чужие яхты 🛥️.\n\n"
        "👇 Выбирай действие в меню:"
    )
    await message.answer(text, reply_markup=main_keyboard())

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    await message.answer("👑 <b>Панель Создателя</b>\n\n(На Vercel база данных отключена)")

@dp.message(Command("give_premium"), F.from_user.id == ADMIN_ID)
async def give_premium_cmd(message: Message):
    await message.answer("✅ Команда сработала.")

@dp.message(Command("send1"), F.from_user.id == ADMIN_ID)
async def broadcast_premium(message: Message):
    await message.answer("🚀 Рассылка...")

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять 🤷‍♂️. Ты и так в главном меню.", reply_markup=main_keyboard())
        return
    await state.clear()
    await message.answer("❌ Добавление подписки отменено. Выдыхай.", reply_markup=main_keyboard())

@dp.callback_query(F.data == "list_subs")
async def list_subscriptions(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])
    await callback.message.edit_text("🕸️ У тебя пока нет подписок (база отключена).", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("del_"))
async def delete_subscription(callback: CallbackQuery):
    await callback.answer("База отключена.")

@dp.callback_query(F.data == "add_sub")
async def start_add_sub(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSubState.title)
    await callback.message.edit_text("✍️ Вводи название сервиса (например: Яндекс, Netflix):\n\n<i>(Если передумал, жми /cancel)</i>")

@dp.message(AddSubState.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddSubState.price)
    await message.answer("💰 Сколько они с тебя сдирают каждый месяц? (Вводи число, например 299):")

@dp.message(AddSubState.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", ".").strip())
        if price <= 0: raise ValueError
    except ValueError:
        await message.answer("🤡 Давай нормальное число, без букв и шуток:")
        return
    await state.update_data(price=price)
    await state.set_state(AddSubState.day)
    await message.answer("📅 В какой день месяца происходит списание? (от 1 до 31):")

@dp.message(AddSubState.day)
async def process_day(message: Message, state: FSMContext):
    try:
        day = int(message.text.strip())
        if not (1 <= day <= 31): raise ValueError
    except ValueError:
        await message.answer("🤦‍♂️ В месяце от 1 до 31 дня. Попробуй еще раз:")
        return
    data = await state.get_data()
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subs")],
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="to_main")]
    ])
    await message.answer(f"✅ Готово. Я напомню тебе про <b>'{data['title']}'</b> за день до того, как они украдут твои {data['price']} ₽ 🥷.", reply_markup=keyboard)

@dp.callback_query(F.data == "buy_premium")
async def buy_premium_info(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить на Lava.top", url=LAVA_PAY_URL)],
        [InlineKeyboardButton(text="✅ Я оплатил (уведомить админа)", callback_data="notify_paid")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
    ])
    user_id = callback.from_user.id
    text = (
        "💎 <b>Premium доступ навсегда</b>\n\n"
        "• Безлимит на добавление подписок\n"
        "• Токсичные уведомления без ограничений\n\n"
        "📌 <b>Инструкция по оплате:</b>\n"
        f"1. Нажми кнопку <b>«Оплатить на Lava.top»</b>\n"
        f"2. При оплате укажи свой ID: <code>{user_id}</code>\n"
        f"3. После перевода нажми кнопку <b>«Я оплатил»</b> ниже 👇"
    )
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "notify_paid")
async def notify_admin_paid(callback: CallbackQuery):
    user = callback.from_user
    username = f"@{user.username}" if user.username else "без юзернейма"
    admin_msg = (
        "🔔 <b>Новая заявка на Premium!</b>\n\n"
        f"👤 Пользователь: {user.full_name} ({username})\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"
        f"Выдай доступ командой:\n<code>/give_premium {user.id}</code>"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_msg)
    except Exception:
        pass
    await callback.answer("Заявка отправлена создателю! 🚀", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("👋 Главное меню:", reply_markup=main_keyboard())
