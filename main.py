from aiogram import Bot, Dispatcher, F
from aiogram.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, CallbackQuery)
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from google.oauth2 import service_account
from googleapiclient.discovery import build

import json


# Все функции Aiogram
class Commands(StatesGroup):
    choice_event = State()
    menu_choice = State()
    create_event = State()
    start_event = State()
    end_event = State()
    delete_event_data = State()
    delete_event = State()
    look_event_start = State()
    look_event_end = State()
    time_event = State()
    create_time_event = State()
    end_time_event = State()
    choice_calendar = State()
    check_event = State()
    new_calendar = State()
    name_calendar = State()


# Авторизация в Google
class GoogleCalendar:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    FILE_PATH = 'credentials.json'

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)


# Авторизация Бота
obj = GoogleCalendar()
bot = Bot(token="7420151175:AAHSnw_VgB-Gtkd7dBEAuSby_c36jjY_uCk")
dp = Dispatcher()


# Меню
@dp.message(Command('menu'))
async def menu(message: Message, state: Commands):
    # Создание кнопок
    new_event = InlineKeyboardButton(
        text='Создать',
        callback_data='new_event'
    )

    delete_event = InlineKeyboardButton(
        text='Удалить',
        callback_data='delete_event'
    )

    choice_event = InlineKeyboardButton(
        text='Просмотреть',
        callback_data='choice_event'
    )

    new_calendar = InlineKeyboardButton(
        text='Доб.календарь',
        callback_data='new_calendar'
    )

    # Создаем объект инлайн-клавиатуры
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[new_event, choice_event],
                         [delete_event, new_calendar]]
    )
    await message.answer(
        text='Меню:\nВыберите действие\n\nЕсли кнопки на работают, введите команду /menu',
        reply_markup=keyboard
    )
    await state.set_state(Commands.menu_choice)


@dp.callback_query(StateFilter(Commands.menu_choice),
                   F.data.in_(['new_calendar']))
async def process_new_calendar(callback: CallbackQuery, state: Commands):
    await callback.message.answer(text='Чтоб добавить новый календарь, открой для "watsonhall@watsonhallbot.iam.gserviceaccount.com" доступ\nСкопируй и отправь сюда Идентификатор календаря')
    await state. set_state(Commands.new_calendar)


@dp.message(StateFilter(Commands.new_calendar))
async def process_new_calendar_2(message: Message, state: Commands):
    id_calendar = str(message.text)
    try:
        calendar_list_entry = {'id': id_calendar}
        obj.service.calendarList().insert(body=calendar_list_entry).execute()
    except:
        await message.answer(text='Произошла ошибка,  попробуйте еще раз!')
        await process_new_calendar(message, state)
    calendar = obj.service.calendarList().get(calendarId=id_calendar).execute()
    await state.update_data(id_calendar=id_calendar)
    await state.update_data(name_calendar=calendar["summary"])
    name_calendar = InlineKeyboardButton(
        text='Оставить',
        callback_data='dont_change'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[name_calendar]])
    await message.answer(text=f'Ваш календраь называется:{calendar["summary"]}\nЕсли хотите оставить название без изменений, нажмите кнопку ниже, иначе введите новое название',
                         reply_markup=keyboard)
    await state.set_state(Commands.name_calendar)

@dp.callback_query(StateFilter(Commands.name_calendar),
                   F.data.in_(['dont_change']))
async def process_name_events(callback: CallbackQuery, state: Commands):
    with open('BD.json') as f:
        calendars = json.load(f)
    new_calendar = await state.get_data()
    id_calendar = new_calendar["id_calendar"]
    name_calendar = new_calendar["name_calendar"]
    chat_id = str(callback.message.chat.id)
    if chat_id in calendars:
        calendars[chat_id].append({"id":id_calendar,
                                   "name":name_calendar})
    else:
        calendars[chat_id] = [{"id": id_calendar,
                                   "name": name_calendar}]
    with open('BD.json', 'w') as f:
        json.dump(calendars, f)
    await menu(callback.message, state)

@dp.callback_query(StateFilter(Commands.name_calendar))
async def process_change_name_calendar(callback:CallbackQuery, state: Commands):
    await state.update_data(name_calendar=str(callback.message.text))
    await process_name_events(callback, state)


# Создание нового мероприятия
# Ввод названия
@dp.callback_query(StateFilter(Commands.menu_choice),
                   F.data.in_(['new_event']))
