from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json

# Словарь для хранения голосов (в реальном проекте используйте базу данных)
polls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    await update.message.reply_text(
        "Привет! Я бот для создания голосований.\n\n"
        "Используйте команду:\n"
        "/poll Ваш вопрос? | Вариант 1 | Вариант 2 | Вариант 3\n\n"
        "Пример:\n"
        "/poll Куда пойдем в выходные? | Кино | Парк | Ресторан | Дома"
    )

async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание голосования"""
    if not context.args:
        await update.message.reply_text(
            "Используйте формат:\n"
            "/poll Вопрос? | Вариант 1 | Вариант 2 | Вариант 3"
        )
        return
    
    # Парсим текст команды
    text = ' '.join(context.args)
    parts = [p.strip() for p in text.split('|')]
    
    if len(parts) < 3:
        await update.message.reply_text(
            "Нужен минимум вопрос и 2 варианта ответа!"
        )
        return
    
    question = parts[0]
    options = parts[1:]
    
    # Создаем уникальный ID для опроса
    poll_id = f"{update.message.chat_id}_{update.message.message_id}"
    
    # Инициализируем данные опроса
    polls[poll_id] = {
        'question': question,
        'options': options,
        'votes': {opt: {} for opt in options}  # Теперь храним {user_id: user_name}
    }
    
    # Создаем клавиатуру с кнопками
    keyboard = []
    for idx, option in enumerate(options):
        keyboard.append([
            InlineKeyboardButton(
                f"⚪ {option} - 0",
                callback_data=f"vote_{poll_id}_{idx}"
            )
        ])
    
    # Добавляем кнопку для просмотра списка проголосовавших
    keyboard.append([
        InlineKeyboardButton(
            "👥 Показать список проголосовавших",
            callback_data=f"show_{poll_id}"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 *{question}*\n\nВыберите вариант:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def format_voters_list(poll_data):
    """Формирует список проголосовавших"""
    voters_text = ""
    total_votes = 0
    
    for option in poll_data['options']:
        voters = poll_data['votes'][option]
        vote_count = len(voters)
        total_votes += vote_count
        
        if vote_count > 0:
            voters_text += f"\n*{option}* ({vote_count}):\n"
            for user_name in voters.values():
                voters_text += f"  • {user_name}\n"
    
    if total_votes == 0:
        return "\nПока никто не проголосовал."
    
    return voters_text

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосования"""
    query = update.callback_query
    await query.answer()
    
    # Парсим данные callback
    data_parts = query.data.split('_', 2)
    if len(data_parts) != 3:
        return
    
    action = data_parts[0]
    poll_id = data_parts[1]
    
    if poll_id not in polls:
        await query.answer("Опрос устарел!", show_alert=True)
        return
    
    poll_data = polls[poll_id]
    
    # Если это запрос на показ списка
    if action == "show":
        voters_list = format_voters_list(poll_data)
        await query.answer(
            f"📋 Список проголосовавших:\n{voters_list}",
            show_alert=True
        )
        return
    
    # Обработка голосования
    option_idx = int(data_parts[2])
    selected_option = poll_data['options'][option_idx]
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Если есть username, используем его
    if query.from_user.username:
        user_name = f"@{query.from_user.username}"
    
    # Удаляем предыдущий голос пользователя (если есть)
    for option in poll_data['options']:
        if user_id in poll_data['votes'][option]:
            del poll_data['votes'][option][user_id]
    
    # Добавляем новый голос
    poll_data['votes'][selected_option][user_id] = user_name
    
    # Обновляем отображение
    keyboard = []
    for idx, option in enumerate(poll_data['options']):
        vote_count = len(poll_data['votes'][option])
        # Показываем галочку для выбранного варианта
        icon = "🔵" if option == selected_option and user_id in poll_data['votes'][option] else "⚪"
        keyboard.append([
            InlineKeyboardButton(
                f"{icon} {option} - {vote_count}",
                callback_data=f"vote_{poll_id}_{idx}"
            )
        ])
    
    # Добавляем кнопку для просмотра списка
    keyboard.append([
        InlineKeyboardButton(
            "👥 Показать список проголосовавших",
            callback_data=f"show_{poll_id}"
        )
    ])
    
    # Подсчитываем общее количество голосов
    total_votes = sum(len(votes) for votes in poll_data['votes'].values())
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📊 *{poll_data['question']}*\n\n"
        f"Всего проголосовало: {total_votes}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def main():
    """Запуск бота"""
    # ВАЖНО: Получите токен у @BotFather для вашего бота Opros_volleyball_bot
    # Вставьте его сюда:
    TOKEN = '7320859699:AAFYU55q8UzYj5vb6E8xRovjY8h7-Xggonk'
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("poll", create_poll))
    application.add_handler(CallbackQueryHandler(handle_vote))
    
    # Запускаем бота
    print("Бот Opros_volleyball_bot запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
