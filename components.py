"""components.py — small reusable pieces, mirrors the JSX <ProgressBar>, <ProgressRing>,
<Donut>, iconBtnStyle, primaryBtnStyle, outlineBtnStyle, chipStyle, ToggleRow, etc."""
import flet as ft
try:
    from .compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight
    from .theme import T, DISPLAY_FONT
except ImportError:
    from compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight
    from theme import T, DISPLAY_FONT


def progress_bar(percent, color=T.accent, height=6):
    """A track Container holding a Row where the fill portion uses
    `expand=percent` and the remainder uses `expand=(100-percent)`.
    Row `expand` weights are core, long-stable Flet behavior, so this is
    safer across versions than trying to set a literal pixel width."""
    percent = max(0, min(100, round(percent or 0)))
    remainder = 100 - percent
    fill = ft.Container(bgcolor=color, border_radius=BorderRadius.all(999), expand=percent if percent > 0 else 1)
    rest = ft.Container(expand=remainder if remainder > 0 else 1)
    row_controls = []
    if percent > 0:
        row_controls.append(fill)
    if remainder > 0:
        row_controls.append(ft.Container(expand=remainder))
    if not row_controls:
        row_controls = [ft.Container(expand=1)]
    return ft.Container(
        height=height,
        bgcolor=T.surface2,
        border_radius=BorderRadius.all(999),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Row(controls=row_controls, spacing=0, expand=True),
    )


def progress_ring(percent, size=56, stroke=6, color=T.accent, center_content=None):
    percent = max(0, min(100, percent or 0))
    ring = ft.ProgressRing(
        value=percent / 100,
        width=size,
        height=size,
        stroke_width=stroke,
        color=color,
        bgcolor=T.surface2,
    )
    if center_content is None:
        return ring
    return ft.Stack(
        controls=[
            ring,
            ft.Container(width=size, height=size, alignment=align("CENTER"), content=center_content),
        ],
        width=size,
        height=size,
    )


