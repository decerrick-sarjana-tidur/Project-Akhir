"""main.py — MyVault (Flet) entrypoint dengan Firebase cloud sync.

Jalankan:
    flet run main.py
    flet run --web main.py   (mode web)

Saat .env berisi Firebase API key dan project ID yang valid, app akan
menampilkan layar login/daftar dan menyimpan seluruh vault ke cloud.
Tanpa .env (atau saat user pilih "tamu"), app berjalan secara lokal persis
seperti sebelum fitur sync ditambahkan.
"""
import json
import random
import uuid

import flet as ft
from flet_secure_storage import SecureStorage
from flet_reminders import NativeGoogleSignInService, VaultReminderService
from flet.auth.providers.google_oauth_provider import GoogleOAuthProvider

try:
    from .compat import (
        Margin, Padding, BorderRadius, Border, BorderSide,
        align, icon, font_weight,
    )
    from .theme import T, DISPLAY_FONT, today_str
    from .data import new_id, seed_vaults
    from . import screens, modals, db, auth_screen as auth_mod
except ImportError:
    from compat import (
        Margin, Padding, BorderRadius, Border, BorderSide,
        align, icon, font_weight,
    )
    from theme import T, DISPLAY_FONT, today_str
    from data import new_id, seed_vaults
    import screens, modals, db
    import auth_screen as auth_mod


PHONE_WIDTH  = 390
PHONE_HEIGHT = 780

NAV_ITEMS = [
    {"key": "dashboard", "icon": "HOME_ROUNDED",                  "label": "Dashboard"},
    {"key": "vaults",    "icon": "ACCOUNT_BALANCE_WALLET_ROUNDED", "label": "Vault"},
    {"key": "stats",     "icon": "TRENDING_UP_ROUNDED",            "label": "Statistik"},
    {"key": "settings",  "icon": "SETTINGS_ROUNDED",               "label": "Pengaturan"},
]


