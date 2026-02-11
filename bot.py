import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = MongoClient(MONGO_URL)
db = client["movie_db"]
collection = db["movies"]

Start command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("🎬 Movie Bot is Ready!\nSend /movie movie_name")

Auto Index movies from channel

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

Search command

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):

if not context.args:
    await update.message.reply_text("Send like this:\n/movie avengers")
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
    await update.message.reply_text("❌ Movie not found.")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("movie", movie))

Listen to channel posts

app.add_handler(MessageHandler(filters.ALL, auto_index))

print("🚀 Bot Running...")
app.run_polling()
