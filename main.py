import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ================== НАСТРОЙКИ ==================
TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 123456789  # ID оператора

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


# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Каталог", callback_data="catalog"))
    kb.add(types.InlineKeyboardButton("Связаться с оператором", callback_data="contact_operator"))
    kb.add(types.InlineKeyboardButton("Оставить отзыв", callback_data="leave_review"))
    return kb

def categories_kb():
    kb = types.InlineKeyboardMarkup()
    for key, cat in products.items():
        kb.add(types.InlineKeyboardButton(cat["title"], callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu"))
    return kb

def products_kb(cat_key):
    kb = types.InlineKeyboardMarkup()
    for item in products[cat_key]["items"]:
        kb.add(types.InlineKeyboardButton(item["name"], callback_data=f"item_{item['id']}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="catalog"))
    return kb

def buy_kb(item_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛒 Заказать", callback_data=f"buy_{item_id}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="catalog"))
    return kb

# ================== БОТ ==================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
pending_orders = {}  # message_id -> user_id
pending_contacts = {}  # message_id -> user_id
pending_reviews = {}  # message_id -> user_id

# ================== ХЕНДЛЕРЫ ==================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в Whitch shop!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def go_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "catalog")
async def open_catalog(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите категорию:", reply_markup=categories_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def open_category(callback: types.CallbackQuery):
    cat_key = callback.data.split("_")[1]
    await callback.message.edit_text(
        f"Категория: {products[cat_key]['title']}",
        reply_markup=products_kb(cat_key)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("item_"))
async def open_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break

    caption = f"{item['name']}\nЦена: {item['price']} ₽\n\n{item['desc']}"

    # Если нет фото, просто отправим текст
    await callback.message.answer(caption, reply_markup=buy_kb(item_id))

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break

    user = callback.from_user
    text = (
        "🆕 Новый заказ!\n\n"
        f"Товар: {item['name']}\n"
        f"Цена: {item['price']} ₽\n\n"
        f"Пользователь: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: {user.id}\n\n"
        "Ответь реплаем на это сообщение, чтобы написать клиенту."
    )

    msg = await bot.send_message(OPERATOR_ID, text)
    pending_orders[msg.message_id] = user.id
    await callback.message.answer("Ваш заказ отправлен оператору!")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "contact_operator")
async def contact_operator(callback: types.CallbackQuery):
    msg = await bot.send_message(callback.from_user.id, "Напишите сообщение оператору:")
    pending_contacts[msg.message_id] = callback.from_user.id

@dp.callback_query_handler(lambda c: c.data == "leave_review")
async def leave_review(callback: types.CallbackQuery):
    msg = await bot.send_message(callback.from_user.id, "Напишите ваш отзыв:")
    pending_reviews[msg.message_id] = callback.from_user.id

@dp.message_handler(lambda m: m.chat.id == OPERATOR_ID)
async def operator_reply(message: types.Message):
    if not message.reply_to_message:
        return

    msg_id = message.reply_to_message.message_id

    # Проверяем заказы
    if msg_id in pending_orders:
        user_id = pending_orders[msg_id]
        await bot.send_message(user_id, f"Оператор: {message.text}")
    # Проверяем контакты
    elif msg_id in pending_contacts:
        user_id = pending_contacts[msg_id]
        await bot.send_message(user_id, f"Оператор: {message.text}")
    # Проверяем отзывы
    elif msg_id in pending_reviews:
        user_id = pending_reviews[msg_id]
        await bot.send_message(user_id, f"Спасибо за ваш отзыв! Вы написали:\n{message.text}")

# ================== ПОЛУЧЕНИЕ СООБЩЕНИЙ ОТ ПОЛЬЗОВАТЕЛЯ ==================
@dp.message_handler()
async def handle_user_message(message: types.Message):
    # Проверяем контакты
    for msg_id, user_id in pending_contacts.items():
        if message.from_user.id == user_id:
            await bot.send_message(OPERATOR_ID, f"Сообщение от пользователя {message.full_name} (@{message.username}):\n{message.text}")
            del pending_contacts[msg_id]
            await message.answer("Ваше сообщение отправлено оператору!")
            return

    # Проверяем отзывы
    for msg_id, user_id in pending_reviews.items():
        if message.from_user.id == user_id:
            await bot.send_message(OPERATOR_ID, f"Отзыв от пользователя {message.full_name} (@{message.username}):\n{message.text}")
            del pending_reviews[msg_id]
            await message.answer("Спасибо за ваш отзыв!")
            return

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
