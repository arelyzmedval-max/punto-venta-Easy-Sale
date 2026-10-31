import flet as ft
from views.inicio import InicioView
from views.ventas import VentasView
from views.inventario import InventarioView
from views.historial import HistorialView
from views.reportes import ReportesView
from views.usuarios import UsuariosView
from views.caja import CajaView
from views.configuracion import ConfiguracionView
from views.clientes import ClientesView
from views.login import LoginView  # <-- Asegúrate de tener tu vista de login en views/
try:
    from database import Database
except ImportError:
    from .database import Database

def main(page: ft.Page):
    page.title = "Easy Sale - Punto de Venta"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0

    db = Database()

    # Función que se ejecuta cuando el login es exitoso
    def mostrar_dashboard(usuario_actual):
        page.clean()

        body_container = ft.Container(expand=True)

        def cambiar_vista(e):
            selected_index = e.control.selected_index
            body_container.content = views_list[selected_index]
            page.update()

        def cerrar_sesion(e):
            # Al cerrar sesión, regresamos a la pantalla de login
            mostrar_login()

        # Lista de vistas que requieren el usuario o la base de datos
        views_list = [
            InicioView(page, db, usuario_actual),
            VentasView(page, db, usuario_actual),
            InventarioView(page, db),
            HistorialView(page, db),
            ReportesView(page, db),
            UsuariosView(page, db),
            CajaView(page, db, usuario_actual),
            ClientesView(page, db, usuario_actual),
            ConfiguracionView(page, db)
        ]

        header = ft.Container(
            bgcolor=ft.colors.BLUE_900,
            padding=10,
            content=ft.Row([
                ft.Text("Easy Sale - Punto de Venta", color=ft.colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text(f"Usuario: {usuario_actual['nombre']} ({usuario_actual['rol']})", color=ft.colors.WHITE),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color=ft.colors.RED_400,
                        tooltip="Cerrar Sesión",
                        on_click=cerrar_sesion
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=180,
            on_change=cambiar_vista,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Inicio"),
                ft.NavigationRailDestination(icon=ft.Icons.POINT_OF_SALE, label="Ventas"),
                ft.NavigationRailDestination(icon=ft.Icons.INVENTORY, label="Inventario"),
                ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial"),
                ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART, label="Reportes"),
                ft.NavigationRailDestination(icon=ft.Icons.PEOPLE, label="Usuarios"),
                ft.NavigationRailDestination(icon=ft.Icons.POINT_OF_SALE_OUTLINED, label="Caja"),
                ft.NavigationRailDestination(icon=ft.Icons.PERSON_PIN, label="Clientes"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Configuración"),
            ],
        )

        body_container.content = views_list[0]

        page.add(
            ft.Column([
                header,
                ft.Row([
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    body_container
                ], expand=True)
            ], expand=True)
        )
        page.update()

    # Función para mostrar la pantalla de inicio de sesión
    def mostrar_login():
        page.clean()
        # Le pasamos la función mostrar_dashboard para que se ejecute al autenticarse bien
        login_view = LoginView(page, db, al_ingresar=mostrar_dashboard)
        page.add(login_view)
        page.update()

    # Arrancamos la app mostrando primero el Login
    mostrar_login()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=main, view=None, port=port, host="0.0.0.0")
