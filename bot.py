from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import os

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "files.json"

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        files = json.load(f)
else:
    files = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(files, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 File Saver Bot\n\n"
        "Send me any file (document, photo, video).\n"
        "I'll save it and you can retrieve it later.\n\n"
        "Commands:\n"
        "/list - List saved files\n"
        "/get <id> - Download a file"
    )

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.document:
            file = update.message.document
            file_name = file.file_name or "Document"
        elif update.message.photo:
            file = update.message.photo[-1]
            file_name = "Photo"
        elif update.message.video:
            file = update.message.video
            file_name = "Video"
        else:
            return
        
        file_id = file.file_id
        file_unique_id = file.file_unique_id
        
        files[file_unique_id] = {
            "file_id": file_id,
            "name": file_name
        }
        
        save_data()
        
        await update.message.reply_text(
            f"✅ File saved!\n"
            f"Name: {file_name}\n"
            f"ID: {file_unique_id}"
        )
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Error saving file.")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not files:
        await update.message.reply_text("No files saved yet.")
        return
    
    text = "Saved files:\n\n"
    for uid, info in files.items():
        text += f"📁 {info['name']}\nID: `{uid}`\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /get <file_id>")
        return
    
    file_id = context.args[0]
    
    if file_id not in files:
        await update.message.reply_text("File not found.")
        return
    
    await update.message.reply_document(files[file_id]["file_id"])

def main():
    if not TOKEN:
        print("ERROR: No token set!")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_files))
    app.add_handler(CommandHandler("get", get_file))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, save_file))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
