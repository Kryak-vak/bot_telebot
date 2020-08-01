import telebot
from telebot import types
import markups as m
import sqlite3
import manage_db as db
import datetime as dt
from pytz import timezone
from threading import Thread
from time import sleep

bot = telebot.TeleBot('1183262455:AAGPPikztj-dcxKaQNBJh7ltcEplibroJdc')
tz = timezone('Europe/Moscow')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, я - бот помощник преподавателя МГСУ\n\n'
                                      'С помощью меня Вы сможете легко и быстро получать расписание\n\n'
                                      'Но для начала мне нужно узнать кто Вы')
    start(message)


def start(message):
    if db.check_id(message.chat.id):
        db.remove_user_by_id(message.chat.id)

    cath_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cath in db.get_all_cathedras():
        cath_markup.add(types.InlineKeyboardButton(cath))

    bot.send_message(message.chat.id, 'Пожалуйста, выберите свою кафедру из появившегося списка\n\n'
                                      '(Список можно листать / Если Вы случайно укажите неправильные данные, '
                                      'то ничего страшного, '
                                      'по окончанию их можно будет поменять)', reply_markup=cath_markup)

    bot.register_next_step_handler(message, got_cathedra)


def got_cathedra(message):
    if not db.check_cathedra(message.text):
        bot.send_message(message.chat.id, 'Пожалуйста, выберите кафедру из списка')
        bot.register_next_step_handler(message, got_cathedra)
        return

    lect_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for lecturer in sorted(db.get_lecturers_by_cathedra(message.text)):
        lect_markup.add(types.InlineKeyboardButton(lecturer))

    bot.send_message(message.chat.id, 'Выберите себя в списке '
                                      'преподавателей указанной кафедры', reply_markup=lect_markup)

    bot.register_next_step_handler(message, got_lecturer, message.text)


def got_lecturer(message, cathedra):
    if not db.check_lecturer(message.text):
        bot.send_message(message.chat.id, 'Пожалуйста, выберите преподователя из списка')
        bot.register_next_step_handler(message, got_lecturer, cathedra)
        return

    db.insert_user({'id': message.chat.id, 'fullname': message.text, 'cathedra': cathedra})

    bot.send_message(message.chat.id, 'Отлично! Теперь можно приступать к работе\n\n'
                                      '(Если Вы случайно указали неправильные данные '
                                      'напишите \n/restart)', reply_markup=m.command_markup)


@bot.message_handler(commands=['restart'])
def restart(message):
    start(message)


@bot.message_handler(func=lambda mess: 'Обратная связь' == mess.text, content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, 'Если у вас возникли проблемы или Вы хотите что-то предложить:\n'
                                      '\n> Автор проекта - Вакашев Шамиль\n'
                                      '\n • VK - https://vk.com/mr.vaflya'
                                      '\n • Почта - mr.vakashev@mail.ru\n'
                                      '\n> Тестировщик - Владислав Ким\n'
                                      '\n • [Инстаграмм](https://instagram.com/vladislavkim.dev)',
                     parse_mode='Markdown')


@bot.message_handler(func=lambda mess: mess.text == 'Сегодня' or mess.text == 'Завтра', content_types=['text'])
def handle_text(message):
    if not db.check_id(message.chat.id):
        false_id_msg(message.chat.id)
        return

    if message.text == 'Сегодня':
        date, lectures = get_lectures(message.chat.id, dt.datetime.now(tz))
        answer = 'Сегодня - ' + int_date_to_string(date) + '\n\n'
    elif message.text == 'Завтра':
        date, lectures = get_lectures(message.chat.id, dt.datetime.now(tz) + dt.timedelta(days=1))
        answer = 'Завтра - ' + int_date_to_string(date) + '\n\n'

    answer += get_answer(lectures, date, message.chat.id)
    bot.send_message(message.chat.id, answer)


@bot.message_handler(func=lambda mess: 'Неделю вперёд' == mess.text, content_types=['text'])
def handle_text(message):
    if not db.check_id(message.chat.id):
        false_id_msg(message.chat.id)
        return

    answer = 'Расписание на ближаюшую неделю\n\n'

    for i in range(1, 8):
        date = dt.datetime.now(tz) + dt.timedelta(days=i)
        date, lectures = get_lectures(message.chat.id, date)
        answer += int_date_to_string(date) + ':\n\n' + get_answer(lectures, date, message.chat.id) + '\n'

    bot.send_message(message.chat.id, answer)


