import logging
from aiogram import Bot, Dispatcher, types, executor

# ================== НАСТРОЙКИ ==================
TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 123456789  # Ваш Telegram ID

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
    kb.add(types.InlineKeyboardButton("Написать оператору", callback_data="contact_operator"))
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

pending_messages = {}  # msg_id оператора -> user_id

# ================== ХЕНДЛЕРЫ ==================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в магазин еды!", reply_markup=main_menu())

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
    await callback.message.answer(caption, reply_markup=buy_kb(item_id))

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = None
    for cat in products.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                item = it
                break
    text = (
        f"🆕 Новый заказ!\n\n"
        f"Товар: {item['name']}\n"
        f"Цена: {item['price']} ₽\n"
        f"Пользователь: {callback.from_user.full_name}\n"
        f"Username: @{callback.from_user.username}\n"
        f"User ID: {callback.from_user.id}\n\n"
        "Ответь на это сообщение, чтобы написать клиенту."
    )
    msg = await bot.send_message(OPERATOR_ID, text)
    pending_messages[msg.message_id] = callback.from_user.id
    await callback.answer("Ваш заказ отправлен оператору!")

@dp.callback_query_handler(lambda c: c.data == "contact_operator")
async def contact_operator(callback: types.CallbackQuery):
    text = "Напишите ваше сообщение оператору:"
    msg = await bot.send_message(callback.from_user.id, text)
    pending_messages[msg.message_id] = OPERATOR_ID
    await callback.answer("Теперь напишите сообщение оператору!")

# Ответ оператора пользователю
@dp.message_handler(lambda m: m.chat.id == OPERATOR_ID)
async def operator_reply(message: types.Message):
    if not message.reply_to_message:
        return
    orig_msg_id = message.reply_to_message.message_id
    user_id = pending_messages.get(orig_msg_id)
    if user_id:
        await bot.send_message(user_id, f"Оператор: {message.text}")

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
