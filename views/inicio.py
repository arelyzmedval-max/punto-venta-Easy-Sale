import flet as ft


class InicioView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario

        # Contenedores dinámicos para las métricas y alertas
        self.contenedor_metricas = ft.Row(spacing=20, wrap=True)
        self.lista_alertas = ft.ListView(spacing=10, expand=True)

        self.content = ft.Container(
            padding=30,
            content=ft.Column([
                ft.Text(f"¡Bienvenido de nuevo, {usuario.get('nombre', 'Admin')}!", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Aquí tienes el resumen y las alertas importantes de tu inventario.", color=ft.Colors.GREY_700,
                        size=14),
                ft.Divider(height=20),

                # Tarjetas de resumen superior
                self.contenedor_metricas,

                ft.Divider(height=10),
                ft.Text("⚠️ Alertas de Reabastecimiento (Stock Bajo)", size=18, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700),
                ft.Text("Productos con 2 unidades o menos que requieren pedido urgente:", size=13,
                        color=ft.Colors.GREY_700),

                # Tarjeta contenedora de la lista de alertas
                ft.Card(
                    expand=True,
                    content=ft.Container(
                        padding=15,
                        content=self.lista_alertas
                    )
                )
            ], spacing=15, expand=True)
        )

        self.cargar_datos_inicio()

    def did_mount(self):
        # Se actualiza automáticamente cada vez que regresas a la página de inicio
        self.cargar_datos_inicio()

    def cargar_datos_inicio(self):
        self.contenedor_metricas.controls.clear()
        self.lista_alertas.controls.clear()

        # 1. Obtener total de productos
        res_total = self.db.obtener_resultados("SELECT COUNT(*) as total FROM productos")
        total_productos = res_total[0]['total'] if res_total else 0

        # 2. Obtener productos con stock bajo (<= 2)
        productos_bajos = self.db.obtener_resultados("SELECT * FROM productos WHERE stock <= 2 ORDER BY stock ASC")
        cantidad_bajos = len(productos_bajos) if productos_bajos else 0

        # 3. Obtener total de deuda pendiente en fiados
        res_deuda = self.db.obtener_resultados(
            "SELECT COALESCE(SUM(total_fiado - abono), 0) as deuda_total FROM creditos WHERE estado = 'Pendiente'")
        deuda_total = float(res_deuda[0]['deuda_total']) if res_deuda else 0.0

        # Tarjetas de métricas superiores
        self.contenedor_metricas.controls.extend([
            self.crear_tarjeta_metrica("Total Productos", str(total_productos), ft.Icons.INVENTORY, ft.Colors.BLUE_700),
            self.crear_tarjeta_metrica("Productos por Agotar", str(cantidad_bajos), ft.Icons.WARNING_AMBER,
                                       ft.Colors.ORANGE_700),
            self.crear_tarjeta_metrica("Total Fiados Pendientes", f"${deuda_total:.2f}",
                                       ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.RED_700)
        ])

        # Llenar la lista de alertas de stock bajo
        if productos_bajos:
            for p in productos_bajos:
                stock_val = float(p['stock'])
                stock_str = f"{stock_val:.3f} kg" if p.get('tipo_venta') == 'por kilo' else str(
                    int(stock_val) if stock_val.is_integer() else stock_val)

                self.lista_alertas.controls.append(
                    ft.Container(
                        padding=12,
                        bgcolor=ft.Colors.RED_50,
                        border_radius=8,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_700),
                            ft.Column([
                                ft.Text(f"{p['nombre']} (Código: {p['codigo']})", weight=ft.FontWeight.BOLD, size=14,
                                        color=ft.Colors.RED_900),
                                ft.Text(
                                    f"Descripción: {p['descripcion'] or 'Sin descripción'} | Precio: ${float(p['precio']):.2f}",
                                    size=12, color=ft.Colors.GREY_700)
                            ], spacing=2, expand=True),
                            ft.Container(
                                padding=8,  # Padding numérico seguro para cualquier versión de Flet
                                bgcolor=ft.Colors.RED_700,
                                border_radius=5,
                                content=ft.Text(f"¡Quedan {stock_str}!", color=ft.Colors.WHITE,
                                                weight=ft.FontWeight.BOLD, size=12)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )
        else:
            self.lista_alertas.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN_700, size=40),
                        ft.Text("¡Excelente! No hay productos con stock crítico en este momento.",
                                color=ft.Colors.GREEN_800, weight=ft.FontWeight.BOLD)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )

        if self.page_ref:
            self.page_ref.update()

    def crear_tarjeta_metrica(self, titulo, valor, icono, color):
        return ft.Card(
            content=ft.Container(
                padding=20,
                width=240,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icono, color=color, size=24),
                        ft.Text(titulo, color=ft.Colors.GREY_700, size=13, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=color)
                ], spacing=5)
            )
        )