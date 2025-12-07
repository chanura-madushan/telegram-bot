from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import json
import os
import time
from datetime import datetime

# Get token from environment variable
TOKEN = os.environ.get("TOKEN")

DATA_FILE = "files.json"
FOLDERS_FILE = "folders.json"

# Load data with error handling
def load_json_file(filename, default={}):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading {filename}: {e}")
        print(f"⚠️ Starting with empty data for {filename}.")
    return default

# Save data with error handling
def save_json_file(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except (IOError, TypeError) as e:
        print(f"⚠️ Error saving {filename}: {e}")
        return False

# Load data
files = load_json_file(DATA_FILE, {})
folders = load_json_file(FOLDERS_FILE, {
    "default": {"name": "Default", "files": [], "created": str(datetime.now())}
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        await update.message.reply_text(
            "📁 **Advanced File Saver Bot** 📁\n\n"
            "📤 **Send me any file** (document, photo, video, audio, voice)\n"
            "I'll save it on Telegram's servers.\n\n"
            "📂 **Folder Commands:**\n"
            "/folders - List all folders\n"
            "/create <name> - Create new folder\n"
            "/rename <old> <new> - Rename folder\n"
            "/deletefolder <name> - Delete folder (moves files to Default)\n"
            "/setfolder <name> - Set active folder\n"
            "/move <file_id> <folder> - Move file to folder\n\n"
            "📋 **File Commands:**\n"
            "/list - List files in current folder\n"
            "/listall - List all files\n"
            "/get <file_id> - Download a file\n"
            "/delete <file_id> - Delete file\n"
            "/search <keyword> - Search files\n\n"
            "📊 **Current Folder:** Default\n"
            "💡 Use /setfolder to change folder"
        )
    except Exception as e:
        print(f"⚠️ Error in start command: {e}")

async def create_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if not context.args:
            await update.message.reply_text("Usage: /create <folder_name>")
            return
        
        folder_name = " ".join(context.args).strip()[:50]  # Limit name length
        
        if folder_name.lower() in [f.lower() for f in folders.keys()]:
            await update.message.reply_text(f"❌ Folder '{folder_name}' already exists!")
            return
        
        # Create folder
        folders[folder_name.lower()] = {
            "name": folder_name,
            "files": [],
            "created": str(datetime.now()),
            "creator": update.message.from_user.id if update.message.from_user else "unknown"
        }
        
        save_json_file(FOLDERS_FILE, folders)
        
        await update.message.reply_text(
            f"✅ Folder created: **{folder_name}**\n"
            f"Use: `/setfolder {folder_name}` to make it active",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error creating folder: {e}")
        try:
            await update.message.reply_text("❌ Error creating folder.")
        except:
            pass

async def list_folders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if len(folders) == 0:
            await update.message.reply_text("📭 No folders created yet.\nUse /create <name> to make one.")
            return
        
        text = "📂 **Your Folders:**\n\n"
        for folder_id, folder_info in folders.items():
            file_count = len(folder_info["files"])
            text += f"• **{folder_info['name']}**\n"
            text += f"  📁 Files: {file_count}\n"
            text += f"  🔑 ID: `{folder_id}`\n\n"
        
        text += "\n💡 Use `/setfolder <name>` to switch folders"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"⚠️ Error listing folders: {e}")
        try:
            await update.message.reply_text("❌ Error listing folders.")
        except:
            pass

async def set_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        user_id = str(update.message.from_user.id) if update.message.from_user else "global"
        
        if not context.args:
            await update.message.reply_text("Usage: /setfolder <folder_name>\nUse /folders to see available folders")
            return
        
        folder_name = " ".join(context.args).strip().lower()
        
        if folder_name not in folders:
            # Try case-insensitive search
            for key in folders.keys():
                if key.lower() == folder_name.lower():
                    folder_name = key
                    break
            else:
                await update.message.reply_text(f"❌ Folder not found!\nUse /folders to see available folders")
                return
        
        # Store user's active folder (simplified - in real use, store in database)
        context.user_data['active_folder'] = folder_name
        
        folder_info = folders[folder_name]
        file_count = len(folder_info["files"])
        
        await update.message.reply_text(
            f"✅ Active folder set to: **{folder_info['name']}**\n"
            f"📁 Files in folder: {file_count}\n"
            f"⏰ Created: {folder_info['created'][:10]}\n\n"
            f"Now all files will be saved here. Use `/list` to see files.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error setting folder: {e}")
        try:
            await update.message.reply_text("❌ Error setting folder.")
        except:
            pass

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message:
            return
        
        # Get active folder for user
        active_folder = context.user_data.get('active_folder', 'default')
        if active_folder not in folders:
            active_folder = 'default'
        
        # Determine file type
        file = None
        file_name = "Unknown File"
        file_type = "file"
        
        if message.document:
            file = message.document
            file_name = file.file_name or "Document"
            file_type = "document"
        elif message.photo:
            file = message.photo[-1]
            file_name = "Photo"
            file_type = "photo"
        elif message.video:
            file = message.video
            file_name = "Video"
            file_type = "video"
        elif message.audio:
            file = message.audio
            file_name = getattr(file, "file_name", "Audio")
            file_type = "audio"
        elif message.voice:
            file = message.voice
            file_name = "Voice Message"
            file_type = "voice"
        else:
            await update.message.reply_text("Please send a file (document, photo, video, audio, or voice).")
            return
        
        if not file:
            await update.message.reply_text("❌ Could not process file.")
            return
        
        file_id = file.file_id
        file_unique_id = file.file_unique_id
        
        # Store file info
        files[file_unique_id] = {
            "file_id": file_id,
            "name": file_name,
            "type": file_type,
            "folder": active_folder,
            "added": str(datetime.now()),
            "user_id": update.message.from_user.id if update.message.from_user else "unknown"
        }
        
        # Add to folder
        if file_unique_id not in folders[active_folder]["files"]:
            folders[active_folder]["files"].append(file_unique_id)
        
        save_json_file(DATA_FILE, files)
        save_json_file(FOLDERS_FILE, folders)
        
        folder_name = folders[active_folder]["name"]
        
        await update.message.reply_text(
            f"✅ File saved to **{folder_name}**!\n\n"
            f"📝 Name: {file_name}\n"
            f"📁 Folder: {folder_name}\n"
            f"🔑 ID: `{file_unique_id}`\n"
            f"💾 Type: {file_type.title()}\n\n"
            f"💡 Move file: `/move {file_unique_id} <folder>`",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error saving file: {e}")
        try:
            await update.message.reply_text("❌ Error saving file. Please try again.")
        except:
            pass

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
        
        # Get active folder
        active_folder = context.user_data.get('active_folder', 'default')
        if active_folder not in folders:
            active_folder = 'default'
        
        folder_files = folders[active_folder]["files"]
        folder_name = folders[active_folder]["name"]
        
        if not folder_files:
            await update.message.reply_text(f"📭 No files in **{folder_name}** folder.")
            return
        
        text = f"📂 **Files in {folder_name}:**\n\n"
        for i, file_id in enumerate(folder_files[:20], 1):  # Show first 20 files
            if file_id in files:
                file_info = files[file_id]
                text += f"{i}. {file_info['name'][:30]}\n"
                text += f"   ID: `{file_id}`\n"
                text += f"   Type: {file_info['type']}\n\n"
        
        if len(folder_files) > 20:
            text += f"\n... and {len(folder_files) - 20} more files\n"
        
        text += f"\nTotal: {len(folder_files)} files"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"⚠️ Error listing files: {e}")
        try:
            await update.message.reply_text("❌ Error listing files.")
        except:
            pass

async def list_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if not files:
            await update.message.reply_text("📭 No files saved yet.")
            return
        
        text = "📂 **All Files:**\n\n"
        for i, (file_id, file_info) in enumerate(list(files.items())[:15], 1):  # Show first 15
            folder_name = folders.get(file_info.get('folder', 'default'), {}).get('name', 'Default')
            text += f"{i}. {file_info['name'][:25]}\n"
            text += f"   📁 {folder_name} | ID: `{file_id}`\n\n"
        
        if len(files) > 15:
            text += f"\n... and {len(files) - 15} more files\n"
        
        text += f"\n📊 Total files: {len(files)}"
        text += f"\n📁 Total folders: {len(folders)}"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"⚠️ Error listing all files: {e}")
        try:
            await update.message.reply_text("❌ Error listing all files.")
        except:
            pass

async def move_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /move <file_id> <folder_name>")
            return
        
        file_id = context.args[0]
        target_folder = " ".join(context.args[1:]).strip().lower()
        
        if file_id not in files:
            await update.message.reply_text("❌ File not found!")
            return
        
        if target_folder not in folders:
            await update.message.reply_text(f"❌ Folder '{target_folder}' not found!")
            return
        
        # Get current folder
        file_info = files[file_id]
        current_folder = file_info.get('folder', 'default')
        
        if current_folder == target_folder:
            await update.message.reply_text(f"⚠️ File is already in {folders[target_folder]['name']} folder!")
            return
        
        # Remove from old folder
        if file_id in folders[current_folder]["files"]:
            folders[current_folder]["files"].remove(file_id)
        
        # Add to new folder
        folders[target_folder]["files"].append(file_id)
        
        # Update file info
        files[file_id]["folder"] = target_folder
        files[file_id]["moved"] = str(datetime.now())
        
        save_json_file(DATA_FILE, files)
        save_json_file(FOLDERS_FILE, folders)
        
        await update.message.reply_text(
            f"✅ File moved!\n\n"
            f"📝 {file_info['name']}\n"
            f"📁 From: {folders[current_folder]['name']}\n"
            f"📁 To: {folders[target_folder]['name']}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error moving file: {e}")
        try:
            await update.message.reply_text("❌ Error moving file.")
        except:
            pass

async def delete_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if not context.args:
            await update.message.reply_text("Usage: /deletefolder <folder_name>")
            return
        
        folder_name = " ".join(context.args).strip().lower()
        
        if folder_name == 'default':
            await update.message.reply_text("❌ Cannot delete the Default folder!")
            return
        
        if folder_name not in folders:
            await update.message.reply_text("❌ Folder not found!")
            return
        
        # Move all files to default folder
        moved_files = 0
        for file_id in folders[folder_name]["files"]:
            if file_id in files:
                files[file_id]["folder"] = "default"
                folders["default"]["files"].append(file_id)
                moved_files += 1
        
        # Delete folder
        deleted_name = folders[folder_name]["name"]
        del folders[folder_name]
        
        save_json_file(DATA_FILE, files)
        save_json_file(FOLDERS_FILE, folders)
        
        await update.message.reply_text(
            f"✅ Folder deleted: **{deleted_name}**\n"
            f"📁 {moved_files} files moved to Default folder",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error deleting folder: {e}")
        try:
            await update.message.reply_text("❌ Error deleting folder.")
        except:
            pass

async def rename_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /rename <old_name> <new_name>")
            return
        
        old_name = context.args[0].lower()
        new_name = " ".join(context.args[1:]).strip()[:50]
        
        if old_name not in folders:
            await update.message.reply_text("❌ Folder not found!")
            return
        
        if new_name.lower() in [f.lower() for f in folders.keys()]:
            await update.message.reply_text(f"❌ Folder '{new_name}' already exists!")
            return
        
        # Rename folder
        folders[new_name.lower()] = folders[old_name]
        folders[new_name.lower()]["name"] = new_name
        del folders[old_name]
        
        # Update files in this folder
        for file_id in folders[new_name.lower()]["files"]:
            if file_id in files:
                files[file_id]["folder"] = new_name.lower()
        
        save_json_file(DATA_FILE, files)
        save_json_file(FOLDERS_FILE, folders)
        
        await update.message.reply_text(
            f"✅ Folder renamed!\n"
            f"📁 {old_name} → **{new_name}**",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ Error renaming folder: {e}")
        try:
            await update.message.reply_text("❌ Error renaming folder.")
        except:
            pass

async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        if not context.args:
            await update.message.reply_text("Usage: /search <keyword>")
            return
        
        keyword = " ".join(context.args).strip().lower()
        results = []
        
        for file_id, file_info in files.items():
            if (keyword in file_info["name"].lower() or 
                keyword in file_info["type"].lower() or
                keyword in file_info.get("folder", "").lower()):
                results.append((file_id, file_info))
        
        if not results:
            await update.message.reply_text(f"🔍 No files found for '{keyword}'")
            return
        
        text = f"🔍 **Search results for '{keyword}':**\n\n"
        for i, (file_id, file_info) in enumerate(results[:10], 1):
            folder_name = folders.get(file_info.get('folder', 'default'), {}).get('name', 'Default')
            text += f"{i}. {file_info['name'][:30]}\n"
            text += f"   📁 {folder_name} | ID: `{file_id}`\n\n"
        
        if len(results) > 10:
            text += f"\n... and {len(results) - 10} more results\n"
        
        text += f"\n📊 Found: {len(results)} files"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"⚠️ Error searching files: {e}")
        try:
            await update.message.reply_text("❌ Error searching files.")
        except:
            pass

# Keep existing get_file and delete_file functions (they work with the new system)

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
            print(f"📁 Loaded {len(files)} files in {len(folders)} folders")
            
            app = ApplicationBuilder().token(TOKEN).build()
            
            # Add error handler
            app.add_error_handler(error_handler)
            
            # Add command handlers - FOLDER COMMANDS
            app.add_handler(CommandHandler("create", create_folder))
            app.add_handler(CommandHandler("folders", list_folders))
            app.add_handler(CommandHandler("setfolder", set_folder))
            app.add_handler(CommandHandler("deletefolder", delete_folder))
            app.add_handler(CommandHandler("rename", rename_folder))
            app.add_handler(CommandHandler("move", move_file))
            app.add_handler(CommandHandler("search", search_files))
            
            # Add command handlers - FILE COMMANDS
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("list", list_files))
            app.add_handler(CommandHandler("listall", list_all_files))
            app.add_handler(CommandHandler("get", get_file))
            app.add_handler(CommandHandler("delete", get_file))  # Keep delete for now
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
