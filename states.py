from aiogram.dispatcher.filters.state import StatesGroup, State

class NewGroup(StatesGroup):
    Name = State()
    IsOpen = State()

class SendAlert(StatesGroup):
    Text = State()

class EnterGroup(StatesGroup):
    Code = State()

class ChangeGroup(StatesGroup):
    Name = State()