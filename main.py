import logging
from aiogram import Bot, Dispatcher, executor, types

# ================== "
TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 7892937398

# ================== ДАННЫЕ 
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
    kb.add(types.InlineKeyboardButton("Оставить отзыв", callback_data="review"))
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
    return kb

# ================== БОТ ==================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

pending_orders = {}  # message_id -> user_id
pending_messages = {}  # operator reply -> user_id

# ================== ХЕНДЛЕРЫ ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в магазин еды!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_main(callback: types.CallbackQuery):
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
    # Если нет фото, просто отправляем текст
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
        f"🆕 Новый заказ!\n\n"
        f"Товар: {item['name']}\n"
        f"Цена: {item['price']} ₽\n\n"
        f"Пользователь: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: {user.id}\n\n"
        "Нажмите 'Ответить пользователю', чтобы написать клиенту."
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Ответить пользователю", callback_data=f"reply_{user.id}"))

    msg = await bot.send_message(OPERATOR_ID, text, reply_markup=kb)
    pending_orders[msg.message_id] = user.id

    await callback.message.answer("Ваш заказ отправлен оператору!")
    await callback.answer()

# ================== Связь с оператором и отзыв ==================

@dp.callback_query_handler(lambda c: c.data == "contact_operator")
async def contact_operator(callback: types.CallbackQuery):
    await callback.message.answer("Введите сообщение для оператора:")
    dp.register_message_handler(operator_message, lambda m: m.from_user.id == callback.from_user.id, state=None)

async def operator_message(message: types.Message):
    text = (
        f"📩 Сообщение от пользователя {message.from_user.full_name} (@{message.from_user.username}, id:{message.from_user.id}):\n\n"
        f"{message.text}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Ответить пользователю", callback_data=f"reply_{message.from_user.id}"))
    await bot.send_message(OPERATOR_ID, text, reply_markup=kb)
    await message.answer("Ваше сообщение отправлено оператору!")

@dp.callback_query_handler(lambda c: c.data == "review")
async def leave_review(callback: types.CallbackQuery):
    await callback.message.answer("Напишите свой отзыв о магазине:")
    dp.register_message_handler(review_message, lambda m: m.from_user.id == callback.from_user.id, state=None)

async def review_message(message: types.Message):
    text = f"📝 Новый отзыв от {message.from_user.full_name} (@{message.from_user.username}):\n\n{message.text}"
    await bot.send_message(OPERATOR_ID, text)
    await message.answer("Спасибо за ваш отзыв!")

# ================== Ответ оператора ==================

@dp.callback_query_handler(lambda c: c.data.startswith("reply_"))
async def operator_reply(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"Введите сообщение для пользователя {user_id}:")
    dp.register_message_handler(send_to_user, lambda m: m.from_user.id == callback.from_user.id and m.chat.id == OPERATOR_ID, state=None)

async def send_to_user(message: types.Message):
    parts = message.text.split("\n", 1)
    await bot.send_message(message.chat.id, "Ответ отправлен!")
    # Находим user_id из последней нажатой кнопки
    user_id = None
    for key, val in pending_orders.items():
        if val == message.chat.id:
            user_id = val
            break
    if user_id:
        await bot.send_message(user_id, f"Оператор: {message.text}")

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
