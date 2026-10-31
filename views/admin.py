import flet as ft


class AdminView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario

        self.crear_interfaz()
        # Carga de datos iniciales sin llamar a update() en la página
        self.cargar_datos_dashboard()

    def crear_interfaz(self):
        # Tarjetas resumen
        self.lbl_ventas_hoy = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.lbl_num_ventas = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
        self.lbl_productos_bajo_stock = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)

        card_ventas = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Ventas de Hoy", size=14, color=ft.Colors.GREY_700),
                    self.lbl_ventas_hoy
                ])
            ),
            expand=True
        )

        card_num_ventas = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Total Transacciones", size=14, color=ft.Colors.GREY_700),
                    self.lbl_num_ventas
                ])
            ),
            expand=True
        )

        card_stock = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Productos con Bajo Stock (<= 5)", size=14, color=ft.Colors.GREY_700),
                    self.lbl_productos_bajo_stock
                ])
            ),
            expand=True
        )

        # Tabla de alertas de stock
        self.tabla_alertas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Stock Actual")),
                ft.DataColumn(ft.Text("Precio")),
            ],
            rows=[]
        )

        self.content = ft.Column([
            ft.Text(f"Bienvenido(a), {self.usuario.get('nombre', 'Administrador')}", size=20,
                    weight=ft.FontWeight.BOLD),
            ft.Row([card_ventas, card_num_ventas, card_stock]),
            ft.Card(
                expand=True,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("Alertas de Reabastecimiento", size=16, weight=ft.FontWeight.BOLD),
                        ft.ListView([self.tabla_alertas], expand=True)
                    ])
                )
            )
        ], expand=True, spacing=15)

    def cargar_datos_dashboard(self):
        # 1. Total ventas de hoy
        q_ventas_hoy = """
            SELECT COALESCE(SUM(total_venta), 0) as total, COUNT(*) as cantidad 
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE
        """
        res_ventas = self.db.obtener_resultados(q_ventas_hoy)
        if res_ventas:
            self.lbl_ventas_hoy.value = f"${float(res_ventas[0]['total']):.2f}"
            self.lbl_num_ventas.value = str(res_ventas[0]['cantidad'])

        # 2. Productos bajo stock (<= 5)
        q_bajo_stock = "SELECT codigo, nombre, stock, precio FROM productos WHERE stock <= 5 ORDER BY stock ASC"
        res_stock = self.db.obtener_resultados(q_bajo_stock)

        self.tabla_alertas.rows.clear()
        if res_stock:
            self.lbl_productos_bajo_stock.value = str(len(res_stock))
            for p in res_stock:
                self.tabla_alertas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p['codigo']))),
                        ft.DataCell(ft.Text(p['nombre'])),
                        ft.DataCell(ft.Text(str(p['stock']), color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"${float(p['precio']):.2f}")),
                    ])
                )
        else:
            self.lbl_productos_bajo_stock.value = "0"

    def mostrar_dashboard(self):
        self.cargar_datos_dashboard()
        if self.page_ref:
            self.page_ref.update()