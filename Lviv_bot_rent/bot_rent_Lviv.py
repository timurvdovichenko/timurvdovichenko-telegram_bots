import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from collections import defaultdict
from dotenv import load_dotenv


# Загрузка переменных из файла .env
load_dotenv()

# Чтение токена и ID канала из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Проверьте, что переменные загружены корректно
if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("Не удалось загрузить BOT_TOKEN или CHANNEL_ID. Проверьте файл .env.")

# Создайте экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Хранилище для сообщений и реакций
reaction_counts = defaultdict(int)  # {message_id: count}
original_messages = {}  # {message_id: Message}

# Количество "сердечек" для отправки сообщения
REQUIRED_HEARTS = 1

# Обработчик входящих сообщений
@dp.message_handler(content_types=types.ContentType.ANY)
async def receive_message(message: types.Message):
    msg_id = message.message_id
    chat_id = message.chat.id

    # Сохраняем сообщение для отслеживания
    original_messages[msg_id] = message
    reaction_counts[msg_id] = 0

    await message.reply(f"Чтобы отправить это сообщение в канал, оно должно набрать {REQUIRED_HEARTS} ❤️.")

# Обработчик добавления реакций
@dp.message_handler(content_types=types.ContentType.ANY)
async def on_emoji_reaction(event: types.Message):
    # Проверяем, что реакция — это сердечко
    if event.sticker and event.sticker.emoji == '❤️':
        replied_msg_id = event.reply_to_message.message_id
        if replied_msg_id in reaction_counts:
            reaction_counts[replied_msg_id] += 1
            current_count = reaction_counts[replied_msg_id]

            # Обновляем пользователя о текущем количестве сердечек
            await event.reply(f"❤️: {current_count}/{REQUIRED_HEARTS}")

            # Если достигли порога, отправляем в канал
            if current_count >= REQUIRED_HEARTS:
                original_msg = original_messages.pop(replied_msg_id, None)
                reaction_counts.pop(replied_msg_id, None)
                if original_msg:
                    await bot.copy_message(
                        chat_id=CHANNEL_ID,
                        from_chat_id=original_msg.chat.id,
                        message_id=original_msg.message_id,
                    )
                    await event.reply("Сообщение отправлено в канал!")
        else:
            await event.reply("Это сообщение не отслеживается ботом.")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
