import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing")

# MongoDB Connection
client = MongoClient(MONGO_URL)
db = client["movie_bot"]
collection = db["movies"]

print("✅ MongoDB Connected Successfully")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Movie Bot is LIVE on Cloud!")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("✅ Bot Started Successfully")

app.run_polling()
