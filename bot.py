from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import os

# ⚠️ REPLACE THIS WITH YOUR ACTUAL BOT TOKEN ⚠️
TOKEN = os.environ.get("8314573143:AAFsbCzpqwr9XLwjB66k8rC7uI7lzOPdVMg")

DATA_FILE = "files.json"

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        files = json.load(f)
else:
    files = {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(files, f, indent=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 File Saver Bot\n\n"
        "Send me any file (document, photo, video, audio, voice).\n"
        "I'll save it on Telegram's servers.\n\n"
        "Commands:\n"
        "/list - Show all saved files\n"
        "/get <id> - Download a file by ID\n"
        "/delete <id> - Remove a file from list"
    )


async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Determine file type
    if message.document:
        file = message.document
        file_name = file.file_name or "Document"
    elif message.photo:
        file = message.photo[-1]
        file_name = "Photo"
    elif message.video:
        file = message.video
        file_name = "Video"
    elif message.audio:
        file = message.audio
        file_name = getattr(file, "file_name", "Audio")
    elif message.voice:
        file = message.voice
        file_name = "Voice Message"
    else:
        await update.message.reply_text("Please send a file (document, photo, video, audio, or voice).")
        return
    
    file_id = file.file_id
    file_unique_id = file.file_unique_id
    
    # Store in dictionary
    files[file_unique_id] = {
        "file_id": file_id,
        "name": file_name,
        "type": file_name.split()[-1].lower()
    }
    
    save_data()
    
    await update.message.reply_text(
        f"✅ File saved!\n\n"
        f"📝 Name: {file_name}\n"
        f"🔑 ID: `{file_unique_id}`\n"
        f"💾 Type: {file_name.split()[-1]}",
        parse_mode="Markdown"
    )


async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not files:
        await update.message.reply_text("📭 No files saved yet.")
        return
    
    text = "📂 Saved files:\n\n"
    for i, (uid, info) in enumerate(files.items(), 1):
        text += f"{i}. {info['name']}\n   ID: `{uid}`\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /get <file_id>\nUse /list to see IDs.")
        return
    
    uid = context.args[0]
    
    if uid not in files:
        await update.message.reply_text("❌ File not found.")
        return
    
    file_info = files[uid]
    file_id = file_info["file_id"]
    
    # Send file back
    try:
        await update.message.reply_document(file_id, caption=f"📁 {file_info['name']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending file: {e}")


async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete <file_id>")
        return
    
    uid = context.args[0]
    
    if uid in files:
        del files[uid]
        save_data()
        await update.message.reply_text("✅ File removed from list.")
    else:
        await update.message.reply_text("❌ File not found.")


def main():
    # Check token
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: You must replace TOKEN with your bot token!")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_files))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(CommandHandler("delete", delete_file))
    
    # Handle all file types
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
        save_file
    ))
    
    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()