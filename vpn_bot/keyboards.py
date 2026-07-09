from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 VPN info")],
            [KeyboardButton(text="💳 Extend VPN"), KeyboardButton(text="🔄 Reset traffic")],
            [KeyboardButton(text="📱 Share phone", request_contact=True)],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➕ New invite")]],
        resize_keyboard=True,
    )


def extend_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 month — 50 ₽", callback_data="extend:1")],
            [InlineKeyboardButton(text="2 months — 100 ₽", callback_data="extend:2")],
            [InlineKeyboardButton(text="3 months — 150 ₽", callback_data="extend:3")],
        ]
    )


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirm reset", callback_data="reset:confirm")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="reset:cancel")],
        ]
    )
