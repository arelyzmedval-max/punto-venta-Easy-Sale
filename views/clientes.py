import flet as ft


class ClientesView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario

        self.txt_nombre = ft.TextField(label="Nombre del Cliente", width=300)
        self.txt_telefono = ft.TextField(label="Teléfono", width=200)
        self.txt_limite = ft.TextField(label="Límite de Crédito ($)", value="1000.00", width=200,
                                       keyboard_type=ft.KeyboardType.NUMBER)

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

        self.content = ft.Container(
            padding=30,
            content=ft.Column([
                ft.Text("Gestión de Clientes y Créditos (Fiados)", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.txt_nombre,
                    self.txt_telefono,
                    self.txt_limite,
                    ft.ElevatedButton("Registrar Cliente", icon=ft.Icons.PERSON_ADD, bgcolor=ft.Colors.BLUE_700,
                                      color=ft.Colors.WHITE, on_click=self.guardar_cliente)
                ], wrap=True, spacing=15),
                ft.Divider(),
                ft.Text("Lista de Clientes", size=18, weight=ft.FontWeight.BOLD),
                ft.ListView([self.tabla_clientes], expand=True)
            ], spacing=15, scroll=ft.ScrollMode.AUTO)
        )

        self.cargar_clientes()

    def cargar_clientes(self):
        self.tabla_clientes.rows.clear()

        query = """
            SELECT c.id_cliente, c.nombre, c.telefono, c.limite_credito,
                   COALESCE(SUM(cr.total_fiado - cr.abono), 0) as total_deuda
            FROM clientes c
            LEFT JOIN creditos cr ON c.id_cliente = cr.id_cliente AND cr.estado = 'Pendiente'
            GROUP BY c.id_cliente, c.nombre, c.telefono, c.limite_credito
        """
        res = self.db.obtener_resultados(query)

        if res:
            for c in res:
                def ver_estado_cuenta(e, cliente=c):
                    self.abrir_modal_credito(cliente)

                deuda = float(c['total_deuda'])
                color_deuda = ft.Colors.RED_700 if deuda > 0 else ft.Colors.GREEN_700

                self.tabla_clientes.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(c['id_cliente']))),
                        ft.DataCell(ft.Text(c['nombre'])),
                        ft.DataCell(ft.Text(c['telefono'] or 'N/A')),
                        ft.DataCell(ft.Text(f"${deuda:.2f}", color=color_deuda, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"${float(c['limite_credito']):.2f}")),
                        ft.DataCell(ft.ElevatedButton("Créditos / Abonos", icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                                                      on_click=ver_estado_cuenta))
                    ])
                )
        self.page_ref.update()

    def guardar_cliente(self, e):
        nombre = self.txt_nombre.value.strip()
        if not nombre:
            self.mostrar_snack("⚠️ El nombre del cliente es obligatorio", ft.Colors.RED_700)
            return

        telefono = self.txt_telefono.value.strip()
        try:
            limite = float(self.txt_limite.value)
        except ValueError:
            limite = 0.0

        self.db.ejecutar_query(
            "INSERT INTO clientes (nombre, telefono, limite_credito) VALUES (%s, %s, %s)",
            (nombre, telefono, limite)
        )
        self.mostrar_snack("✅ Cliente registrado con éxito", ft.Colors.GREEN_700)
        self.txt_nombre.value = ""
        self.txt_telefono.value = ""
        self.txt_limite.value = "1000.00"
        self.cargar_clientes()

    def abrir_modal_credito(self, cliente):
        txt_monto_cargo = ft.TextField(label="Monto a sumar / adeudo ($)", keyboard_type=ft.KeyboardType.NUMBER)
        txt_monto_abono = ft.TextField(label="Monto de pago / abono ($)", keyboard_type=ft.KeyboardType.NUMBER)

        def cerrar(e):
            if modal in self.page_ref.overlay:
                self.page_ref.overlay.remove(modal)
            self.page_ref.update()

        def agregar_cargo_manual(e):
            try:
                monto = float(txt_monto_cargo.value.replace(",", "."))
                if monto <= 0: raise ValueError
            except ValueError:
                self.mostrar_snack("⚠️ Ingresa un monto válido mayor a 0", ft.Colors.RED_700)
                return

            # Insertamos un crédito manual (sin id_venta, con id_venta = 0 o NULL)
            self.db.ejecutar_query(
                "INSERT INTO creditos (id_cliente, id_venta, total_fiado, abono, estado) VALUES (%s, 0, %s, 0.00, 'Pendiente')",
                (cliente['id_cliente'], monto)
            )
            self.mostrar_snack("✅ Adeudo agregado correctamente", ft.Colors.GREEN_700)
            cerrar(e)
            self.cargar_clientes()

        def registrar_abono_general(e):
            try:
                abono = float(txt_monto_abono.value.replace(",", "."))
                if abono <= 0: raise ValueError
            except ValueError:
                self.mostrar_snack("⚠️ Ingresa un abono válido mayor a 0", ft.Colors.RED_700)
                return

            # Buscamos los créditos pendientes de este cliente para ir descontando el abono
            creditos_pendientes = self.db.obtener_resultados(
                "SELECT id_credito, total_fiado, abono FROM creditos WHERE id_cliente = %s AND estado = 'Pendiente' ORDER BY fecha_creacion ASC",
                (cliente['id_cliente'],)
            )

            restante_abono = abono
            for cr in creditos_pendientes:
                if restante_abono <= 0:
                    break

                deuda_pendiente_fila = float(cr['total_fiado']) - float(cr['abono'])

                if restante_abono >= deuda_pendiente_fila:
                    # Se paga por completo este crédito
                    nuevo_abono = float(cr['total_fiado'])
                    self.db.ejecutar_query(
                        "UPDATE creditos SET abono = %s, estado = 'Pagado' WHERE id_credito = %s",
                        (nuevo_abono, cr['id_credito'])
                    )
                    restante_abono -= deuda_pendiente_fila
                else:
                    # Se le abona una parte a este crédito
                    nuevo_abono = float(cr['abono']) + restante_abono
                    self.db.ejecutar_query(
                        "UPDATE creditos SET abono = %s WHERE id_credito = %s",
                        (nuevo_abono, cr['id_credito'])
                    )
                    restante_abono = 0

            self.mostrar_snack("✅ Abono registrado con éxito", ft.Colors.GREEN_700)
            cerrar(e)
            self.cargar_clientes()

        modal = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cerrar),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    padding=25,
                    border_radius=10,
                    width=450,
                    content=ft.Column([
                        ft.Text(f"Estado de Cuenta: {cliente['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Text(f"Deuda Total Actual: ${float(cliente['total_deuda']):.2f}", size=16,
                                color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Límite Asignado: ${float(cliente['limite_credito']):.2f}"),
                        ft.Divider(),
                        ft.Text("Agregar Saldo / Deuda Anterior:", weight=ft.FontWeight.BOLD, size=14),
                        txt_monto_cargo,
                        ft.ElevatedButton("Sumar al Debe", icon=ft.Icons.ADD_CARD, bgcolor=ft.Colors.ORANGE_800,
                                          color=ft.Colors.WHITE, on_click=agregar_cargo_manual),
                        ft.Divider(),
                        ft.Text("Registrar Pago / Abono:", weight=ft.FontWeight.BOLD, size=14),
                        txt_monto_abono,
                        ft.ElevatedButton("Aplicar Abono", icon=ft.Icons.PAYMENTS, bgcolor=ft.Colors.GREEN_700,
                                          color=ft.Colors.WHITE, on_click=registrar_abono_general),
                        ft.Container(height=10),
                        ft.Row([ft.ElevatedButton("Cerrar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE,
                                                  on_click=cerrar)], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=10)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])

        self.page_ref.overlay.append(modal)
        self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()