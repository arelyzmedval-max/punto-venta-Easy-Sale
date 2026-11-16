import flet as ft

class ClientesView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario

        self.crear_interfaz()
        self.cargar_clientes()

    def crear_interfaz(self):
        self.txt_nombre = ft.TextField(label="Nombre del Cliente", expand=True)
        self.txt_telefono = ft.TextField(label="Teléfono", expand=True)
        self.txt_limite = ft.TextField(label="Límite de Crédito ($)", value="1000.00", width=150, keyboard_type=ft.KeyboardType.NUMBER)

        btn_registrar = ft.ElevatedButton(
            text="Registrar Cliente",
            icon=ft.icons.PERSON_ADD,
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE,
            on_click=self.registrar_cliente
        )

        self.tabla_clientes = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Teléfono")),
                ft.DataColumn(ft.Text("Deuda Actual")),
                ft.DataColumn(ft.Text("Límite Crédito")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Contenedor principal con ALINEACIÓN SUPERIOR (top_left)
        self.content = ft.Container(
            padding=20,
            alignment=ft.alignment.top_left,
            content=ft.Column([
                ft.Text("Gestión de Clientes y Créditos (Fiados)", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.txt_nombre, self.txt_telefono, self.txt_limite, btn_registrar]),
                ft.Divider(),
                ft.Text("Lista de Clientes", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.ListView([self.tabla_clientes], expand=True),
                    expand=True
                )
            ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def cargar_clientes(self):
        self.tabla_clientes.rows.clear()
        resultados = self.db.obtener_resultados("""
            SELECT c.id_crediticio AS id_cliente, c.id_cliente AS cli_id_real, 
                   COALESCE(cli.nombre, 'Desconocido') AS nombre, 
                   COALESCE(cli.telefono, 'N/A') AS telefono, 
                   c.total_fiado - c.abono AS deuda_actual, c.total_fiado AS limite_credito
            FROM creditos c
            LEFT JOIN clientes cli ON c.id_cliente = cli.id_cliente
            WHERE c.estado = 'Pendiente'
        """)
        
        # Si tienes una tabla de clientes pura, ajustamos la consulta si es necesario:
        res_clientes = self.db.obtener_resultados("SELECT * FROM clientes")

        if res_clientes:
            for cli in res_clientes:
                id_cli = cli['id_cliente']
                
                # Calcular deuda pendiente de este cliente
                deuda_res = self.db.obtener_resultados(
                    "SELECT SUM(total_fiado - abono) as deuda FROM creditos WHERE id_cliente = %s AND estado = 'Pendiente'", 
                    (id_cli,)
                )
                deuda_actual = float(deuda_res[0]['deuda'] or 0.0) if deuda_res else 0.0

                def ver_detalles(e, id_c=id_cli, nom=cli['nombre']):
                    self.mostrar_snack(f"Abriendo créditos para {nom}", ft.colors.BLUE_700)

                self.tabla_clientes.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(id_cli))),
                        ft.DataCell(ft.Text(cli['nombre'])),
                        ft.DataCell(ft.Text(cli.get('telefono') or 'N/A')),
                        ft.DataCell(ft.Text(f"${deuda_actual:.2f}", color=ft.colors.RED_700 if deuda_actual > 0 else ft.colors.GREEN_700, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"${float(cli.get('limite_credito', 1000.00)):.2f}")),
                        ft.DataCell(ft.ElevatedButton(
                            text="Créditos / Abonos",
                            icon=ft.icons.ACCOUNT_BALANCE_WALLET,
                            scale=0.85,
                            on_click=ver_detalles
                        ))
                    ])
                )
        self.page_ref.update()

    def registrar_cliente(self, e):
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        telefono = self.txt_telefono.value.strip() if self.txt_telefono.value else ""
        
        try:
            limite = float(self.txt_limite.value.replace(",", ".")) if self.txt_limite.value else 1000.00
        except ValueError:
            limite = 1000.00

        if not nombre:
            self.mostrar_snack("⚠️ El nombre del cliente es obligatorio", ft.colors.RED_700)
            return

        self.db.ejecutar_query(
            "INSERT INTO clientes (nombre, telefono, limite_credito) VALUES (%s, %s, %s)",
            (nombre, telefono, limite)
        )

        self.mostrar_snack("✅ Cliente registrado con éxito", ft.colors.GREEN_700)
        self.txt_nombre.value = ""
        self.txt_telefono.value = ""
        self.txt_limite.value = "1000.00"
        self.cargar_clientes()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()
