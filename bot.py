import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN:
raise RuntimeError("BOT_TOKEN missing")

if not MONGO_URL:
raise RuntimeError("MONGO_URL missing")

if not CHANNEL_ID:
raise RuntimeError("CHANNEL_ID missing")

CHANNEL_ID = int(CHANNEL_ID)

client = MongoClient(MONGO_URL)
db = client["movie_db"]
collection = db["movies"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("🎬 Movie Bot is Running!")

async def auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.channel_post and update.channel_post.document:

    file_name = update.channel_post.document.file_name
    message_id = update.channel_post.message_id

    collection.update_one(
        {"file_name": file_name},
        {"$set": {"message_id": message_id}},
        upsert=True
    )

    print("Indexed:", file_name)

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

if not context.args:
    await update.message.reply_text("Use like:\n/movie avengers")
    return

query = " ".join(context.args)

results = collection.find({
    "file_name": {"$regex": query, "$options": "i"}
}).limit(5)

found = False

for film in results:
    found = True
    await context.bot.forward_message(
        chat_id=update.effective_chat.id,
        from_chat_id=CHANNEL_ID,
        message_id=film["message_id"]
    )

if not found:
    await update.message.reply_text("Movie not found.")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("movie", movie))
app.add_handler(MessageHandler(filters.ALL, auto_index))

print("🚀 Bot Running...")
app.run_polling()
