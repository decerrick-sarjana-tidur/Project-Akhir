"""screens.py — the four tabs + vault detail, mirroring the JSX screens."""
import flet as ft
try:
    from .compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight, top_colored_border
    from .theme import T, DISPLAY_FONT, CATEGORIES, fmt, days_between, today_str, MONTHS_ID
    from .components import (
        progress_bar, progress_ring, donut, icon_btn, primary_btn, outline_btn,
        section_label, toggle_row, category_icon_box,
    )
except ImportError:
    from compat import Margin, Padding, BorderRadius, Border, align, icon, font_weight, top_colored_border
    from theme import T, DISPLAY_FONT, CATEGORIES, fmt, days_between, today_str, MONTHS_ID
    from components import (
        progress_bar, progress_ring, donut, icon_btn, primary_btn, outline_btn,
        section_label, toggle_row, category_icon_box,
    )


def _card(content, **kwargs):
    defaults = dict(
        bgcolor=T.surface, border=Border.all(1, T.surface_border),
        border_radius=BorderRadius.all(18), padding=Padding.all(14),
    )
    defaults.update(kwargs)
    return ft.Container(content=content, **defaults)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def dashboard_screen(vaults, currency, on_open_vault):
    total_saved = sum(v["current"] for v in vaults)
    total_target = sum(v["target"] for v in vaults)
    overall_pct = round((total_saved / total_target) * 100) if total_target else 0
    completed = sum(1 for v in vaults if v["current"] >= v["target"])
    priority_vaults = [v for v in vaults if v["priority"]]

    recent_tx = []
    for v in vaults:
        for h in v["history"]:
            recent_tx.append({**h, "vaultName": v["name"], "color": CATEGORIES[v["category"]]["color"]})
    recent_tx.sort(key=lambda t: t["date"], reverse=True)
    recent_tx = recent_tx[:4]

    hero = ft.Container(
        margin=Margin.only(left=16, right=16, top=4, bottom=18),
        padding=Padding.symmetric(vertical=24, horizontal=20),
        border_radius=BorderRadius.all(24),
        # Approximates the JSX's layered
        # radial-gradient(...at 15% 0%...) + linear-gradient(160deg...)
        # as one RadialGradient (Container only takes a single gradient):
        # bright indigo glow near the top-left, fading to the dark surface.
        gradient=ft.RadialGradient(
            center=ft.Alignment(-0.7, -1.0), radius=1.3,
            colors=[T.accent + "59", T.surface, "#100C24"],
            stops=[0.0, 0.55, 1.0],
        ),
        border=Border.all(1, T.surface_border),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Row(spacing=6, controls=[
                    ft.Icon(icon("LOCK_ROUNDED"), size=13, color=T.brass),
                    ft.Text("Total tersimpan", size=12, color=T.muted),
                ]),
                ft.Container(height=10),
                ft.Text(fmt(total_saved, currency), size=34, weight=font_weight("BOLD"),
                         color=T.text, font_family=DISPLAY_FONT),
                ft.Container(height=10),
                ft.Row(spacing=8, controls=[
                    ft.Container(expand=True, content=progress_bar(overall_pct, color=T.brass)),
                    ft.Text(f"{overall_pct}%", size=12, color=T.brass_soft, weight=font_weight("W_600") or font_weight("BOLD")),
                ]),
                ft.Container(height=16),
                ft.Row(spacing=18, controls=[
                    ft.Column(spacing=0, controls=[
                        ft.Text(str(len(vaults)), size=17, weight=font_weight("BOLD"), color=T.text, font_family=DISPLAY_FONT),
                        ft.Text("Vault aktif", size=11, color=T.muted),
                    ]),
                    ft.Column(spacing=0, controls=[
                        ft.Text(str(completed), size=17, weight=font_weight("BOLD"), color=T.success, font_family=DISPLAY_FONT),
                        ft.Text("Selesai", size=11, color=T.muted),
                    ]),
                ]),
            ],
        ),
    )

    sections = [hero]

    if priority_vaults:
        cards = []
        for v in priority_vaults:
            pct = round((v["current"] / v["target"]) * 100) if v["target"] else 0
            cat = CATEGORIES[v["category"]]
            cards.append(
                ft.Container(
                    width=148, padding=Padding.all(14),
                    bgcolor=T.surface,
                    border=top_colored_border(cat["color"], T.surface_border),
                    border_radius=BorderRadius.all(18),
                    on_click=lambda e, vid=v["id"]: on_open_vault(vid),
                    content=ft.Column(spacing=0, controls=[
                        ft.Icon(icon(cat["icon"]), size=16, color=cat["color"]),
                        ft.Container(height=8),
                        ft.Text(v["name"], size=13, color=T.text, weight=font_weight("W_600") or font_weight("BOLD"), max_lines=2),
                        ft.Container(height=6),
                        ft.Text(fmt(v["current"], currency), size=11, color=T.muted),
                        ft.Container(height=8),
                        progress_bar(pct, color=cat["color"]),
                    ]),
                )
            )
        sections.append(
            ft.Column(spacing=10, controls=[
                ft.Row(
                    controls=[
                        ft.Text("Vault prioritas", size=14, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
                        ft.Icon(icon("STAR_ROUNDED"), size=13, color=T.brass),
                    ],
                    alignment=ft.MainAxisAlignment.START, spacing=6,
                ),
                ft.Row(controls=cards, scroll=ft.ScrollMode.AUTO, spacing=10),
            ])
        )

    tx_rows = []
    for t in recent_tx:
        is_add = t["type"] == "tambah"
        tx_rows.append(
            ft.Container(
                padding=Padding.symmetric(vertical=10, horizontal=12),
                bgcolor=T.surface, border=Border.all(1, T.surface_border), border_radius=BorderRadius.all(14),
                content=ft.Row(spacing=10, controls=[
                    ft.Container(
                        width=30, height=30, border_radius=BorderRadius.all(10),
                        bgcolor="#34D39926" if is_add else "#F5637A26", alignment=align("CENTER"),
                        content=ft.Icon(icon("ADD_ROUNDED" if is_add else "REMOVE_ROUNDED"),
                                        size=14, color=T.success if is_add else T.danger),
                    ),
                    ft.Column(expand=True, spacing=0, controls=[
                        ft.Text(t["vaultName"], size=13, color=T.text, max_lines=1),
                        ft.Text(t["date"], size=11, color=T.muted),
                    ]),
                    ft.Text(
                        ("+" if is_add else "-") + fmt(t["amount"], currency), size=13,
                        weight=font_weight("W_600") or font_weight("BOLD"),
                        color=T.success if is_add else T.danger,
                    ),
                ]),
            )
        )
    if not tx_rows:
        tx_rows = [ft.Text("Belum ada transaksi.", size=12.5, color=T.muted)]

    sections.append(
        ft.Column(spacing=10, controls=[
            ft.Text("Aktivitas terbaru", size=14, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
            ft.Column(spacing=8, controls=tx_rows),
        ])
    )

    return ft.Column(
        spacing=18,
        controls=[hero] + sections[1:],
        scroll=ft.ScrollMode.AUTO,
    )


# --------------------------------------------------------------------------
# Vaults list
# --------------------------------------------------------------------------
def vaults_screen(vaults, currency, on_open_vault):
    sorted_vaults = sorted(vaults, key=lambda v: 0 if v["priority"] else 1)
    rows = []
    for v in sorted_vaults:
        pct = round((v["current"] / v["target"]) * 100) if v["target"] else 0
        cat = CATEGORIES[v["category"]]
        done = v["current"] >= v["target"]
        ring_color = T.success if done else cat["color"]
        rows.append(
            ft.Container(
                padding=Padding.all(14), bgcolor=T.surface,
                border=top_colored_border(cat["color"], T.surface_border),
                border_radius=BorderRadius.all(18),
                on_click=lambda e, vid=v["id"]: on_open_vault(vid),
                content=ft.Row(spacing=12, controls=[
                    progress_ring(pct, size=48, stroke=5, color=ring_color,
                                  center_content=ft.Icon(icon(cat["icon"]), size=16, color=ring_color)),
                    ft.Column(expand=True, spacing=2, controls=[
                        ft.Row(spacing=6, controls=[
                            ft.Text(v["name"], size=14, weight=font_weight("W_600") or font_weight("BOLD"),
                                    color=T.text, max_lines=1),
                            ft.Icon(icon("STAR_ROUNDED"), size=11, color=T.brass) if v["priority"] else ft.Container(),
                        ]),
                        ft.Text(v["category"], size=11, color=T.muted),
                        ft.Text(
                            spans=[
                                ft.TextSpan(fmt(v["current"], currency),
                                            style=ft.TextStyle(color=T.text, weight=font_weight("W_600") or font_weight("BOLD"), size=12)),
                                ft.TextSpan(f" dari {fmt(v['target'], currency)}", style=ft.TextStyle(color=T.muted, size=12)),
                            ],
                        ),
                    ]),
                    ft.Icon(icon("CHEVRON_RIGHT_ROUNDED"), size=16, color=T.muted_faint),
                ]),
            )
        )
    if not rows:
        rows = [ft.Container(padding=Padding.all(20), alignment=align("CENTER"),
                              content=ft.Text("Belum ada vault. Buat satu dengan tombol +", color=T.muted))]
    return ft.Column(spacing=10, controls=rows, scroll=ft.ScrollMode.AUTO)


# --------------------------------------------------------------------------
# Vault detail
# --------------------------------------------------------------------------
def vault_detail_screen(vault, currency, on_back, on_toggle_priority, on_open_tx, on_share, on_open_link=None, on_delete=None):
    cat = CATEGORIES[vault["category"]]
    pct = round((vault["current"] / vault["target"]) * 100) if vault["target"] else 0
    remaining = max(0, vault["target"] - vault["current"])
    days_left = days_between(today_str(), vault["deadline"])
    done = vault["current"] >= vault["target"]

    if done:
        tone, note_text = "success", "Target sudah tercapai. Saatnya wujudkan rencanamu! 🎉"
    elif days_left <= 0:
        tone = "warning"
        note_text = f"Deadline sudah lewat. Sisa {fmt(remaining, currency)} lagi untuk mencapai target."
    else:
        daily = -(-remaining // days_left)  # ceil(remaining / days_left)
        weekly = -(-(remaining * 7) // days_left)  # ceil(remaining / (days_left / 7))
        tone = "info"
        note_text = f"Nabung sekitar {fmt(daily, currency)}/hari (± {fmt(weekly, currency)}/minggu) agar target tercapai tepat waktu."

    tone_bg = {"success": "#34D3991A", "warning": "#F5637A1A", "info": "#6366F11F"}[tone]
    tone_border = {"success": "#34D3994D", "warning": "#F5637A4D", "info": "#6366F14D"}[tone]
    tone_color = {"success": T.success, "warning": T.danger, "info": T.accent_soft}[tone]

    header = ft.Row(spacing=10, controls=[
        icon_btn("ARROW_BACK_ROUNDED", on_click=lambda e: on_back()),
        ft.Text("Detail vault", size=15, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text, expand=True),
        icon_btn("STAR_ROUNDED", on_click=lambda e: on_toggle_priority(vault["id"]),
                  color=T.brass),
        icon_btn("SHARE_ROUNDED", on_click=lambda e: on_share()),
        icon_btn("DELETE_ROUNDED", on_click=lambda e: on_delete(vault["id"]) if on_delete else None,
                  color=T.danger),
    ])

    hero = ft.Container(
        margin=Margin.only(bottom=16), padding=Padding.symmetric(vertical=22, horizontal=16),
        border_radius=BorderRadius.all(22), bgcolor=T.surface,
        border=top_colored_border(cat["color"], T.surface_border),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0,
            controls=[
                category_icon_box(vault["category"]),
                ft.Container(height=10),
                ft.Text(vault["name"], size=17, weight=font_weight("BOLD"), color=T.text, text_align=ft.TextAlign.CENTER),
                ft.Text(vault["category"], size=12, color=T.muted),
                ft.Container(width=176, height=176, content=donut(pct, color=T.success if done else cat["color"])),
                ft.Text(fmt(vault["current"], currency), size=22, weight=font_weight("BOLD"), color=T.text, font_family=DISPLAY_FONT),
                ft.Text(f"dari target {fmt(vault['target'], currency)}", size=12, color=T.muted),
                ft.Container(height=16),
                ft.Row(spacing=20, alignment=ft.MainAxisAlignment.CENTER, controls=[
                    ft.Row(spacing=5, controls=[
                        ft.Icon(icon("FLAG_ROUNDED"), size=13, color=T.muted),
                        ft.Text(f"{fmt(remaining, currency)} lagi", size=12, color=T.muted),
                    ]),
                    ft.Row(spacing=5, controls=[
                        ft.Icon(icon("CALENDAR_MONTH_ROUNDED"), size=13, color=T.muted),
                        ft.Text(vault["deadline"], size=12, color=T.muted),
                    ]),
                ]),
            ],
        ),
    )

    smart_note = ft.Container(
        margin=Margin.only(bottom=16), padding=Padding.symmetric(vertical=12, horizontal=14),
        border_radius=BorderRadius.all(16), bgcolor=tone_bg, border=Border.all(1, tone_border),
        content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
            ft.Icon(icon("NOTIFICATIONS_ROUNDED"), size=15, color=tone_color),
            ft.Text(note_text, size=12.5, color=T.text, expand=True),
        ]),
    )

    blocks = [header, hero, smart_note]

    if vault.get("itemLink"):
        blocks.append(
            ft.Container(
                margin=Margin.only(bottom=16), padding=Padding.symmetric(vertical=12, horizontal=14),
                border_radius=BorderRadius.all(16), bgcolor=T.surface, border=Border.all(1, T.surface_border),
                on_click=(lambda e: on_open_link(vault["itemLink"])) if on_open_link else None,
                content=ft.Row(spacing=10, controls=[
                    ft.Container(width=30, height=30, border_radius=BorderRadius.all(10), bgcolor="#C9A66B26",
                                 alignment=align("CENTER"), content=ft.Icon(icon("LINK_ROUNDED"), size=14, color=T.brass)),
                    ft.Column(expand=True, spacing=0, controls=[
                        ft.Text("Barang tujuan", size=12, color=T.muted),
                        ft.Text(vault["itemLink"], size=12.5, color=T.brass_soft, max_lines=1),
                    ]),
                    ft.Icon(icon("CHEVRON_RIGHT_ROUNDED"), size=15, color=T.muted_faint),
                ]),
            )
        )

    blocks.append(
        ft.Row(spacing=10, controls=[
            primary_btn("Tambah saldo", on_click=lambda e: on_open_tx("tambah"), icon_name="ADD_ROUNDED"),
            outline_btn("Tarik saldo", on_click=lambda e: on_open_tx("tarik"), icon_name="REMOVE_ROUNDED"),
        ])
    )

    sorted_hist = sorted(vault["history"], key=lambda h: h["date"], reverse=True)
    hist_rows = []
    for h in sorted_hist:
        is_add = h["type"] == "tambah"
        hist_rows.append(
            ft.Container(
                padding=Padding.symmetric(vertical=10, horizontal=12),
                bgcolor=T.surface, border=Border.all(1, T.surface_border), border_radius=BorderRadius.all(14),
                content=ft.Row(spacing=10, controls=[
                    ft.Container(width=28, height=28, border_radius=BorderRadius.all(9),
                                 bgcolor="#34D39926" if is_add else "#F5637A26", alignment=align("CENTER"),
                                 content=ft.Icon(icon("ADD_ROUNDED" if is_add else "REMOVE_ROUNDED"),
                                                 size=13, color=T.success if is_add else T.danger)),
                    ft.Text(h["date"], size=12.5, color=T.muted, expand=True),
                    ft.Text(("+" if is_add else "-") + fmt(h["amount"], currency), size=13,
                            weight=font_weight("W_600") or font_weight("BOLD"),
                            color=T.success if is_add else T.danger),
                ]),
            )
        )
    if not hist_rows:
        hist_rows = [ft.Container(padding=Padding.symmetric(vertical=20, horizontal=0), alignment=align("CENTER"),
                                   content=ft.Text("Belum ada transaksi.", size=12.5, color=T.muted))]

    blocks.append(ft.Container(margin=Margin.only(top=20), content=ft.Column(spacing=10, controls=[
        ft.Text("Riwayat transaksi", size=14, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
        ft.Column(spacing=8, controls=hist_rows),
    ])))

    return ft.Column(spacing=0, controls=blocks, scroll=ft.ScrollMode.AUTO)


# --------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------
def stats_screen(vaults, currency):
    monthly = {}
    for v in vaults:
        for h in v["history"]:
            y, m, _ = h["date"].split("-")
            key = (int(y), int(m))
            entry = monthly.setdefault(key, {"label": MONTHS_ID[int(m) - 1], "value": 0})
            entry["value"] += h["amount"] if h["type"] == "tambah" else -h["amount"]
    monthly_sorted = [monthly[k] for k in sorted(monthly.keys())]
    max_abs = max([abs(m["value"]) for m in monthly_sorted], default=1) or 1

    BAR_H = 90   # total column height (mirrors JSX height:160 minus axes)
    bars = []
    for m in monthly_sorted:
        filled_h = max(6, int(BAR_H * abs(m["value"]) / max_abs))
        bar_color = T.accent if m["value"] >= 0 else T.danger
        val_label = f"{'+' if m['value'] >= 0 else '-'}{abs(round(m['value'] / 1000))}rb"
        bars.append(
            ft.Column(
                spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # value label above bar
                    ft.Text(val_label, size=9, color=bar_color,
                            weight=font_weight("W_600") or font_weight("BOLD")),
                    # bar aligned to bottom inside a fixed-height container
                    ft.Container(
                        height=BAR_H, alignment=align("BOTTOM_CENTER"),
                        content=ft.Container(
                            width=20, height=filled_h, bgcolor=bar_color,
                            border_radius=BorderRadius.only(top_left=6, top_right=6,
                                                            bottom_left=3, bottom_right=3),
                        ),
                    ),
                    # month label
                    ft.Text(m["label"], size=10, color=T.muted),
                ],
            )
        )
    if not bars:
        bars = [ft.Text("Belum ada data transaksi.", size=12.5, color=T.muted)]

    chart_card = _card(
        ft.Column(spacing=10, controls=[
            ft.Row(spacing=6, controls=[
                ft.Icon(icon("TRENDING_UP_ROUNDED"), size=14, color=T.accent_soft),
                ft.Text("Setoran bersih per bulan", size=13, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
            ]),
            # baseline separator
            ft.Divider(height=1, thickness=1, color=T.surface2),
            ft.Row(spacing=10, controls=bars, alignment=ft.MainAxisAlignment.START,
                   scroll=ft.ScrollMode.AUTO, vertical_alignment=ft.CrossAxisAlignment.END),
        ]),
        margin=Margin.only(bottom=14),
    )

    cat_totals = {}
    for v in vaults:
        cat_totals.setdefault(v["category"], 0)
        cat_totals[v["category"]] += v["current"]
    cat_totals = {k: val for k, val in cat_totals.items() if val > 0}
    total_saved = sum(v["current"] for v in vaults)

    legend_rows = []
    seg_controls = []
    for name, val in cat_totals.items():
        color = CATEGORIES[name]["color"]
        pct = round((val / total_saved) * 100) if total_saved else 0
        legend_rows.append(
            ft.Row(spacing=7, controls=[
                ft.Container(width=8, height=8, border_radius=BorderRadius.all(3), bgcolor=color),
                ft.Text(name, size=12, color=T.text, expand=True),
                ft.Text(f"{pct}%", size=12, color=T.muted),
            ])
        )
        seg_controls.append(ft.Container(bgcolor=color, expand=max(pct, 1)))
    if not seg_controls:
        seg_controls = [ft.Container(bgcolor=T.surface2, expand=1)]
        legend_rows = [ft.Text("Belum ada tabungan untuk ditampilkan.", size=12.5, color=T.muted)]

    breakdown_card = _card(
        ft.Column(spacing=10, controls=[
            ft.Row(spacing=6, controls=[
                ft.Icon(icon("BAR_CHART_ROUNDED"), size=14, color=T.brass),
                ft.Text("Tabungan per kategori", size=13, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
            ]),
            ft.Container(height=14, border_radius=BorderRadius.all(999), clip_behavior=ft.ClipBehavior.HARD_EDGE,
                         content=ft.Row(spacing=0, controls=seg_controls, expand=True)),
            ft.Column(spacing=8, controls=legend_rows),
        ]),
        margin=Margin.only(bottom=14),
    )

    completed_vaults = [v for v in vaults if v["current"] >= v["target"]]
    if completed_vaults:
        chips = [
            ft.Container(
                padding=Padding.symmetric(vertical=6, horizontal=12), border_radius=BorderRadius.all(999),
                bgcolor="#34D39920", border=Border.all(1, "#34D3994D"),
                content=ft.Row(spacing=6, controls=[
                    ft.Icon(icon("CHECK_ROUNDED"), size=12, color=T.success),
                    ft.Text(v["name"], size=12, color=T.text),
                ]),
            ) for v in completed_vaults
        ]
        completed_content = ft.Row(spacing=8, wrap=True, controls=chips)
    else:
        completed_content = ft.Text("Belum ada vault yang selesai. Terus nabung!", size=12.5, color=T.muted)

    completed_card = _card(
        ft.Column(spacing=10, controls=[
            ft.Row(spacing=6, controls=[
                ft.Icon(icon("AUTO_AWESOME_ROUNDED"), size=14, color=T.success),
                ft.Text("Vault selesai", size=13, weight=font_weight("W_600") or font_weight("BOLD"), color=T.text),
            ]),
            completed_content,
        ]),
    )

    return ft.Column(spacing=0, controls=[chart_card, breakdown_card, completed_card], scroll=ft.ScrollMode.AUTO)


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
def settings_screen(
    currency, on_set_currency,
    notif_auto, on_set_notif_auto,
    notif_custom, on_set_notif_custom,
    on_logout,
    user_email: str = "pengguna@myvault.app",
    is_guest: bool = False,
    user_name: str | None = None,
):
    # ── Profile card ─────────────────────────────────────────────────────────
    display_name = "Tamu" if is_guest else (user_name or user_email.split("@")[0])
    display_email = "Mode tamu — data tersimpan lokal" if is_guest else user_email

    avatar_gradient = ft.LinearGradient(
        begin=align("TOP_LEFT"), end=align("BOTTOM_RIGHT"),
        colors=[T.muted_faint, T.muted] if is_guest else [T.accent, T.accent_soft],
    )

    guest_badge = ft.Container(
        padding=Padding.symmetric(vertical=3, horizontal=8),
        border_radius=BorderRadius.all(999),
        bgcolor=T.surface2,
        border=Border.all(1, T.surface_border),
        content=ft.Text("Tamu", size=10, color=T.muted),
    ) if is_guest else ft.Container()

    profile = ft.Container(
        margin=Margin.only(bottom=16), padding=Padding.all(16),
        bgcolor=T.surface, border=Border.all(1, T.surface_border),
        border_radius=BorderRadius.all(18),
        content=ft.Row(spacing=12, controls=[
            ft.Container(
                width=46, height=46, border_radius=BorderRadius.all(14),
                gradient=avatar_gradient, alignment=align("CENTER"),
                content=ft.Icon(
                    icon("PERSON_ROUNDED" if not is_guest else "PERSON_OUTLINE_ROUNDED"),
                    size=20, color="#FFFFFF",
                ),
            ),
            ft.Column(expand=True, spacing=4, controls=[
                ft.Row(spacing=8, controls=[
                    ft.Text(
                        display_name, size=14,
                        weight=font_weight("W_600") or font_weight("BOLD"),
                        color=T.text,
                    ),
                    guest_badge,
                ]),
                ft.Text(display_email, size=12, color=T.muted),
            ]),
        ]),
    )

    # ── Currency selector ─────────────────────────────────────────────────────
    currency_row = ft.Row(spacing=8, controls=[
        ft.Container(
            expand=True, padding=Padding.symmetric(vertical=10, horizontal=0),
            border_radius=BorderRadius.all(12),
            bgcolor=T.accent if currency == c else T.surface,
            border=Border.all(1, T.accent if currency == c else T.surface_border),
            alignment=align("CENTER"),
            on_click=lambda e, cur=c: on_set_currency(cur),
            content=ft.Text(
                c, size=13,
                weight=font_weight("W_600") or font_weight("BOLD"),
                color="#FFFFFF" if currency == c else T.muted,
            ),
        ) for c in ["IDR", "USD"]
    ])

    # ── Logout / kembali ke login button ─────────────────────────────────────
    logout_label = "Kembali ke login" if is_guest else "Keluar"
    logout_btn = ft.Container(
        margin=Margin.only(top=20), padding=Padding.symmetric(vertical=12, horizontal=0),
        border_radius=BorderRadius.all(14), bgcolor="#F5637A1A",
        border=Border.all(1, "#F5637A4D"), alignment=align("CENTER"),
        on_click=lambda e: on_logout(),
        content=ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER, controls=[
            ft.Icon(icon("LOGOUT_ROUNDED"), size=15, color=T.danger),
            ft.Text(
                logout_label, size=13.5,
                weight=font_weight("W_600") or font_weight("BOLD"),
                color=T.danger,
            ),
        ]),
    )

    return ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, controls=[
        profile,
        section_label("Mata uang"),
        ft.Container(margin=Margin.only(bottom=16), content=currency_row),
        section_label("Notifikasi"),
        toggle_row("NOTIFICATIONS_ROUNDED", "Notifikasi otomatis",
                   "Hitung jadwal menabung & progres milestone", notif_auto,
                   on_set_notif_auto),
        toggle_row("CALENDAR_MONTH_ROUNDED", "Jadwal kustom",
                   "Atur pengingat menabung di waktu tertentu", notif_custom,
                   on_set_notif_custom),
        logout_btn,
    ])
