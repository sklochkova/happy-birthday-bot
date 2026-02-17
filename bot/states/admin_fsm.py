from aiogram.fsm.state import State, StatesGroup


class AdminFSM(StatesGroup):
    select_channel = State()
    main_menu = State()
    add_birthday_user = State()
    add_birthday_date = State()
    remove_birthday_user = State()
    set_time = State()
    set_timezone = State()
    edit_user_select = State()
    edit_user_name = State()
    grant_admin_user = State()
    revoke_admin_user = State()
