import logging
from aiogram import Bot, Dispatcher, types, executor

# ================== НАСТРОЙКИ ==================

TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 7892937398  # ID оператора

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


pending_messages = {}  # operator_id -> user_id

# ================== КЛАВИАТУРЫ ==================

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Каталог", callback_data="catalog"))
    kb.add(types.InlineKeyboardButton("Оставить отзыв", callback_data="review"))
    return kb

def categories_kb():
    kb = types.InlineKeyboardMarkup()
    for key, cat in products.items():
        kb.add(types.InlineKeyboardButton(cat["title"], callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="start"))
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

# ================== ЛОГИ ==================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================== ХЭНДЛЕРЫ ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в Whitch shop!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "start")
async def go_start(callback: types.CallbackQuery):
    await callback.message.edit_text("Добро пожаловать в Whitch shop!", reply_markup=main_menu())

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
        "Нажмите кнопку ниже, чтобы ответить пользователю."
    )

    # Кнопка для ответа оператору
    kb_reply = types.InlineKeyboardMarkup()
    kb_reply.add(types.InlineKeyboardButton("Ответить пользователю", callback_data=f"reply_{user.id}"))

    await bot.send_message(OPERATOR_ID, text, reply_markup=kb_reply)
    await callback.message.answer("Ваш заказ отправлен оператору!")
    await callback.answer()

# ================== СВЯЗЬ С ОПЕРАТОРОМ ==================

@dp.callback_query_handler(lambda c: c.data.startswith("reply_"))
async def operator_reply(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    pending_messages[callback.from_user.id] = user_id
    await callback.message.answer(f"Введите сообщение для пользователя {user_id}:")

@dp.message_handler(lambda m: m.from_user.id in pending_messages)
async def send_to_user(message: types.Message):
    operator_id = message.from_user.id
    user_id = pending_messages.get(operator_id)
    if user_id:
        await bot.send_message(user_id, f"Оператор: {message.text}")
        await message.answer("✅ Ответ отправлен пользователю!")
        del pending_messages[operator_id]

# ================== ОТЗЫВЫ ==================

@dp.callback_query_handler(lambda c: c.data == "review")
async def review_start(callback: types.CallbackQuery):
    pending_messages[callback.from_user.id] = "review"
    await callback.message.answer("Напишите ваш отзыв:")

@dp.message_handler(lambda m: pending_messages.get(m.from_user.id) == "review")
async def send_review(message: types.Message):
    await bot.send_message(OPERATOR_ID, f"📝 Отзыв от {message.from_user.full_name}:\n{message.text}")
    await message.answer("Спасибо за ваш отзыв!")
    del pending_messages[message.from_user.id]

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
