import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from pymongo import MongoClient

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set")

# ---------------- DATABASE ----------------

client = MongoClient(MONGO_URL)
db = client["moviebot"]
movies = db["movies"]

# Create index for FAST search (VERY IMPORTANT)
movies.create_index("title")

print("✅ MongoDB Connected Successfully")

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Movie Bot is LIVE!\n\n"
        "Send movies to auto-index.\n"
        "Use:\n"
        "/movie <name> to search."
    )

# ---------------- AUTO INDEX ----------------

async def auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    file = message.document or message.video
    if not file:
        return

    title = (
        message.caption
        or file.file_name
        or "unknown movie"
    ).lower()

    file_id = file.file_id
    size = file.file_size

    # Avoid duplicates
    if movies.find_one({"file_id": file_id}):
        return

    movies.insert_one({
        "title": title,
        "file_id": file_id,
        "size": size
    })

    await message.reply_text("✅ Movie indexed successfully!")

# ---------------- SEARCH ----------------

async def movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n/movie movie_name"
        )
        return

    query = " ".join(context.args).lower()

    results = movies.find({
        "title": {"$regex": query}
    }).limit(5)

    found = False

    for movie in results:
        found = True
        await update.message.reply_document(movie["file_id"])

    if not found:
        await update.message.reply_text(
            "❌ No movie found."
        )

# ---------------- APP ----------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("movie", movie_search))

# Auto index handler
app.add_handler(
    MessageHandler(
        filters.Document.ALL | filters.VIDEO,
        auto_index
    )
)

print("🚀 Bot Started Successfully")

app.run_polling()
