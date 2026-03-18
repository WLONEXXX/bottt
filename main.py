import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ================== НАСТРОЙКИ ==================

TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 123456789  # Ваш ID в Телеграм

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

pending = {}  # message_id оператора -> user_id

# ================== КЛАВИАТУРЫ ==================

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Каталог", callback_data="catalog"))
    kb.add(types.InlineKeyboardButton("Связаться с оператором", callback_data="contact"))
    kb.add(types.InlineKeyboardButton("Оставить отзыв", callback_data="review"))
    return kb

def categories_kb():
    kb = types.InlineKeyboardMarkup()
    for key, cat in products.items():
        kb.add(types.InlineKeyboardButton(cat["title"], callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main"))
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

# ================== ХЕНДЛЕРЫ ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в магазин Whitch shop!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "main")
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
    await callback.message.edit_text(caption, reply_markup=buy_kb(item_id))

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
        "Ответь на это сообщение реплаем, чтобы написать клиенту."
    )
    msg = await bot.send_message(OPERATOR_ID, text)
    pending[msg.message_id] = user.id
    await callback.answer("Ваш заказ отправлен оператору!")

@dp.callback_query_handler(lambda c: c.data == "contact")
async def contact_operator(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Напишите сообщение для оператора. Он ответит вам в этом чате."
    )
    pending[callback.from_user.id] = "contact"

@dp.callback_query_handler(lambda c: c.data == "review")
async def leave_review(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Напишите ваш отзыв. Оператор получит его в личку."
    )
    pending[callback.from_user.id] = "review"

@dp.message_handler()
async def handle_user_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in pending:
        mode = pending[user_id]
        if mode == "contact":
            await bot.send_message(OPERATOR_ID, f"Сообщение от пользователя {message.full_name}:\n{message.text}")
            await message.answer("Ваше сообщение отправлено оператору!")
        elif mode == "review":
            await bot.send_message(OPERATOR_ID, f"Отзыв от пользователя {message.full_name}:\n{message.text}")
            await message.answer("Спасибо за ваш отзыв!")
        del pending[user_id]

@dp.message_handler(lambda m: m.chat.id == OPERATOR_ID)
async def operator_reply(message: types.Message):
    if not message.reply_to_message:
        return
    orig = message.reply_to_message.message_id
    user_id = pending.get(orig)
    if user_id:
        await bot.send_message(user_id, f"Оператор: {message.text}")
        del pending[orig]

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
