import telebot
import os
import logging
import time
import threading
import random
from telebot import types

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

# Проверка текущей рабочей директории
print(f'текущая рабочая директория: {os.getcwd()}')

# Инициализация Telegram-бота
API_TOKEN = 'YOUR_API_TOKEN_HERE'
bot = telebot.TeleBot(API_TOKEN)

# Список фактов
facts = [
    "Вода составляет около 70% массы тела взрослого человека.",
    "Питьевая вода помогает поддерживать здоровый баланс жидкости в вашем теле.",
    "Ваш мозг и сердце состоят примерно на 73% из воды.",
    "Вода помогает регулировать температуру тела.",
    "Употребление достаточного количества воды может помочь вам сосредоточиться и повысить концентрацию.",
    "Вода может помочь улучшить энергию и уменьшить усталость.",
    "Рекомендуется употреблять около 2-2,5 литров воды в день для женщин и около 3 литров для мужчин."
    " Это включает все жидкости, получаемые из напитков и пищи.",
    "Лучше всего пить воду равномерно в течение дня, не дожидаясь появления чувства жажды."
    " Например, можно выпивать стакан воды утром после пробуждения, затем пить воду между"
    " приемами пищи и во время или после тренировок.",
    "Пожилым людям следует следить за тем, чтобы не допускать обезвоживания, так как"
    " с возрастом чувство жажды может притупляться. Детям также необходимо следить за"
    " достаточным потреблением жидкости, так как они могут быть более активны и терять больше воды.",
    "При повышенной физической активности или в жарком климате потребность в воде увеличивается."
    " В таких условиях важно пить больше, чтобы компенсировать потерю жидкости через потоотделение.",
    "Важно прислушиваться к своему организму: если вы чувствуете жажду, это сигнал о том, что нужно выпить воды."
    " Также следует помнить, что чрезмерное потребление воды может привести к водной интоксикации,"
    " поэтому важно соблюдать баланс."
    "Для поддержания высокой работоспособности в течение рабочего дня рекомендуется делать регулярные перерывы."
    " Один из популярных подходов — это техника Помидоро, которая предполагает работу в течение 25 минут,"
    " а затем перерыв на 5 минут. После четырех таких циклов рекомендуется делать более длительный перерыв,"
    " около 15-30 минут.",
    "Для поддержания высокой работоспособности в течение рабочего дня предлагают делать перерывы каждые 60-90 минут, поскольку это соответствует"
    " естественным ритмам нашего тела, таким как ультрадианный ритм. Важно помнить, что перерывы"
    " должны включать в себя смену деятельности — например, небольшую прогулку, упражнения"
    " или просто отдых от экрана компьютера — чтобы помочь восстановить концентрацию и энергию."
]

# Флаг для уведомлений каждые 5 минут
notify_enabled = {}

# Глобальные переменные для отслеживания состояния таймера
timers = {}
paused = {}
stop_flags = {}

# Обработчик ошибок
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            bot.send_message(args[0].chat.id, "Произошла ошибка! Попробуйте снова.")
    return wrapper

# Функция для отправки напоминаний о чистой воде
def send_water_reminder(chat_id):
    while True:
        try:
            bot.send_message(chat_id, "Не забудьте выпить чистой воды! 💧")
            time.sleep(3000)  # Каждое напоминание каждые 50 минут
        except Exception as e:
            logging.error(f"Ошибка в напоминаниях о воде: {e}")
            break  # Прерывание потока в случае ошибки

# Функция для отправки таймера
def start_timer(chat_id, work_time, break_time):
    def timer_cycle():
        # Инициализация таймера, сброс "elapsed" при старте нового таймера
        timers[chat_id] = {"elapsed": 0, "is_running": True}
        stop_flags[chat_id] = False

        while not stop_flags[chat_id]:
            if paused.get(chat_id, False):
                time.sleep(1)
                continue

            # Добавляем проверку на паузу и обновляем elapsed только при работающем таймере
           # if not paused.get(chat_id, False):
            #    elapsed_time += 1
             #   timers[chat_id]["elapsed"] = elapsed_time

            bot.send_message(chat_id, f"Время работать! Следующие {work_time} минут.")
            elapsed_time = timers[chat_id]["elapsed"]
            work_seconds = work_time * 60

            for elapsed_time in range(timers[chat_id]["elapsed"], work_seconds):
                if stop_flags.get(chat_id, False):
                    timers[chat_id]["elapsed"] = 0  # Сброс при остановке
                    break
                if paused.get(chat_id, False):
                    timers[chat_id]["elapsed"] = elapsed_time
                    break
                time.sleep(1)

                # Обновляем счетчик таймера
                timers[chat_id]["elapsed"] = elapsed_time

                # Каждые 300 секунд обновляем время
                if elapsed_time % 300 == 0:
                    bot.send_message(chat_id, f"Прошло {elapsed_time // 60} минут {elapsed_time % 60} секунд работы.")

            if stop_flags.get(chat_id, False):
                timers[chat_id]["elapsed"] = 0
                break

            if not paused.get(chat_id, False):
                timers[chat_id]["elapsed"] = 0  # Сброс elapsed после завершения рабочего времени
                bot.send_message(chat_id, f"Время на перерыв! Отдыхайте {break_time} минут.")
                time.sleep(break_time * 60)

    thread = threading.Thread(target=timer_cycle)
    thread.start()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, 'Привет! Я чат бот, буду помогать тебе с режимом труда\nи отдыха, '
                          'нужно вовремя отдыхать для повышения\nпроизводительности и не забывать пить чистую воду! 💧\n'
                          '\nВыбери подходящий режим работы и отдыха:'
                 '\nВариант 1: (25/5) или Вариант 2: (50/10)')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Вариант 1: (25/5)')
    btn2 = types.KeyboardButton('Вариант 2: (50/10)')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Выбери кнопку с вариантом:', reply_markup=markup)


