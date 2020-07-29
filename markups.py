from telebot import types

command_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
command_markup.row('Расписание на:')
command_markup.row('Сегодня', 'Завтра')
command_markup.row('Неделю вперёд', 'Определённый день')
command_markup.row('Обратная связь')
