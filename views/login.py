import flet as ft

class LoginView(ft.Container):
    def __init__(self, page: ft.Page, db, al_ingresar):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.al_ingresar = al_ingresar

        self.txt_usuario = ft.TextField(label="Usuario", width=300)
        self.txt_password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)
        self.lbl_error = ft.Text("", color=ft.Colors.RED_400, size=14)

        def intentar_login(e):
            usuario = self.txt_usuario.value.strip() if self.txt_usuario.value else ""
            password = self.txt_password.value.strip() if self.txt_password.value else ""

            if not usuario or not password:
                self.lbl_error.value = "Por favor, ingresa usuario y contraseña."
                self.page_ref.update()
                return

            # Consulta exacta apuntando a la columna 'usuario' y 'password' de tu tabla
            query = "SELECT id_usuario, nombre, rol FROM usuarios WHERE usuario = %s AND password = %s"
            resultado = self.db.obtener_resultados(query, (usuario, password))

            if resultado:
                usuario_actual = resultado[0]
                self.al_ingresar(usuario_actual)
            else:
                self.lbl_error.value = "Usuario o contraseña incorrectos."
                self.page_ref.update()

        # Estructura centrada del login
        self.content = ft.Container(
            expand=True,
            bgcolor=ft.Colors.GREY_100,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Container(
                                padding=30,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=10,
                                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.GREY_400),
                                content=ft.Column([
                                    ft.Text("Iniciar Sesión - Easy Sale", size=24, weight=ft.FontWeight.BOLD),
                                    self.txt_usuario,
                                    self.txt_password,
                                    self.lbl_error,
                                    ft.ElevatedButton("Ingresar", on_click=intentar_login, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, width=300)
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, tight=True)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True
            )
        )