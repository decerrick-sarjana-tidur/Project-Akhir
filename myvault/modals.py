"""modals.py — Tambah/Tarik saldo sheet & Buat vault baru sheet.

These are plain `ft.Container` panels rendered inside `main.py`'s
`modal_holder` overlay (bottom-aligned, scrim behind) — NOT `ft.BottomSheet`
dialogs. `main.py` toggles `modal_holder.visible`/`.content` directly and
calls `page.update()`; there's no `show_dialog()`/`pop_dialog()` involved
for these two sheets. (The one control in this app that *does* use the
real dialog API is the deadline `ft.DatePicker` in `main.py`, opened via
`page.show_dialog(self.date_picker)`.)
"""
import flet as ft
try:
    from .compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight
    from .theme import T, CATEGORIES, fmt
    from .components import icon_btn, primary_btn, chip, field_label, styled_textfield
except ImportError:
    from compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight
    from theme import T, CATEGORIES, fmt
    from components import icon_btn, primary_btn, chip, field_label, styled_textfield

def sheet_wrapper(title, body, on_close, width=390):
    """Build a sheet panel that is hosted inside the phone Stack."""
    return ft.Container(
        width=width,
        bgcolor=T.surface,
        border_radius=BorderRadius.only(top_left=26, top_right=26),
        padding=Padding.only(left=18, right=18, top=18, bottom=22),
        content=ft.Column(
            tight=True, spacing=0,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[ft.Container(
                        width=36, height=4, border_radius=BorderRadius.all(999),
                        bgcolor=T.muted, margin=Margin.only(bottom=18),
                    )],
                ),
                ft.Row(controls=[
                    ft.Text(title, size=15, weight=font_weight("W_600") or font_weight("BOLD"),
                            color=T.text, expand=True),
                    icon_btn("CLOSE_ROUNDED", on_click=lambda e: on_close()),
                ]),
                ft.Container(height=14),
                body,
            ],
        ),
    )


def tx_sheet(vault, mode, currency, on_close, on_confirm, width=390):
    is_tambah = mode == "tambah"
    chips_values = [50_000, 100_000, 250_000, 500_000, 1_000_000]

    amount_field = styled_textfield(hint="0", value="", keyboard_type=ft.KeyboardType.NUMBER)
    confirm_btn_ref = {"btn": None}

    def parse_amount():
        try:
            return int(float(amount_field.value or 0))
        except ValueError:
            return 0

    def refresh_confirm(page):
        amt = parse_amount()
        confirm_btn_ref["btn"].opacity = 1 if amt > 0 else 0.5
        page.update()

    def on_amount_change(e):
        refresh_confirm(e.page)

    amount_field.on_change = on_amount_change

    def add_chip(delta):
        def handler(e):
            current = parse_amount()
            amount_field.value = str(current + delta)
            refresh_confirm(e.page)
        return handler

    def confirm(e):
        amt = parse_amount()
        if amt > 0:
            on_confirm(amt)

    confirm_button = primary_btn("Simpan setoran" if is_tambah else "Tarik dana", on_click=confirm, expand=True)
    confirm_btn_ref["btn"] = confirm_button

    body = ft.Column(
        spacing=0, tight=True,
        controls=[
            ft.Text(vault["name"], size=12, color=T.muted),
            ft.Container(height=6),
            amount_field,
            ft.Container(height=10),
            ft.Row(spacing=8, wrap=True, controls=[
                chip(f"+{fmt(c, currency)}", on_click=add_chip(c)) for c in chips_values
            ]),
            ft.Container(height=18),
            confirm_button,
        ],
    )
    return sheet_wrapper("Tambah saldo" if is_tambah else "Tarik saldo", body, on_close, width)


class NewVaultState:
    def __init__(self):
        self.name = ""
        self.category = "Gadget"
        self.target = ""
        self.deadline = ""
        self.item_link = ""
        self.priority = False


