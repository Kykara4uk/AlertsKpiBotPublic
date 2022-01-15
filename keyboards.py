import json

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram import types

from utils.db_api.db_commands import get_groups_by_ids, get_group_by_id, get_open_groups, get_group_users, get_user, \
    get_group_admins, where_user_can_send_alerts

menu_cd = CallbackData("show_menu", "level", "id", "i", "id2")


def make_callback_data(level, id= 0, i = 0, id2=0):
    return menu_cd.new(level=level, id = id, i = i, id2=id2)


async def menu_markup(user_id):

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(text="Мои комнаты", callback_data=make_callback_data(level=1)),)
    markup.row(InlineKeyboardButton(text="Войти в новую комнату", callback_data=make_callback_data(level=2)),)
    markup.row(InlineKeyboardButton(text="Создать новую комнату", callback_data=make_callback_data(level=0)))
    isCanSend = await where_user_can_send_alerts(user_id)
    if len(isCanSend)>0:
        markup.row(InlineKeyboardButton(text="Написать уведомление", callback_data=make_callback_data(level=23)), )
    return markup


async def my_groups_markup(groups):
    markup = InlineKeyboardMarkup(row_width=2)

    groups_sorted = (await get_groups_by_ids(groups))
    groups_sorted.sort(key=lambda x: x.name)
    for group in groups_sorted:
        markup.insert(
            InlineKeyboardButton(text=group.name, callback_data=make_callback_data(level=3, id=group.group_id)),)
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=4)),)
    return markup


async def send_alert_choose_group_markup(user_id):
    markup = InlineKeyboardMarkup(row_width=2)

    groups_sorted = (await where_user_can_send_alerts(user_id))
    groups_sorted.sort(key=lambda x: x.name)
    for group in groups_sorted:
        markup.insert(
            InlineKeyboardButton(text=group.name, callback_data=make_callback_data(level=5, id=group.group_id)),)
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=4)),)
    return markup


async def enter_group_markup(i, user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(InlineKeyboardButton(text="Ввести код доступа", callback_data=make_callback_data(level=13)))
    markup.row()
    groups = (await get_open_groups())
    groups_sorted = list(groups)
    for group in groups:
        users = json.loads(group.users)
        if user_id in users:
            groups_sorted.remove(group)
    groups_sorted.sort(key=lambda x: x.name)
    groups = groups_sorted[10 * int(i):10 * int(i) + 10]
    for j in range(len(groups)):
        button_text = f"{groups[int(j)].name}"
        callback_data = make_callback_data(level=12, id=groups[int(j)].group_id, i=i)

        markup.insert(InlineKeyboardMarkup(text=button_text, callback_data=callback_data))
    if len(groups_sorted) % 10==0:
        caption = f"{int(i) + 1}/{(len(groups_sorted) // 10) }"
    else:
        caption = f"{int(i) + 1}/{(len(groups_sorted) // 10) + 1}"
    size = len(groups_sorted) - 1
    if int(i) + 1 > (size // 10):
        i1 = 0
    else:
        i1 = int(i) + 1
    if int(i) - 1 < 0:
        i2 = (size // 10)
    else:
        i2 = int(i) - 1

    markup.row(InlineKeyboardButton(text="◀️", callback_data=make_callback_data(level=2, i=i2)),
               InlineKeyboardButton(text=caption, callback_data=make_callback_data(level=2, i=i)),
               InlineKeyboardButton(text="▶️", callback_data=make_callback_data(level=2, i=i1)))
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=4)))
    return markup


async def change_group_users_markup(i, group_id):
    markup = InlineKeyboardMarkup(row_width=1)

    markup.row()
    users_sorted = json.loads(await get_group_users(group_id))
    users_sorted.sort()
    users = users_sorted[10 * int(i):10 * int(i) + 10]
    for j in range(len(users)):
        user = await get_user(users[int(j)])
        button_text = f"{user.fullname}"

        callback_data = make_callback_data(level=15, id=users[int(j)], i=i, id2=group_id)

        markup.insert(InlineKeyboardMarkup(text=button_text, callback_data=callback_data))
    caption = f"{int(i) + 1}/{(len(users_sorted) // 10) + 1}"
    size = len(users_sorted) - 1
    if int(i) + 1 > (size // 10):
        i1 = 0
    else:
        i1 = int(i) + 1
    if int(i) - 1 < 0:
        i2 = (size // 10)
    else:
        i2 = int(i) - 1
    markup.row(InlineKeyboardButton(text="◀️", callback_data=make_callback_data(level=11, i=i2, id=group_id)),
               InlineKeyboardButton(text=caption, callback_data=make_callback_data(level=11, i=i, id=group_id)),
               InlineKeyboardButton(text="▶️", callback_data=make_callback_data(level=11, i=i1, id=group_id)))
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=3, id=group_id)))
    return markup


