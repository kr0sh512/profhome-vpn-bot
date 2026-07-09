from __future__ import annotations

from typing import Any

import httpx

from .utils import (
    DAYS_PER_MONTH,
    PAID_TRAFFIC_BYTES,
    TRIAL_DAYS,
    TRIAL_TRAFFIC_BYTES,
    add_days_from_base,
    build_marzban_note,
    calculate_reset_expire,
    format_marzban_username,
    now_ts,
)

DEFAULT_PROXIES = {"vless": {"flow": "xtls-rprx-vision"}}
DEFAULT_INBOUNDS = {"vless": ["VLESS TCP REALITY"]}


class MarzbanError(RuntimeError):
    pass


class MarzbanClient:
    def __init__(self, *, base_url: str, username: str, password: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._token: str | None = None
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def build_trial_user_payload(
        *,
        tg_user_id: int,
        first_name: str | None,
        last_name: str | None,
        tg_username: str | None,
        phone: str | None,
        now: int | None = None,
    ) -> dict[str, Any]:
        current = now_ts() if now is None else now
        return {
            "username": format_marzban_username(tg_user_id),
            "proxies": DEFAULT_PROXIES,
            "inbounds": DEFAULT_INBOUNDS,
            "expire": current + TRIAL_DAYS * 24 * 60 * 60,
            "data_limit": TRIAL_TRAFFIC_BYTES,
            "data_limit_reset_strategy": "no_reset",
            "status": "active",
            "note": build_marzban_note(
                first_name=first_name,
                last_name=last_name,
                username=tg_username,
                phone=phone,
            ),
        }

    async def authenticate(self) -> str:
        response = await self._client.post(
            "/api/admin/token",
            data={"username": self.username, "password": self.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code >= 400:
            raise MarzbanError(f"Marzban auth failed: {response.status_code} {response.text}")
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise MarzbanError("Marzban auth response does not contain access_token")
        self._token = str(token)
        return self._token

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._token:
            await self.authenticate()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        response = await self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code == 401:
            await self.authenticate()
            headers["Authorization"] = f"Bearer {self._token}"
            response = await self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise MarzbanError(f"Marzban API error {method} {path}: {response.status_code} {response.text}")
        if not response.content:
            return None
        return response.json()

    async def create_trial_user(
        self,
        *,
        tg_user_id: int,
        first_name: str | None,
        last_name: str | None,
        tg_username: str | None,
        phone: str | None = None,
    ) -> dict[str, Any]:
        payload = self.build_trial_user_payload(
            tg_user_id=tg_user_id,
            first_name=first_name,
            last_name=last_name,
            tg_username=tg_username,
            phone=phone,
        )
        return await self._request("POST", "/api/user", json=payload)

    async def get_user(self, username: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/user/{username}")

    async def modify_user(self, username: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PUT", f"/api/user/{username}", json=payload)

    async def reset_user_usage(self, username: str) -> dict[str, Any] | None:
        return await self._request("POST", f"/api/user/{username}/reset")

    async def extend_user(self, username: str, months: int) -> dict[str, Any]:
        user = await self.get_user(username)
        current_expire = user.get("expire")
        new_expire = add_days_from_base(current_expire=current_expire, days=months * DAYS_PER_MONTH)
        payload = {
            "expire": new_expire,
            "data_limit": PAID_TRAFFIC_BYTES,
            "data_limit_reset_strategy": "no_reset",
            "status": "active",
        }
        await self.modify_user(username, payload)
        await self.reset_user_usage(username)
        return await self.get_user(username)

    async def reset_paid_traffic_with_time_penalty(self, username: str) -> tuple[dict[str, Any], int, int]:
        user = await self.get_user(username)
        new_expire, full_months = calculate_reset_expire(expire=user.get("expire"))
        payload = {
            "expire": new_expire,
            "data_limit": PAID_TRAFFIC_BYTES,
            "data_limit_reset_strategy": "no_reset",
            "status": "active",
        }
        await self.modify_user(username, payload)
        await self.reset_user_usage(username)
        fresh = await self.get_user(username)
        return fresh, full_months, new_expire