def new_vault_sheet(on_close, on_create, on_pick_date=None, width=390):
    state = NewVaultState()

    name_field = styled_textfield(hint="cth: Laptop baru")
    target_field = styled_textfield(hint="cth: 5000000", keyboard_type=ft.KeyboardType.NUMBER)
    deadline_field = styled_textfield(hint="YYYY-MM-DD", read_only=on_pick_date is not None)
    link_field = styled_textfield(hint="https://...")

    def open_deadline_picker(e):
        if not on_pick_date:
            return

        def receive(date_str):
            deadline_field.value = date_str
            e.page.update()

        on_pick_date(receive)

    if on_pick_date:
        deadline_field.on_click = open_deadline_picker
        deadline_field.suffix_icon = icon("CALENDAR_MONTH_ROUNDED")

    category_chips_col = {"row": None}
    priority_box = {"container": None, "check": None}

    def select_category(cat_key):
        def handler(e):
            state.category = cat_key
            rebuild_category_row()
            e.page.update()
        return handler

    def build_category_pill(key):
        cat = CATEGORIES[key]
        selected = state.category == key
        return ft.Container(
            padding=Padding.symmetric(vertical=8, horizontal=12), border_radius=BorderRadius.all(999),
            bgcolor=(cat["color"] + "22") if selected else T.surface2,
            border=Border.all(1, cat["color"] if selected else T.surface_border),
            on_click=select_category(key),
            content=ft.Row(spacing=6, tight=True, controls=[
                ft.Icon(icon(cat["icon"]), size=13, color=cat["color"]),
                ft.Text(key, size=12, color=T.text),
            ]),
        )

    category_row = ft.Row(spacing=8, wrap=True, controls=[build_category_pill(k) for k in CATEGORIES])
    category_chips_col["row"] = category_row

    def rebuild_category_row():
        category_row.controls = [build_category_pill(k) for k in CATEGORIES]

    def toggle_priority(e):
        state.priority = not state.priority
        rebuild_priority_box()
        e.page.update()

    def build_priority_box():
        return ft.Container(
            on_click=toggle_priority,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Container(
                        width=18, height=18, border_radius=BorderRadius.all(6),
                        border=Border.all(1.5, T.brass if state.priority else T.surface_border),
                        bgcolor=T.brass if state.priority else None, alignment=align("CENTER"),
                        content=ft.Icon(icon("CHECK_ROUNDED"), size=12, color=T.bg) if state.priority else None,
                    ),
                    ft.Text("Tandai sebagai prioritas", size=12.5, color=T.text),
                ],
            ),
        )

    priority_row = build_priority_box()

    def rebuild_priority_box():
        priority_row.content = build_priority_box().content

    def submit(e):
        try:
            target_val = float(target_field.value or 0)
        except ValueError:
            target_val = 0
        if not (name_field.value or "").strip() or target_val <= 0 or not (deadline_field.value or "").strip():
            return
        on_create({
            "name": name_field.value.strip(),
            "category": state.category,
            "target": target_val,
            "deadline": deadline_field.value.strip(),
            "itemLink": (link_field.value or "").strip(),
            "priority": state.priority,
        })

    submit_btn = primary_btn("Buat vault", on_click=submit, expand=True)

    body = ft.Column(
        spacing=0, tight=True,
        controls=[
            field_label("Nama vault"),
            name_field,
            ft.Container(height=8),
            field_label("Kategori"),
            category_row,
            ft.Container(height=14),
            field_label("Target nominal"),
            target_field,
            ft.Container(height=8),
            field_label("Deadline (YYYY-MM-DD)"),
            deadline_field,
            ft.Container(height=8),
            field_label("Link barang (opsional)"),
            link_field,
            ft.Container(height=10),
            priority_row,
            ft.Container(height=18),
            submit_btn,
        ],
    )
    return sheet_wrapper("Buat vault baru", body, on_close, width)
