from aiogram import Dispatcher

from .dm import router as dm_router
from .group import router as group_router
from .owner import router as owner_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(group_router)
    dp.include_router(owner_router)  # before dm so owner middleware runs first
    dp.include_router(dm_router)
