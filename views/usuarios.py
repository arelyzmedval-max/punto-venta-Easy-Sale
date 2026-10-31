import flet as ft


class UsuariosView(ft.Container):
    def __init__(self, page: ft.Page, db):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.id_usuario_seleccionado = None

        self.crear_interfaz()
        # Llenamos la tabla sin invocar update() en la página durante el __init__
        self.cargar_datos_tabla()

    def crear_interfaz(self):
        # Campos del Formulario
        self.txt_nombre = ft.TextField(label="Nombre Completo", expand=True)
        self.txt_usuario = ft.TextField(label="Usuario / Alias", expand=True)
        self.txt_password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, expand=True)

        self.dd_rol = ft.Dropdown(
            label="Rol de Usuario",
            options=[
                ft.dropdown.Option("administrador"),
                ft.dropdown.Option("cajero")
            ],
            value="cajero",
            expand=True
        )

        btn_agregar = ft.Button(
            content=ft.Text("Agregar Usuario"),
            icon=ft.Icons.PERSON_ADD,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.agregar_usuario
        )

        btn_editar = ft.Button(
            content=ft.Text("Guardar Cambios"),
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.AMBER_700,
            color=ft.Colors.WHITE,
            on_click=self.editar_usuario
        )

        btn_limpiar = ft.OutlinedButton(
            content=ft.Text("Limpiar Formulario"),
            icon=ft.Icons.CLEAR_ALL,
            on_click=self.limpiar_formulario
        )

        # Tabla de Usuarios
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

        # Layout
        self.content = ft.Column([
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Gestión de Usuarios y Roles", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([self.txt_nombre, self.txt_usuario, self.txt_password]),
                        ft.Row([self.dd_rol]),
                        ft.Row([btn_agregar, btn_editar, btn_limpiar], alignment=ft.MainAxisAlignment.END)
                    ], spacing=10)
                )
            ),
            ft.Card(
                expand=True,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Text("Usuarios Registrados", size=16, weight=ft.FontWeight.BOLD),
                        ft.ListView([self.tabla_usuarios], expand=True)
                    ])
                )
            )
        ], expand=True, spacing=10)

    def cargar_datos_tabla(self):
        self.tabla_usuarios.rows.clear()
        usuarios = self.db.obtener_resultados("SELECT id_usuario, nombre, usuario, rol FROM usuarios")

        if usuarios:
            for u in usuarios:
                def cargar_u(e, usr=u):
                    self.cargar_usuario_en_formulario(usr)

                def eliminar_u(e, id_u=u['id_usuario']):
                    self.eliminar_usuario(id_u)

                self.tabla_usuarios.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(u['id_usuario']))),
                        ft.DataCell(ft.Text(u['nombre'])),
                        ft.DataCell(ft.Text(u['usuario'])),
                        ft.DataCell(ft.Text(u['rol'])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.AMBER_700, on_click=cargar_u),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=eliminar_u)
                            ])
                        )
                    ])
                )

    def mostrar_usuarios(self):
        self.cargar_datos_tabla()
        if self.page_ref:
            self.page_ref.update()

    def agregar_usuario(self, e):
        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        usuario = self.txt_usuario.value.strip() if self.txt_usuario.value else ""
        password = self.txt_password.value.strip() if self.txt_password.value else ""
        rol = self.dd_rol.value

        if not (nombre and usuario and password and rol):
            self.mostrar_snack("⚠️ Todos los campos son obligatorios", ft.Colors.RED_700)
            return

        query = "INSERT INTO usuarios (nombre, usuario, password, rol) VALUES (%s, %s, %s, %s)"
        try:
            self.db.ejecutar_query(query, (nombre, usuario, password, rol))
            self.mostrar_snack("✅ Usuario registrado exitosamente", ft.Colors.GREEN_700)
            self.limpiar_formulario()
            self.mostrar_usuarios()
        except Exception as ex:
            self.mostrar_snack(f"❌ Error al registrar usuario: {ex}", ft.Colors.RED_700)

    def editar_usuario(self, e):
        if not self.id_usuario_seleccionado:
            self.mostrar_snack("⚠️ Selecciona un usuario de la tabla para editar", ft.Colors.ORANGE_800)
            return

        nombre = self.txt_nombre.value.strip() if self.txt_nombre.value else ""
        usuario = self.txt_usuario.value.strip() if self.txt_usuario.value else ""
        password = self.txt_password.value.strip() if self.txt_password.value else ""
        rol = self.dd_rol.value

        if not (nombre and usuario and rol):
            self.mostrar_snack("⚠️ El nombre, usuario y rol son obligatorios", ft.Colors.RED_700)
            return

        if password:
            query = "UPDATE usuarios SET nombre = %s, usuario = %s, password = %s, rol = %s WHERE id_usuario = %s"
            params = (nombre, usuario, password, rol, self.id_usuario_seleccionado)
        else:
            query = "UPDATE usuarios SET nombre = %s, usuario = %s, rol = %s WHERE id_usuario = %s"
            params = (nombre, usuario, rol, self.id_usuario_seleccionado)

        cursor = self.db.ejecutar_query(query, params)
        if cursor:
            self.mostrar_snack("✅ Usuario actualizado exitosamente", ft.Colors.GREEN_700)
            self.limpiar_formulario()
            self.mostrar_usuarios()

    def eliminar_usuario(self, id_u):
        def confirmar(e):
            self.page_ref.close(dlg)
            self.db.ejecutar_query("DELETE FROM usuarios WHERE id_usuario = %s", (id_u,))
            self.mostrar_snack("✅ Usuario eliminado", ft.Colors.GREEN_700)
            self.mostrar_usuarios()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Deseas eliminar el usuario con ID '{id_u}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_dialogo(dlg)),
                ft.Button(content=ft.Text("Eliminar"), bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
                          on_click=confirmar)
            ]
        )
        self.page_ref.open(dlg)

    def cargar_usuario_en_formulario(self, user):
        self.id_usuario_seleccionado = user['id_usuario']
        self.txt_nombre.value = user['nombre']
        self.txt_usuario.value = user['usuario']
        self.txt_password.value = ""  # Por seguridad dejamos el campo vacio si no se requiere cambiar
        self.dd_rol.value = user['rol']
        if self.page_ref:
            self.page_ref.update()

    def limpiar_formulario(self, e=None):
        self.id_usuario_seleccionado = None
        self.txt_nombre.value = ""
        self.txt_usuario.value = ""
        self.txt_password.value = ""
        self.dd_rol.value = "cajero"
        if self.page_ref:
            self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()

    def cerrar_dialogo(self, dlg):
        self.page_ref.close(dlg)