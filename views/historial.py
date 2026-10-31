import flet as ft


class HistorialView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db

        self.crear_interfaz()
        # Carga los datos en memoria SIN llamar a page.update() dentro del __init__
        self.cargar_datos_historial()

    def did_mount(self):
        # Se ejecuta automáticamente cada vez que abres la pestaña de Historial
        self.cargar_datos_historial()
        if self.page_ref:
            self.page_ref.update()

    def crear_interfaz(self):
        self.txt_buscar = ft.TextField(
            label="Buscar por folio o usuario",
            expand=True,
            on_change=self.filtrar_historial
        )

        self.tabla_historial = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Folio Venta")),
                ft.DataColumn(ft.Text("Fecha")),
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Método Pago")),
                ft.DataColumn(ft.Text("Impuesto")),
                ft.DataColumn(ft.Text("Total Venta")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        self.content = ft.Column([
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Historial de Ventas Registradas", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([self.txt_buscar])
                    ])
                )
            ),
            ft.Card(
                expand=True,
                content=ft.Container(
                    padding=10,
                    content=ft.ListView([self.tabla_historial], expand=True)
                )
            )
        ], expand=True, spacing=10)

    def cargar_datos_historial(self, termino=""):
        self.tabla_historial.rows.clear()

        if termino:
            query = """
                SELECT v.id_venta, v.fecha, u.nombre as usuario, m.metodo, v.impuesto, v.total_venta 
                FROM ventas v
                JOIN usuarios u ON v.id_usuario = u.id_usuario
                JOIN metodos_pago m ON v.metodo_pago_id = m.id_metodo
                WHERE v.id_venta LIKE %s OR u.nombre LIKE %s
                ORDER BY v.fecha DESC
            """
            res = self.db.obtener_resultados(query, (f"%{termino}%", f"%{termino}%"))
        else:
            query = """
                SELECT v.id_venta, v.fecha, u.nombre as usuario, m.metodo, v.impuesto, v.total_venta 
                FROM ventas v
                JOIN usuarios u ON v.id_usuario = u.id_usuario
                JOIN metodos_pago m ON v.metodo_pago_id = m.id_metodo
                ORDER BY v.fecha DESC
            """
            res = self.db.obtener_resultados(query)

        if res:
            for v in res:
                def ver_detalle(e, folio=v['id_venta']):
                    self.mostrar_detalle_venta(folio)

                self.tabla_historial.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(f"#{v['id_venta']}")),
                        ft.DataCell(ft.Text(str(v['fecha']))),
                        ft.DataCell(ft.Text(v['usuario'])),
                        ft.DataCell(ft.Text(v['metodo'])),
                        ft.DataCell(ft.Text(f"{v['impuesto']}%")),
                        ft.DataCell(ft.Text(f"${float(v['total_venta']):.2f}")),
                        ft.DataCell(
                            ft.IconButton(ft.Icons.RECEIPT_LONG, icon_color=ft.Colors.BLUE_700, on_click=ver_detalle)
                        )
                    ])
                )

    def mostrar_historial(self):
        self.cargar_datos_historial()
        if self.page_ref:
            self.page_ref.update()

    def filtrar_historial(self, e):
        txt = self.txt_buscar.value.strip() if self.txt_buscar.value else ""
        self.cargar_datos_historial(txt)
        if self.page_ref:
            self.page_ref.update()

    def mostrar_detalle_venta(self, id_venta):
        query = """
            SELECT d.codigo_producto, p.nombre, d.cantidad, d.precio_unitario, (d.cantidad * d.precio_unitario) as subtotal
            FROM ventas_detalle d
            JOIN productos p ON d.codigo_producto = p.codigo
            WHERE d.id_venta = %s
        """
        detalles = self.db.obtener_resultados(query, (id_venta,))

        tabla_detalles = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Cant.")),
                ft.DataColumn(ft.Text("Precio U.")),
                ft.DataColumn(ft.Text("Subtotal")),
            ],
            rows=[]
        )

        if detalles:
            for d in detalles:
                tabla_detalles.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(d['codigo_producto']))),
                        ft.DataCell(ft.Text(d['nombre'])),
                        ft.DataCell(ft.Text(str(d['cantidad']))),
                        ft.DataCell(ft.Text(f"${float(d['precio_unitario']):.2f}")),
                        ft.DataCell(ft.Text(f"${float(d['subtotal']):.2f}")),
                    ])
                )

        def cerrar_modal(e):
            if dlg in self.page_ref.overlay:
                self.page_ref.overlay.remove(dlg)
            self.page_ref.update()

        # Ventana modal más ancha y con scroll horizontal seguro
        dlg = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cerrar_modal),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    padding=25,
                    border_radius=10,
                    width=720,
                    content=ft.Column([
                        ft.Text(f"Detalle de Venta #{id_venta}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Row(
                                [tabla_detalles],
                                scroll=ft.ScrollMode.AUTO
                            ),
                            height=280
                        ),
                        ft.Divider(),
                        ft.Row([
                            ft.ElevatedButton("Cerrar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=cerrar_modal)
                        ], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=10)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])

        self.page_ref.overlay.append(dlg)
        self.page_ref.update()