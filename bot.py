import os
from pymongo import MongoClient
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing")


# MongoDB
client = MongoClient(MONGO_URL)
db = client["movie_bot"]
collection = db["movies"]

print("✅ MongoDB Connected Successfully")


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Movie Bot Ready!\n\nJust send me a movie name."
    )


# AUTO INDEX WHEN FILE POSTED IN CHANNEL
async def auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RAW UPDATE:", update)

    msg = update.channel_post
    if not msg:
        return

    file_id = None
    file_name = "Unknown"

    if msg.document:
        file_id = msg.document.file_id
        file_name = msg.document.file_name or "Document"

    elif msg.video:
        file_id = msg.video.file_id
        file_name = msg.video.file_name or "Video"

    if file_id:

        if collection.find_one({"file_id": file_id}):
            return

        collection.insert_one({
            "file_name": file_name.lower(),
            "file_id": file_id
        })

        print(f"✅ Indexed: {file_name}")


# SEARCH MOVIE
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    query = update.message.text.lower()

    results = collection.find(
        {"file_name": {"$regex": query, "$options": "i"}}
    ).limit(5)

    found = False

    for movie in results:
        found = True
        await update.message.reply_document(movie["file_id"])

    if not found:
        await update.message.reply_text("❌ Movie not found.")


# ---------------- MAIN ----------------

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.Chat(CHANNEL_ID), auto_index)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    print("✅ Bot Started Successfully")

    app.run_polling()


if __name__ == "__main__":
    main()