# Обработчик нажатий на кнопки выбора режима
@bot.message_handler(func=lambda message: message.text in ['Вариант 1: (25/5)', 'Вариант 2: (50/10)'])
def handle_choice(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pause_btn = types.KeyboardButton('/pause_timer')
    stop_btn = types.KeyboardButton('/stop_timer')
    resume_timer_btn = types.KeyboardButton('/resume_timer')
    markup.add(pause_btn, stop_btn, resume_timer_btn)

    if message.text == 'Вариант 1: (25/5)':
        work_time, break_time = 25, 5
    elif message.text == 'Вариант 2: (50/10)':
        work_time, break_time = 50, 10

    bot.send_message(chat_id, f"Вы выбрали Вариант: {work_time} минут работы, {break_time} минут перерыва.", reply_markup=markup)
    stop_flags[chat_id] = False
    # Запуск таймера с выбранными параметрами
    start_timer(chat_id, work_time, break_time)

# Обработчик команды /pause_timer
@bot.message_handler(commands=['pause_timer'])
def pause_timer(message):
    chat_id = message.chat.id
    if chat_id in timers:
        paused[chat_id] = True
        bot.send_message(chat_id, "Таймер на паузе.")
    else:
        bot.send_message(chat_id, "Таймер еще не был запущен.")

# Обработчик команды /stop_timer
@bot.message_handler(commands=['stop_timer'])
def stop_timer(message):
    chat_id = message.chat.id
    if chat_id in timers:
        stop_flags[chat_id] = True
        paused[chat_id] = False
        timers[chat_id]["elapsed"] = 0  # Сброс времени
        bot.send_message(chat_id, "Таймер остановлен и сброшен.")
    else:
        bot.send_message(chat_id, "Таймер еще не был запущен.")

# Обработчик команды /resume_timer
@bot.message_handler(commands=['resume_timer'])
def resume_timer(message):
    chat_id = message.chat.id
    if chat_id in timers and paused.get(chat_id, False):
        paused[chat_id] = False
        bot.send_message(chat_id, "Таймер возобновлен.")
    else:
        bot.send_message(chat_id, "Таймер не был на паузе или еще не запущен.")

# Обработчик команды /time
@bot.message_handler(commands=['time'])
def send_time(message):
    chat_id = message.chat.id
    if chat_id in timers:
        elapsed = timers[chat_id].get("elapsed", 0)
        minutes, seconds = divmod(elapsed, 60)
        bot.reply_to(message, f"Прошло {minutes} минут {seconds} секунд.")
    else:
        bot.reply_to(message, "Таймер еще не запущен.")


# Обработчик команды /help
@bot.message_handler(commands=['help'])
@error_handler
def send_help(message):
    help_text = (
        "/start - Начать общение с ботом\n"
        "/help - Показать это сообщение с командами\n"
        "/reminder - Начать напоминания о питье воды\n"
        "/fact - Получить интересный факт о воде 💧 и не только\n"
        "/time - Показать прошедшее время работы\n"
        "/pause_timer - Поставить таймер на паузу\n"
        "/stop_timer - Остановить таймер\n"
        "/resume_timer - Возобновить таймер\n"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pause_btn = types.KeyboardButton('/pause_timer')
    stop_btn = types.KeyboardButton('/stop_timer')
    resume_timer_btn = types.KeyboardButton('/resume_timer')
    markup.add(pause_btn, stop_btn, resume_timer_btn)
    bot.send_message(message.chat.id, help_text, reply_markup=markup)

# Обработчик команды /reminder
@bot.message_handler(commands=['reminder'])
@error_handler
def start_reminder(message):
    thread = threading.Thread(target=send_water_reminder, args=(message.chat.id,))
    thread.start()
    bot.reply_to(message, "Напоминания о питье воды включены!💧")

# Обработчик команды /fact
@bot.message_handler(commands=['fact'])
@error_handler
def send_fact(message):
    fact = random.choice(facts)
    bot.reply_to(message, fact)


# Запуск бота
if __name__ == "__main__":
    logging.info("Запуск бота")
    bot.polling(none_stop=True, timeout=10, long_polling_timeout=20)
