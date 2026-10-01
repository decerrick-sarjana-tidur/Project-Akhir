import flet as ft


@ft.control("NativeGoogleSignInService")
class NativeGoogleSignInService(ft.Service):
    async def sign_in(self, server_client_id: str) -> str | None:
        return await self._invoke_method(
            "sign_in",
            arguments={"server_client_id": server_client_id},
        )


@ft.control("VaultReminderService")
class VaultReminderService(ft.Service):
    async def request_permission(self) -> bool:
        return await self._invoke_method("request_permission")

    async def schedule_daily(
        self, notification_id: int, title: str, body: str, hour: int, minute: int
    ) -> None:
        await self._invoke_method(
            "schedule_daily",
            arguments={
                "id": notification_id,
                "title": title,
                "body": body,
                "hour": hour,
                "minute": minute,
            },
        )

    async def show(
        self, notification_id: int, title: str, body: str
    ) -> None:
        await self._invoke_method(
            "show",
            arguments={"id": notification_id, "title": title, "body": body},
        )

    async def cancel(self, notification_id: int) -> None:
        await self._invoke_method("cancel", arguments={"id": notification_id})