async def process_name_events(callback: CallbackQuery, state: Commands):
    await callback.message.delete()
    await callback.message.answer(text='Название мероприятия')
    # Устанавливаем состояние ожидания ввода названия
    await state.set_state(Commands.start_event)


# Создание нового мероприятия
# Ввод даты
@dp.message(StateFilter(Commands.start_event))
async def process_start_events(message: Message, state: Commands):
    await state.update_data(name=message.text)
    await message.answer(text='Дата начала:\nФормат:дд.мм.гг')
    # Устанавливаем состояние ожидания ввода Даты
    await state.set_state(Commands.time_event)


@dp.message(StateFilter(Commands.choice_calendar))
async def process_choice_calendar(message: Message, state: Commands):
    with open('BD.json') as f:
        calendars = json.load(f)
    calendars = calendars[str(message.chat.id)]
    await state.update_data(calendars=calendars)
    keyboard = InlineKeyboardBuilder()
    for i in range(len(calendars)):
        keyboard.add(InlineKeyboardButton(
            text=calendars[i]["name"],
            callback_data=str(i))
        )
    await message.answer(
        text='Выберите календарь',
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(Commands.create_event)


# Создание нового мероприятия
# Отправка в гугл
@dp.callback_query(StateFilter(Commands.create_event))
async def process_create_events(callback: CallbackQuery, state: Commands):
    # Формирование нового мероприятия
    event_dict = await state.get_data()
    calendar_id = event_dict["calendars"][int(callback.data)]["id"]
    start = event_dict['start']
    if event_dict['time']:
        start_time = event_dict['start_time']
        end_time = event_dict['end_time']
        date_start = {'dateTime': f'20{start[-2:]}-{start[3:5]}-{start[:2]}T{start_time}:00+03:00'}
        date_end = {'dateTime': f'20{start[-2:]}-{start[3:5]}-{start[:2]}T{end_time}:00+03:00'}
    else:
        date_start = {'date': f'20{start[-2:]}-{start[3:5]}-{start[:2]}',
                      'timeZone': 'Europe/Moscow'
                      }
        date_end = {'date': f'20{start[-2:]}-{start[3:5]}-{start[:2]}',
                    'timeZone': 'Europe/Moscow'
                    }

    event = {
        'summary': event_dict['name'],
        'description': 'описание',
        'start': date_start,
        'end': date_end
    }
    obj.service.events().insert(calendarId=calendar_id, body=event).execute()
    await callback.message.answer('Мероприятие создано!')
    await menu(callback.message, state)


@dp.message(StateFilter(Commands.time_event))
async def process_time_events(message: Message, state: Commands):
    await state.update_data(start=message.text)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Весь день",
        callback_data="no_time")
    )
    await message.answer(
        'Введите время начала мероприятия или нажмите "Весь день"\nФормат ввода:ЧЧ:ММ',
        reply_markup=builder.as_markup()
    )
    await state.set_state(Commands.create_time_event)


@dp.callback_query(StateFilter(Commands.create_time_event),
                   F.data.in_(['no_time']))
async def process_create_events_no_time(callback: CallbackQuery, state: Commands):
    await state.update_data(time=False)
    await process_choice_calendar(callback.message, state)


@dp.message(StateFilter(Commands.create_time_event))
async def process_create_time_event(message: Message, state: Commands):
    await state.update_data(start_time=message.text)
    await state.update_data(time=True)
    await message.answer(text='Введите время окончания мероприятия\nФормат ввода:ЧЧ:ММ')
    await state.set_state(Commands.end_time_event)


@dp.message(StateFilter(Commands.end_time_event))
async def process_create_end_time_event(message: Message, state: Commands):
    await state.update_data(end_time=message.text)
    await process_choice_calendar(message, state)


# Удаление мероприятия
# Ввод даты
@dp.callback_query(StateFilter(Commands.menu_choice),
                   F.data.in_(['delete_event']))
async def process_delete_event_data(callback: CallbackQuery, state: Commands):
    await callback.message.delete()
    await callback.message.answer(text='Введите дату мероприятия:\nФормат:дд.мм.гг')
    await state.set_state(Commands.delete_event_data)


