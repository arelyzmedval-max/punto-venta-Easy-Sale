import flet as ft

class InventarioView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.producto_editando_codigo = None

        self.crear_interfaz()
        self.cargar_productos()

    def crear_interfaz(self):
        # Campos del formulario de inventario
        self.txt_codigo = ft.TextField(label="Código", expand=True)
        self.txt_nombre = ft.TextField(label="Nombre", expand=True)
        self.txt_descripcion = ft.TextField(label="Descripción", expand=True)
        
        self.txt_precio = ft.TextField(label="Precio ($)", keyboard_type=ft.KeyboardType.NUMBER, width=200)
        self.txt_stock = ft.TextField(label="Stock Inicial", keyboard_type=ft.KeyboardType.NUMBER, width=200)
        
        self.dd_tipo_venta = ft.Dropdown(
            label="Tipo de Venta",
            value="por unidad",
            options=[
                ft.dropdown.Option("por unidad"),
                ft.dropdown.Option("por kilo")
            ],
            width=200
        )

        self.btn_guardar = ft.ElevatedButton(
            text="Guardar Producto",
            icon=ft.icons.SAVE,
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE,
            on_click=self.guardar_producto
        )

        self.btn_cancelar = ft.ElevatedButton(
            text="Cancelar Edición",
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
            visible=False,
            on_click=self.limpiar_formulario
        )

        self.tabla_productos = ft.DataTable(
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

        self.content = ft.Container(
            padding=20,
            alignment=ft.alignment.top_left,
            content=ft.Column([
                ft.Text("Gestión de Inventario y Productos", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.txt_codigo, self.txt_nombre, self.txt_descripcion]),
                ft.Row([self.txt_precio, self.txt_stock, self.dd_tipo_venta, self.btn_guardar, self.btn_cancelar]),
                ft.Divider(),
                ft.Text("Productos Registrados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.ListView([self.tabla_productos], expand=True),
                    expand=True
                )
            ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def cargar_productos(self):
        self.tabla_productos.rows.clear()
        resultados = self.db.obtener_resultados("SELECT * FROM productos")
        if resultados:
            for prod in resultados:
                codigo = prod['codigo']
                
                def editar(e, p=prod):
                    self.producto_editando_codigo = p['codigo']
                    self.txt_codigo.value = str(p['codigo'])
                    self.txt_codigo.disabled = True  # No se edita la PK
                    self.txt_nombre.value = p['nombre']
                    self.txt_descripcion.value = p['descripcion'] or ""
                    self.txt_precio.value = str(p['precio'])
                    self.txt_stock.value = str(p['stock'])
                    self.dd_tipo_venta.value = p.get('tipo_venta', 'por unidad')
                    self.btn_guardar.text = "Actualizar Producto"
                    self.btn_cancelar.visible = True
                    self.page_ref.update()

                def eliminar(e, cod=codigo):
                    self.db.ejecutar_query("DELETE FROM productos WHERE codigo = %s", (cod,))
                    self.mostrar_snack("🗑️ Producto eliminado", ft.colors.RED_700)
                    self.cargar_productos()

                stock_str = f"{float(prod['stock']):.3f} kg" if prod.get('tipo_venta') == 'por kilo' else str(int(prod['stock']) if float(prod['stock']).is_integer() else prod['stock'])

                self.tabla_productos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(codigo))),
                        ft.DataCell(ft.Text(prod['nombre'])),
                        ft.DataCell(ft.Text(prod['descripcion'] or "")),
                        ft.DataCell(ft.Text(f"${float(prod['precio']):.2f}")),
                        ft.DataCell(ft.Text(stock_str)),
                        ft.DataCell(ft.Text(prod.get('tipo_venta', 'por unidad'))),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.icons.EDIT, icon_color=ft.colors.AMBER_700, on_click=editar, tooltip="Editar"),
                            ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=eliminar, tooltip="Eliminar")
                        ], spacing=0))
                    ])
                )
        self.page_ref.update()

    def guardar_producto(self, e):
        codigo = self.txt_codigo.value.strip() if self.txt_codigo.value else ""
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        descripcion = self.txt_descripcion.value.strip() if self.txt_descripcion.value else ""
        
        try:
            precio = float(self.txt_precio.value.replace(",", ".")) if self.txt_precio.value else 0.0
            stock = float(self.txt_stock.value.replace(",", ".")) if self.txt_stock.value else 0.0
        except ValueError:
            self.mostrar_snack("⚠️ Precio y stock deben ser numéricos", ft.colors.RED_700)
            return

        if not codigo or not nombre:
            self.mostrar_snack("⚠️ El código y el nombre son obligatorios", ft.colors.RED_700)
            return

        tipo_v = self.dd_tipo_venta.value

        if self.producto_editando_codigo:
            # Actualizar
            self.db.ejecutar_query(
                "UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, stock = %s, tipo_venta = %s WHERE codigo = %s",
                (nombre, descripcion, precio, stock, tipo_v, self.producto_editando_codigo)
            )
            self.mostrar_snack("✅ Producto actualizado con éxito", ft.colors.GREEN_700)
        else:
            # Insertar nuevo
            existe = self.db.obtener_resultados("SELECT * FROM productos WHERE codigo = %s", (codigo,))
            if existe:
                self.mostrar_snack("⚠️ Ya existe un producto con ese código", ft.colors.RED_700)
                return
            self.db.ejecutar_query(
                "INSERT INTO productos (codigo, nombre, descripcion, precio, stock, tipo_venta) VALUES (%s, %s, %s, %s, %s, %s)",
                (codigo, nombre, descripcion, precio, stock, tipo_v)
            )
            self.mostrar_snack("✅ Producto guardado con éxito", ft.colors.GREEN_700)

        self.limpiar_formulario(None)
        self.cargar_productos()

    def limpiar_formulario(self, e):
        self.producto_editando_codigo = None
        self.txt_codigo.value = ""
        self.txt_codigo.disabled = False
        self.txt_nombre.value = ""
        self.txt_descripcion.value = ""
        self.txt_precio.value = ""
        self.txt_stock.value = ""
        self.dd_tipo_venta.value = "por unidad"
        self.btn_guardar.text = "Guardar Producto"
        self.btn_cancelar.visible = False
        self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()
