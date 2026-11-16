import flet as ft

class UsuariosView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario_editando_id = None

        self.crear_interfaz()
        self.cargar_usuarios()

    def crear_interfaz(self):
        self.txt_nombre = ft.TextField(label="Nombre Completo", expand=True)
        self.txt_usuario = ft.TextField(label="Usuario / Alias", expand=True)
        self.txt_password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, expand=True)
        
        self.dd_rol = ft.Dropdown(
            label="Rol de Usuario",
            value="usuario",
            options=[
                ft.dropdown.Option("admin"),
                ft.dropdown.Option("usuario"),
                ft.dropdown.Option("cajero")
            ],
            expand=True
        )

        self.btn_guardar = ft.ElevatedButton(
            text="Guardar Usuario",
            icon=ft.icons.SAVE,
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE,
            on_click=self.guardar_usuario
        )

        self.btn_cancelar = ft.ElevatedButton(
            text="Cancelar",
            icon=ft.icons.CANCEL,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
            visible=False,
            on_click=self.limpiar_formulario
        )

        self.tabla_usuarios = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Rol")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        self.content = ft.Container(
            padding=20,
            alignment=ft.alignment.top_left,
            content=ft.Column([
                ft.Text("Gestión de Usuarios y Roles", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([self.txt_nombre, self.txt_usuario, self.txt_password]),
                ft.Row([self.dd_rol, self.btn_guardar, self.btn_cancelar]),
                ft.Divider(),
                ft.Text("Usuarios Registrados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.ListView([self.tabla_usuarios], expand=True),
                    expand=True
                )
            ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def cargar_usuarios(self):
        self.tabla_usuarios.rows.clear()
        resultados = self.db.obtener_resultados("SELECT id_usuario, nombre, usuario, rol FROM usuarios")
        if resultados:
            for usr in resultados:
                uid = usr['id_usuario']

                def editar(e, u=usr):
                    self.usuario_editando_id = u['id_usuario']
                    self.txt_nombre.value = u['nombre']
                    self.txt_usuario.value = u['usuario']
                    self.txt_password.value = ""  # No mostramos la contraseña por seguridad
                    self.txt_password.hint_text = "Dejar en blanco para mantener la actual"
                    self.dd_rol.value = u['rol']
                    self.btn_guardar.text = "Actualizar Usuario"
                    self.btn_cancelar.visible = True
                    self.page_ref.update()

                def eliminar(e, id_u=uid):
                    if id_u == 1:
                        self.mostrar_snack("⚠️ No se puede eliminar al usuario administrador principal", ft.colors.ORANGE_800)
                        return
                    self.db.ejecutar_query("DELETE FROM usuarios WHERE id_usuario = %s", (id_u,))
                    self.mostrar_snack("🗑️ Usuario eliminado", ft.colors.RED_700)
                    self.cargar_usuarios()

                self.tabla_usuarios.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(uid))),
                        ft.DataCell(ft.Text(usr['nombre'])),
                        ft.DataCell(ft.Text(usr['usuario'])),
                        ft.DataCell(ft.Text(usr['rol'])),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.icons.EDIT, icon_color=ft.colors.AMBER_700, on_click=editar, tooltip="Editar"),
                            ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=eliminar, tooltip="Eliminar")
                        ], spacing=0))
                    ])
                )
        self.page_ref.update()

    def guardar_usuario(self, e):
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        usuario = self.txt_usuario.value.strip() if self.txt_usuario.value else ""
        password = self.txt_password.value.strip() if self.txt_password.value else ""
        rol = self.dd_rol.value

        if not nombre or not usuario:
            self.mostrar_snack("⚠️ El nombre y el usuario son obligatorios", ft.colors.RED_700)
            return

        if self.usuario_editando_id:
            if password:
                self.db.ejecutar_query(
                    "UPDATE usuarios SET nombre = %s, usuario = %s, password = %s, rol = %s WHERE id_usuario = %s",
                    (nombre, usuario, password, rol, self.usuario_editando_id)
                )
            else:
                self.db.ejecutar_query(
                    "UPDATE usuarios SET nombre = %s, usuario = %s, rol = %s WHERE id_usuario = %s",
                    (nombre, usuario, rol, self.usuario_editando_id)
                )
            self.mostrar_snack("✅ Usuario actualizado con éxito", ft.colors.GREEN_700)
        else:
            if not password:
                self.mostrar_snack("⚠️ La contraseña es obligatoria para nuevos usuarios", ft.colors.RED_700)
                return
            existe = self.db.obtener_resultados("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
            if existe:
                self.mostrar_snack("⚠️ El nombre de usuario ya está registrado", ft.colors.RED_700)
                return
            self.db.ejecutar_query(
                "INSERT INTO usuarios (nombre, usuario, password, rol) VALUES (%s, %s, %s, %s)",
                (nombre, usuario, password, rol)
            )
            self.mostrar_snack("✅ Usuario registrado con éxito", ft.colors.GREEN_700)

        self.limpiar_formulario(None)
        self.cargar_usuarios()

    def limpiar_formulario(self, e):
        self.usuario_editando_id = None
        self.txt_nombre.value = ""
        self.txt_usuario.value = ""
        self.txt_password.value = ""
        self.txt_password.hint_text = None
        self.dd_rol.value = "usuario"
        self.btn_guardar.text = "Guardar Usuario"
        self.btn_cancelar.visible = False
        self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()
