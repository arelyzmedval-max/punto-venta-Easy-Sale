import flet as ft

class VentasView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario, al_completar_venta=None):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario
        self.al_completar_venta = al_completar_venta
        self.carrito = []
        self.cliente_seleccionado_id = None  # Guardará el ID del cliente elegido

        self.crear_interfaz()

    def crear_interfaz(self):
        # 1. Buscador de Productos
        self.txt_codigo = ft.TextField(
            label="Código o Nombre de producto",
            expand=True,
            on_change=self.filtrar_sugerencias_productos,
            on_submit=self.agregar_por_enter
        )

        btn_buscar = ft.Button(
            content=ft.Text("Agregar"),
            icon=ft.Icons.ADD_SHOPPING_CART,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.agregar_por_enter
        )

        self.lista_sugerencias = ft.ListView(spacing=5, height=150)
        self.card_sugerencias = ft.Card(
            content=ft.Container(content=self.lista_sugerencias, padding=5),
            visible=False
        )

        # 2. Menú de Métodos de Pago
        self.dd_metodo_pago = ft.Dropdown(
            label="Método de Pago",
            expand=True
        )
        self.cargar_metodos_pago()

        # 3. BUSCADOR DE CLIENTES EN TIEMPO REAL
        self.txt_buscar_cliente = ft.TextField(
            label="Buscar Cliente (para Fiados)",
            expand=True,
            on_change=self.filtrar_sugerencias_clientes,
            prefix_icon=ft.Icons.SEARCH
        )

        self.lista_clientes_sugeridos = ft.ListView(spacing=3, height=120)
        self.card_clientes_sugeridos = ft.Card(
            content=ft.Container(content=self.lista_clientes_sugeridos, padding=5),
            visible=False
        )

        self.txt_impuesto = ft.TextField(
            label="Impuesto (%)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
            on_change=self.recalcular_totales
        )

        self.tabla_carrito = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Cant. / Peso")),
                ft.DataColumn(ft.Text("Precio U.")),
                ft.DataColumn(ft.Text("Subtotal")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        self.lbl_subtotal = ft.Text("$0.00", size=16)
        self.lbl_impuesto = ft.Text("$0.00", size=16)
        self.lbl_total = ft.Text("$0.00", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)

        btn_cobrar = ft.Button(
            content=ft.Text("Procesar Venta"),
            icon=ft.Icons.POINT_OF_SALE,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            height=50,
            on_click=self.procesar_venta
        )

        self.content = ft.Column([
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([self.txt_codigo, btn_buscar]),
                        self.card_sugerencias
                    ])
                )
            ),
            ft.Row([
                ft.Card(
                    expand=2,
                    content=ft.Container(
                        padding=10,
                        content=ft.ListView([self.tabla_carrito], expand=True)
                    )
                ),
                ft.Card(
                    expand=1,
                    content=ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Text("Resumen de Venta", size=18, weight=ft.FontWeight.BOLD),
                            self.dd_metodo_pago,
                            # Contenedor del buscador de clientes con sus sugerencias flotantes
                            ft.Column([
                                self.txt_buscar_cliente,
                                self.card_clientes_sugeridos
                            ], spacing=0),
                            self.txt_impuesto,
                            ft.Divider(),
                            ft.Row([ft.Text("Subtotal:"), self.lbl_subtotal], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Impuesto:"), self.lbl_impuesto], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Total:"), self.lbl_total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(),
                            btn_cobrar
                        ], spacing=15)
                    )
                )
            ], expand=True)
        ], expand=True, spacing=10)

    def cargar_metodos_pago(self):
        metodos = self.db.obtener_resultados("SELECT id_metodo, metodo FROM metodos_pago")
        if metodos:
            self.dd_metodo_pago.options = [
                ft.dropdown.Option(key=str(m['id_metodo']), text=m['metodo']) for m in metodos
            ]

    # --- LÓGICA DE BÚSQUEDA DE CLIENTES EN TIEMPO REAL ---
    def filtrar_sugerencias_clientes(self, e):
        texto = self.txt_buscar_cliente.value.strip() if self.txt_buscar_cliente.value else ""
        if not texto:
            self.card_clientes_sugeridos.visible = False
            self.cliente_seleccionado_id = None
            self.page_ref.update()
            return

        res = self.db.obtener_resultados(
            "SELECT id_cliente, nombre, telefono FROM clientes WHERE nombre LIKE %s OR telefono LIKE %s LIMIT 5",
            (f"%{texto}%", f"%{texto}%")
        )

        if not res:
            self.card_clientes_sugeridos.visible = False
            self.page_ref.update()
            return

        self.lista_clientes_sugeridos.controls.clear()
        for cli in res:
            def elegir_cliente(e, c=cli):
                self.cliente_seleccionado_id = c['id_cliente']
                self.txt_buscar_cliente.value = c['nombre']  # Rellena el campo con el nombre elegido
                self.card_clientes_sugeridos.visible = False
                self.page_ref.update()

            item = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_700, size=16),
                    ft.Text(f"{cli['nombre']} ({cli['telefono'] or 'Sin tel'})", size=13, weight=ft.FontWeight.BOLD)
                ]),
                padding=8,
                ink=True,
                on_click=elegir_cliente
            )
            self.lista_clientes_sugeridos.controls.append(item)

        self.card_clientes_sugeridos.visible = True
        self.page_ref.update()

    # --- LÓGICA DE BÚSQUEDA DE PRODUCTOS ---
    def filtrar_sugerencias_productos(self, e):
        texto = self.txt_codigo.value.strip() if self.txt_codigo.value else ""
        if not texto:
            self.card_sugerencias.visible = False
            self.page_ref.update()
            return

        res = self.db.obtener_resultados(
            "SELECT * FROM productos WHERE codigo = %s OR nombre LIKE %s LIMIT 5",
            (texto, f"%{texto}%")
        )

        if not res:
            self.card_sugerencias.visible = False
            self.page_ref.update()
            return

        self.lista_sugerencias.controls.clear()
        for prod in res:
            # CONSULTA FRESCA DE STOCK AL MOMENTO DE MOSTRAR LA SUGERENCIA
            prod_actualizado = self.db.obtener_resultados("SELECT * FROM productos WHERE codigo = %s",
                                                          (prod['codigo'],))
            stock_actual = float(prod_actualizado[0]['stock']) if prod_actualizado else float(prod['stock'])

            def elegir_producto(e, codigo_prod=prod['codigo']):
                self.card_sugerencias.visible = False
                self.txt_codigo.value = ""
                self.page_ref.update()

                # Consultamos directamente de la BD el producto fresco al hacer clic
                p_real = self.db.obtener_resultados("SELECT * FROM productos WHERE codigo = %s", (codigo_prod,))
                if p_real:
                    self.evaluar_y_agregar(p_real[0])

            item_sugerencia = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SHOPPING_BAG, color=ft.Colors.BLUE_700, size=18),
                    ft.Column([
                        ft.Text(prod['nombre'], weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(f"Código: {prod['codigo']} | Stock: {stock_actual} | ${float(prod['precio']):.2f}",
                                size=11, color=ft.Colors.GREY_700)
                    ], spacing=2, expand=True)
                ]),
                padding=10,
                ink=True,
                on_click=elegir_producto
            )
            self.lista_sugerencias.controls.append(item_sugerencia)

        self.card_sugerencias.visible = True
        self.page_ref.update()

    def agregar_por_enter(self, e):
        texto = self.txt_codigo.value.strip() if self.txt_codigo.value else ""
        if not texto: return

        # Consulta directa y fresca de la BD al presionar Enter
        res = self.db.obtener_resultados("SELECT * FROM productos WHERE codigo = %s OR nombre LIKE %s LIMIT 1",
                                         (texto, f"%{texto}%"))
        if res:
            self.card_sugerencias.visible = False
            self.txt_codigo.value = ""
            self.page_ref.update()
            self.evaluar_y_agregar(res[0])
        else:
            self.mostrar_snack("❌ Producto no encontrado", ft.Colors.RED_700)

    def evaluar_y_agregar(self, prod):
        if prod.get('tipo_venta') == 'por kilo':
            self.pedir_peso_producto(prod)
        else:
            self.pedir_cantidad_producto(prod)

    def pedir_cantidad_producto(self, prod):
        txt_cantidad = ft.TextField(label="Cantidad", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, value="1")
        def confirmar(e):
            try:
                cant = float(txt_cantidad.value.replace(",", "."))
                if cant <= 0: raise ValueError
            except ValueError:
                self.mostrar_snack("⚠️ Ingresa una cantidad válida", ft.Colors.RED_700)
                return
            if modal_container in self.page_ref.overlay: self.page_ref.overlay.remove(modal_container)
            self.page_ref.update()
            self.procesar_item_al_carrito(prod, cant)
        def cancelar(e):
            if modal_container in self.page_ref.overlay: self.page_ref.overlay.remove(modal_container)
            self.page_ref.update()

        modal_container = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cancelar),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE, padding=20, border_radius=10, width=380,
                    content=ft.Column([
                        ft.Text(f"Cantidad para: {prod['nombre']}", size=16, weight=ft.FontWeight.BOLD),
                        txt_cantidad,
                        ft.Row([ft.TextButton("Cancelar", on_click=cancelar), ft.ElevatedButton("Agregar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=confirmar)], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=15)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])
        self.page_ref.overlay.append(modal_container)
        self.page_ref.update()

    def pedir_peso_producto(self, prod):
        txt_peso = ft.TextField(label="Kilos (ej. 0.750)", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, value="1.0")
        def confirmar(e):
            try:
                peso = float(txt_peso.value.replace(",", "."))
                if peso <= 0: raise ValueError
            except ValueError:
                self.mostrar_snack("⚠️ Ingresa un peso válido", ft.Colors.RED_700)
                return
            if modal_container in self.page_ref.overlay: self.page_ref.overlay.remove(modal_container)
            self.page_ref.update()
            self.procesar_item_al_carrito(prod, peso)
        def cancelar(e):
            if modal_container in self.page_ref.overlay: self.page_ref.overlay.remove(modal_container)
            self.page_ref.update()

        modal_container = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cancelar),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE, padding=20, border_radius=10, width=380,
                    content=ft.Column([
                        ft.Text(f"Peso para: {prod['nombre']}", size=16, weight=ft.FontWeight.BOLD),
                        txt_peso,
                        ft.Row([ft.TextButton("Cancelar", on_click=cancelar), ft.ElevatedButton("Agregar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=confirmar)], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=15)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])
        self.page_ref.overlay.append(modal_container)
        self.page_ref.update()

    def procesar_item_al_carrito(self, prod, cantidad=1.0):
        if prod['stock'] <= 0:
            self.mostrar_snack("⚠️ Sin stock disponible", ft.Colors.ORANGE_800)
            return
        for item in self.carrito:
            if item['codigo'] == prod['codigo']:
                item['cantidad'] += cantidad
                self.actualizar_tabla_carrito()
                return
        self.carrito.append({
            'codigo': prod['codigo'], 'nombre': prod['nombre'],
            'precio': float(prod['precio']), 'cantidad': cantidad,
            'tipo_venta': prod.get('tipo_venta', 'por unidad'), 'stock': prod['stock']
        })
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        self.tabla_carrito.rows.clear()
        subtotal_acum = 0.0
        for idx, item in enumerate(self.carrito):
            subtotal_item = item['precio'] * item['cantidad']
            subtotal_acum += subtotal_item

            def quitar_item(e, pos=idx):
                self.carrito.pop(pos)
                self.actualizar_tabla_carrito()
                self.page_ref.update()

            cant_str = f"{item['cantidad']:.3f} kg" if item['tipo_venta'] == 'por kilo' else str(int(item['cantidad']) if item['cantidad'].is_integer() else item['cantidad'])

            self.tabla_carrito.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(item['codigo']))),
                    ft.DataCell(ft.Text(item['nombre'])),
                    ft.DataCell(ft.Text(cant_str)),
                    ft.DataCell(ft.Text(f"${item['precio']:.2f}")),
                    ft.DataCell(ft.Text(f"${subtotal_item:.2f}")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=quitar_item))
                ])
            )

        try:
            imp_pct = float(self.txt_impuesto.value) if self.txt_impuesto.value else 0.0
        except ValueError:
            imp_pct = 0.0

        total = subtotal_acum + (subtotal_acum * (imp_pct / 100))
        self.lbl_subtotal.value = f"${subtotal_acum:.2f}"
        self.lbl_impuesto.value = f"${subtotal_acum * (imp_pct / 100):.2f}"
        self.lbl_total.value = f"${total:.2f}"
        if self.page_ref: self.page_ref.update()

    def recalcular_totales(self, e):
        self.actualizar_tabla_carrito()

    def procesar_venta(self, e):
        if not self.carrito:
            self.mostrar_snack("⚠️ El carrito está vacío", ft.Colors.ORANGE_800)
            return

        # 1. VERIFICACIÓN OBLIGATORIA DE CAJA ABIERTA
        q_caja = "SELECT id_caja FROM caja WHERE id_usuario = %s AND estado = 'ABIERTA' LIMIT 1"
        caja_activa = self.db.obtener_resultados(q_caja, (self.usuario['id_usuario'],))

        if not caja_activa:
            self.mostrar_snack("⚠️ Debe abrir caja antes de realizar una venta", ft.Colors.RED_700)
            return

        if not self.dd_metodo_pago.value:
            self.mostrar_snack("⚠️ Selecciona un método de pago", ft.Colors.RED_700)
            return

        metodo_id = int(self.dd_metodo_pago.value)
        metodo_texto = ""
        for opt in self.dd_metodo_pago.options:
            if opt.key == str(metodo_id):
                metodo_texto = opt.text.lower()
                break

        es_fiado = "fiado" in metodo_texto or "crédito" in metodo_texto or "credito" in metodo_texto

        if es_fiado and not self.cliente_seleccionado_id:
            self.mostrar_snack("⚠️ Debes buscar y seleccionar un cliente válido para el fiado", ft.Colors.RED_700)
            return

        subtotal = sum(i['precio'] * i['cantidad'] for i in self.carrito)
        total = subtotal + (subtotal * (float(self.txt_impuesto.value or 0) / 100))

        # 2. Registrar la venta principal
        q_venta = "INSERT INTO ventas (id_usuario, metodo_pago_id, impuesto, total_venta) VALUES (%s, %s, %s, %s)"
        cursor = self.db.ejecutar_query(q_venta, (
        self.usuario['id_usuario'], metodo_id, float(self.txt_impuesto.value or 0), total))

        if cursor and cursor.lastrowid:
            id_venta = cursor.lastrowid

            # 3. Si es fiado, registrar en créditos
            if es_fiado:
                q_credito = "INSERT INTO creditos (id_cliente, id_venta, total_fiado, abono, estado) VALUES (%s, %s, %s, 0.00, 'Pendiente')"
                self.db.ejecutar_query(q_credito, (self.cliente_seleccionado_id, id_venta, total))

            # 4. Guardar detalles y descontar stock correctamente
            for item in self.carrito:
                sub_item = item['precio'] * item['cantidad']
                self.db.ejecutar_query(
                    "INSERT INTO ventas_detalle (id_venta, codigo_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (id_venta, item['codigo'], item['cantidad'], item['precio'], sub_item))
                self.db.ejecutar_query("UPDATE productos SET stock = stock - %s WHERE codigo = %s",
                                       (item['cantidad'], item['codigo']))

            self.mostrar_snack("✅ Venta procesada con éxito", ft.Colors.GREEN_700)
            self.carrito.clear()
            self.txt_buscar_cliente.value = ""
            self.cliente_seleccionado_id = None
            self.actualizar_tabla_carrito()
            if self.al_completar_venta: self.al_completar_venta()
        else:
            self.mostrar_snack("❌ Error al procesar venta", ft.Colors.RED_700)

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()