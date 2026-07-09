from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from .config import Config
from .db import Database
from .keyboards import admin_menu, extend_keyboard, main_menu, reset_confirm_keyboard
from .marzban import MarzbanClient, MarzbanError
from .messages import format_vpn_info, generate_invite_token, payment_amount, user_display_name
from .utils import build_marzban_note, format_marzban_username, format_timestamp, now_ts


@dataclass
class PendingPayment:
    months: int
    amount: int


class BotApp:
    def __init__(self, *, config: Config, db: Database, marzban: MarzbanClient):
        self.config = config
        self.db = db
        self.marzban = marzban
        self.router = Router()
        self.pending_payments: dict[int, PendingPayment] = {}
        self._register_handlers()

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.config.admin_ids

    def _register_handlers(self) -> None:
        self.router.message(CommandStart())(self.start)
        self.router.message(F.text == "➕ Новое приглашение")(self.new_invite)
        self.router.message(F.text == "/new_user")(self.new_invite)
        self.router.message(F.text == "📄 Информация о VPN")(self.vpn_info)
        self.router.message(F.text == "💳 Продлить VPN")(self.extend_menu)
        self.router.message(F.text == "🔄 Сбросить трафик")(self.reset_explain)
        self.router.message(F.contact)(self.save_contact)
        self.router.callback_query(F.data.startswith("extend:"))(self.select_extend)
        self.router.callback_query(F.data == "reset:confirm")(self.confirm_reset)
        self.router.callback_query(F.data == "reset:cancel")(self.cancel_reset)
        self.router.message(F.photo | F.document)(self.payment_proof)

    async def start(self, message: Message) -> None:
        user_id = message.from_user.id if message.from_user else None
        args = message.text.split(maxsplit=1)[1].strip() if message.text and " " in message.text else ""

        if args:
            await self.activate_invite(message, args)
            return

        if self.is_admin(user_id):
            await message.answer("Меню администратора", reply_markup=admin_menu())
            return

        if user_id and self.db.get_by_tg_user_id(user_id):
            await message.answer("С возвращением.", reply_markup=main_menu())
            return

        await message.answer("Попросите администратора выдать ссылку-приглашение.")

    async def new_invite(self, message: Message) -> None:
        if not self.is_admin(message.from_user.id if message.from_user else None):
            await message.answer("Создавать приглашения могут только администраторы.")
            return
        bot_user = await message.bot.get_me()
        token = generate_invite_token()
        self.db.create_invite(token=token, admin_id=message.from_user.id, created_at=now_ts())
        link = f"https://t.me/{bot_user.username}?start={token}"
        text = f"Ссылка-приглашение создана:\n{link}"
        await message.answer(text)
        await self.notify_admins(message.bot, f"➕ Новое приглашение создано администратором {message.from_user.id}\n{link}")

    async def activate_invite(self, message: Message, token: str) -> None:
        tg = message.from_user
        if tg is None:
            return
        existing = self.db.get_by_tg_user_id(tg.id)
        if existing:
            await message.answer("Вы уже активированы.", reply_markup=main_menu())
            return
        invite = self.db.get_by_token(token)
        if invite is None:
            await message.answer("Некорректная ссылка-приглашение.")
            return
        if invite["tg_user_id"] is not None:
            await message.answer("Эта ссылка-приглашение уже использована.")
            return

        marzban_username = format_marzban_username(tg.id)
        try:
            await self.marzban.create_trial_user(
                tg_user_id=tg.id,
                first_name=tg.first_name,
                last_name=tg.last_name,
                tg_username=tg.username,
            )
            self.db.activate_invite(
                token=token,
                tg_user_id=tg.id,
                tg_username=tg.username,
                tg_first_name=tg.first_name,
                tg_last_name=tg.last_name,
                tg_phone=None,
                marzban_username=marzban_username,
                activated_at=now_ts(),
            )
            user = await self.marzban.get_user(marzban_username)
        except (MarzbanError, ValueError) as exc:
            await message.answer(f"Не удалось активировать VPN: {exc}")
            await self.notify_admins(message.bot, f"⚠️ Ошибка активации для {tg.id}: {exc}")
            return

        await message.answer("Пробный VPN активирован на 3 дня / 10 GB.", reply_markup=main_menu())
        await message.answer(format_vpn_info(user))
        await self.notify_admins(
            message.bot,
            f"✅ Пользователь активировал приглашение\nTelegram: {tg.first_name or ''} {tg.last_name or ''} @{tg.username or '-'}\nMarzban: {marzban_username}",
        )

    async def get_current_local_user(self, message_or_query: Message | CallbackQuery) -> dict[str, Any] | None:
        from_user = message_or_query.from_user
        if from_user is None:
            return None
        return self.db.get_by_tg_user_id(from_user.id)

    async def vpn_info(self, message: Message) -> None:
        row = await self.get_current_local_user(message)
        if not row or not row.get("marzban_username"):
            await message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            return
        try:
            user = await self.marzban.get_user(row["marzban_username"])
        except MarzbanError as exc:
            await message.answer(f"Не удалось получить информацию о VPN: {exc}")
            return
        await message.answer(format_vpn_info(user))

    async def extend_menu(self, message: Message) -> None:
        row = await self.get_current_local_user(message)
        if not row:
            await message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            return
        await message.answer("Выберите срок продления:", reply_markup=extend_keyboard())

    async def select_extend(self, query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        row = self.db.get_by_tg_user_id(query.from_user.id)
        if not row:
            await query.message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            await query.answer()
            return
        months = int(query.data.split(":", 1)[1])
        amount = payment_amount(months)
        self.pending_payments[query.from_user.id] = PendingPayment(months=months, amount=amount)
        await query.message.answer(
            f"Выбрано продление: {months} мес., {amount} ₽.\n\n"
            f"{self.config.payment_text}\n\n"
            "После оплаты пришлите сюда скриншот/фото или файл с подтверждением."
        )
        await query.answer()

    async def payment_proof(self, message: Message) -> None:
        if message.from_user is None:
            return
        pending = self.pending_payments.get(message.from_user.id)
        if pending is None:
            return
        row = self.db.get_by_tg_user_id(message.from_user.id)
        if not row or not row.get("marzban_username"):
            await message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            return
        try:
            user = await self.marzban.extend_user(row["marzban_username"], pending.months)
        except MarzbanError as exc:
            await message.answer(f"Не удалось продлить VPN: {exc}")
            await self.notify_admins(message.bot, f"⚠️ Ошибка продления для {row['marzban_username']}: {exc}")
            return
        self.pending_payments.pop(message.from_user.id, None)
        await message.answer("Подтверждение оплаты получено. VPN автоматически продлён.")
        await message.answer(format_vpn_info(user))
        caption = (
            "💳 Получено подтверждение оплаты, VPN продлён\n"
            f"Пользователь: {user_display_name(row)}\n"
            f"Marzban: {row['marzban_username']}\n"
            f"Период: {pending.months} мес.\n"
            f"Сумма: {pending.amount} ₽\n"
            f"Новая дата окончания: {format_timestamp(user.get('expire'))}"
        )
        await self.forward_payment_to_admins(message, caption)

    async def reset_explain(self, message: Message) -> None:
        row = await self.get_current_local_user(message)
        if not row:
            await message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            return
        await message.answer(
            "Сброс трафика восстановит лимит до 50 GB.\n\n"
            "Важно: все дни текущего неполного оплаченного месяца будут удалены. "
            "Оставшееся время VPN будет округлено вниз до целых периодов по 30 дней.\n\n"
            "Пример: если осталось 1 месяц и 12 дней, после сброса останется ровно 1 месяц.\n\n"
            "Продолжить?",
            reply_markup=reset_confirm_keyboard(),
        )

    async def confirm_reset(self, query: CallbackQuery) -> None:
        row = self.db.get_by_tg_user_id(query.from_user.id)
        if not row or not row.get("marzban_username"):
            await query.message.answer("Вы не активированы. Сначала откройте ссылку-приглашение.")
            await query.answer()
            return
        try:
            user, full_months, _new_expire = await self.marzban.reset_paid_traffic_with_time_penalty(row["marzban_username"])
        except MarzbanError as exc:
            await query.message.answer(f"Не удалось сбросить трафик: {exc}")
            await query.answer()
            return
        await query.message.answer(
            f"Трафик сброшен. Оставшееся время округлено вниз до {full_months} полн. мес."
        )
        await query.message.answer(format_vpn_info(user))
        await query.answer()

    async def cancel_reset(self, query: CallbackQuery) -> None:
        await query.message.answer("Сброс отменён.")
        await query.answer()

    async def save_contact(self, message: Message) -> None:
        if not message.from_user or not message.contact:
            return
        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer("Пожалуйста, отправьте свой контакт, а не чужой.")
            return
        phone = message.contact.phone_number
        self.db.update_phone(tg_user_id=message.from_user.id, phone=phone)
        row = self.db.get_by_tg_user_id(message.from_user.id)
        if row and row.get("marzban_username"):
            note = build_marzban_note(
                first_name=row.get("tg_first_name"),
                last_name=row.get("tg_last_name"),
                username=row.get("tg_username"),
                phone=phone,
            )
            try:
                await self.marzban.modify_user(row["marzban_username"], {"note": note})
            except MarzbanError:
                await message.answer("Телефон сохранён локально, но сейчас не удалось обновить заметку в Marzban.")
                return
        await message.answer("Телефон сохранён.", reply_markup=main_menu())

    async def notify_admins(self, bot: Bot, text: str) -> None:
        for admin_id in self.config.admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception:
                pass

    async def forward_payment_to_admins(self, message: Message, caption: str) -> None:
        for admin_id in self.config.admin_ids:
            try:
                if message.photo:
                    await message.bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption)
                elif message.document:
                    await message.bot.send_document(admin_id, message.document.file_id, caption=caption)
                else:
                    await message.bot.send_message(admin_id, caption)
            except Exception:
                pass


def build_dispatcher(app: BotApp) -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(app.router)
    return dp
