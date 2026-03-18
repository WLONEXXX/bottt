import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== НАСТРОЙКИ ==================

TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"  # Ваш токен
OPERATOR_ID = 7892937398  # Ваш ID

# ================== ДАННЫЕ ==================

# Каталог товаров
products = {
    "food": {
        "title": "Вкусняшки",
        "items": [
            {"id": 1, "name": "Мефедрон", "price": 4400, "desc": "цена за 1 грам, покупка от 2 грамм"},
            {"id": 2, "name": "Шишки Ice", "price": 2200, "desc": "цена за 1 грам, покупка от 2 грамм"},
            {"id": 3, "name": "Шишки Jack", "price": 3000, "desc": "покупка от 1 грамма"},
            {"id": 4, "name": "Кокаин", "price": 7140, "desc": "цена за 0,3 грамма, покупка от 0,3 грама"},
        ]
    }
}


# Хранилище сообщений: message_id -> user_id
user_messages = {}

# Состояния пользователей
user_states = {}

# ================== КЛАВИАТУРЫ ==================

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🛍 Каталог", callback_data="catalog"),
        InlineKeyboardButton("💬 Связаться с оператором", callback_data="contact")
    )
    return kb

def categories_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    for key, cat in products.items():
        kb.add(InlineKeyboardButton(cat["title"], callback_data=f"cat_{key}"))
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main"))
    return kb

