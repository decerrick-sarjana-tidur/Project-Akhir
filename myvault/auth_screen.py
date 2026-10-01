"""auth_screen.py — Layar Login / Daftar akun untuk MyVault.

Digunakan sebelum layar utama muncul.  Mengembalikan sebuah objek
``AuthScreen`` yang mengekspos:

  .widget        → ft.Control yang siap di-mount ke phone content
  .set_error(msg)  → tampilkan pesan error di bawah form
  .set_loading(bool) → tunjukkan/sembunyikan state loading pada tombol submit
"""
import flet as ft

try:
    from .compat import Padding, BorderRadius, Border, align, icon, font_weight
    from .theme import T, DISPLAY_FONT
    from .components import styled_textfield, field_label
except ImportError:
    from compat import Padding, BorderRadius, Border, align, icon, font_weight
    from theme import T, DISPLAY_FONT
    from components import styled_textfield, field_label


class AuthScreen:
    """
    Layar login/daftar yang muncul di dalam phone shell.

    Parameters
    ----------
    on_login    : callable(email, password, page)
    on_register : callable(name, email, password, page)
    on_google   : callable(page)
    on_guest    : callable()  — dipanggil saat user pilih "tamu"
    """

    def __init__(self, on_login, on_register, on_guest, on_google=None):
        self._cb_login    = on_login
        self._cb_register = on_register
        self._cb_guest    = on_guest
        self._cb_google   = on_google
        self._tab = "login"   # "login" | "register"
        self._build()

    # ── Public API ─────────────────────────────────────────────────────

    def set_error(self, msg: str) -> None:
        """Tampilkan / sembunyikan pesan error di bawah form."""
        self._err_text.value   = msg
        self._err_text.visible = bool(msg)

    def set_loading(self, loading: bool) -> None:
        """Nonaktifkan tombol submit saat request sedang berjalan."""
        self._submit_btn.opacity = 0.55 if loading else 1.0
        self._submit_btn.disabled = loading
        self._google_btn.opacity = 0.55 if loading else 1.0
        self._google_btn.disabled = loading

    # ── Internal ───────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Input fields
        self._email_field = styled_textfield(
            hint="email@contoh.com",
            keyboard_type=ft.KeyboardType.EMAIL,
        )
        self._name_field = styled_textfield(hint="Nama lengkap")
        self._pwd_field = styled_textfield(
            hint="Kata sandi (min. 6 karakter)",
            password=True,
        )
        self._name_group = ft.Column(
            spacing=6,
            tight=True,
            visible=False,
            controls=[
                field_label("Nama lengkap"),
                self._name_field,
                ft.Container(height=6),
            ],
        )

        # ── Error label
        self._err_text = ft.Text(
            "", size=12, color=T.danger, visible=False,
        )

        # ── Tab buttons (Masuk / Daftar)
        self._btn_masuk  = self._make_tab_btn("Masuk",  "login")
        self._btn_daftar = self._make_tab_btn("Daftar", "register")
        self._refresh_tabs()

        # ── Submit button
        self._submit_btn = ft.Container(
            padding=Padding.symmetric(vertical=13),
            bgcolor=T.accent,
            border_radius=BorderRadius.all(14),
            alignment=align("CENTER"),
            on_click=self._on_submit,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=7,
                controls=[
                    ft.Icon(icon("LOGIN_ROUNDED"), size=16, color="#FFFFFF"),
                    ft.Text(
                        "Masuk", size=13.5,
                        weight=font_weight("W_600") or font_weight("BOLD"),
                        color="#FFFFFF",
                    ),
                ],
            ),
        )

        self._google_btn = ft.Container(
            padding=Padding.symmetric(vertical=12),
            bgcolor=T.surface2,
            border=Border.all(1, T.surface_border),
            border_radius=BorderRadius.all(14),
            alignment=align("CENTER"),
            on_click=self._on_google_click,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text("G", size=16, weight=font_weight("BOLD"), color=T.text),
                    ft.Text(
                        "Masuk dengan Google", size=13,
                        weight=font_weight("W_600") or font_weight("BOLD"),
                        color=T.text,
                    ),
                ],
            ),
        )

        # ── Guest link
        guest_btn = ft.Container(
            padding=Padding.symmetric(vertical=8),
            alignment=align("CENTER"),
            on_click=lambda e: self._cb_guest(),
            content=ft.Text(
                spans=[
                    ft.TextSpan(
                        "Lanjutkan sebagai tamu",
                        style=ft.TextStyle(
                            size=12.5,
                            color=T.muted,
                        ),
                    )
                ],
            ),
        )

        # ── Card container
        card = ft.Container(
            width=346,
            padding=Padding.all(24),
            bgcolor=T.surface,
            border=Border.all(1, T.surface_border),
            border_radius=BorderRadius.all(24),
            content=ft.Column(
                spacing=0, tight=True,
                controls=[
                    # Logo + judul
                    ft.Row(
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon("SAVINGS_ROUNDED"), size=30, color=T.brass),
                            ft.Text(
                                "MyVault", size=26,
                                weight=font_weight("BOLD"),
                                color=T.text, font_family=DISPLAY_FONT,
                            ),
                        ],
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Celengan digital pribadimu",
                        size=12, color=T.muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=22),

                    # Tab switcher
                    ft.Row(spacing=8, controls=[self._btn_masuk, self._btn_daftar]),
                    ft.Container(height=18),

                    # Form
                    self._name_group,
                    field_label("Email"),
                    self._email_field,
                    ft.Container(height=6),
                    field_label("Kata sandi"),
                    self._pwd_field,
                    ft.Container(height=8),
                    self._err_text,
                    ft.Container(height=12),

                    # Submit
                    self._submit_btn,
                    ft.Container(height=8),
                    self._google_btn,
                    ft.Container(height=10),
                    ft.Divider(color=T.surface_border, height=1),
                    ft.Container(height=2),
                    guest_btn,
                ],
            ),
        )

        # ── Root widget (full phone body fill)
        self.widget = ft.Container(
            expand=True,
            bgcolor=T.bg,
            alignment=align("CENTER"),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[card],
            ),
        )

    # ── Tab helpers ─────────────────────────────────────────────────────

    def _make_tab_btn(self, label: str, key: str) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=Padding.symmetric(vertical=10),
            border_radius=BorderRadius.all(12),
            alignment=align("CENTER"),
            on_click=lambda e, k=key: self._switch_tab(k, e.page),
            content=ft.Text(
                label, size=13,
                weight=font_weight("W_600") or font_weight("BOLD"),
                color=T.muted,
            ),
        )

    def _refresh_tabs(self) -> None:
        """Perbarui tampilan tab aktif/tidak-aktif dan label submit button."""
        is_login = self._tab == "login"
        for btn, active in [
            (self._btn_masuk,  is_login),
            (self._btn_daftar, not is_login),
        ]:
            btn.bgcolor = T.accent if active else T.surface2
            btn.border  = Border.all(1, T.accent if active else T.surface_border)
            btn.content.color = "#FFFFFF" if active else T.muted

        # Sinkronkan label + ikon submit button
        if hasattr(self, "_submit_btn"):
            row = self._submit_btn.content
            row.controls[0] = ft.Icon(
                icon("LOGIN_ROUNDED" if is_login else "PERSON_ADD_ROUNDED"),
                size=16, color="#FFFFFF",
            )
            row.controls[1].value = "Masuk" if is_login else "Daftar"

    def _switch_tab(self, key: str, page: ft.Page) -> None:
        self._tab = key
        self.set_error("")
        self._name_field.value = ""
        self._email_field.value = ""
        self._pwd_field.value   = ""
        self._name_group.visible = key == "register"
        self._refresh_tabs()
        page.update()

    # ── Submit ──────────────────────────────────────────────────────────

    def _on_submit(self, e) -> None:
        email = (self._email_field.value or "").strip()
        pwd   = (self._pwd_field.value   or "").strip()

        self.set_error("")

        if not email or not pwd:
            self.set_error("Email dan kata sandi tidak boleh kosong.")
            e.page.update()
            return
        if len(pwd) < 6:
            self.set_error("Kata sandi minimal 6 karakter.")
            e.page.update()
            return
        name = (self._name_field.value or "").strip()
        if self._tab == "register" and not name:
            self.set_error("Nama lengkap wajib diisi.")
            e.page.update()
            return

        self.set_loading(True)
        e.page.update()

        if self._tab == "login":
            self._cb_login(email, pwd, e.page)
        else:
            self._cb_register(name, email, pwd, e.page)

    async def _on_google_click(self, e) -> None:
        if self._cb_google is None:
            self.set_error("Login Google belum dikonfigurasi.")
            e.page.update()
            return
        self.set_error("")
        self.set_loading(True)
        e.page.update()
        await self._cb_google(e.page)