@bot.message_handler(func=lambda mess: 'Определённый день' == mess.text, content_types=['text'])
def handle_text(message):
    if not db.check_id(message.chat.id):
        false_id_msg(message.chat.id)
        return

    answer = 'Выберите день, расписание которого Вы хотите увидеть\n' \
             'Для переключения между месяцами нажмите "Предыдущий" или "Следующий"\n' \
             'Вернуться в основное меню можно нажав соответсвующую кнопку внизу"'

    date = dt.datetime.now(tz)
    keyboard = create_month_keyboard(date)
    bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    bot.register_next_step_handler(message, switch_months, date)


def switch_months(message, date):
    if message.text == 'Предыдущий':
        date -= dt.timedelta(days=date.day)
        keyboard = create_month_keyboard(date)
        bot.send_message(message.chat.id, f'Месяц переключён на {int_month_to_string(date.month)} {date.year}',
                         reply_markup=keyboard)

    elif message.text == 'Следующий':
        date += dt.timedelta(days=max_day(date.year, date.month) - date.day + 1)
        keyboard = create_month_keyboard(date)
        bot.send_message(message.chat.id, f'Месяц переключён на {int_month_to_string(date.month)} {date.year}',
                         reply_markup=keyboard)

    elif message.text == 'Вернуться в основное меню' or message.text == '/mainmenu':
        goto_main_menu(message)
        return

    elif message.text[0].isdigit() and message.text.find(' ') != -1:
        day = int(message.text[:message.text.find(' ')])

        if day > max_day(date.year, date.month) or day < 1:
            bot.send_message(message.chat.id, 'Введён некорректный день, пожалуйста, не вводите данные вручную')
            bot.register_next_step_handler(message, switch_months, date)
            return

        fdate, lectures = get_lectures(message.chat.id, dt.datetime(date.year, date.month, day, tzinfo=tz))
        answer = int_date_to_string(fdate) + ' ' + str(date.year) + ':\n\n' + get_answer(lectures, fdate, message.chat.id)
        bot.send_message(message.chat.id, answer)

    bot.register_next_step_handler(message, switch_months, date)


def create_month_keyboard(date):
    count_days = max_day(date.year, date.month)
    column_count, row_count = 6, count_days // 6
    month_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row_buttons, day, button = [], 1, 0

    month_keyboard.row(types.InlineKeyboardButton('Предыдущий'),
                       types.InlineKeyboardButton(int_month_to_string(date.month)),
                       types.InlineKeyboardButton('Следующий'))

    while count_days - day >= column_count:
        while button != column_count:
            if month_keyboard_buttons_text(date, day) != 'Вс':
                text = f'{day} {month_keyboard_buttons_text(date, day)}'
                row_buttons.append(types.InlineKeyboardButton(text))
                button += 1
            day += 1

        month_keyboard.row(row_buttons[0], row_buttons[1], row_buttons[2], row_buttons[3],
                           row_buttons[4], row_buttons[5])
        row_buttons = []
        button = 0

    while button <= count_days - day:
        if month_keyboard_buttons_text(date, day + button) != 'Вс':
            text = f'{day + button} {month_keyboard_buttons_text(date, day + button)}'
            row_buttons.append(types.InlineKeyboardButton(text))
        button += 1

    blank = types.InlineKeyboardButton('-')
    if len(row_buttons) == 1:
        month_keyboard.row(row_buttons[0], blank, blank, blank, blank, blank)
    elif len(row_buttons) == 2:
        month_keyboard.row(row_buttons[0], row_buttons[1], blank, blank, blank, blank)
    elif len(row_buttons) == 3:
        month_keyboard.row(row_buttons[0], row_buttons[1], row_buttons[2], blank, blank, blank)
    elif len(row_buttons) == 4:
        month_keyboard.row(row_buttons[0], row_buttons[1], row_buttons[2], row_buttons[3], blank, blank)
    elif len(row_buttons) == 5:
        month_keyboard.row(row_buttons[0], row_buttons[1], row_buttons[2], row_buttons[3], row_buttons[4], blank)

    month_keyboard.row(types.InlineKeyboardButton('Вернуться в основное меню'))

    return month_keyboard


