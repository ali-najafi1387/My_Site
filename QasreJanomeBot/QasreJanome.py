import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import json
import os

TOKEN = '7613835439:AAHeENV_sgRTNIL4uZ_C40v_M0'
bot = telebot.TeleBot(TOKEN)


USERS_FILE = 'users.json'
LESSONS_FILE = 'lessons.json'
user_states = {}

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_lessons():
    if not os.path.exists(LESSONS_FILE):
        return []
    with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id in users:
        bot.send_message(message.chat.id, f"👋 خوش برگشتی {users[user_id]['first_name']}!")
        show_main_menu(message.chat.id)
    else:
        user_states[user_id] = {'step': 'first_name'}
        bot.send_message(message.chat.id, "👤 لطفاً نام خود را وارد کنید:")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    users = load_users()

    if user_id in user_states:
        step = user_states[user_id]['step']

        if step == 'first_name':
            user_states[user_id]['first_name'] = text
            user_states[user_id]['step'] = 'last_name'
            bot.send_message(message.chat.id, "🧾 حالا نام خانوادگی‌تان را وارد کنید:")
            return

        elif step == 'last_name':
            user_states[user_id]['last_name'] = text
            user_states[user_id]['step'] = 'phone'
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(KeyboardButton("📱 ارسال شماره تلفن", request_contact=True))
            bot.send_message(message.chat.id, "📞 لطفاً شماره تلفن خود را ارسال کنید:", reply_markup=markup)
            return

        elif step == 'select_category':
            lessons = load_lessons()
            selected_category = next((c for c in lessons if c['category'] == text), None)
            if selected_category:
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for item in selected_category['items']:
                    markup.add(KeyboardButton(item['title']))
                markup.add(KeyboardButton("🔙 بازگشت به دسته‌ها"))
                user_states[user_id] = {
                    "step": "select_lesson_from_category",
                    "category": selected_category['category']
                }
                bot.send_message(message.chat.id, f"📘 آموزش‌های دسته «{text}»:", reply_markup=markup)
            elif text == "🔙 بازگشت به منو":
                user_states.pop(user_id)
                show_main_menu(message.chat.id)
            return

        elif step == 'select_lesson_from_category':
            lessons = load_lessons()
            category = user_states[user_id]["category"]
            selected_category = next((c for c in lessons if c['category'] == category), None)
            selected_lesson = next((l for l in selected_category['items'] if l['title'] == text), None)

            if selected_lesson:
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton(f"💳 خرید {selected_lesson['price']} تومان", callback_data=f"buy_{selected_lesson['id']}")
                )
                bot.send_message(message.chat.id, f"🎓 {selected_lesson['title']}", reply_markup=markup)
            elif text == "🔙 بازگشت به دسته‌ها":
                user_states[user_id] = {"step": "select_category"}
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for cat in lessons:
                    markup.add(KeyboardButton(cat['category']))
                markup.add(KeyboardButton("🔙 بازگشت به منو"))
                bot.send_message(message.chat.id, "📂 لطفاً یک دسته آموزش را انتخاب کن:", reply_markup=markup)
            return

        elif step == 'select_lesson':
            lessons = load_lessons()
            purchased_ids = users[user_id]["purchased"]
            all_lessons = [item for cat in lessons for item in cat['items']]
            selected = next((l for l in all_lessons if l['title'] == text and l['id'] in purchased_ids), None)

            if selected:
                video_path = f"videos/{selected['id']}.mp4"
                if os.path.exists(video_path):
                    bot.send_chat_action(message.chat.id, "upload_video")
                    with open(video_path, 'rb') as video:
                        bot.send_video(message.chat.id, video, caption=f"🎥 آموزش: {selected['title']}")
                else:
                    bot.send_message(message.chat.id, "❗ فایل ویدیویی این آموزش هنوز بارگذاری نشده.")
            elif text == "🔙 بازگشت به منو":
                user_states.pop(user_id)
                show_main_menu(message.chat.id)
            else:
                bot.send_message(message.chat.id, "❗ لطفاً یکی از آموزش‌های خریداری‌شده را انتخاب کن.")
            return

    if text == "🧵 مشاهده آموزش‌ها":
        lessons = load_lessons()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for category in lessons:
            markup.add(KeyboardButton(category['category']))
        markup.add(KeyboardButton("🔙 بازگشت به منو"))
        user_states[user_id] = {"step": "select_category"}
        bot.send_message(message.chat.id, "📂 لطفاً یک دسته آموزش را انتخاب کن:", reply_markup=markup)

    elif text == "📦 آموزش‌های من":
        if user_id not in users or "purchased" not in users[user_id] or not users[user_id]["purchased"]:
            bot.send_message(message.chat.id, "📦 شما هنوز آموزشی نخریده‌اید.")
        else:
            lessons = load_lessons()
            purchased = users[user_id]["purchased"]
            markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for category in lessons:
                for lesson in category['items']:
                    if lesson['id'] in purchased:
                        markup.add(KeyboardButton(lesson['title']))
            markup.add(KeyboardButton("🔙 بازگشت به منو"))
            user_states[user_id] = {"step": "select_lesson"}
            bot.send_message(message.chat.id, "🎓 یکی از آموزش‌های زیر را انتخاب کن:", reply_markup=markup)

    elif text == "ℹ️ درباره ما":
        bot.send_message(message.chat.id, "این ربات برای آموزش چرخ خیاطی طراحی شده است. تولید شده توسط علی 🌟")

    elif text == "📞 پشتیبانی":
        bot.send_message(message.chat.id, "برای پشتیبانی با ما در تماس باشید:\n@YourSupport")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    contact = message.contact

    if user_id not in user_states or user_states[user_id]['step'] != 'phone':
        return

    phone_number = contact.phone_number
    first_name = user_states[user_id]['first_name']
    last_name = user_states[user_id]['last_name']
    username = message.from_user.username or ""

    users = load_users()
    users[user_id] = {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone_number,
        "username": username,
        "purchased": []
    }
    save_users(users)

    bot.send_message(message.chat.id, f"✅ اطلاعات شما با موفقیت ذخیره شد.\nخوش آمدی {first_name}!", reply_markup=ReplyKeyboardRemove())
    user_states.pop(user_id)
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🧵 مشاهده آموزش‌ها"),
        KeyboardButton("📦 آموزش‌های من"),
        KeyboardButton("ℹ️ درباره ما"),
        KeyboardButton("📞 پشتیبانی")
    )
    bot.send_message(chat_id, "از منوی زیر یکی رو انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    user_id = str(call.from_user.id)
    lesson_id = int(call.data.split("_")[1])
    lessons = load_lessons()
    all_lessons = [item for cat in lessons for item in cat['items']]
    lesson = next((l for l in all_lessons if l['id'] == lesson_id), None)

    if not lesson:
        bot.answer_callback_query(call.id, "❌ آموزش پیدا نشد.")
        return

    # شبیه‌سازی لینک پرداخت
    fake_payment_link = f"https://idpay.ir/yourusername/invoice?amount={lesson['price']}&desc={lesson['title']}"
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💳 پرداخت", url=fake_payment_link),
        InlineKeyboardButton("✅ پرداخت کردم", callback_data=f"confirm_{lesson_id}")
    )
    bot.send_message(call.message.chat.id, f"💰 برای خرید «{lesson['title']}» روی دکمه زیر کلیک کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirm(call):
    user_id = str(call.from_user.id)
    lesson_id = int(call.data.split("_")[1])
    lessons = load_lessons()
    all_lessons = [item for cat in lessons for item in cat['items']]
    lesson = next((l for l in all_lessons if l['id'] == lesson_id), None)

    if not lesson:
        bot.send_message(call.message.chat.id, "❌ آموزش پیدا نشد.")
        return

    users = load_users()
    if user_id not in users:
        bot.send_message(call.message.chat.id, "❗ ابتدا باید ثبت‌نام کنید.")
        return

    if lesson_id in users[user_id]["purchased"]:
        bot.send_message(call.message.chat.id, "✅ شما قبلاً این آموزش را خریده‌اید.")
    else:
        users[user_id]["purchased"].append(lesson_id)
        save_users(users)
        bot.send_message(call.message.chat.id, f"🎉 آموزش «{lesson['title']}» با موفقیت به لیست شما اضافه شد.")


bot.polling()
