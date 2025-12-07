from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📁 File Saver Bot\n\n"
        "Send me any file (document, photo, video).\n"
        "I'll save it and you can retrieve it later.\n\n"
        "Commands:\n"
        "/list - List saved files\n"
        "/get <id> - Download a file"
    )

def save_file(update: Update, context: CallbackContext):
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
        
        update.message.reply_text(
            f"✅ File saved!\n"
            f"Name: {file_name}\n"
            f"ID: {file_unique_id}"
        )
        
    except Exception as e:
        print(f"Error: {e}")

def list_files(update: Update, context: CallbackContext):
    if not files:
        update.message.reply_text("No files saved yet.")
        return
    
    text = "Saved files:\n\n"
    for uid, info in files.items():
        text += f"📁 {info['name']}\nID: {uid}\n\n"
    
    update.message.reply_text(text)

def get_file(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Use: /get <file_id>")
        return
    
    file_id = context.args[0]
    
    if file_id not in files:
        update.message.reply_text("File not found.")
        return
    
    update.message.reply_document(files[file_id]["file_id"])

def main():
    if not TOKEN:
        print("ERROR: No token set!")
        return
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list", list_files))
    dp.add_handler(CommandHandler("get", get_file))
    dp.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video, save_file))
    
    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