@bot.message_handler(commands=['mainmenu'])
def goto_main_menu(message):
    bot.send_message(message.chat.id, 'Главное меню', reply_markup=m.command_markup)


@bot.message_handler(func=lambda mess: 'Вернуться в основное меню' == mess.text, content_types=['text'])
def handle_text(message):
    goto_main_menu(message)


def month_keyboard_buttons_text(date, day):
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    return week_days[dt.datetime(date.year, date.month, day, tzinfo=tz).weekday()]


def get_lectures(chat_id, date):
    lectures = db.get_lectures_by_month(db.get_lecturer_by_id(chat_id), date.month)
    date = date_format(date)
    db_date = date[:date.rfind('.')]

    if db_date in lectures:
        return date, lectures
    else:
        return date, None


def get_answer(lectures, date, chat_id):
    if not lectures:
        lecture_not_found_error(chat_id)
        return 'Не найдено'

    db_date = date[:date.rfind('.')]
    schedule = get_schedule()
    lecture_num = 1
    no_lects = True
    answer = ''

    for lecture in lectures[db_date]:
        answer += f'     {lecture_num}) {schedule[lecture_num - 1]}'
        lecture_num += 1

        if lecture != 'None':
            answer += ' - ' + lecture + '\n'
            no_lects = False
        else:
            answer += '\n'

    if no_lects:
        return 'Ни одной пары! Можете отдыхать :)\n\n'
    else:
        return answer


def int_date_to_string(int_date):
    day, month, year = [int(i) for i in int_date.split('.')]

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    return f'{day}-ое {months[month - 1]} {week_days[dt.datetime(year, month, day, tzinfo=tz).weekday()]}'


def int_month_to_string(int_month):
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

    return months[int(int_month) - 1]


def date_format(date):
    date = date.strftime("%d.%m.%Y")

    if date.startswith('0'):
        date = date[1:]

    return date


def max_day(year, month):
    month = int(month)
    max_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if year % 4:
        max_days[1] = 28

    return max_days[month - 1]


def get_schedule():
    return ['8:30', '10:10', '11:50', '13:30', '15:10', '16:50']


def false_id_msg(chat_id):
    bot.send_message(chat_id, 'Упс! Похоже информации о вас потерялась из базы данных :(\n'
                              'Пожалуйста, напишите /restart, чтобы я мог узнать кто Вы')


def lecture_not_found_error(chat_id):
    bot.send_message(chat_id, 'Не удалось получить расписание на выбранную дату\n'
                              'Возможно произошла утечка данных\n'
                              'Если вам не сложно, сообщите об ошибке автору\n\n'
                              'Приносим свои извенения :(', reply_markup=m.command_markup)


def lecture_notification(notify_users):
    for user_id in notify_users.keys():
        try:
            bot.send_message(user_id, 'До следующей пары осталось меньше 10 минут!\n\n'
                                      '     ' + notify_users[user_id],
                             reply_markup=m.command_markup)
        except telebot.apihelper.ApiException:
            db.remove_user_by_id(user_id)


def get_next_lectures(number):
    notify_users = {}
    date = dt.datetime.now(tz)

    for user_id in db.get_all_users_id():
        fdate, lectures = get_lectures(user_id, date)

        if not lectures:
            lecture_not_found_error(user_id)
            continue

        if lectures[fdate][number]:
            notify_users[user_id] = lectures[fdate][number]

    lecture_notification(notify_users)


def which_lecture_soon():
    while True:
        time = dt.datetime.now()
        schedule = [(8, 30), (10, 10), (11, 50), (13, 30), (15, 10), (16, 50)]
        number = 0

        for hour, minute in schedule:
            timedelta = dt.datetime(time.year, time.month, time.day, hour, minute) - time

            if timedelta.seconds < 600:
                get_next_lectures(number)
                sleep(540)
                break

            number += 1

        sleep(60)


if __name__ == '__main__':
    Thread(target=which_lecture_soon).start()

    bot.polling(none_stop=True)

# for user_id in db.get_all_users_id():
#     try:
#         bot.send_message(user_id, '> Произошла перезагрузка сервера', reply_markup=m.command_markup)
#     except telebot.apihelper.ApiException:
#         db.remove_user_by_id(user_id)
