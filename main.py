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
        InlineKeyboardButton("💬 Связаться с оператором", callback_data="contact"),
        InlineKeyboardButton("💰 Выбрать валюту", callback_data="currency")
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

def currency_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🇷🇺 Рубли", callback_data="currency_rub"),
        InlineKeyboardButton("🇺🇸 Доллары", callback_data="currency_usd"),
        InlineKeyboardButton("🇪🇺 Евро", callback_data="currency_eur"),
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
        "🌟 Добро пожаловать в Witch shop!\n\n"
        "🛍 Смотрите каталог\n"
        "💬 Общайтесь с оператором\n"
        "💰 Выбирайте валюту",
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
        
        # Отправляем заказ оператору
        sent_msg = await bot.send_message(OPERATOR_ID, order_text, parse_mode='HTML')
        
        # Сохраняем связь для ответа
        user_messages[sent_msg.message_id] = user.id
        
        await callback.message.edit_text(
            f"✅ <b>Заказ отправлен!</b>\n\n"
            f"Товар: {item['name']}\n"
            f"Цена: {item['price']} ₽\n\n"
            f"Оператор скоро свяжется с вами.",
            reply_markup=back_kb(),
            parse_mode='HTML'
        )
    await callback.answer()

# ================== ХЕНДЛЕРЫ ВАЛЮТЫ ==================

@dp.callback_query_handler(lambda c: c.data == "currency")
async def currency_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 Выберите валюту:",
        reply_markup=currency_kb()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("currency_"))
async def set_currency(callback: types.CallbackQuery):
    currency = callback.data.split("_")[1]
    currency_names = {
        'rub': '🇷🇺 Рубли',
        'usd': '🇺🇸 Доллары',
        'eur': '🇪🇺 Евро'
    }
    
    await callback.message.edit_text(
        f"✅ Валюта изменена на {currency_names.get(currency, currency)}\n\n"
        f"<i>Цены пока отображаются в рублях</i>",
        reply_markup=back_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

# ================== ХЕНДЛЕРЫ СВЯЗИ ==================

@dp.callback_query_handler(lambda c: c.data == "contact")
async def contact_handler(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = "waiting_message"
    
    await callback.message.edit_text(
        "💬 Напишите ваше сообщение оператору.\n"
        "Я отвечу вам как можно скорее!",
        reply_markup=back_kb()
    )
    await callback.answer()

# ================== ОБРАБОТКА СООБЩЕНИЙ ==================

@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    
    # Если это оператор
    if user_id == OPERATOR_ID:
        if message.reply_to_message:
            original_msg_id = message.reply_to_message.message_id
            
            if original_msg_id in user_messages:
                target_user_id = user_messages[original_msg_id]
                
                try:
                    await bot.send_message(
                        target_user_id,
                        f"📞 <b>Ответ оператора:</b>\n\n{message.text}",
                        parse_mode='HTML'
                    )
                    await message.reply("✅ Ответ отправлен!")
                except Exception as e:
                    await message.reply(f"❌ Ошибка: {e}")
            else:
                await message.reply("❌ Не могу найти пользователя")
        else:
            await message.reply(
                "ℹ️ Нажмите 'Ответить' на сообщение пользователя"
            )
    
    # Если это пользователь
    else:
        if user_id in user_states and user_states[user_id] == "waiting_message":
            try:
                operator_text = (
                    f"💬 <b>Сообщение от пользователя</b>\n\n"
                    f"👤 {message.from_user.full_name}\n"
                    f"🆔 {user_id}\n"
                    f"📱 @{message.from_user.username if message.from_user.username else 'нет'}\n\n"
                    f"📝 {message.text}"
                )
                
                sent_msg = await bot.send_message(
                    OPERATOR_ID,
                    operator_text,
                    parse_mode='HTML'
                )
                
                user_messages[sent_msg.message_id] = user_id
                
                await message.reply(
                    "✅ Сообщение отправлено!",
                    reply_markup=back_kb()
                )
                
                del user_states[user_id]
                
            except Exception as e:
                await message.reply(f"❌ Ошибка: {e}")
        else:
            await message.reply(
                "❓ Используйте кнопки меню",
                reply_markup=main_menu()
            )

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    print("=" * 50)
    print("🌟 Бот запущен!")
    print(f"👤 Оператор: {OPERATOR_ID}")
    print("=" * 50)
    print("\n📝 Функции:")
    print("✅ Каталог товаров")
    print("✅ Связь с оператором")
    print("✅ Выбор валюты")
    print("✅ Заказы")
    print("=" * 50)
    
    executor.start_polling(dp, skip_updates=True)
