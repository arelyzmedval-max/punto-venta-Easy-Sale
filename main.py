import traceback
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
from views.login import LoginView
from database import Database

def main(page: ft.Page):
    page.title = "Easy Sale - Punto de Venta"
    page.padding = 0
    page.bgcolor = ft.colors.WHITE

    db = Database()

    def mostrar_dashboard(usuario_actual):
        try:
            page.clean()

            view_factories = [
                lambda: InicioView(page, db, usuario_actual),
                lambda: VentasView(page, db, usuario_actual),
                lambda: InventarioView(page, db),
                lambda: HistorialView(page, db),
                lambda: ReportesView(page, db),
                lambda: UsuariosView(page, db),
                lambda: CajaView(page, db, usuario_actual),
                lambda: ClientesView(page, db, usuario_actual),
                lambda: ConfiguracionView(page, db),
            ]
            views_cache = {}

            def obtener_vista(index):
                if index not in views_cache:
                    try:
                        views_cache[index] = view_factories[index]()
                    except Exception as err:
                        print(f"ERROR AL CARGAR VISTA {index}:")
                        traceback.print_exc()
                        views_cache[index] = ft.Container(
                            padding=30,
                            content=ft.Text(f"Error al cargar esta sección:\n{err}", color=ft.colors.RED_700, size=16)
                        )
                return views_cache[index]

            body_container = ft.Container(content=obtener_vista(0), expand=True)

            def cambiar_vista(e):
                selected_index = e.control.selected_index
                body_container.content = obtener_vista(selected_index)
                page.update()

            def cerrar_sesion(e):
                mostrar_login()

            header = ft.Container(
                bgcolor=ft.colors.BLUE_900,
                padding=10,
                content=ft.Row([
                    ft.Text("Easy Sale - Punto de Venta", color=ft.colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(f"Usuario: {usuario_actual['nombre']} ({usuario_actual['rol']})", color=ft.colors.WHITE),
                        ft.IconButton(
                            icon=ft.icons.LOGOUT,
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
                    ft.NavigationRailDestination(icon=ft.icons.HOME, label="Inicio"),
                    ft.NavigationRailDestination(icon=ft.icons.POINT_OF_SALE, label="Ventas"),
                    ft.NavigationRailDestination(icon=ft.icons.INVENTORY, label="Inventario"),
                    ft.NavigationRailDestination(icon=ft.icons.HISTORY, label="Historial"),
                    ft.NavigationRailDestination(icon=ft.icons.BAR_CHART, label="Reportes"),
                    ft.NavigationRailDestination(icon=ft.icons.PEOPLE, label="Usuarios"),
                    ft.NavigationRailDestination(icon=ft.icons.POINT_OF_SALE_OUTLINED, label="Caja"),
                    ft.NavigationRailDestination(icon=ft.icons.PERSON_PIN, label="Clientes"),
                    ft.NavigationRailDestination(icon=ft.icons.SETTINGS, label="Configuración"),
                ],
            )

            main_layout = ft.Column([
                header,
                ft.Row([
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    body_container
                ], expand=True)
            ], expand=True)

            page.add(main_layout)
            page.update()

        except Exception as e:
            print("ERROR CRÍTICO EN MOSTRAR_DASHBOARD:")
            traceback.print_exc()

    def mostrar_login():
        page.clean()
        login_view = LoginView(page, db, al_ingresar=mostrar_dashboard)
        page.add(login_view)
        page.update()

    mostrar_login()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=main, port=port, host="0.0.0.0")
