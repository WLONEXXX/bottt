import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== НАСТРОЙКИ ==================

TOKEN = "8794489664:AAEf5XAfIpzgojDuDmGMow9JEmpGYjJ6230"
OPERATOR_ID = 7892937398 # Ваш ID

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

# ================== ХЕНДЛЕРЫ ==================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Нажмите кнопку ниже чтобы связаться с оператором:",
        reply_markup=main_menu()
    )

@dp.callback_query_handler(lambda c: c.data == "main")
async def main_menu_callback(callback: types.CallbackQuery):
    # Очищаем состояние пользователя
    if callback.from_user.id in user_states:
        del user_states[callback.from_user.id]
    
    await callback.message.edit_text(
        "👋 Главное меню:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "contact")
async def contact_handler(callback: types.CallbackQuery):
    # Устанавливаем режим ожидания сообщения
    user_states[callback.from_user.id] = "waiting_message"
    
    await callback.message.edit_text(
        "💬 Напишите ваше сообщение оператору.\n"
        "Я отвечу вам как можно скорее!",
        reply_markup=back_kb()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "catalog")
async def catalog_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📚 Каталог временно пуст.\n"
        "Но вы можете связаться с оператором!",
        reply_markup=back_kb()
    )
    await callback.answer()

# Обработка всех текстовых сообщений
@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    
    # Если это оператор
    if user_id == OPERATOR_ID:
        # Проверяем, является ли это ответом на чье-то сообщение
        if message.reply_to_message:
            # Получаем ID оригинального сообщения
            original_msg_id = message.reply_to_message.message_id
            
            # Ищем пользователя в нашей базе
            if original_msg_id in user_messages:
                target_user_id = user_messages[original_msg_id]
                
                try:
                    # Отправляем ответ пользователю
                    await bot.send_message(
                        target_user_id,
                        f"📞 <b>Ответ оператора:</b>\n\n{message.text}",
                        parse_mode='HTML'
                    )
                    await message.reply("✅ Ответ отправлен!")
                except Exception as e:
                    await message.reply(f"❌ Ошибка: {e}")
            else:
                await message.reply("❌ Не могу найти пользователя для ответа")
        else:
            await message.reply(
                "ℹ️ Чтобы ответить пользователю:\n"
                "1. Нажмите на его сообщение\n"
                "2. Выберите 'Ответить'\n"
                "3. Напишите текст"
            )
    
    # Если это обычный пользователь
    else:
        # Проверяем режим пользователя
        if user_id in user_states and user_states[user_id] == "waiting_message":
            # Отправляем сообщение оператору
            try:
                # Формируем текст для оператора
                operator_text = (
                    f"💬 <b>Сообщение от пользователя</b>\n\n"
                    f"👤 Имя: {message.from_user.full_name}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📱 Username: @{message.from_user.username if message.from_user.username else 'нет'}\n\n"
                    f"📝 Текст:\n{message.text}"
                )
                
                # Отправляем оператору
                sent_msg = await bot.send_message(
                    OPERATOR_ID,
                    operator_text,
                    parse_mode='HTML'
                )
                
                # Сохраняем связь: ID отправленного сообщения -> ID пользователя
                user_messages[sent_msg.message_id] = user_id
                
                # Уведомляем пользователя
                await message.reply(
                    "✅ Сообщение отправлено оператору!\n"
                    "Ожидайте ответа.",
                    reply_markup=back_kb()
                )
                
                # Очищаем состояние
                del user_states[user_id]
                
            except Exception as e:
                await message.reply(f"❌ Ошибка при отправке: {e}")
                logging.error(f"Ошибка отправки оператору: {e}")
        else:
            # Если пользователь просто пишет без выбора опции
            await message.reply(
                "❓ Используйте кнопку 'Связаться с оператором'",
                reply_markup=main_menu()
            )

# ================== ЗАПУСК ==================

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Бот запущен!")
    print(f"👤 ID оператора: {OPERATOR_ID}")
    print("=" * 50)
    print("\n📝 ИНСТРУКЦИЯ:")
    print("1. Пользователь нажимает 'Связаться с оператором'")
    print("2. Пишет сообщение")
    print("3. Вам приходит уведомление")
    print("4. Чтобы ответить - нажмите на сообщение пользователя")
    print("5. Выберите 'Ответить' (Reply)")
    print("6. Напишите ответ и отправьте")
    print("=" * 50)
    
    executor.start_polling(dp, skip_updates=True)