def products_kb(cat_key):
    kb = InlineKeyboardMarkup(row_width=1)
    for item in products[cat_key]["items"]:
        btn_text = f"{item['name']} - {item['price']} ₽"
        kb.add(InlineKeyboardButton(btn_text, callback_data=f"item_{item['id']}"))
    kb.add(
        InlineKeyboardButton("◀️ Назад к категориям", callback_data="catalog"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main")
    )
    return kb

def item_kb(item_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✅ Заказать", callback_data=f"buy_{item_id}"),
        InlineKeyboardButton("◀️ Назад к товарам", callback_data="back_to_products"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main")
    )
    return kb

def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main"))
    return kb

# ================== БОТ ==================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================== ХЕНДЛЕРЫ КАТАЛОГА ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🌟 Добро пожаловать в магазин!\n\n"
        "🛍 Смотрите каталог\n"
        "💬 Связь с оператором",
        reply_markup=main_menu()
    )

@dp.callback_query_handler(lambda c: c.data == "main")
async def main_menu_callback(callback: types.CallbackQuery):
    if callback.from_user.id in user_states:
        del user_states[callback.from_user.id]
    
    await callback.message.edit_text(
        "🌟 Главное меню:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "catalog")
async def catalog_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📁 Выберите категорию:",
        reply_markup=categories_kb()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def category_handler(callback: types.CallbackQuery):
    cat_key = callback.data.split("_")[1]
    category = products.get(cat_key)
    if category:
        await callback.message.edit_text(
            f"📦 {category['title']}\n\nВыберите товар:",
            reply_markup=products_kb(cat_key)
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_kb("food")
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("item_"))
async def item_handler(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break
    
    if item:
        await callback.message.edit_text(
            f"✨ <b>{item['name']}</b>\n\n"
            f"💰 Цена: {item['price']} ₽\n"
            f"📝 {item['desc']}\n\n"
            f"Нажмите 'Заказать' для покупки:",
            reply_markup=item_kb(item_id),
            parse_mode='HTML'
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_handler(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break
    
    if item:
        user = callback.from_user
        order_text = (
            f"🆕 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"📦 Товар: {item['name']}\n"
            f"💰 Цена: {item['price']} ₽\n"
            f"📝 {item['desc']}\n\n"
            f"👤 Покупатель: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 @{user.username if user.username else 'нет'}"
        )
        
        sent_msg = await bot.send_message(OPERATOR_ID, order_text, parse_mode='HTML')
        user_messages[sent_msg.message_id] = user.id
        
        await callback.message.edit_text(
            f"✅ <b>Заказ отправлен!</b>",
            reply_markup=back_kb(),
            parse_mode='HTML'
        )
    await callback.answer()

# ================== ХЕНДЛЕРЫ СВЯЗИ ==================

@dp.callback_query_handler(lambda c: c.data == "contact")
async def contact_handler(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = "waiting_message"
    
    await callback.message.edit_text(
        "💬 Напишите сообщение оператору\n"
        "Можно отправлять текст и фото",
        reply_markup=back_kb()
    )
    await callback.answer()

# ================== ОБРАБОТКА ВСЕХ ТИПОВ СООБЩЕНИЙ ==================

@dp.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'sticker'])
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    
    # Если это оператор
    if user_id == OPERATOR_ID:
        if message.reply_to_message:
            original_msg_id = message.reply_to_message.message_id
            
            if original_msg_id in user_messages:
                target_user_id = user_messages[original_msg_id]
                
                try:
                    # Пересылаем сообщение пользователю в зависимости от типа
                    if message.photo:
                        photo = message.photo[-1]
                        caption = message.caption or "📸 Фото от оператора"
                        await bot.send_photo(target_user_id, photo.file_id, caption=caption)
                    
                    elif message.video:
                        await bot.send_video(target_user_id, message.video.file_id, caption=message.caption)
                    
                    elif message.document:
                        await bot.send_document(target_user_id, message.document.file_id, caption=message.caption)
                    
                    elif message.voice:
                        await bot.send_voice(target_user_id, message.voice.file_id)
                    
                    elif message.sticker:
                        await bot.send_sticker(target_user_id, message.sticker.file_id)
                    
                    else:  # Текстовое сообщение
                        await bot.send_message(target_user_id, f"📞 {message.text}")
                    
                    await message.reply("✅ Отправлено!")
                except Exception as e:
                    await message.reply(f"❌ Ошибка: {e}")
            else:
                await message.reply("❌ Не могу найти пользователя")
        else:
            await message.reply("ℹ️ Нажмите 'Ответить' на сообщение пользователя")
    
    # Если это пользователь
    else:
        if user_id in user_states and user_states[user_id] == "waiting_message":
            try:
                # Информация о пользователе
                user_info = (
                    f"👤 {message.from_user.full_name}\n"
                    f"🆔 {user_id}\n"
                    f"📱 @{message.from_user.username if message.from_user.username else 'нет'}"
                )
                
                # Отправляем оператору в зависимости от типа
                if message.photo:
                    photo = message.photo[-1]
                    caption = f"📸 Фото от пользователя\n\n{user_info}"
                    if message.caption:
                        caption += f"\n\n📝 {message.caption}"
                    sent_msg = await bot.send_photo(OPERATOR_ID, photo.file_id, caption=caption)
                
                elif message.video:
                    caption = f"🎥 Видео от пользователя\n\n{user_info}"
                    if message.caption:
                        caption += f"\n\n📝 {message.caption}"
                    sent_msg = await bot.send_video(OPERATOR_ID, message.video.file_id, caption=caption)
                
                elif message.document:
                    caption = f"📎 Файл от пользователя\n\n{user_info}"
                    if message.caption:
                        caption += f"\n\n📝 {message.caption}"
                    sent_msg = await bot.send_document(OPERATOR_ID, message.document.file_id, caption=caption)
                
                elif message.voice:
                    caption = f"🎤 Голосовое от пользователя\n\n{user_info}"
                    sent_msg = await bot.send_voice(OPERATOR_ID, message.voice.file_id, caption=caption)
                
                elif message.sticker:
                    sent_msg = await bot.send_message(OPERATOR_ID, f"😊 Стикер от пользователя\n\n{user_info}")
                    await bot.send_sticker(OPERATOR_ID, message.sticker.file_id)
                
                else:  # Текстовое сообщение
                    text = f"💬 Сообщение от пользователя\n\n{user_info}\n\n📝 {message.text}"
                    sent_msg = await bot.send_message(OPERATOR_ID, text)
                
                # Сохраняем связь для ответа
                if 'sent_msg' in locals():
                    user_messages[sent_msg.message_id] = user_id
                
                await message.reply("✅ Отправлено оператору!")
                
                # Не очищаем состояние, чтобы можно было отправлять несколько сообщений
                # user_states остается "waiting_message"
                
            except Exception as e:
                await message.reply(f"❌ Ошибка: {e}")
        else:
            await message.reply(
                "❓ Нажмите 'Связаться с оператором'",
                reply_markup=main_menu()
            )

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    print("=" * 50)
    print("🌟 Бот запущен!")
    print(f"👤 Оператор: {OPERATOR_ID}")
    print("=" * 50)
    print("\n📱 Поддерживаются:")
    print("✅ Текст")
    print("✅ Фото")
    print("✅ Видео")
    print("✅ Документы")
    print("✅ Голосовые")
    print("✅ Стикеры")
    print("=" * 50)
    
    executor.start_polling(dp, skip_updates=True)
