import os
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,   # ⭐ ADD THIS
    ContextTypes,
    filters,
)
    
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
FORCE_CHANNEL_1 = -1003505309336
FORCE_CHANNEL_2 = -1003747985447
CHANNEL_1_LINK = "https://t.me/+CZ5r2Hcn9fg3YWY0"
CHANNEL_2_LINK = "https://t.me/+zqWLUjg6wEw2ZGJk"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing")


# MongoDB
client = MongoClient(MONGO_URL)
db = client["movie_bot"]
collection = db["movies"]

print("✅ MongoDB Connected Successfully")

async def check_force_join(user_id, context):

    try:
        member1 = await context.bot.get_chat_member(FORCE_CHANNEL_1, user_id)
        member2 = await context.bot.get_chat_member(FORCE_CHANNEL_2, user_id)

        if member1.status in ["member", "administrator", "creator"] and \
           member2.status in ["member", "administrator", "creator"]:
            return True

        return False

    except:
        return False
        
# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    joined = await check_force_join(user_id, context)

    if not joined:

    keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/+zqWLUjg6wEw2ZGJk")],
            [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+CZ5r2Hcn9fg3YWY0")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ Please join both channels to use this bot.",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text(
        "🎬 Movie Bot Ready!\n\nSend me a movie name."
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    joined = await check_force_join(user_id, context)

    if joined:
            await query.edit_message_text(
            "✅ You can now use the bot!\nSend a movie name."
        )
    else:
        await query.answer(
            "❌ You haven't joined the channels yet!",
            show_alert=True
        )

# AUTO INDEX WHEN FILE POSTED IN CHANNEL
async def auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.channel_post:
        print("CHANNEL ID:", update.channel_post.chat.id)
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

user_id = update.effective_user.id
joined = await check_force_join(user_id, context)

if not joined:

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("📢 Join Channel 2", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ Please join both channels to use this bot.",
        reply_markup=reply_markup
    )
    return

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
    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(
        MessageHandler(filters.ALL, auto_index)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    print("✅ Bot Started Successfully")

    app.run_polling()


if __name__ == "__main__":
    main()
