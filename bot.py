from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import os
import time

# Get token from environment variable
TOKEN = os.environ.get("TOKEN")

DATA_FILE = "files.json"

# Load data with error handling
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading data file: {e}")
        print("⚠️ Starting with empty data.")
    return {}

files = load_data()

# Save data with error handling
def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(files, f, indent=4)
    except (IOError, TypeError) as e:
        print(f"⚠️ Error saving data: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        await update.message.reply_text(
            "📁 File Saver Bot\n\n"
            "Send me any file (document, photo, video, audio, voice).\n"
            "I'll save it on Telegram's servers.\n\n"
            "Commands:\n"
            "/list - Show all saved files\n"
            "/get <id> - Download a file by ID\n"
            "/delete <id> - Remove a file from list\n\n"
            "⚠️ Note: Files are stored on Telegram servers, not locally."
        )
    except Exception as e:
        print(f"⚠️ Error in start command: {e}")

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return
            
        # Determine file type
        file = None
        file_name = "Unknown File"
        
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
        
        if not file:
            await update.message.reply_text("❌ Could not process file.")
            return
        
        file_id = file.file_id
        file_unique_id = file.file_unique_id
        
        # Store in dictionary
        files[file_unique_id] = {
            "file_id": file_id,
            "name": file_name,
            "type": file_name.split()[-1].lower() if " " in file_name else "file"
        }
        
        save_data()
        
        await update.message.reply_text(
            f"✅ File saved!\n\n"
            f"📝 Name: {file_name}\n"
            f"🔑 ID: `{file_unique_id}`\n"
            f"💾 Type: {files[file_unique_id]['type'].title()}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error saving file: {e}")
        try:
            await update.message.reply_text("❌ Error saving file. Please try again.")
        except:
            pass  # Ignore if we can't send message

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if not files:
            await update.message.reply_text("📭 No files saved yet.")
            return
        
        text = "📂 Saved files:\n\n"
        for i, (uid, info) in enumerate(files.items(), 1):
            text += f"{i}. {info['name']}\n   ID: `{uid}`\n\n"
        
        # Telegram has 4096 character limit
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (list truncated)"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ Error listing files: {e}")
        try:
            await update.message.reply_text("❌ Error listing files.")
        except:
            pass

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
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
        await update.message.reply_document(
            file_id, 
            caption=f"📁 {file_info['name']}\nID: `{uid}`",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error getting file: {e}")
        try:
            await update.message.reply_text("❌ Error sending file. It may have expired.")
        except:
            pass

async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
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
            
    except Exception as e:
        print(f"⚠️ Error deleting file: {e}")
        try:
            await update.message.reply_text("❌ Error deleting file.")
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot."""
    try:
        print(f"⚠️ Update {update} caused error {context.error}")
    except:
        print("⚠️ Error in error handler itself")

def main():
    # Check token
    if not TOKEN:
        print("❌ ERROR: TOKEN environment variable not set!")
        print("Please set TOKEN in Railway variables.")
        return
    
    # Auto-restart loop
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            print(f"🚀 Starting bot (attempt {restart_count + 1}/{max_restarts})...")
            
            app = ApplicationBuilder().token(TOKEN).build()
            
            # Add error handler
            app.add_error_handler(error_handler)
            
            # Add command handlers
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("list", list_files))
            app.add_handler(CommandHandler("get", get_file))
            app.add_handler(CommandHandler("delete", delete_file))
            app.add_handler(CommandHandler("help", start))
            
            # Add file handler
            app.add_handler(MessageHandler(
                filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
                save_file
            ))
            
            print("🤖 Bot is running...")
            app.run_polling()
            
        except Exception as e:
            restart_count += 1
            print(f"🤖 Bot crashed: {e}")
            print(f"🔄 Restarting in 10 seconds... ({restart_count}/{max_restarts})")
            
            if "InvalidToken" in str(e):
                print("❌ INVALID TOKEN! Check Railway variables.")
                break
            elif "Conflict" in str(e):
                print("❌ Another instance is running. Waiting...")
                time.sleep(30)
            else:
                time.sleep(10)
    
    print("🛑 Bot stopped. Too many crashes.")

if __name__ == "__main__":
    main()
