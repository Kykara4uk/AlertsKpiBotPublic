import json
from typing import List
import datetime
from sqlalchemy import and_


from loader import bot
from utils.db_api.database import db
from utils.db_api.models import User, Group


async def get_user(tg_id):
    user = await User.query.where(User.tg_id == tg_id).gino.first()
    return user

async def get_user_groups(tg_id):
    user = await User.query.where(User.tg_id == tg_id).gino.first()
    return user

async def add_user(**kwargs):
    newuser = await User(**kwargs).create()
    return newuser


async def is_name_busy(name):
    return await Group.query.where(Group.name==name).gino.first()

async def get_group_by_code(code):
    return await Group.query.where(Group.code==code).gino.first()

async def get_group_by_id(code):
    return await Group.query.where(Group.group_id==int(code)).gino.first()

async def get_groups_by_ids(groups):
    list_of_groups = []
    for group_id in groups:
        group = await get_group_by_id(int(group_id))
        list_of_groups.append(group)

    return list_of_groups

async def get_open_groups():
    return await Group.query.where(Group.isOpen==True).gino.all()

async def get_group_users(group_id):
    group = await Group.query.where(Group.group_id==int(group_id)).gino.first()
    return group.users

async def get_group_admins(group_id):
    group = await Group.query.where(Group.group_id==int(group_id)).gino.first()
    return group.admins

async def where_user_can_send_alerts(user_id):
    groups = await Group.query.gino.all()
    groups_to_return=[]
    for group in groups:
        group_admins = json.loads(group.admins)
        if int(user_id) in group_admins:
            groups_to_return.append(group)
    return groups_to_return