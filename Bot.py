#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8682713815:AAGgDMvxbjekGqZVFsriY3iAs6lP9ssEVDM'
YOUR_USER_ID = 8259326703
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 8000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('👋 Привет! Я бот-пересыльщик.\n\nОтправляйте мне:\n• Текстовые сообщения\n• Фото\n• Видео\n\nЯ перешлю их моему владельцу.')

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = "📌 **Как мне вам ответить?**\n\nЧтобы владелец бота мог вам ответить, выполните следующие шаги:\n\n1️⃣ Откройте **Настройки** Telegram\n2️⃣ Перейдите в **Конфиденциальность**\n3️⃣ Выберите **Личные сообщения**\n4️⃣ Установите опцию **Кто может писать мне** → **Все**"
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        message = update.message
        user_info = f"📨 **Новое сообщение**\n\n**От:** {user.first_name} {user.last_name or ''}\n**ID:** `{user.id}`\n**Username:** @{user.username or 'отсутствует'}\n\n**Текст:**\n{message.text}"
        await context.bot.send_message(chat_id=YOUR_USER_ID, text=user_info, parse_mode='Markdown')
        await message.reply_text("✅ Сообщение доставлено владельцу!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply_text("❌ Произошла ошибка.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        message = update.message
        photo = message.photo[-1]
        caption = f"📸 **Фото от** @{user.username or 'пользователя'}"
        if message.caption:
            caption += f"\n\n**Подпись:** {message.caption}"
        await context.bot.send_photo(chat_id=YOUR_USER_ID, photo=photo.file_id, caption=caption, parse_mode='Markdown')
        await message.reply_text("✅ Фото доставлено владельцу!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        message = update.message
        caption = f"🎥 **Видео от** @{user.username or 'пользователя'}"
        if message.caption:
            caption += f"\n\n**Подпись:** {message.caption}"
        await context.bot.send_video(chat_id=YOUR_USER_ID, video=message.video.file_id, caption=caption, parse_mode='Markdown')
        await message.reply_text("✅ Видео доставлено владельцу!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def main():
    app = Application.builder().token(TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    webhook_url = f"{URL}/telegram"
    await app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"Webhook установлен на {webhook_url}")
    
    async def telegram(request: Request) -> Response:
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.update_queue.put(update)
            return Response()
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return Response(status_code=500)
    
    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")
    
    starlette_app = Starlette(routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ])
    
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app=starlette_app, host="0.0.0.0", port=PORT, log_level="info"))
    
    async with app:
        await app.start()
        await server.serve()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())