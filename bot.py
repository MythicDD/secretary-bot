import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import BusinessConnection, Message

from ai import get_ai_reply
from config import settings
from storage import PROMPTS, state

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
router = Router()


def is_owner(message: Message) -> bool:
    return message.from_user.id == settings.YOUR_USER_ID


# ── Новое Business подключение ───────────────────────────────────────────────
@router.business_connection()
async def on_connect(bc: BusinessConnection, bot: Bot):
    status = "✅ Подключён" if bc.is_enabled else "❌ Отключён"
    await bot.send_message(
        settings.YOUR_USER_ID,
        f"🔗 <b>Business подключение:</b> {status}\n"
        f"👤 {bc.user.full_name}\n"
        f"💬 Может отвечать: {'Да ✅' if bc.can_reply else 'Нет ❌'}",
        parse_mode="HTML",
    )


# ── Входящее сообщение в твой аккаунт ───────────────────────────────────────
@router.business_message()
async def on_business_message(message: Message, bot: Bot):
    if message.from_user.id == settings.YOUR_USER_ID:
        return

    conn_id   = message.business_connection_id
    user_name = message.from_user.full_name
    text      = message.text or "[медиа/файл/стикер]"
    tag       = "⏸ ПАУЗА" if state.is_paused else f"🤖 {state.active_prompt}"

    await bot.send_message(
        settings.YOUR_USER_ID,
        f"📩 <b>Сообщение [{tag}]</b>\n👤 {user_name}\n💬 {text}",
        parse_mode="HTML",
    )

    if state.is_paused:
        return

    try:
        reply = await get_ai_reply(text, user_name)
        await bot.send_message(
            message.chat.id,
            reply,
            business_connection_id=conn_id,
        )
        await bot.send_message(
            settings.YOUR_USER_ID,
            f"✅ <b>AI ответил:</b>\n<i>{reply}</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        logging.error(f"AI error: {e}")
        await bot.send_message(
            settings.YOUR_USER_ID,
            f"⚠️ Ошибка AI. Ответь <b>{user_name}</b> вручную!\n<code>{e}</code>",
            parse_mode="HTML",
        )


# ── Команды ──────────────────────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>AI Secretary Bot запущен!</b>\n\n"
        "Подключи меня к своему аккаунту:\n"
        "<b>Настройки → Telegram Business → Chatbots</b>\n\n"
        "⚡️ Команды:\n"
        "/status — состояние бота\n"
        "/pause — поставить на паузу\n"
        "/resume — возобновить\n"
        "/mode — сменить режим ответов",
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    if not is_owner(message):
        return
    s = "⏸ На паузе" if state.is_paused else "▶️ Активен"
    pause_info = f"\n📝 Причина: {state.pause_reason}" if state.is_paused else ""
    await message.answer(
        f"📊 <b>Статус:</b> {s}{pause_info}\n🤖 Режим: <code>{state.active_prompt}</code>",
        parse_mode="HTML",
    )


@router.message(Command("pause"))
async def cmd_pause(message: Message):
    if not is_owner(message):
        return
    args = message.text.split(maxsplit=1)
    state.is_paused = True
    state.pause_reason = args[1] if len(args) > 1 else "занят"
    await message.answer(
        f"⏸ <b>Пауза:</b> {state.pause_reason}\n\n/resume — возобновить",
        parse_mode="HTML",
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message):
    if not is_owner(message):
        return
    state.is_paused = False
    state.pause_reason = None
    await message.answer(
        f"▶️ <b>Бот снова активен!</b>\n🤖 Режим: <code>{state.active_prompt}</code>",
        parse_mode="HTML",
    )


@router.message(Command("mode"))
async def cmd_mode(message: Message):
    if not is_owner(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        modes = "\n".join([f"• <code>{k}</code>" for k in PROMPTS])
        await message.answer(
            f"🎭 <b>Доступные режимы:</b>\n{modes}\n\nПример: /mode sales",
            parse_mode="HTML",
        )
        return
    mode = args[1].strip()
    if mode not in PROMPTS:
        await message.answer(f"❌ Режим <code>{mode}</code> не найден", parse_mode="HTML")
        return
    state.active_prompt = mode
    await message.answer(f"✅ Режим переключён: <b>{mode}</b>", parse_mode="HTML")


# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp.include_router(router)
    logging.info("🤖 Secretary Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