def donut(percent, color=T.accent, size=176):
    percent_i = int(max(0, min(100, round(percent or 0))))
    center = ft.Column(
        controls=[
            ft.Text(f"{percent_i}%", size=30, weight=font_weight("BOLD"), color=T.text, font_family=DISPLAY_FONT),
            ft.Text("tercapai", size=11, color=T.muted),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=2,
        tight=True,
    )
    return progress_ring(percent, size=size, stroke=16, color=color, center_content=center)


def icon_btn(name, on_click=None, color=T.text, fallback="HELP_OUTLINE_ROUNDED"):
    return ft.Container(
        width=34, height=34, border_radius=BorderRadius.all(11),
        bgcolor=T.surface, border=Border.all(1, T.surface_border),
        alignment=align("CENTER"), on_click=on_click,
        content=ft.Icon(icon(name, fallback), size=16, color=color),
    )


def primary_btn(text, on_click=None, expand=True, icon_name=None, disabled=False):
    row = []
    if icon_name:
        row.append(ft.Icon(icon(icon_name), size=15, color="#FFFFFF"))
    row.append(ft.Text(text, size=13.5, weight=font_weight("W_600") or font_weight("BOLD"), color="#FFFFFF"))
    return ft.Container(
        expand=expand, padding=Padding.symmetric(vertical=12, horizontal=0),
        bgcolor=T.muted_faint if disabled else T.accent,
        border_radius=BorderRadius.all(14),
        alignment=align("CENTER"),
        on_click=None if disabled else on_click,
        opacity=0.5 if disabled else 1,
        content=ft.Row(controls=row, alignment=ft.MainAxisAlignment.CENTER, spacing=6, tight=True),
    )


def outline_btn(text, on_click=None, expand=True, icon_name=None):
    row = []
    if icon_name:
        row.append(ft.Icon(icon(icon_name), size=15, color=T.text))
    row.append(ft.Text(text, size=13.5, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text))
    return ft.Container(
        expand=expand, padding=Padding.symmetric(vertical=12, horizontal=0),
        bgcolor=None, border=Border.all(1, T.surface_border), border_radius=BorderRadius.all(14),
        alignment=align("CENTER"), on_click=on_click,
        content=ft.Row(controls=row, alignment=ft.MainAxisAlignment.CENTER, spacing=6, tight=True),
    )


def chip(text, on_click=None):
    return ft.Container(
        padding=Padding.symmetric(vertical=6, horizontal=11),
        border_radius=BorderRadius.all(999),
        bgcolor=T.surface2, border=Border.all(1, T.surface_border),
        on_click=on_click,
        content=ft.Text(text, size=11.5, color=T.muted),
    )


def section_label(text):
    return ft.Container(
        padding=Padding.only(left=2, right=2, top=4, bottom=8),
        content=ft.Text(text, size=12.5, color=T.muted),
    )


def field_label(text):
    return ft.Container(
        padding=Padding.only(left=2, right=2, top=0, bottom=6),
        content=ft.Text(text, size=12, color=T.muted),
    )


def styled_textfield(hint="", value="", on_change=None, keyboard_type=None, password=False, read_only=False):
    return ft.TextField(
        value=value, hint_text=hint, on_change=on_change, password=password, read_only=read_only,
        keyboard_type=keyboard_type, color=T.text, hint_style=ft.TextStyle(color=T.muted_faint),
        bgcolor=T.surface2, border_color=T.surface_border, focused_border_color=T.accent,
        border_radius=BorderRadius.all(12), content_padding=Padding.symmetric(vertical=11, horizontal=13),
        text_size=13.5,
    )


def toggle_row(icon_name, label, desc, value, on_change):
    toggle = ft.Container(width=52, height=30, padding=Padding.all(4))

    def build_toggle_knob(enabled):
        return ft.Row(
            controls=[ft.Container(width=22, height=22, border_radius=BorderRadius.all(999), bgcolor="#FFFFFF")],
            alignment=ft.MainAxisAlignment.END if enabled else ft.MainAxisAlignment.START,
        )

    def handle_toggle(e):
        toggle.data = not bool(toggle.data)
        toggle.bgcolor = T.accent if toggle.data else T.surface2
        toggle.border = Border.all(1, T.accent if toggle.data else T.surface_border)
        toggle.content = build_toggle_knob(toggle.data)
        on_change(toggle.data)

    toggle.data = bool(value)
    toggle.bgcolor = T.accent if toggle.data else T.surface2
    toggle.border = Border.all(1, T.accent if toggle.data else T.surface_border)
    toggle.border_radius = BorderRadius.all(8)
    toggle.alignment = align("CENTER")
    toggle.content = build_toggle_knob(toggle.data)
    toggle.on_click = handle_toggle

    return ft.Container(
        padding=Padding.all(14), margin=Margin.only(bottom=10),
        border_radius=BorderRadius.all(16), bgcolor=T.surface, border=Border.all(1, T.surface_border),
        content=ft.Row(
            spacing=12,
            controls=[
                ft.Container(
                    width=34, height=34, border_radius=BorderRadius.all(11), bgcolor=T.surface2,
                    alignment=align("CENTER"),
                    content=ft.Icon(icon(icon_name), size=15, color=T.accent_soft),
                ),
                ft.Column(
                    expand=True, spacing=2,
                    controls=[
                        ft.Text(label, size=13, color=T.text, weight=font_weight("W_500")),
                        ft.Text(desc, size=11, color=T.muted),
                    ],
                ),
                toggle,
            ],
        ),
    )


def category_icon_box(category, size=38, icon_size=18):
    try:
        from .theme import CATEGORIES
    except ImportError:
        from theme import CATEGORIES
    cat = CATEGORIES[category]
    return ft.Container(
        width=size, height=size, border_radius=BorderRadius.all(12),
        bgcolor=cat["color"] + "22", alignment=align("CENTER"),
        content=ft.Icon(icon(cat["icon"]), size=icon_size, color=cat["color"]),
    )
