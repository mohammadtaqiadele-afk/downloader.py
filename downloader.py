import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp
import asyncio
import subprocess
import sys

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من بات حرفه‌ای دانلودر تو هستم 🚀\n"
        "لینک یوتیوب یا اینستاگرام رو بفرست تا بپرسم چی می‌خوای."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "http" not in url:
        await update.message.reply_text("لطفاً یک لینک معتبر بفرست!")
        return

    context.user_data['target_url'] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 دانلود ویدیو", callback_data='dl_video'),
            InlineKeyboardButton("🎵 دانلود آهنگ (MP3)", callback_data='dl_audio')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "لینک دریافت شد! حالا انتخاب کن چه چیزی برات بفرستم:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('target_url')
    if not url:
        await query.edit_message_text("❌ خطا: لینکی پیدا نشد. لطفاً دوباره لینک بفرست.")
        return

    choice = query.data
    await query.edit_message_text(text="⏳ در حال دانلود و آماده‌سازی... لطفاً صبور باش.")

    try:
        # پاکسازی فایل کوکی اگر احیاناً جایی مونده باشه
        if os.path.exists('cookies.txt'):
            os.remove('cookies.txt')

        if choice == 'dl_video':
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloaded_media.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded', 'mweb']
                    }
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, 'rb') as f:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f)
            os.remove(filename)

        elif choice == 'dl_audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloaded_audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = os.path.splitext(filename)[0] + '.mp3'

            with open(filename, 'rb') as f:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f)
            os.remove(filename)

    except Exception as e:
        if os.path.exists('cookies.txt'):
            os.remove('cookies.txt')
        
        error_msg = f"خطا در دانلود:\n{str(e)}"
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=error_msg
        )

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN environment variable is missing!")
        return

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Professional Bot is running...")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            pass
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
