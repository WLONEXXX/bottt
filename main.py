import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== НАСТРОЙКИ ==================

TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"  # Замените на ваш токен
OPERATOR_ID = 123456789  # Замените на ваш ID в Telegram

# ================== ДАННЫЕ ==================

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

# Хранилище состояний: user_id -> {'mode': str, 'data': dict}
user_states = {}
# Хранилище для связи сообщений оператора с пользователями
operator_messages = {}  # message_id оператора -> user_id
user_messages = {}  # message_id пользователя -> user_id (для ответов)

# ================== КЛАВИАТУРЫ ==================

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🛍 Каталог", callback_data="catalog"),
        InlineKeyboardButton("💬 Связаться с оператором", callback_data="contact"),
        InlineKeyboardButton("⭐️ Оставить отзыв", callback_data="review"),
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
        # Добавляем цену в кнопку для наглядности
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
        InlineKeyboardButton("🇷🇺 Рубли (RUB)", callback_data="currency_rub"),
        InlineKeyboardButton("🇺🇸 Доллары (USD)", callback_data="currency_usd"),
        InlineKeyboardButton("🇪🇺 Евро (EUR)", callback_data="currency_eur"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main")
    )
    return kb

def back_to_main_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main"))
    return kb

# ================== БОТ ==================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ================== ХЕНДЛЕРЫ ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    welcome_text = (
        "🌟 Добро пожаловать в наш магазин!\n\n"
        "Здесь вы можете:\n"
        "🛍 Просмотреть каталог товаров\n"
        "💬 Связаться с оператором\n"
        "⭐️ Оставить отзыв\n"
        "💰 Выбрать удобную валюту\n\n"
        "Используйте кнопки ниже для навигации:"
    )
    await message.answer(welcome_text, reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "main")