async def change_group_admins_markup(i, group_id):
    markup = InlineKeyboardMarkup(row_width=1)

    markup.row()
    users_sorted = json.loads(await get_group_admins(group_id))
    users_sorted.sort()
    users = users_sorted[10 * int(i):10 * int(i) + 10]
    for j in range(len(users)):
        user = await get_user(users[int(j)])
        button_text = f"{user.fullname}"

        callback_data = make_callback_data(level=18, id=users[int(j)], i=i, id2=group_id)

        markup.insert(InlineKeyboardMarkup(text=button_text, callback_data=callback_data))
    caption = f"{int(i) + 1}/{(len(users_sorted) // 10) + 1}"
    size = len(users_sorted) - 1
    if int(i) + 1 > (size // 10):
        i1 = 0
    else:
        i1 = int(i) + 1
    if int(i) - 1 < 0:
        i2 = (size // 10)
    else:
        i2 = int(i) - 1
    markup.row(InlineKeyboardButton(text="◀️", callback_data=make_callback_data(level=6, i=i2, id=group_id)),
               InlineKeyboardButton(text=caption, callback_data=make_callback_data(level=6, i=i, id=group_id)),
               InlineKeyboardButton(text="▶️", callback_data=make_callback_data(level=6, i=i1, id=group_id)))
    markup.row(InlineKeyboardButton(text="Добавить администратора", callback_data=make_callback_data(level=21, id=group_id)))
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=3, id=group_id)))
    return markup


async def group_markup(group_id, user_id):
    markup = InlineKeyboardMarkup()
    group = await get_group_by_id(int(group_id))
    group_admins = json.loads(group.admins)
    if user_id == group.owner:
        markup.row(InlineKeyboardButton(text="Написать в группу", callback_data=make_callback_data(level=5, id=group_id)), )
        markup.row(InlineKeyboardButton(text="Участники", callback_data=make_callback_data(level=11, id=group_id)), )
        markup.row(InlineKeyboardButton(text="Админы", callback_data=make_callback_data(level=6, id=group_id)), )

        markup.row(InlineKeyboardButton(text="Изменить название", callback_data=make_callback_data(level=7, id=group_id)), )
        markup.row(InlineKeyboardButton(text="Обновить код и ссылку", callback_data=make_callback_data(level=8, id=group_id)), )
        if group.isOpen:
            markup.row(InlineKeyboardButton(text="Сделать группу закрытой",
                                            callback_data=make_callback_data(level=22, id=group_id)), )
        else:
            markup.row(InlineKeyboardButton(text="Сделать группу открытой",
                                            callback_data=make_callback_data(level=22, id=group_id)), )
        markup.row(InlineKeyboardButton(text="Удалить группу", callback_data=make_callback_data(level=9, id=group_id)), )
    elif user_id in group_admins:
        markup.row(InlineKeyboardButton(text="Написать в группу", callback_data=make_callback_data(level=5, id=group_id)), )
        markup.row(InlineKeyboardButton(text="Выйти из группы", callback_data=make_callback_data(level=14, id=group_id)), )
    else:
        markup.row(InlineKeyboardButton(text="Выйти из группы", callback_data=make_callback_data(level=10, id=group_id)), )
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=1, id=group_id)), )
    return markup


async def user_markup(group_id, user_id, i):
    markup = InlineKeyboardMarkup()
    group = await get_group_by_id(int(group_id))
    group_admins = json.loads(group.admins)
    if int(user_id) != group.owner:
        if int(user_id) not in group_admins:
            markup.row(InlineKeyboardButton(text="Выдать права админа",
                                            callback_data=make_callback_data(level=20, id=group_id, i=i,
                                                                             id2=user_id)), )
        else:
            markup.row(InlineKeyboardButton(text="Забрать права админа",
                                            callback_data=make_callback_data(level=19, id=group_id, i=i,
                                                                             id2=user_id)), )
        markup.row(InlineKeyboardButton(text="Удалить",
                                        callback_data=make_callback_data(level=16, id=group_id, i=i, id2=user_id)), )

    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=11, id=group_id, i=i)), )

    return markup


async def admin_markup(group_id, user_id, i):
    markup = InlineKeyboardMarkup()
    group = await get_group_by_id(int(group_id))

    if int(user_id) != group.owner:
        markup.row(InlineKeyboardButton(text="Забрать права админа",
                                        callback_data=make_callback_data(level=19, id=group_id, i=i, id2=user_id)), )
    markup.row(InlineKeyboardButton(text="Удалить",
                                    callback_data=make_callback_data(level=16, id=group_id, i=i, id2=user_id)), )
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=6, id=group_id, i=i)), )

    return markup


async def close_or_open_group_markup():
    markup = types.ReplyKeyboardMarkup(input_field_placeholder="Нажми на кнопку ниже")

    markup.add("Открытая")
    markup.add("Закрытая")

    return markup


async def confirm_group_delete_markup(group_id):
    markup = InlineKeyboardMarkup(row_width=2)

    markup.row(InlineKeyboardButton(text="Да, удалить", callback_data=make_callback_data(level=17, id=group_id)),

               InlineKeyboardButton(text="Нет", callback_data=make_callback_data(level=3, id=group_id)))

    return markup