class MyVaultApp:
    def __init__(self, page: ft.Page):
        self.page = page

        # ── Data ──────────────────────────────────────────────────────────────
        self.vaults: list = []

        # ── Auth state ────────────────────────────────────────────────────────
        self.user: dict | None = None   # {"id": str, "email": str} setelah login
        self.is_guest: bool    = False  # True → mode tamu (data lokal saja)
        self._auth_obj         = None   # AuthScreen instance saat auth screen aktif
        self._google_provider = None
        if db.google_is_configured():
            self._google_provider = GoogleOAuthProvider(
                client_id=db.GOOGLE_CLIENT_ID,
                client_secret=db.GOOGLE_CLIENT_SECRET,
                redirect_url=db.FIREBASE_OAUTH_REDIRECT_URL,
            )

        # ── App / UI state ────────────────────────────────────────────────────
        self.tab         = "dashboard"
        self.detail_id   = None
        self.tx_mode     = None
        self.show_new_vault = False
        self.currency    = "IDR"
        self.notif_auto = self._get_stored("myvault.notif_auto") == "true"
        self.notif_custom = self._get_stored("myvault.notif_custom") == "true"
        self.custom_reminder_hour = int(
            self._get_stored("myvault.custom_reminder_hour") or 20
        )
        self.custom_reminder_minute = int(
            self._get_stored("myvault.custom_reminder_minute") or 0
        )
        self._offline_mode = False
        self._reminders_initialized = False
        self.toast_message = None
        self._toast_task_token = 0

        self.secure_storage = SecureStorage()
        self.page.services.append(self.secure_storage)
        self.reminder_service = VaultReminderService()
        self.page.services.append(self.reminder_service)
        self.native_google_sign_in = NativeGoogleSignInService()
        self.page.services.append(self.native_google_sign_in)

        # ── DatePicker (dibuat sekali, dipakai oleh new_vault_sheet) ──────────
        self.date_picker = ft.DatePicker(on_change=self._on_date_picked)
        self.page.overlay.append(self.date_picker)
        self._date_picker_target = None
        self.time_picker = ft.TimePicker(on_change=self._on_custom_time_picked)
        self.page.overlay.append(self.time_picker)

        self._setup_page()
        self._build_shell()
        # Jangan panggil render() dulu — tunggu hasil auth check
        self._startup()

    # ══════════════════════════════════════════════════════════════════════════
    # Page / shell setup
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_page(self):
        self.page.title = "MyVault"
        self.page.bgcolor = T.bg
        self.page.padding = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment   = ft.MainAxisAlignment.CENTER
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.fonts  = {
            DISPLAY_FONT: (
                "https://raw.githubusercontent.com/google/fonts/main/ofl/"
                "spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"
            )
        }
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.on_login = self._on_firebase_google_login
        self.page.on_resize = self._on_page_resize

    def _build_shell(self):
        # AnimatedSwitcher — cross-fades saat konten tab berubah
        self.content_area = ft.AnimatedSwitcher(
            content=ft.Container(expand=True),
            duration=ft.Duration(milliseconds=220),
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            transition=ft.AnimatedSwitcherTransition.FADE,
            expand=True,
        )

        # FAB (+ tambah vault)
        self.fab = ft.Container(
            right=18, bottom=18, width=52, height=52,
            border_radius=BorderRadius.all(18),
            gradient=ft.LinearGradient(
                begin=align("TOP_LEFT"), end=align("BOTTOM_RIGHT"),
                colors=[T.accent, T.accent_soft],
            ),
            alignment=align("CENTER"),
            on_click=lambda e: self.open_new_vault(),
            content=ft.Icon(icon("ADD_ROUNDED"), size=22, color="#FFFFFF"),
        )

        # Toast + modal holders
        self.toast_holder = ft.Container(left=14, right=14, top=14, content=None)
        self.modal_holder = ft.Container(
            expand=True, bgcolor="#05030E99",
            alignment=align("BOTTOM_CENTER"),
            visible=False, content=None,
        )

        # Stack utama (content + overlay)
        self.body_stack = ft.Stack(
            expand=True,
            controls=[self.content_area, self.toast_holder, self.fab, self.modal_holder],
        )

        # Nav bar bawah
        self.nav_bar = self._build_nav_bar()

        # Column layout normal (app mode)
        self.app_column = ft.Column(
            spacing=0, expand=True,
            controls=[
                self._status_bar(),
                ft.Container(expand=True, content=self.body_stack),
                self.nav_bar,
            ],
        )

        # The viewport displays a phone frame on desktop and fills mobile screens.
        self.phone = ft.Container(
            width=PHONE_WIDTH,
            height=PHONE_HEIGHT,
            bgcolor=T.bg,
            border_radius=BorderRadius.all(42),
            border=Border.all(8, "#000000"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self.app_column,  # diganti oleh _show_auth / _show_loading
        )
        self.viewport = ft.Container(
            expand=True,
            alignment=align("CENTER"),
            content=self.phone,
        )
        self._apply_viewport_size(self.page.width, self.page.height)
        self.page.add(self.viewport)

    def _on_page_resize(self, _event):
        self._apply_viewport_size(self.page.width, self.page.height)
        self.page.update()

    def _apply_viewport_size(self, width, height):
        if not width or not height:
            return

        self.viewport.width = width
        self.viewport.height = height

        if width <= 600:
            self.phone.width = width
            self.phone.height = height
            self.phone.border = None
            self.phone.border_radius = BorderRadius.all(0)
        else:
            self.phone.width = min(PHONE_WIDTH, max(320, width - 32))
            self.phone.height = min(PHONE_HEIGHT, max(480, height - 32))
            self.phone.border = Border.all(8, "#000000")
            self.phone.border_radius = BorderRadius.all(42)

    def _status_bar(self):
        return ft.Container(
            padding=Padding.only(left=24, right=24, top=14, bottom=6),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("9:41", size=12, color=T.muted),
                    ft.Row(spacing=5, controls=[
                        ft.Icon(icon("SAVINGS_ROUNDED"), size=12, color=T.brass),
                        ft.Text(
                            "MyVault", size=12,
                            weight=font_weight("W_600") or font_weight("BOLD"),
                            color=T.brass, font_family=DISPLAY_FONT,
                        ),
                    ]),
                ],
            ),
        )

    def _build_nav_bar(self):
        buttons = [self._nav_button(item) for item in NAV_ITEMS]
        return ft.Container(
            padding=Padding.only(left=8, right=8, top=10, bottom=16),
            border=(Border.only(top=BorderSide(1, T.surface_border)) if BorderSide else None),
            bgcolor=T.surface,
            content=ft.Row(controls=buttons, expand=True),
        )

    def _nav_button(self, item):
        active = self.tab == item["key"] and self.detail_id is None
        color  = T.accent_soft if active else T.muted_faint
        return ft.Container(
            expand=True, on_click=lambda e, key=item["key"]: self.go_tab(key),
            padding=Padding.symmetric(vertical=6, horizontal=0),
            content=ft.Column(
                spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon(item["icon"]), size=19, color=color),
                    ft.Text(
                        item["label"], size=10, color=color,
                        weight=(font_weight("W_600") or font_weight("BOLD")) if active else None,
                    ),
                    ft.Container(
                        width=4, height=4,
                        border_radius=BorderRadius.all(999),
                        bgcolor=T.accent_soft,
                    ) if active else ft.Container(height=4),
                ],
            ),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Startup & Auth
    # ══════════════════════════════════════════════════════════════════════════

    def _startup(self):
        """Dipanggil sekali setelah shell dibangun. Cek sesi atau tampilkan auth."""
        if not db.is_configured():
            self._show_auth()
            return

        access_token  = self._get_stored("myvault.access_token")
        refresh_token = self._get_stored("myvault.refresh_token")

        if access_token and refresh_token:
            self._show_loading("Memuat vault kamu...")
            self._bg(
                self._restore_session_threaded,
                access_token,
                refresh_token,
                on_done=self._handle_restore_session_result,
                on_error=self._handle_restore_session_error,
            )
        else:
            self._show_auth()

    # ── Background thread helper ───────────────────────────────────────────────

    def _bg(self, func, *args, on_done=None, on_error=None):
        """Jalankan func(*args) di background thread, lalu kirim hasil ke UI thread."""
        import asyncio
        import inspect

        async def runner():
            try:
                result = await asyncio.to_thread(func, *args)
                if on_done is not None:
                    callback_result = on_done(result)
                    if inspect.isawaitable(callback_result):
                        await callback_result
            except Exception as exc:
                print(f"[bg] {func.__name__} error: {exc}")
                if on_error is not None:
                    on_error(exc)

        self.page.run_task(runner)

    # ── Threaded: restore session ─────────────────────────────────────────────

    def _restore_session_threaded(self, access_token: str, refresh_token: str):
        return db.restore_session(access_token, refresh_token)

    def _handle_restore_session_result(self, result):
        try:
            if result["error"] or not result["user"]:
                if self._is_network_error(result.get("error")):
                    user_id = self._get_stored("myvault.user_id")
                    if user_id:
                        self._show_offline_cache(user_id)
                        return
                self._clear_saved_session()
                self._show_auth()
                return
            self.user = self._user_data(result["user"])
            if result["session"]:
                self._save_session(result["session"])
            self._load_vaults_and_show()
        except Exception as exc:
            print(f"[startup] restore session error: {exc}")
            self._clear_saved_session()
            self._show_auth()

    def _handle_restore_session_error(self, exc):
        print(f"[startup] restore session error: {exc}")
        user_id = self._get_stored("myvault.user_id")
        if self._is_network_error(exc) and user_id:
            self._show_offline_cache(user_id)
            return
        self._clear_saved_session()
        self._show_auth()

    def _load_vaults_and_show(self):
        """Muat vault tanpa memblokir event loop UI."""
        self._bg(
            db.load_vaults,
            self.user["id"],
            on_done=self._handle_vaults_loaded,
            on_error=self._handle_vaults_load_error,
        )

    def _handle_vaults_loaded(self, vaults):
        self.vaults = vaults
        self.is_guest = False
        self._offline_mode = False
        self.page.run_task(self._save_vault_cache, self.user["id"], vaults)
        self._show_app()
        self.render()

    def _handle_vaults_load_error(self, exc):
        print(f"[startup] load vaults error: {exc}")
        user_id = self.user["id"] if self.user else None
        if self._is_network_error(exc) and user_id:
            self._show_offline_cache(user_id)
            return
        self._show_auth()

    @staticmethod
    def _is_network_error(error) -> bool:
        message = str(error).casefold()
        return any(term in message for term in (
            "tidak dapat terhubung", "timed out", "timeout", "network",
            "unavailable", "connection", "name or service not known",
        ))

    async def _save_vault_cache(self, user_id: str, vaults: list) -> None:
        try:
            await self.secure_storage.set(
                f"myvault.vaults.{user_id}", json.dumps(vaults, separators=(",", ":"))
            )
        except Exception as exc:
            print(f"[cache] secure vault cache write failed: {exc}")

    def _show_offline_cache(self, user_id: str) -> None:
        async def load_cache():
            try:
                raw = await self.secure_storage.get(f"myvault.vaults.{user_id}")
                vaults = json.loads(raw) if raw is not None else None
                if not isinstance(vaults, list) or any(not isinstance(v, dict) for v in vaults):
                    self._show_auth()
                    return
                self.user = {
                    "id": user_id,
                    "email": self._get_stored("myvault.email") or "",
                    "name": "",
                }
                self.vaults = vaults
                self.is_guest = False
                self._offline_mode = True
                self._show_app()
                self.render()
                self.show_toast("Mode offline: vault hanya dapat dilihat, perubahan tidak disimpan.")
            except Exception as exc:
                print(f"[cache] secure vault cache read failed: {exc}")
                self._show_auth()

        self.page.run_task(load_cache)

    async def _on_google_login(self, page: ft.Page):
        if page.platform == ft.PagePlatform.ANDROID:
            if not db.GOOGLE_CLIENT_ID:
                self._handle_google_oauth_error(
                    "GOOGLE_CLIENT_ID belum diisi di file .env."
                )
                return
            try:
                google_id_token = await self.native_google_sign_in.sign_in(
                    db.GOOGLE_CLIENT_ID
                )
                if not google_id_token:
                    raise RuntimeError("Google tidak mengembalikan ID token.")
                self._show_loading("Menyelesaikan login Google...")
                self._bg(
                    db.sign_in_with_google_id_token,
                    google_id_token,
                    on_done=self._handle_google_oauth_result,
                    on_error=self._handle_google_oauth_error,
                )
            except Exception as exc:
                self._handle_google_oauth_error(exc)
            return

        if not self._google_provider:
            if self._auth_obj:
                self._auth_obj.set_error(
                    "Login Google belum dikonfigurasi. Isi GOOGLE_CLIENT_ID dan "
                    "GOOGLE_CLIENT_SECRET di file .env."
                )
                self._auth_obj.set_loading(False)
            page.update()
            return
        try:
            await page.login(self._google_provider)
        except Exception as exc:
            self._handle_google_oauth_error(exc)

    async def _on_firebase_google_login(self, event):
        if event.error:
            self._handle_google_oauth_error(event.error_description or event.error)
            return
        try:
            google_token = await self.page.auth.get_token()
            self._show_loading("Menyelesaikan login Google...")
            self._bg(
                db.sign_in_with_google,
                google_token.access_token,
                on_done=self._handle_google_oauth_result,
                on_error=self._handle_google_oauth_error,
            )
        except Exception as exc:
            self._handle_google_oauth_error(exc)

    def _handle_google_oauth_result(self, result):
        if result.get("error") or not result.get("user") or not result.get("session"):
            self._handle_google_oauth_error(result.get("error") or "Login Google gagal.")
            return
        self.user = {"id": result["user"].id, "email": result["user"].email}
        self._save_session(result["session"])
        self._load_vaults_and_show()

    def _handle_google_oauth_error(self, exc):
        detail = str(exc).strip()
        error_type = type(exc).__name__
        log_detail = detail or repr(exc)
        print(f"[auth] Google OAuth error ({error_type}): {log_detail}")
        if not detail:
            detail = f"{error_type} tanpa detail. Periksa log aplikasi."
        if self._auth_obj:
            self.phone.content = ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    self._status_bar(),
                    ft.Container(expand=True, content=self._auth_obj.widget),
                ],
            )
            self._auth_obj.set_error(f"Login Google gagal: {detail}")
            self._auth_obj.set_loading(False)
            self.page.update()

    # ── Auth callbacks (dipanggil oleh AuthScreen) ────────────────────────────

    def _on_login_submit(self, email: str, password: str, page: ft.Page):
        self._bg(
            self._do_login_threaded,
            email,
            password,
            on_done=lambda result: self._handle_login_result(result, page),
            on_error=lambda exc: self._handle_login_error(exc, page),
        )

    def _on_register_submit(self, name: str, email: str, password: str, page: ft.Page):
        self._bg(
            self._do_register_threaded,
            name,
            email,
            password,
            on_done=lambda result: self._handle_register_result(result, page),
            on_error=lambda exc: self._handle_register_error(exc, page),
        )

    def _on_guest(self):
        self.is_guest = True
        self.vaults   = seed_vaults()
        self._show_app()
        self.render()

    def _do_login_threaded(self, email: str, password: str):
        return db.sign_in(email, password)

    @staticmethod
    def _user_data(user) -> dict:
        return {
            "id": user.id,
            "email": user.email or "",
            "name": getattr(user, "display_name", "") or "",
        }

    def _handle_login_result(self, result, page: ft.Page):
        try:
            if result["error"]:
                if self._auth_obj:
                    message = (
                        "Login Firebase belum dikonfigurasi di APK ini."
                        if "FIREBASE_API_KEY" in result["error"]
                        else "Email atau kata sandi salah. Coba lagi."
                    )
                    self._auth_obj.set_error(message)
                    self._auth_obj.set_loading(False)
                page.update()
                return
            if not result.get("user") or not result.get("session"):
                if self._auth_obj:
                    self._auth_obj.set_error("Login gagal. Coba lagi.")
                    self._auth_obj.set_loading(False)
                page.update()
                return
            self.user = self._user_data(result["user"])
            self._save_session(result["session"])
            self._show_loading("Memuat vault kamu...")
            self._load_vaults_and_show()
        except Exception as exc:
            print(f"[auth] login error: {exc}")
            if self._auth_obj:
                self._auth_obj.set_error("Gagal terhubung. Coba lagi.")
                self._auth_obj.set_loading(False)
            page.update()

    def _handle_login_error(self, exc, page: ft.Page):
        print(f"[auth] login error: {exc}")
        if self._auth_obj:
            self._auth_obj.set_error("Gagal terhubung. Coba lagi.")
            self._auth_obj.set_loading(False)
        page.update()

    def _do_register_threaded(self, name: str, email: str, password: str):
        return db.sign_up(email, password, display_name=name)

    def _handle_register_result(self, result, page: ft.Page):
        try:
            if result["error"]:
                if self._auth_obj:
                    self._auth_obj.set_error(result["error"])
                    self._auth_obj.set_loading(False)
                page.update()
                return
            if result["user"] and result["session"]:
                self.user = self._user_data(result["user"])
                self._save_session(result["session"])
                self._show_loading("Akun dibuat! Menyiapkan vault...")
                self._load_vaults_and_show()
            else:
                if self._auth_obj:
                    self._auth_obj.set_error(
                        "Akun dibuat! Cek email untuk konfirmasi, lalu login."
                    )
                    self._auth_obj.set_loading(False)
                page.update()
        except Exception as exc:
            print(f"[auth] register error: {exc}")
            if self._auth_obj:
                self._auth_obj.set_error("Gagal membuat akun. Coba lagi.")
                self._auth_obj.set_loading(False)
            page.update()

    def _handle_register_error(self, exc, page: ft.Page):
        print(f"[auth] register error: {exc}")
        if self._auth_obj:
            self._auth_obj.set_error("Gagal membuat akun. Coba lagi.")
            self._auth_obj.set_loading(False)
        page.update()

    # ── Session helpers ───────────────────────────────────────────────────────

    def _save_session(self, session) -> None:
        self._set_stored("myvault.access_token",  session.access_token)
        self._set_stored("myvault.refresh_token", session.refresh_token)
        if self.user:
            self._set_stored("myvault.user_id", self.user["id"])
            self._set_stored("myvault.email", self.user.get("email", ""))

    def _clear_saved_session(self) -> None:
        self._remove_stored("myvault.access_token")
        self._remove_stored("myvault.refresh_token")
        self._remove_stored("myvault.user_id")
        self._remove_stored("myvault.email")

    def _get_stored(self, key: str):
        try:
            return self.page.client_storage.get(key)
        except Exception:
            return None

    def _set_stored(self, key: str, value: str) -> None:
        try:
            self.page.client_storage.set(key, value)
        except Exception:
            pass

    def _remove_stored(self, key: str) -> None:
        try:
            self.page.client_storage.remove(key)
        except Exception:
            pass

    # ── Phone content switchers ───────────────────────────────────────────────

    def _show_loading(self, msg: str = "Memuat...") -> None:
        loading_view = ft.Container(
            expand=True, bgcolor=T.bg, alignment=align("CENTER"),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.ProgressRing(color=T.accent, width=42, height=42, stroke_width=4),
                    ft.Text(msg, size=13, color=T.muted),
                ],
            ),
        )
        self.phone.content = ft.Column(
            spacing=0, expand=True,
            controls=[
                self._status_bar(),
                ft.Container(expand=True, content=loading_view),
            ],
        )
        self.page.update()

    def _show_auth(self) -> None:
        self._auth_obj = auth_mod.AuthScreen(
            on_login=self._on_login_submit,
            on_register=self._on_register_submit,
            on_guest=self._on_guest,
            on_google=self._on_google_login,
        )
        self.phone.content = ft.Column(
            spacing=0, expand=True,
            controls=[
                self._status_bar(),
                ft.Container(expand=True, content=self._auth_obj.widget),
            ],
        )
        self.page.update()
        if not db.is_configured():
            self._auth_obj.set_error(
                "Login akun belum dikonfigurasi di APK ini. Kamu tetap bisa "
                "memilih lanjut sebagai tamu."
            )
            self.page.update()

    def _show_app(self) -> None:
        self._auth_obj = None
        self.phone.content = self.app_column
        self.page.update()
        if not self._reminders_initialized:
            self._reminders_initialized = True
            self.page.run_task(self._restore_reminders)

    async def _restore_reminders(self) -> None:
        if self.notif_auto:
            await self._schedule_daily_reminder(
                71001, "Waktunya menabung", "Sedikit demi sedikit, targetmu makin dekat.", 20, 0
            )
        if self.notif_custom:
            await self._schedule_daily_reminder(
                71002,
                "Pengingat MyVault",
                "Luangkan waktu untuk menambah tabunganmu hari ini.",
                self.custom_reminder_hour,
                self.custom_reminder_minute,
            )

    async def _schedule_daily_reminder(
        self, notification_id: int, title: str, body: str, hour: int, minute: int
    ) -> None:
        try:
            await self.reminder_service.schedule_daily(
                notification_id, title, body, hour, minute
            )
        except Exception as exc:
            print(f"[notifications] schedule failed: {exc}")

    # ══════════════════════════════════════════════════════════════════════════
    # Rendering
    # ══════════════════════════════════════════════════════════════════════════

    def render(self):
        # Konten utama
        if self.detail_id is not None:
            vault = self._find_vault(self.detail_id)
            if vault is None:
                self.detail_id = None
                self.content_area.content = self._render_tab()
            else:
                self.content_area.content = ft.Container(
                    key=f"detail-{vault['id']}",
                    padding=Padding.symmetric(vertical=4, horizontal=16),
                    content=screens.vault_detail_screen(
                        vault, self.currency,
                        on_back=self.close_detail,
                        on_toggle_priority=self.toggle_priority,
                        on_open_tx=self.open_tx,
                        on_share=self.share_progress,
                        on_open_link=self._open_link,
                        on_delete=self.delete_vault_handler,
                    ),
                )
        else:
            self.content_area.content = self._render_tab()

        # FAB hanya di dashboard/vaults, bukan saat detail terbuka
        show_fab = self.detail_id is None and self.tab in ("dashboard", "vaults")
        self.fab.visible = show_fab

        # Nav bar disembunyikan saat detail terbuka
        self.nav_bar.visible = self.detail_id is None
        self.nav_bar.content = ft.Row(
            controls=[self._nav_button(i) for i in NAV_ITEMS], expand=True
        )

        # Toast
        self.toast_holder.content = self._render_toast()

        self.body_stack.controls = [
            self.content_area, self.toast_holder, self.fab, self.modal_holder,
        ]
        self.page.update()

    def _render_tab(self):
        if self.tab == "dashboard":
            return ft.Container(
                key="tab-dashboard",
                padding=Padding.symmetric(vertical=4, horizontal=16),
                content=screens.dashboard_screen(self.vaults, self.currency, self.open_vault),
            )
        if self.tab == "vaults":
            return ft.Container(
                key="tab-vaults",
                padding=Padding.symmetric(vertical=4, horizontal=16),
                content=screens.vaults_screen(self.vaults, self.currency, self.open_vault),
            )
        if self.tab == "stats":
            return ft.Container(
                key="tab-stats",
                padding=Padding.symmetric(vertical=4, horizontal=16),
                content=screens.stats_screen(self.vaults, self.currency),
            )
        if self.tab == "settings":
            return ft.Container(
                key="tab-settings",
                padding=Padding.symmetric(vertical=4, horizontal=16),
                content=screens.settings_screen(
                    self.currency,       self.set_currency,
                    self.notif_auto,     self.set_notif_auto,
                    self.notif_custom,   self.set_notif_custom,
                    self.logout,
                    user_email=self.user["email"] if self.user else "Tamu",
                    is_guest=self.is_guest,
                    user_name=self.user.get("name") if self.user else None,
                ),
            )
        return ft.Container(key="tab-empty")

    def _render_toast(self):
        if not self.toast_message:
            return None
        return ft.Container(
            padding=Padding.symmetric(vertical=12, horizontal=14),
            bgcolor=T.surface2, border=Border.all(1, T.surface_border),
            border_radius=BorderRadius.all(16),
            content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(
                    width=30, height=30, border_radius=BorderRadius.all(10),
                    bgcolor="#C9A66B2E", alignment=align("CENTER"),
                    content=ft.Icon(icon("NOTIFICATIONS_ROUNDED"), size=15, color=T.brass),
                ),
                ft.Text(self.toast_message, size=13, color=T.text, expand=True),
                ft.Container(
                    on_click=lambda e: self.dismiss_toast(),
                    content=ft.Icon(icon("CLOSE_ROUNDED"), size=14, color=T.muted),
                ),
            ]),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _find_vault(self, vault_id):
        for v in self.vaults:
            if v["id"] == vault_id:
                return v
        return None

    def _open_link(self, url: str) -> None:
        if not url:
            return
        try:
            self.page.launch_url(url)
        except Exception:
            pass

    def _is_db_mode(self) -> bool:
        """True jika user sudah login dan bukan mode tamu."""
        return bool(self.user and not self.is_guest and not self._offline_mode)

    def _new_vault_id(self):
        """UUID string saat DB mode, integer saat guest mode."""
        return str(uuid.uuid4()) if self._is_db_mode() else new_id()

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════════

    def go_tab(self, key: str) -> None:
        self.tab       = key
        self.detail_id = None
        self.render()

    def open_vault(self, vault_id) -> None:
        self.detail_id = vault_id
        self.render()

    def close_detail(self) -> None:
        self.detail_id = None
        self.render()

    def toggle_priority(self, vault_id) -> None:
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        v = self._find_vault(vault_id)
        if v:
            v["priority"] = not v["priority"]
        self.render()
        # ── Sync ──
        if v and self._is_db_mode():
            self._bg(db.update_vault_priority, str(vault_id), v["priority"])
            self.page.run_task(self._save_vault_cache, self.user["id"], self.vaults)

    def share_progress(self) -> None:
        self.show_toast("Link progres siap dibagikan ke WhatsApp / Instagram 📤")

    def delete_vault_handler(self, vault_id) -> None:
        """Tampilkan konfirmasi hapus menggunakan modal_holder (konsisten dengan tx_sheet)."""
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        vault = self._find_vault(vault_id)
        if not vault:
            return

        def confirm(e):
            self._close_modal()
            self._execute_delete(vault_id)

        def cancel(e):
            self._close_modal()

        # Custom confirm sheet (sama polanya dengan tx_sheet/new_vault_sheet)
        confirm_sheet = ft.Container(
            bgcolor=T.surface,
            border_radius=BorderRadius.only(top_left=28, top_right=28),
            padding=Padding.all(24),
            content=ft.Column(
                tight=True, spacing=0,
                controls=[
                    # Handle bar
                    ft.Container(
                        margin=Margin.only(bottom=20),
                        alignment=align("CENTER"),
                        content=ft.Container(
                            width=40, height=4,
                            bgcolor=T.surface_border,
                            border_radius=BorderRadius.all(999),
                        ),
                    ),
                    # Ikon peringatan
                    ft.Container(
                        alignment=align("CENTER"), margin=Margin.only(bottom=12),
                        content=ft.Container(
                            width=52, height=52,
                            border_radius=BorderRadius.all(16),
                            bgcolor="#F5637A1A",
                            alignment=align("CENTER"),
                            content=ft.Icon(icon("DELETE_ROUNDED"), size=24, color=T.danger),
                        ),
                    ),
                    # Judul
                    ft.Container(
                        alignment=align("CENTER"), margin=Margin.only(bottom=6),
                        content=ft.Text(
                            "Hapus Vault?",
                            size=17, weight=font_weight("BOLD"),
                            color=T.text, text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                    # Deskripsi
                    ft.Container(
                        alignment=align("CENTER"), margin=Margin.only(bottom=28),
                        content=ft.Text(
                            f'Vault "{vault["name"]}" dan semua riwayat\n'
                            f'transaksinya akan dihapus permanen.',
                            size=13, color=T.muted,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                    # Tombol aksi
                    ft.Row(spacing=10, controls=[
                        ft.Container(
                            expand=True,
                            padding=Padding.symmetric(vertical=13),
                            bgcolor=T.surface2,
                            border=Border.all(1, T.surface_border),
                            border_radius=BorderRadius.all(14),
                            alignment=align("CENTER"),
                            on_click=cancel,
                            content=ft.Text(
                                "Batal", size=13.5,
                                weight=font_weight("W_600") or font_weight("BOLD"),
                                color=T.muted,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=Padding.symmetric(vertical=13),
                            bgcolor="#F5637A22",
                            border=Border.all(1, "#F5637A66"),
                            border_radius=BorderRadius.all(14),
                            alignment=align("CENTER"),
                            on_click=confirm,
                            content=ft.Text(
                                "Hapus", size=13.5,
                                weight=font_weight("W_600") or font_weight("BOLD"),
                                color=T.danger,
                            ),
                        ),
                    ]),
                    ft.Container(height=8),
                ],
            ),
        )

        self.modal_holder.content = confirm_sheet
        self.modal_holder.visible = True
        self.page.update()

    def _close_modal(self) -> None:
        self.modal_holder.content = None
        self.modal_holder.visible = False
        self.page.update()

    def _execute_delete(self, vault_id) -> None:
        """Hapus vault dari list lokal, navigasi ke vaults tab, lalu sync ke DB."""
        if self._offline_mode:
            return
        self.vaults    = [v for v in self.vaults if v["id"] != vault_id]
        self.detail_id = None
        self.tab       = "vaults"
        self.render()
        if self._is_db_mode():
            self._bg(db.delete_vault, str(vault_id))
            self.page.run_task(self._save_vault_cache, self.user["id"], self.vaults)

    # ══════════════════════════════════════════════════════════════════════════
    # Transactions
    # ══════════════════════════════════════════════════════════════════════════

    def open_tx(self, mode: str) -> None:
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        vault = self._find_vault(self.detail_id)
        if not vault:
            return
        self.tx_mode = mode
        sheet = modals.tx_sheet(
            vault, mode, self.currency,
            on_close=self.close_tx, on_confirm=self.confirm_tx,
            width=self.phone.width,
        )
        self.modal_holder.content = sheet
        self.modal_holder.visible = True
        self.page.update()

    def close_tx(self) -> None:
        self.tx_mode = None
        self.modal_holder.content = None
        self.modal_holder.visible = False
        self.page.update()

    def confirm_tx(self, amount: float) -> None:
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        vault = self._find_vault(self.detail_id)
        if not vault or not self.tx_mode:
            return

        prev_pct = min(100, (vault["current"] / vault["target"]) * 100) if vault["target"] else 0

        new_current = (
            vault["current"] + amount if self.tx_mode == "tambah"
            else max(0, vault["current"] - amount)
        )
        new_pct = min(100, (new_current / vault["target"]) * 100) if vault["target"] else 0

        tx_record = {
            "id":     self._new_vault_id(),
            "type":   self.tx_mode,
            "amount": amount,
            "date":   today_str(),
        }
        vault["current"] = new_current
        vault["history"].append(tx_record)

        mode_used = self.tx_mode
        self.tx_mode = None
        self.close_tx()

        # Milestone notifications
        if mode_used == "tambah":
            thresholds = [25, 50, 75, 100]
            crossed = [t for t in thresholds if prev_pct < t <= new_pct]
            if crossed:
                t = max(crossed)
                msgs = {
                    25:  f'Seperempat jalan menuju "{vault["name"]}"! Terus lanjutkan 💪',
                    50:  f'Setengah jalan menuju "{vault["name"]}"! 🎯',
                    75:  f'Hampir sampai untuk "{vault["name"]}"! Tinggal sedikit lagi 🔥',
                    100: f'Target "{vault["name"]}" tercapai! Saatnya wujudkan rencanamu 🎉',
                }
                self.show_toast(msgs[t], confetti=(t == 100))
                self.page.run_task(
                    self.reminder_service.show,
                    72000 + t,
                    "Progres tabungan MyVault",
                    msgs[t],
                )

        self.render()

        # ── Sync ──
        if self._is_db_mode():
            vid = str(vault["id"])
            uid = self.user["id"]
            self._bg(db.add_transaction, vid, uid, tx_record)
            self._bg(db.update_vault_current, vid, new_current)
            self.page.run_task(self._save_vault_cache, uid, self.vaults)

    # ══════════════════════════════════════════════════════════════════════════
    # New vault
    # ══════════════════════════════════════════════════════════════════════════

    def open_new_vault(self) -> None:
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        self.show_new_vault = True
        sheet = modals.new_vault_sheet(
            on_close=self.close_new_vault,
            on_create=self.create_vault,
            on_pick_date=self.open_date_picker,
            width=self.phone.width,
        )
        self.modal_holder.content = sheet
        self.modal_holder.visible = True
        self.page.update()

    def close_new_vault(self) -> None:
        self.show_new_vault = False
        self.modal_holder.content = None
        self.modal_holder.visible = False
        self.page.update()

    def create_vault(self, data: dict) -> None:
        if self._offline_mode:
            self.show_toast("Mode offline: perubahan belum dapat disimpan.")
            return
        vault = {
            "id":      self._new_vault_id(),
            "current": 0,
            "history": [],
            **data,
        }
        self.vaults.append(vault)
        self.show_new_vault = False
        self.tab = "vaults"
        self.close_new_vault()
        self.render()

        # ── Sync ──
        if self._is_db_mode():
            self._bg(db.upsert_vault, vault, self.user["id"])
            self.page.run_task(self._save_vault_cache, self.user["id"], self.vaults)

    # ══════════════════════════════════════════════════════════════════════════
    # Date picker
    # ══════════════════════════════════════════════════════════════════════════

    def open_date_picker(self, on_picked) -> None:
        self._date_picker_target = on_picked
        self.page.show_dialog(self.date_picker)

    def _on_date_picked(self, e) -> None:
        if self._date_picker_target and self.date_picker.value:
            picked = self.date_picker.value
            try:
                d = picked.date()
            except AttributeError:
                d = picked
            self._date_picker_target(d.isoformat())
        self._date_picker_target = None

    # ══════════════════════════════════════════════════════════════════════════
    # Settings
    # ══════════════════════════════════════════════════════════════════════════

    def set_currency(self, value: str) -> None:
        self.currency = value
        self.render()

    def set_notif_auto(self, value: bool) -> None:
        self.notif_auto = value
        self._set_stored("myvault.notif_auto", str(value).lower())
        self.render()
        self.page.run_task(self._apply_auto_reminder, value)

    async def _apply_auto_reminder(self, enabled: bool) -> None:
        try:
            if enabled and not await self.reminder_service.request_permission():
                self.notif_auto = False
                self._set_stored("myvault.notif_auto", "false")
                self.show_toast("Izin notifikasi belum diberikan.")
                return
            if enabled:
                await self._schedule_daily_reminder(
                    71001,
                    "Waktunya menabung",
                    "Sedikit demi sedikit, targetmu makin dekat.",
                    20,
                    0,
                )
            else:
                await self.reminder_service.cancel(71001)
        except Exception as exc:
            self.notif_auto = False if enabled else self.notif_auto
            self._set_stored("myvault.notif_auto", str(self.notif_auto).lower())
            self.show_toast(f"Pengingat gagal diatur: {exc}")

    def set_notif_custom(self, value: bool) -> None:
        self.notif_custom = value
        self._set_stored("myvault.notif_custom", str(value).lower())
        self.render()
        if value:
            self.page.run_task(self._enable_custom_reminder)
        else:
            self.page.run_task(self.reminder_service.cancel, 71002)

    async def _enable_custom_reminder(self) -> None:
        try:
            if not await self.reminder_service.request_permission():
                self.notif_custom = False
                self._set_stored("myvault.notif_custom", "false")
                self.show_toast("Izin notifikasi belum diberikan.")
                return
            await self._schedule_daily_reminder(
                71002,
                "Pengingat MyVault",
                "Luangkan waktu untuk menambah tabunganmu hari ini.",
                self.custom_reminder_hour,
                self.custom_reminder_minute,
            )
            self.page.show_dialog(self.time_picker)
        except Exception as exc:
            self.notif_custom = False
            self._set_stored("myvault.notif_custom", "false")
            self.show_toast(f"Pengingat gagal diatur: {exc}")

    def _on_custom_time_picked(self, _event) -> None:
        picked = self.time_picker.value
        if picked is None:
            return
        self.custom_reminder_hour = picked.hour
        self.custom_reminder_minute = picked.minute
        self._set_stored("myvault.custom_reminder_hour", str(picked.hour))
        self._set_stored("myvault.custom_reminder_minute", str(picked.minute))
        self.page.run_task(
            self._schedule_daily_reminder,
            71002,
            "Pengingat MyVault",
            "Luangkan waktu untuk menambah tabunganmu hari ini.",
            picked.hour,
            picked.minute,
        )
        self.show_toast(f"Pengingat harian diatur pukul {picked.hour:02d}:{picked.minute:02d}.")

    def logout(self) -> None:
        if self._is_db_mode():
            self._bg(self._do_logout_threaded, on_done=self._handle_logout_done)
        else:
            if self._offline_mode:
                db.sign_out()
                self._clear_saved_session()
            self._reset_state()
            self._show_auth()

    def _do_logout_threaded(self) -> None:
        try:
            db.sign_out()
        except Exception:
            pass
        return True

    def _handle_logout_done(self, _result):
        self._clear_saved_session()
        self._reset_state()
        self._show_auth()

    def _reset_state(self) -> None:
        self.user      = None
        self.is_guest  = False
        self._offline_mode = False
        self.vaults    = []
        self.tab       = "dashboard"
        self.detail_id = None
        self.tx_mode   = None
        self.toast_message = None

    # ══════════════════════════════════════════════════════════════════════════
    # Toast & Confetti
    # ══════════════════════════════════════════════════════════════════════════

    def show_toast(self, message: str, confetti: bool = False) -> None:
        self.toast_message = message
        self._toast_task_token += 1
        token = self._toast_task_token
        self.render()
        self.page.run_task(self._auto_dismiss_toast, token)
        if confetti:
            self.page.run_task(self._confetti_burst)

    def dismiss_toast(self) -> None:
        self.toast_message = None
        self.render()

    async def _auto_dismiss_toast(self, token: int) -> None:
        import asyncio
        await asyncio.sleep(4.2)
        if token == self._toast_task_token:
            self.toast_message = None
            self.render()

    async def _confetti_burst(self) -> None:
        import asyncio
        colors = [T.brass, T.accent, T.success, T.accent_soft, T.warning]
        pieces = []
        for i in range(40):
            c = ft.Container(
                width=8, height=12,
                bgcolor=colors[i % len(colors)],
                left=random.uniform(0, PHONE_WIDTH - 8), top=-20,
                border_radius=BorderRadius.all(2),
                rotate=ft.Rotate(angle=random.uniform(0, 6.28)),
                animate_position=ft.Animation(
                    1800 + int(random.uniform(0, 900)), ft.AnimationCurve.EASE_IN
                ),
                opacity=0.9,
                animate_opacity=ft.Animation(1800, ft.AnimationCurve.EASE_IN),
            )
            pieces.append(c)

        confetti_layer = ft.Stack(
            controls=pieces, width=PHONE_WIDTH, height=PHONE_HEIGHT,
        )
        self.body_stack.controls = self.body_stack.controls + [confetti_layer]
        self.page.update()

        await asyncio.sleep(0.05)
        for p in pieces:
            p.top     = PHONE_HEIGHT
            p.opacity = 0
        self.page.update()

        await asyncio.sleep(2.4)
        try:
            self.body_stack.controls.remove(confetti_layer)
            self.page.update()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# Entrypoint
# ══════════════════════════════════════════════════════════════════════════════

def main(page: ft.Page):
    MyVaultApp(page)


if __name__ == "__main__":
    ft.run(main)
