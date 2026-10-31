import flet as ft

class InventarioView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario=None):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario
        self.codigo_seleccionado = None

        self.crear_interfaz()
        self.cargar_datos_tabla()

    def did_mount(self):
        # Se ejecuta automáticamente cada vez que entras a la pestaña de Inventario
        self.cargar_datos_tabla()

    def crear_interfaz(self):
        # Campos del Formulario
        self.txt_codigo = ft.TextField(label="Código", expand=True)
        self.txt_nombre = ft.TextField(label="Nombre", expand=True)
        self.txt_descripcion = ft.TextField(label="Descripción", expand=True)
        self.txt_precio = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.txt_stock = ft.TextField(label="Stock", keyboard_type=ft.KeyboardType.NUMBER, expand=True)

        self.dd_tipo_venta = ft.Dropdown(
            label="Tipo de Venta",
            options=[
                ft.dropdown.Option("por unidad"),
                ft.dropdown.Option("por kilo"),
                ft.dropdown.Option("por paquete")
            ],
            value="por unidad",
            expand=True
        )

        btn_agregar = ft.Button(
            content=ft.Text("Agregar Producto"),
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.agregar_producto
        )

        btn_editar = ft.Button(
            content=ft.Text("Guardar Cambios"),
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.AMBER_700,
            color=ft.Colors.WHITE,
            on_click=self.editar_producto
        )

        btn_limpiar = ft.OutlinedButton(
            content=ft.Text("Limpiar Formulario"),
            icon=ft.Icons.CLEAR_ALL,
            on_click=self.limpiar_formulario
        )

        # Tabla del Inventario
        self.tabla_inventario = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Descripción")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("Stock Actual")),
                ft.DataColumn(ft.Text("Tipo Venta")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Contenedor Visual
        self.content = ft.Column([
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Gestión de Inventario y Productos", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([self.txt_codigo, self.txt_nombre, self.txt_descripcion]),
                        ft.Row([self.txt_precio, self.txt_stock, self.dd_tipo_venta]),
                        ft.Row([btn_agregar, btn_editar, btn_limpiar], alignment=ft.MainAxisAlignment.END)
                    ], spacing=10)
                )
            ),
            ft.Card(
                expand=True,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("Productos Registrados", size=16, weight=ft.FontWeight.BOLD),
                        ft.ListView([self.tabla_inventario], expand=True)
                    ])
                )
            )
        ], expand=True, spacing=10)

    def cargar_datos_tabla(self):
        self.tabla_inventario.rows.clear()
        productos = self.db.obtener_resultados("SELECT * FROM productos")

        if productos:
            for p in productos:
                def cargar_p(e, prod=p):
                    self.cargar_producto_en_formulario(prod)

                def eliminar_p(e, cod=p['codigo']):
                    self.eliminar_producto(cod)

                stock_val = float(p['stock'])
                stock_str = f"{stock_val:.3f} kg" if p.get('tipo_venta') == 'por kilo' else str(int(stock_val) if stock_val.is_integer() else stock_val)
                color_stock = ft.Colors.RED_700 if stock_val <= 0 else ft.Colors.BLACK

                self.tabla_inventario.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p['codigo']))),
                        ft.DataCell(ft.Text(p['nombre'])),
                        ft.DataCell(ft.Text(p['descripcion'] or '')),
                        ft.DataCell(ft.Text(f"${float(p['precio']):.2f}")),
                        ft.DataCell(ft.Text(stock_str, color=color_stock, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(p['tipo_venta'])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.AMBER_700, on_click=cargar_p),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=eliminar_p)
                            ])
                        )
                    ])
                )
        if self.page_ref:
            self.page_ref.update()

    def obtener_siguiente_codigo_autogenerado(self):
        query = """
            SELECT MAX(CAST(codigo AS UNSIGNED)) AS ultimo_id 
            FROM productos 
            WHERE codigo REGEXP '^[0-9]+$' AND LENGTH(codigo) <= 6
        """
        res = self.db.obtener_resultados(query)
        if res and res[0]['ultimo_id'] is not None:
            return str(int(res[0]['ultimo_id']) + 1)
        return "1"

    def agregar_producto(self, e):
        codigo = self.txt_codigo.value.strip() if self.txt_codigo.value else ""
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        descripcion = self.txt_descripcion.value.strip() if self.txt_descripcion.value else ""
        precio = self.txt_precio.value.strip() if self.txt_precio.value else ""
        stock = self.txt_stock.value.strip() if self.txt_stock.value else ""
        tipo_venta = self.dd_tipo_venta.value

        if not codigo:
            codigo = self.obtener_siguiente_codigo_autogenerado()

        if not (nombre and precio and stock and tipo_venta):
            self.mostrar_snack("⚠️ Nombre, precio y stock son obligatorios", ft.Colors.RED_700)
            return

        try:
            precio_val = float(precio)
            stock_val = float(stock)
            if precio_val < 0 or stock_val < 0:
                raise ValueError
        except ValueError:
            self.mostrar_snack("⚠️ Precio y stock deben ser números positivos", ft.Colors.RED_700)
            return

        query = "INSERT INTO productos (codigo, nombre, descripcion, precio, stock, tipo_venta) VALUES (%s, %s, %s, %s, %s, %s)"
        try:
            self.db.ejecutar_query(query, (codigo, nombre, descripcion, precio_val, stock_val, tipo_venta))
            self.mostrar_snack(f"✅ Producto agregado con código: {codigo}", ft.Colors.GREEN_700)
            self.limpiar_formulario()
            self.cargar_datos_tabla()
        except Exception as ex:
            self.mostrar_snack(f"❌ Error al agregar producto: {ex}", ft.Colors.RED_700)

    def editar_producto(self, e):
        if not self.codigo_seleccionado:
            self.mostrar_snack("⚠️ Selecciona un producto de la tabla para editar", ft.Colors.ORANGE_800)
            return

        codigo = self.txt_codigo.value.strip() if self.txt_codigo.value else self.codigo_seleccionado
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        descripcion = self.txt_descripcion.value.strip() if self.txt_descripcion.value else ""
        precio = self.txt_precio.value.strip() if self.txt_precio.value else ""
        stock = self.txt_stock.value.strip() if self.txt_stock.value else ""
        tipo_venta = self.dd_tipo_venta.value

        try:
            precio_val = float(precio)
            stock_val = float(stock)
            if precio_val < 0 or stock_val < 0:
                raise ValueError
        except ValueError:
            self.mostrar_snack("⚠️ Precio y stock deben ser números positivos", ft.Colors.RED_700)
            return

        query = """
            UPDATE productos
            SET codigo = %s, nombre = %s, descripcion = %s, precio = %s, stock = %s, tipo_venta = %s
            WHERE codigo = %s
        """
        cursor = self.db.ejecutar_query(query, (
            codigo, nombre, descripcion, precio_val, stock_val, tipo_venta, self.codigo_seleccionado
        ))
        if cursor is not None:
            self.mostrar_snack("✅ Producto actualizado exitosamente", ft.Colors.GREEN_700)
            self.limpiar_formulario()
            self.cargar_datos_tabla()

    def eliminar_producto(self, codigo):
        def confirmar(e):
            if dlg in self.page_ref.overlay:
                self.page_ref.overlay.remove(dlg)
            self.db.ejecutar_query("DELETE FROM productos WHERE codigo = %s", (codigo,))
            self.mostrar_snack("✅ Producto eliminado", ft.Colors.GREEN_700)
            self.cargar_datos_tabla()

        def cancelar(e):
            if dlg in self.page_ref.overlay:
                self.page_ref.overlay.remove(dlg)
            self.page_ref.update()

        # Modal seguro compatible con tu versión usando Stack overlay
        dlg = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cancelar),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE, padding=20, border_radius=10, width=380,
                    content=ft.Column([
                        ft.Text("Confirmar Eliminación", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"¿Deseas eliminar el producto con código '{codigo}'?"),
                        ft.Row([
                            ft.TextButton("Cancelar", on_click=cancelar),
                            ft.ElevatedButton("Eliminar", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=confirmar)
                        ], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=15)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])
        self.page_ref.overlay.append(dlg)
        self.page_ref.update()

    def cargar_producto_en_formulario(self, producto):
        self.codigo_seleccionado = producto['codigo']
        self.txt_codigo.value = str(producto['codigo'])
        self.txt_nombre.value = producto['nombre']
        self.txt_descripcion.value = producto['descripcion'] or ""
        self.txt_precio.value = str(producto['precio'])
        self.txt_stock.value = str(producto['stock'])
        self.dd_tipo_venta.value = producto['tipo_venta']
        self.page_ref.update()

    def limpiar_formulario(self, e=None):
        self.codigo_seleccionado = None
        self.txt_codigo.value = ""
        self.txt_nombre.value = ""
        self.txt_descripcion.value = ""
        self.txt_precio.value = ""
        self.txt_stock.value = ""
        self.dd_tipo_venta.value = "por unidad"
        if self.page_ref:
            self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()