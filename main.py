import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# Ichki fayllar
from ai_service import ask_ai
from config import OWNER_ID, REQUIRED_CHANNELS
from database import (
    init_db, add_user, get_user, add_almaz, get_leaderboard,
    add_admin, remove_admin, list_admins, is_admin,
    add_group, list_groups,
    add_payment, get_pending_payments, confirm_payment,
    create_listing, add_listing_image, set_listing_meta
)

# --- ENV yuklash ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Foydalanuvchi holatini aniqlash ---
AI_MODE = {}

# --- FSM: Akkount Sotish ---
class SellStates(StatesGroup):
    TITLE = State()
    IMAGES = State()
    META = State()
    RESERVE = State()
    ISSUE = State()
    PRICE = State()

# --- Asosiy menyu ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 AI bilan suhbat")],
        [KeyboardButton(text="💎 Almaz ishlash"), KeyboardButton(text="📊 Profilim")],
        [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="🛒 Akkount Bozor")],
        [KeyboardButton(text="💰 Almaz sotib olish")]
    ],
    resize_keyboard=True
)

# --- Kanal obuna tekshirish ---
async def check_subscription(user_id):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return not_subscribed

# --- /start ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    not_subscribed = await check_subscription(message.from_user.id)
    if not_subscribed:
        text = "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:\n\n"
        for ch in not_subscribed:
            text += f"👉 {ch}\n"
        text += "\n✅ A’zolikni tasdiqlash uchun /start ni qayta yuboring."
        return await message.answer(text)

    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    await add_user(message.from_user.id, message.from_user.username or "Noma’lum", ref_id)
    AI_MODE[message.from_user.id] = False
    await message.answer(
        f"Salom, {message.from_user.first_name}! 👋\n"
        "Men Free Fire uchun yaratilgan sun’iy intellektli yordamchi botman.\n"
        "Quyidagi menyudan tanlang 👇",
        reply_markup=main_menu
    )

# --- 🧠 AI bilan suhbat ---
@dp.message(lambda m: m.text == "🧠 AI bilan suhbat")
async def ai_chat(message: Message):
    AI_MODE[message.from_user.id] = True
    await message.answer("🤖 AI rejimi yoqildi. Savolingizni yozing.\n\nOrqaga qaytish uchun ⬅️ Orqaga tugmasini bosing.")

# --- Orqaga ---
@dp.message(lambda m: m.text == "⬅️ Orqaga")
async def go_back(message: Message):
    AI_MODE[message.from_user.id] = False
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=main_menu)

# --- 💎 Almaz ishlash ---
@dp.message(lambda m: m.text == "💎 Almaz ishlash")
async def earn_almaz(message: Message):
    AI_MODE[message.from_user.id] = False
    me = await bot.get_me()
    await message.answer(
        "💎 Almaz ishlash yo‘llari:\n"
        "1) Do‘stlaringizni taklif qiling (har bir yangi foydalanuvchi = 10 Almaz).\n"
        "👇 Sizning havolangiz:\n"
        f"https://t.me/{me.username}?start={message.from_user.id}"
    )

# --- 📊 Profil ---
@dp.message(lambda m: m.text == "📊 Profilim")
async def show_profile(message: Message):
    AI_MODE[message.from_user.id] = False
    user = await get_user(message.from_user.id)
    if not user:
        await add_user(message.from_user.id, message.from_user.username or "Noma’lum")
        user = await get_user(message.from_user.id)
    almaz = user[3]
    me = await bot.get_me()
    await message.answer(
        f"👤 Profil: @{user[2] or 'Anonim'}\n"
        f"💎 Almaz: {almaz}\n"
        f"🔗 Referral link: https://t.me/{me.username}?start={message.from_user.id}"
    )

# --- 🏆 Reyting ---
@dp.message(lambda m: m.text == "🏆 Reyting")
async def leaderboard(message: Message):
    AI_MODE[message.from_user.id] = False
    leaders = await get_leaderboard()
    if not leaders:
        return await message.answer("Hali reyting bo‘sh.")
    text = "🏆 Eng faol foydalanuvchilar:\n\n"
    for i, (username, almaz) in enumerate(leaders, 1):
        text += f"{i}. @{username or 'Anonim'} — 💎 {almaz}\n"
    await message.answer(text)

# --- 💰 Almaz sotib olish ---
@dp.message(lambda m: m.text == "💰 Almaz sotib olish")
async def buy_almaz(message: Message):
    AI_MODE[message.from_user.id] = False
    text = (
        "💰 <b>Almaz sotib olish</b>\n\n"
        "1️⃣ 10 000 so‘m → 100 Almaz\n"
        "2️⃣ 25 000 so‘m → 300 Almaz\n"
        "3️⃣ 40 000 so‘m → 500 Almaz\n\n"
        "💳 To‘lov: Click / Payme / Telegram Stars\n"
        "Raqam: <b>+998 99 123 45 67</b>\n\n"
        "To‘lovdan so‘ng quyidagicha yozing:\n"
        "<code>10000 123456789</code> (summa + ID)"
    )
    await message.answer(text, parse_mode="HTML")

