import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Your Movie Bot is LIVE on cloud!"
    )

app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .connect_timeout(60)
    .read_timeout(60)
    .build()
)

app.add_handler(CommandHandler("start", start))

print("Bot started...")
app.run_polling()
