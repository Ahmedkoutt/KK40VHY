import telebot
from telebot import types
import os
import subprocess

TOKEN = "8230055864:AAHWItMDRDf7rVi8dKWIPui2HYRXa8rljHo"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

running_processes = {}
bot_speed = 1

def main_menu():
    mar = types.InlineKeyboardMarkup(row_width=2)
    mar.add(
        types.InlineKeyboardButton("🟢 تشغيل البوتات", callback_data="start_all"),
        types.InlineKeyboardButton("🔴 إيقاف البوتات", callback_data="stop_all")
    )
    mar.add(
        types.InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
        types.InlineKeyboardButton("🗑 حذف بوت", callback_data="delete_bot")
    )
    mar.add(
        types.InlineKeyboardButton("⚡ سرعة البوت", callback_data="set_speed"),
        types.InlineKeyboardButton("📦 تحميل مكتبة", callback_data="install_library")
    )
    return mar

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك!\n\n"
        "يمكنك رفع ملفات <code>.py</code> (بوتات) والتحكم بها بالأزرار:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id

    if data == "start_all":
        started = 0
        for file in os.listdir(UPLOAD_FOLDER):
            if file.endswith(".py") and file not in running_processes:
                path = os.path.join(UPLOAD_FOLDER, file)
                p = subprocess.Popen(["python3", path])
                running_processes[file] = p
                started += 1
        bot.edit_message_text(
            f"✅ تم تشغيل {started} بوت/ملف.", chat_id, call.message.id, reply_markup=main_menu()
        )

    elif data == "stop_all":
        stopped = 0
        for name, proc in list(running_processes.items()):
            proc.terminate()
            stopped += 1
        running_processes.clear()
        bot.edit_message_text(
            f"🛑 تم إيقاف {stopped} بوت/ملف.", chat_id, call.message.id, reply_markup=main_menu()
        )

    elif data == "add_bot":
        bot.edit_message_text(
            "📤 أرسل ملف Python (.py) لإضافته وتشغيله.",
            chat_id, call.message.id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="back")
            )
        )

    elif data == "delete_bot":
        files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".py")]
        if not files:
            bot.edit_message_text(
                "❌ لا توجد بوتات حالياً.", chat_id, call.message.id, reply_markup=main_menu()
            )
            return
        buttons = [
            [types.InlineKeyboardButton(f"🗑 {f}", callback_data=f"delete_{f}"),
             types.InlineKeyboardButton(f"⏯ تشغيل/إيقاف {f}", callback_data=f"toggle_{f}")]
            for f in files
        ]
        buttons.append([types.InlineKeyboardButton("🔙 رجوع", callback_data="back")])
        mar = types.InlineKeyboardMarkup(buttons)
        bot.edit_message_text("🔽 اختر البوت:", chat_id, call.message.id, reply_markup=mar)

    elif data.startswith("delete_"):
        filename = data.replace("delete_", "")
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(path):
            try:
                if filename in running_processes:
                    running_processes[filename].terminate()
                    del running_processes[filename]
                os.remove(path)
                bot.edit_message_text(f"🗑 تم حذف البوت: {filename}", chat_id, call.message.id, reply_markup=main_menu())
            except Exception as e:
                bot.edit_message_text(f"⚠️ فشل الحذف: {e}", chat_id, call.message.id, reply_markup=main_menu())
        else:
            bot.edit_message_text("❌ الملف غير موجود.", chat_id, call.message.id, reply_markup=main_menu())

    elif data.startswith("toggle_"):
        filename = data.replace("toggle_", "")
        path = os.path.join(UPLOAD_FOLDER, filename)
        if filename in running_processes:
            running_processes[filename].terminate()
            del running_processes[filename]
            bot.answer_callback_query(call.id, f"🛑 تم إيقاف {filename}")
        else:
            p = subprocess.Popen(["python3", path])
            running_processes[filename] = p
            bot.answer_callback_query(call.id, f"✅ تم تشغيل {filename}")

    elif data == "set_speed":
        bot.edit_message_text(
            "⚡ اختر سرعة البوت:\n1: بطيء\n2: متوسط\n3: سريع",
            chat_id, call.message.id,
            reply_markup=types.InlineKeyboardMarkup(row_width=3).add(
                types.InlineKeyboardButton("1", callback_data="speed_1"),
                types.InlineKeyboardButton("2", callback_data="speed_2"),
                types.InlineKeyboardButton("3", callback_data="speed_3"),
                types.InlineKeyboardButton("🔙 رجوع", callback_data="back")
            )
        )

    elif data.startswith("speed_"):
        global bot_speed
        bot_speed = int(data.split("_")[1])
        bot.answer_callback_query(call.id, f"⚡ تم تعيين سرعة البوت إلى {bot_speed}")
        bot.edit_message_text("✅ تم تعديل السرعة.", chat_id, call.message.id, reply_markup=main_menu())

    elif data == "install_library":
        bot.send_message(chat_id, "📦 أرسل اسم المكتبة لتثبيتها:")
        bot.register_next_step_handler_by_chat_id(chat_id, install_library_step)

    elif data == "back":
        bot.edit_message_text("🔙 رجعت للقائمة الرئيسية:", chat_id, call.message.id, reply_markup=main_menu())

def install_library_step(message):
    library_name = message.text.strip()
    try:
        subprocess.check_call(["pip3", "install", library_name])
        bot.send_message(message.chat.id, f"✅ تم تثبيت المكتبة: {library_name}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ فشل تثبيت المكتبة: {library_name}\n{e}")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    document = message.document
    file_info = bot.get_file(document.file_id)
    file_path = os.path.join(UPLOAD_FOLDER, document.file_name)

    downloaded = bot.download_file(file_info.file_path)
    with open(file_path, "wb") as f:
        f.write(downloaded)

    bot.reply_to(message, f"📁 تم حفظ الملف: {document.file_name}")

    if file_path.endswith(".py"):
        if document.file_name in running_processes:
            running_processes[document.file_name].terminate()
            del running_processes[document.file_name]
        p = subprocess.Popen(["python3", file_path])
        running_processes[document.file_name] = p
        bot.reply_to(message, f"✅ تم تشغيل البوت: {document.file_name}")
    else:
        bot.reply_to(message, "📎 الملف ليس Python لذلك لن يتم تشغيله.")

bot.infinity_polling()
