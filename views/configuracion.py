import flet as ft

class ConfiguracionView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db

        self.txt_nombre = ft.TextField(label="Nombre de la Tienda", width=400)
        self.txt_rfc = ft.TextField(label="RFC / Tax ID", width=400)
        self.txt_direccion = ft.TextField(label="Dirección", width=400, multiline=True, height=80)
        self.txt_telefono = ft.TextField(label="Teléfono", width=400)
        self.txt_mensaje = ft.TextField(label="Mensaje al final del Ticket", width=400, value="¡Gracias por su compra!")

        self.content = ft.Container(
            padding=30,
            content=ft.Column([
                ft.Text("Configuración General del Negocio", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.txt_nombre,
                self.txt_rfc,
                self.txt_direccion,
                self.txt_telefono,
                self.txt_mensaje,
                ft.Container(height=10),
                ft.ElevatedButton(
                    content=ft.Text("Guardar Configuración"),
                    icon=ft.Icons.SAVE,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    on_click=self.guardar_configuracion
                )
            ], spacing=15, scroll=ft.ScrollMode.AUTO)
        )

        self.cargar_configuracion()

    def cargar_configuracion(self):
        res = self.db.obtener_resultados("SELECT clave, valor FROM configuracion")
        if res:
            config_dict = {row['clave']: row['valor'] for row in res}
            self.txt_nombre.value = config_dict.get('nombre_tienda', '')
            self.txt_rfc.value = config_dict.get('rfc', '')
            self.txt_direccion.value = config_dict.get('direccion', '')
            self.txt_telefono.value = config_dict.get('telefono', '')
            self.txt_mensaje.value = config_dict.get('mensaje_ticket', '¡Gracias por su compra!')
            self.page_ref.update()

    def guardar_configuracion(self, e):
        datos = {
            'nombre_tienda': self.txt_nombre.value or '',
            'rfc': self.txt_rfc.value or '',
            'direccion': self.txt_direccion.value or '',
            'telefono': self.txt_telefono.value or '',
            'mensaje_ticket': self.txt_mensaje.value or '¡Gracias por su compra!'
        }

        for clave, valor in datos.items():
            existe = self.db.obtener_resultados("SELECT * FROM configuracion WHERE clave = %s", (clave,))
            if existe:
                self.db.ejecutar_query("UPDATE configuracion SET valor = %s WHERE clave = %s", (valor, clave))
            else:
                self.db.ejecutar_query("INSERT INTO configuracion (clave, valor) VALUES (%s, %s)", (clave, valor))

        snack = ft.SnackBar(content=ft.Text("✅ Configuración guardada correctamente", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN_700, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()