# Удаление мероприятия
@dp.message(StateFilter(Commands.delete_event_data))
async def process_delete_event_choice(message: Message, state: Commands):
    data = message.text
    calendars_events = []
    long = 0
    with open('BD.json') as f:
        calendars = json.load(f)
    calendars = calendars[str(message.chat.id)]
    for i in calendars:
        events = obj.service.events().list(calendarId=i["id"],
                                           timeMax=f'20{data[-2:]}-{data[3:5]}-{data[:2]}T21:00:00+03:00',
                                           timeMin=f'20{data[-2:]}-{data[3:5]}-{data[:2]}T00:00:00+03:00'
                                           ).execute()
        events = events['items']
        long += len(events)
        calendars_events.append(events)
    await state.update_data(events=events)
    await state.update_data(long=long)
    answer = ''
    event_dict = []
    for j in range(len(calendars_events)):
        events = calendars_events[j]
        for i in range(len(events)):
            if "dateTime" in events[i]["start"]:
                date = f'{events[i]["start"]["dateTime"][11:16]} - {events[i]["end"]["dateTime"][11:16]} {events[i]["start"]["dateTime"][8:10]}.{events[i]["start"]["dateTime"][5:7]}'
            else:
                date = f'{events[i]["start"]["date"][-2:]}.{events[i]["start"]["date"][5:7]}'
            answer = f'{long}. {events[i]["summary"]}, {date},  {calendars[j]["name"]}' + '\n' + answer
            evcal = {"id":events[i]["id"], "calendar":calendars[j]["id"]}
            event_dict.append(evcal)
            long -= 1
    await state.update_data(event_dict=event_dict)
    await message.answer(text=answer)
    await state.set_state(Commands.delete_event)


# Выбор мероприятия для удаления
@dp.message(StateFilter(Commands.delete_event))
async def process_delete_event(message: Message, state: Commands):
    event = await state.get_data()
    id_event = abs(int(message.text) - int(event['long']))
    obj.service.events().delete(calendarId=event["event_dict"][id_event]["calendar"],
                                eventId=event["event_dict"][id_event]["id"]).execute()
    await message.answer(text='Выполено')
    await menu(message, state)


# Просмотр мероприятий
# Ввод даты начала
@dp.callback_query(StateFilter(Commands.menu_choice),
                   F.data.in_(['choice_event']))
async def process_look_event_data_start(callback: CallbackQuery, state: Commands):
    await callback.message.delete()
    await callback.message.answer(text='Введите c какого числа искать мероприятия:\nФормат:дд.мм.гг')
    await state.set_state(Commands.look_event_start)


# Просмотр мероприятий
# Ввод даты окончания
@dp.message(StateFilter(Commands.look_event_start))
async def process_look_event_data_end(message: Message, state: Commands):
    await state.update_data(start_look=message.text)
    await message.answer(text='Введите до какого числа искать мероприятия:\nФормат:дд.мм.гг')
    # Устанавливаем состояние ожидания ввода Даты
    await state.set_state(Commands.look_event_end)


# Просмотр мероприятий
# Вывод мероприятий
@dp.message(StateFilter(Commands.look_event_end))
async def process_look_event_data_end(message: Message, state: Commands):
    with open('BD.json') as f:
        calendars = json.load(f)
    calendars = calendars[str(message.chat.id)]
    await state.update_data(end_look=message.text)
    events_dict = await state.get_data()
    data_start = events_dict['start_look']
    data_end = events_dict['end_look']
    calendars_events = []
    long = 0
    for i in calendars:
        events = obj.service.events().list(calendarId=i["id"],
                                           timeMax=f'20{data_end[-2:]}-{data_end[3:5]}-{data_end[:2]}T21:00:00+03:00',
                                           timeMin=f'20{data_start[-2:]}-{data_start[3:5]}-{data_start[:2]}T00:00:00+03:00'
                                           ).execute()
        events = events['items']
        long += len(events)
        calendars_events.append(events)
    answer = ''
    for j in range(len(calendars_events)):
        events = calendars_events[j]
        for i in range(len(events)):
            if "dateTime" in events[i]["start"]:
                date = f'{events[i]["start"]["dateTime"][11:16]} - {events[i]["end"]["dateTime"][11:16]} {events[i]["start"]["dateTime"][8:10]}.{events[i]["start"]["dateTime"][5:7]}'
            else:
                date = f'{events[i]["start"]["date"][-2:]}.{events[i]["start"]["date"][5:7]}'
            answer = f'{long}. {events[i]["summary"]}, {date},  {calendars[j]["name"]}' + '\n' + answer
            long -= 1
    await message.answer(text=answer)
    await menu(message, state)


if __name__ == '__main__':
    dp.run_polling(bot)
