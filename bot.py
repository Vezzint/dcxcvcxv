import asyncio
import random
from datetime import datetime, timedelta
import aiosqlite
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
DB_NAME = "subscriptions.db" 
LAVA_PAY_URL = "https://app.lava.top/products/9aad4276-e009-4438-969d-3cf175a430c2"

# Обязательно добавляем DefaultBotProperties для корректной работы
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class AddSubState(StatesGroup):
    title = State()
    price = State()
    day = State()

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                price REAL,
                billing_day INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_premium INTEGER DEFAULT 0
            )
        """)
        await db.commit()

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub", style="success"),
            InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subs", style="primary")
        ],
        [
            InlineKeyboardButton(text="⭐ Купить Premium", callback_data="buy_premium"),
            InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()

    text = (
        "👋 Привет! Я твой токсичный финансовый помощник 😈\n\n"
        "Моя задача - бить тебя по рукам ✋ до того, как сервисы сожрут твои деньги 💸. "
        "Вноси свои подписки, а я позабочусь, чтобы ты перестал спонсировать чужие яхты 🛥️.\n\n"
        "👇 Выбирай действие в меню:"
    )
    await message.answer(text, reply_markup=main_keyboard())

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM subscriptions")
        total_subs = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT SUM(price) FROM subscriptions")
        total_money = (await cursor.fetchone())[0] or 0
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = (await cursor.fetchone())[0]

    text = (
        "👑 <b>Секретная панель Создателя</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"💎 С Premium: <b>{premium_users}</b>\n"
        f"📝 Добавлено подписок: <b>{total_subs}</b>\n"
        f"💸 Сумма трат всех юзеров: <b>{total_money:.2f} ₽</b> в месяц\n\n"
        "<b>Команды управления:</b>\n"
        "• <code>/send1</code> - рассылка предложения Premium\n"
        "• <code>/give_premium &lt;ID&gt;</code> - вручную выдать Premium"
    )
    await message.answer(text)

@dp.message(Command("give_premium"), F.from_user.id == ADMIN_ID)
async def give_premium_cmd(message: Message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("⚠️ Используй: <code>/give_premium &lt;user_id&gt;</code>")
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ ID должен быть числом.")
        return
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (target_id,))
        await db.commit()
    await message.answer(f"✅ Пользователю <code>{target_id}</code> успешно выдан Premium!")
    try:
        await bot.send_message(
            target_id,
            "🎉 <b>Твой платеж подтвержден!</b>\n\nPremium статус активирован навсегда 👑. Все лимиты сняты!",
            reply_markup=main_keyboard()
        )
    except Exception:
        pass

@dp.message(Command("send1"), F.from_user.id == ADMIN_ID)
async def broadcast_premium(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        users = await cursor.fetchall()
    await message.answer(f"🚀 Начинаю рассылку для {len(users)} пользователей...")
    success = 0
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⭐ Купить Premium", callback_data="buy_premium")]])
    for (uid,) in users:
        try:
            await bot.send_message(
                uid,
                "💎 Хватит терпеть лимиты!\n\nПереходи на <b>Premium</b> и добавляй бесконечное количество подписок. Один раз взял - пользуешься всегда. Защити все свои деньги от скрытых списаний! 🛡️",
                reply_markup=keyboard
            )
            success += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await message.answer(f"✅ Рассылка завершена! Доставлено: {success} из {len(users)}.")

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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, title, price, billing_day FROM subscriptions WHERE user_id = ?", (callback.from_user.id,))
        rows = await cursor.fetchall()
    if not rows:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_sub", style="success")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
        ])
        await callback.message.edit_text("🕸️ У тебя пока нет подписок. Твой кошелек в безопасности (пока что) 🛡️.", reply_markup=keyboard)
        return
    total_month = sum(row[2] for row in rows)
    total_year = total_month * 12
    text = f"💸 Твои финансовые черные дыры 🕳️:\n\n"
    keyboard_buttons = []
    for sub_id, title, price, day in rows:
        text += f"▫️ {title} - {price} ₽ (списание {day}-го числа)\n"
        keyboard_buttons.append([InlineKeyboardButton(text=f"🗑️ Удалить {title}", callback_data=f"del_{sub_id}", style="danger")])
    text += f"\n💳 В месяц улетает: {total_month:.2f} ₽"
    text += f"\n🔥 За год ты сжигаешь: {total_year:.2f} ₽ 💀"
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="to_main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))

@dp.callback_query(F.data.startswith("del_"))
async def delete_subscription(callback: CallbackQuery):
    sub_id = int(callback.data.split("_")[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subscriptions WHERE id = ? AND user_id = ?", (sub_id, callback.from_user.id))
        await db.commit()
    await callback.answer("✂️ Подписка отсечена! Минус одна бессмысленная трата.")
    await list_subscriptions(callback)

@dp.callback_query(F.data == "add_sub")
async def start_add_sub(callback: CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT is_premium FROM users WHERE user_id = ?", (callback.from_user.id,))
        user_data = await cursor.fetchone()
        is_premium = user_data[0] if user_data else 0
        cursor = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id = ?", (callback.from_user.id,))
        count = (await cursor.fetchone())[0]
    if not is_premium and count >= 3:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Купить Premium", callback_data="buy_premium", style="primary")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")]
        ])
        await callback.message.edit_text("🛑 Лимит исчерпан! 3 подписки - это потолок для бесплатной версии 🐸.\n\n💎 Хочешь вести больше? Покупай Premium и не жадничай.", reply_markup=keyboard)
        return
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO subscriptions (user_id, title, price, billing_day) VALUES (?, ?, ?, ?)",
            (message.from_user.id, data["title"], data["price"], day)
        )
        await db.commit()
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subs", style="primary")],
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
        "• Токсичные уведомления без ограничений\n"
        "• Поддержка проекта\n\n"
        "📌 <b>Инструкция по оплате:</b>\n"
        f"1. Нажми кнопку <b>«Оплатить на Lava.top»</b>\n"
        f"2. При оплате (или в комментарии) укажи свой ID: <code>{user_id}</code>\n"
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
        f"Проверь поступление на Lava.top и выдай доступ командой:\n"
        f"<code>/give_premium {user.id}</code>"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_msg)
    except Exception:
        pass
    await callback.answer("Заявка отправлена создателю! Доступ будет активирован сразу после проверки оплаты 🚀", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("👋 Главное меню:", reply_markup=main_keyboard())
