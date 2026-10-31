import flet as ft

class ReportesView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.crear_interfaz()

    def crear_interfaz(self):
        btn_generar = ft.Button(
            content=ft.Text("Generar Reporte"),
            icon=ft.Icons.ANALYTICS,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=lambda e: self.generar_reporte()
        )

        self.tabla_reporte = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha")),
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Total Vendido")),
                ft.DataColumn(ft.Text("Num. Ventas")),
            ],
            rows=[]
        )

        self.content = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Reporte de Ventas por Usuario y Día", size=18, weight=ft.FontWeight.BOLD),
                        btn_generar
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ListView([self.tabla_reporte], expand=True)
                ], expand=True, spacing=10)
            ),
            expand=True
        )

    def generar_reporte(self):
        self.tabla_reporte.rows.clear()
        query = """
            SELECT DATE(v.fecha) AS dia, u.nombre AS nombre_usuario, 
                   SUM(v.total_venta) AS total_vendido, COUNT(*) AS num_ventas
            FROM ventas v
            JOIN usuarios u ON v.id_usuario = u.id_usuario
            GROUP BY DATE(v.fecha), u.nombre
            ORDER BY dia DESC
        """
        resultados = self.db.obtener_resultados(query)
        total_acumulado = 0.0

        if resultados:
            for fila in resultados:
                val_total = float(fila['total_vendido'])
                total_acumulado += val_total

                self.tabla_reporte.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(fila['dia']))),
                        ft.DataCell(ft.Text(fila['nombre_usuario'])),
                        ft.DataCell(ft.Text(f"${val_total:.2f}")),
                        ft.DataCell(ft.Text(str(fila['num_ventas']))),
                    ])
                )

            # Fila de Total Acumulado General
            self.tabla_reporte.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("TOTAL GENERAL", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text(f"${total_acumulado:.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)),
                        ft.DataCell(ft.Text("")),
                    ]
                )
            )
        else:
            self.page_ref.update(ft.SnackBar(ft.Text("No hay registros para generar reporte"), bgcolor=ft.Colors.ORANGE_800))

        self.page.update()