async def back_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "catalog")
async def open_catalog(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📁 Выберите категорию товаров:",
        reply_markup=categories_kb()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def open_category(callback: types.CallbackQuery):
    cat_key = callback.data.split("_")[1]
    category = products.get(cat_key)
    if category:
        await callback.message.edit_text(
            f"📦 Категория: {category['title']}\n\nВыберите товар:",
            reply_markup=products_kb(cat_key)
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery):
    # Возвращаемся к списку товаров последней просмотренной категории
    # В реальном проекте нужно хранить последнюю категорию пользователя
    await callback.message.edit_text(
        "📦 Выберите товар:",
        reply_markup=products_kb("food")  # По умолчанию показываем первую категорию
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("item_"))
async def open_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break
    
    if item:
        # Сохраняем последний просмотренный товар пользователя
        user_states[callback.from_user.id] = {'mode': 'viewing_item', 'item_id': item_id}
        
        item_text = (
            f"✨ <b>{item['name']}</b>\n\n"
            f"💰 Цена: {item['price']} ₽\n"
            f"📝 Описание: {item['desc']}\n\n"
            f"Чтобы заказать этот товар, нажмите кнопку ниже:"
        )
        await callback.message.edit_text(
            item_text,
            reply_markup=item_kb(item_id),
            parse_mode='HTML'
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break
    
    if item:
        user = callback.from_user
        # Формируем сообщение для оператора
        order_text = (
            f"🆕 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"📦 Товар: {item['name']}\n"
            f"💰 Цена: {item['price']} ₽\n"
            f"📝 Описание: {item['desc']}\n\n"
            f"👤 Покупатель: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 Username: @{user.username if user.username else 'нет'}\n\n"
            f"💬 <i>Ответьте на это сообщение, чтобы написать покупателю</i>"
        )
        
        # Отправляем заказ оператору
        msg = await bot.send_message(OPERATOR_ID, order_text, parse_mode='HTML')
        
        # Сохраняем связь сообщения оператора с пользователем
        operator_messages[msg.message_id] = user.id
        
        # Уведомляем пользователя
        await callback.message.edit_text(
            f"✅ <b>Заказ отправлен!</b>\n\n"
            f"Товар: {item['name']}\n"
            f"Цена: {item['price']} ₽\n\n"
            f"Оператор свяжется с вами в ближайшее время.\n"
            f"Вы можете продолжить покупки в каталоге.",
            reply_markup=back_to_main_kb(),
            parse_mode='HTML'
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "contact")
async def contact_operator(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = {'mode': 'waiting_for_message'}
    await callback.message.edit_text(
        "💬 <b>Связь с оператором</b>\n\n"
        "Напишите ваше сообщение в чат.\n"
        "Оператор ответит вам как можно скорее.\n\n"
        "<i>Для отмены нажмите кнопку ниже</i>",
        reply_markup=back_to_main_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "review")
async def leave_review(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = {'mode': 'waiting_for_review'}
    await callback.message.edit_text(
        "⭐️ <b>Оставить отзыв</b>\n\n"
        "Напишите ваш отзыв в чат.\n"
        "Ваше мнение очень важно для нас!\n\n"
        "<i>Для отмены нажмите кнопку ниже</i>",
        reply_markup=back_to_main_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "currency")
async def currency_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Выбор валюты</b>\n\n"
        "Выберите удобную для вас валюту отображения цен:",
        reply_markup=currency_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("currency_"))
async def set_currency(callback: types.CallbackQuery):
    currency = callback.data.split("_")[1]
    currency_names = {
        'rub': '🇷🇺 Рубли (RUB)',
        'usd': '🇺🇸 Доллары (USD)',
        'eur': '🇪🇺 Евро (EUR)'
    }
    
    # Сохраняем выбранную валюту для пользователя
    user_states[callback.from_user.id] = {'mode': 'currency_set', 'currency': currency}
    
    await callback.message.edit_text(
        f"✅ <b>Валюта успешно изменена!</b>\n\n"
        f"Теперь цены будут отображаться в: {currency_names.get(currency, currency)}\n\n"
        f"<i>Примечание: в текущей версии все цены отображаются в рублях.\n"
        f"Конвертация валют будет добавлена в следующем обновлении.</i>",
        reply_markup=back_to_main_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.message_handler()
async def handle_user_messages(message: types.Message):
    user_id = message.from_user.id
    
    # Пропускаем сообщения от оператора (их обрабатываем отдельно)
    if user_id == OPERATOR_ID:
        return
    
    # Проверяем, ожидаем ли мы сообщение от пользователя
    if user_id in user_states:
        state = user_states[user_id]
        
        if state['mode'] == 'waiting_for_message':
            # Отправляем сообщение оператору
            user_info = f"Сообщение от @{message.from_user.username if message.from_user.username else 'пользователя'} (ID: {user_id}):"
            await bot.send_message(
                OPERATOR_ID, 
                f"💬 {user_info}\n\n{message.text}",
                parse_mode='HTML'
            )
            
            # Сохраняем сообщение пользователя для возможности ответа
            user_messages[message.message_id] = user_id
            
            await message.reply(
                "✅ Ваше сообщение отправлено оператору!\n"
                "Ожидайте ответа в этом чате.",
                reply_markup=back_to_main_kb()
            )
            # Очищаем состояние
            del user_states[user_id]
            
        elif state['mode'] == 'waiting_for_review':
            # Отправляем отзыв оператору
            await bot.send_message(
                OPERATOR_ID,
                f"⭐️ Новый отзыв от @{message.from_user.username if message.from_user.username else 'пользователя'} (ID: {user_id}):\n\n{message.text}"
            )
            
            await message.reply(
                "✅ Спасибо за ваш отзыв!\n"
                "Мы ценим ваше мнение.",
                reply_markup=back_to_main_kb()
            )
            # Очищаем состояние
            del user_states[user_id]
    else:
        # Если пользователь просто пишет без выбора опции
        await message.reply(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=main_menu()
        )

@dp.message_handler(lambda m: m.chat.id == OPERATOR_ID)
async def operator_reply(message: types.Message):
    """Обработка ответов оператора на сообщения пользователей"""
    
    # Проверяем, является ли сообщение ответом на другое сообщение
    if message.reply_to_message:
        original_msg_id = message.reply_to_message.message_id
        
        # Проверяем, есть ли это сообщение в наших хранилищах
        if original_msg_id in operator_messages:
            # Это ответ на уведомление о заказе
            user_id = operator_messages[original_msg_id]
            await bot.send_message(
                user_id,
                f"📞 <b>Ответ оператора:</b>\n\n{message.text}",
                parse_mode='HTML'
            )
            await message.reply("✅ Ответ отправлен пользователю!")
            
        elif original_msg_id in user_messages:
            # Это ответ на сообщение пользователя
            user_id = user_messages[original_msg_id]
            await bot.send_message(
                user_id,
                f"📞 <b>Ответ оператора:</b>\n\n{message.text}",
                parse_mode='HTML'
            )
            await message.reply("✅ Ответ отправлен пользователю!")
        else:
            await message.reply("❌ Не могу определить, кому отправить ответ.")
    else:
        await message.reply(
            "ℹ️ Чтобы ответить пользователю, используйте 'ответить' (Reply) "
            "на его сообщение в этом чате."
        )

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    print("Бот запущен и готов к работе!")
    print(f"ID оператора: {OPERATOR_ID}")
    executor.start_polling(dp, skip_updates=True)