# --- 🛒 Akkount Bozor ---
@dp.message(lambda m: m.text == "🛒 Akkount Bozor")
async def open_market(message: Message):
    AI_MODE[message.from_user.id] = False
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Akkount Sotish")],
            [KeyboardButton(text="🟡 Akkount Sotib olish")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🛒 <b>Akkount Bozoriga xush kelibsiz!</b>\n\nQuyidagilardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# --- 🟢 Akkount Sotish FSM ---
@dp.message(lambda m: m.text == "🟢 Akkount Sotish")
async def start_sell(message: Message, state: FSMContext):
    await message.answer(
        "📋 Akkount sarlavhasini kiriting.\n\n"
        "Masalan:\n"
        "<i>Akkount Leveli: 55\nLayklar: 5000\nEmotsiyalar: 50\nEvolyutsiyalar: 5\nFutbolkalar: 55\nQo‘shimcha ma’lumot bo‘lsa yozing.</i>",
        parse_mode="HTML"
    )
    await state.set_state(SellStates.TITLE)

@dp.message(SellStates.TITLE)
async def sell_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📸 Endi akkount rasmlarini yuboring (barcha rasmlarni birlashtirib, bir jo‘natishda yuboring, maksimal 10 ta).")
    await state.set_state(SellStates.IMAGES)

@dp.message(SellStates.IMAGES, F.photo)
async def sell_images(message: Message, state: FSMContext):
    photos = [p.file_id for p in message.photo]
    if len(photos) > 10:
        return await message.answer("❗ Maksimal 10 ta rasm jo‘natish mumkin.")
    await state.update_data(images=photos)
    await message.answer("🔗 Akkount qaysi xizmatlarga ulangan? (Masalan: Google, Facebook, VK, WA)")
    await state.set_state(SellStates.META)

@dp.message(SellStates.META)
async def sell_meta(message: Message, state: FSMContext):
    await state.update_data(linked=message.text)
    await message.answer("📧 Rezerv Gmail mavjudmi? (ha / yo‘q)")
    await state.set_state(SellStates.RESERVE)

@dp.message(SellStates.RESERVE)
async def sell_reserve(message: Message, state: FSMContext):
    text = message.text.lower()
    await state.update_data(reserve=(text in ["ha", "bor", "yes"]))
    await message.answer("⚠️ Akkountda muammo bormi? (ban, blok, priv yo‘qolgan)? Agar yo‘q bo‘lsa 'yo‘q' deb yozing.")
    await state.set_state(SellStates.ISSUE)

@dp.message(SellStates.ISSUE)
async def sell_issue(message: Message, state: FSMContext):
    desc = message.text
    has_issue = desc.lower() != "yo‘q"
    await state.update_data(issue=desc, has_issue=has_issue)
    await message.answer("💰 Akkount narxini kiriting (so‘mda). Masalan: 250.000")
    await state.set_state(SellStates.PRICE)

@dp.message(SellStates.PRICE)
async def sell_price(message: Message, state: FSMContext):
    text = message.text.replace(".", "")
    if not text.isdigit():
        return await message.answer("❗ Faqat raqam kiriting. Masalan: 250.000")
    price = int(text)
    data = await state.get_data()

    listing_id = await create_listing(message.from_user.id, data["title"], data["issue"], price)
    for i, file_id in enumerate(data["images"], start=1):
        await add_listing_image(listing_id, file_id, i)
    await set_listing_meta(listing_id, data["linked"], int(data["reserve"]), int(data["has_issue"]), data["issue"])

    caption = (
        f"📦 <b>Yangi Akkount</b>\n\n"
        f"{data['title']}\n\n"
        f"💰 Narx: <b>{price:,} so‘m</b>\n"
        f"🔗 Ulangan: {data['linked']}\n"
        f"📧 Rezerv Gmail: {'✅' if data['reserve'] else '❌'}\n"
        f"⚠️ Muammo: {data['issue']}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ To‘g‘ri", callback_data=f"approve:{listing_id}")],
            [InlineKeyboardButton(text="❌ Noto‘g‘ri", callback_data=f"reject:{listing_id}")],
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit:{listing_id}")]
        ]
    )

    admins = await list_admins()
    if admins:
        await bot.send_message(admins[0][0], caption, parse_mode="HTML", reply_markup=kb)

    await message.answer("✅ Ma’lumotlaringiz yuborildi. Admin tasdiqlagandan so‘ng e’lon joylanadi.", reply_markup=main_menu)
    await state.clear()

# --- 🟡 Akkount Sotib olish ---
@dp.message(lambda m: m.text == "🟡 Akkount Sotib olish")
async def buy_menu(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 100 000 - 200 000 so‘m")],
            [KeyboardButton(text="💸 200 000 - 300 000 so‘m")],
            [KeyboardButton(text="💸 300 000 - 400 000 so‘m")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )
    await message.answer("💰 Sizga mos narx oralig‘ini tanlang:", reply_markup=keyboard)

# --- AI javoblari ---
@dp.message()
async def handle_ai(message: Message):
    if AI_MODE.get(message.from_user.id):
        await message.answer("🤖 AI javob tayyorlamoqda...")
        reply = await ask_ai(message.text or "")
        await message.answer(reply)
    else:
        await message.answer("Iltimos, menyudan kerakli bo‘limni tanlang 👇", reply_markup=main_menu)

# --- BOTNI ISHGA TUSHIRISH ---
async def main():
    await init_db()
    print("✅ Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
