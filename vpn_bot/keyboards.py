from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Информация о VPN")],
            [KeyboardButton(text="💳 Продлить VPN"), KeyboardButton(text="🔄 Сбросить трафик")],
            [KeyboardButton(text="📱 Поделиться телефоном", request_contact=True)],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➕ Новое приглашение")]],
        resize_keyboard=True,
    )


def extend_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц — 50 ₽", callback_data="extend:1")],
            [InlineKeyboardButton(text="2 месяца — 100 ₽", callback_data="extend:2")],
            [InlineKeyboardButton(text="3 месяца — 150 ₽", callback_data="extend:3")],
        ]
    )


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить сброс", callback_data="reset:confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="reset:cancel")],
        ]
    )
