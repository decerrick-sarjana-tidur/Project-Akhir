import flet as ft

from flet_reminders import FletReminders


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=FletReminders(
                    tooltip="My new FletReminders Control tooltip",
                    value = "My new FletReminders Flet Control",
                ),),

    )


ft.run(main)
