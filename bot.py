import os
from pymongo import MongoClient
from rapidfuzz import process

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
OWNER_ID = 7938487616
ADMINS = [OWNER_ID]
def is_admin(user_id):
    return user_id in ADMINS
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
users_collection = db["users"]

collection.create_index([("file_name", "text")])

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
        
async def save_user(user):

    if not users_collection.find_one({"user_id": user.id}):

        users_collection.insert_one({
            "user_id": user.id,
            "name": user.first_name
        })

        print(f"✅ New User Saved: {user.first_name}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Allow only admins
    if update.effective_user.id not in ADMINS:
        return

    total_users = users_collection.count_documents({})

    await update.message.reply_text(
        f"📊 Bot Statistics\n\n👥 Total Users: {total_users}"
    )

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Prevent crash if no message
    if not update.message:
        return

    user_id = update.effective_user.id
    await save_user(update.effective_user)
    joined = await check_force_join(user_id, context)

    # If user NOT joined channels
    if not joined:

        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/+CZ5r2Hcn9fg3YWY0")],
            [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+zqWLUjg6wEw2ZGJk")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ Please join both channels to use this bot.",
            reply_markup=reply_markup
        )
        return

    # If joined
    await update.message.reply_text(
        "🎬 Movie Bot Ready!\n\nSend me a movie name."
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/broadcast Your message")
        return

    message_text = " ".join(context.args)

    users = users_collection.find()

    success = 0
    failed = 0

    status_msg = await update.message.reply_text("🚀 Broadcasting started...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=message_text
            )
            success += 1

        except:
            failed += 1

    await status_msg.edit_text(
        f"✅ Broadcast Complete!\n\n"
        f"👥 Success: {success}\n"
        f"❌ Failed/Blocked: {failed}"
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
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/+CZ5r2Hcn9fg3YWY0")],
            [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+zqWLUjg6wEw2ZGJk")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ Please join both channels to use this bot.",
            reply_markup=reply_markup
        )
        return

    query = update.message.text
    
    results = collection.find(
    {"$text": {"$search": query}}
).limit(5)

    found = False

    for movie in results:
        found = True
        await update.message.reply_document(movie["file_id"])

if not found:

    # Get all movie names
    all_movies = list(collection.find({}, {"file_name": 1}))

    movie_names = [m["file_name"] for m in all_movies]

    # Find closest match
    match = process.extractOne(query, movie_names)

    if match and match[1] > 70:   # similarity score
        similar_movie = collection.find_one({"file_name": match[0]})

        await update.message.reply_text(
            f"🎬 Did you mean: {match[0]} ?"
        )

        await update.message.reply_document(similar_movie["file_id"])

    else:
        await update.message.reply_text("❌ Movie not found.")

# ---------------- MAIN ----------------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    try:
        member1 = await context.bot.get_chat_member(FORCE_CHANNEL_1, user_id)
        member2 = await context.bot.get_chat_member(FORCE_CHANNEL_2, user_id)

        if member1.status in ["member", "administrator", "creator"] and \
           member2.status in ["member", "administrator", "creator"]:

            await query.edit_message_text(
                "✅ You have joined both channels! Now send a movie name."
            )

        else:
            await query.answer(
                "❌ You haven't joined both channels!",
                show_alert=True
            )

    except Exception as e:
        print("JOIN CHECK ERROR:", e)
        await query.answer(
            "⚠️ Bot must be admin in both channels!",
            show_alert=True
        )

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    # ✅ Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))

    # ✅ Button clicks (Force Join)
    app.add_handler(CallbackQueryHandler(button, pattern="check_join"))

    # ✅ Auto index movies from channel
    app.add_handler(MessageHandler(filters.Chat(CHANNEL_ID), auto_index))

    # ✅ User search
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    print("✅ Bot Started Successfully")

    app.run_polling()


if __name__ == "__main__":
    main()
