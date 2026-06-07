from nicegui import app, ui

from src.infrastructure.container import get_container


def register_register_page() -> None:
    @ui.page("/register")
    def register_page() -> None:
        if app.storage.user.get("token"):
            ui.navigate.to("/")
            return

        ui.query("body").classes("bg-gray-100")

        with ui.column().classes("absolute-center items-center gap-0 w-full"):
            with ui.card().classes("w-96 shadow-xl rounded-2xl p-8 gap-4"):
                # Header
                with ui.column().classes("items-center gap-1 mb-2"):
                    ui.icon("person_add", size="3rem", color="blue-7")
                    ui.label("Gestiones SOS").classes(
                        "text-2xl font-bold text-blue-800"
                    )
                    ui.label("Crear nueva cuenta").classes("text-sm text-gray-500")

                ui.separator()

                # Form
                username_input = (
                    ui.input(
                        label="Nombre de usuario",
                        placeholder="minombre",
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                email_input = (
                    ui.input(
                        label="Correo electrónico",
                        placeholder="usuario@ejemplo.com",
                    )
                    .props("type=email outlined dense")
                    .classes("w-full")
                )

                password_input = (
                    ui.input(
                        label="Contraseña",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                password_confirm_input = (
                    ui.input(
                        label="Confirmar contraseña",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                error_label = ui.label("").classes("text-red-600 text-sm hidden")
                success_label = ui.label("").classes("text-green-600 text-sm hidden")

                def do_register() -> None:
                    error_label.classes(add="hidden")
                    success_label.classes(add="hidden")

                    user_name = username_input.value.strip()
                    email = email_input.value.strip()
                    password = password_input.value
                    password_confirm = password_confirm_input.value

                    if not all([user_name, email, password, password_confirm]):
                        error_label.set_text("Completá todos los campos.")
                        error_label.classes(remove="hidden")
                        return

                    if len(user_name) < 3:
                        error_label.set_text(
                            "El nombre de usuario debe tener al menos 3 caracteres."
                        )
                        error_label.classes(remove="hidden")
                        return

                    if password != password_confirm:
                        error_label.set_text("Las contraseñas no coinciden.")
                        error_label.classes(remove="hidden")
                        return

                    if len(password) < 6:
                        error_label.set_text(
                            "La contraseña debe tener al menos 6 caracteres."
                        )
                        error_label.classes(remove="hidden")
                        return

                    try:
                        container = get_container()
                        container.auth_router.register(user_name, email, password)
                        success_label.set_text(
                            "¡Cuenta creada! Redirigiendo al login..."
                        )
                        success_label.classes(remove="hidden")
                        ui.timer(1.5, lambda: ui.navigate.to("/login"), once=True)
                    except ValueError as e:
                        error_label.set_text(str(e))
                        error_label.classes(remove="hidden")

                password_confirm_input.on("keydown.enter", lambda _: do_register())

                ui.button("Registrarse", on_click=do_register, icon="person_add").props(
                    "unelevated color=blue-7"
                ).classes("w-full mt-2")

                ui.separator()

                with ui.row().classes(
                    "items-center justify-center gap-1 text-sm text-gray-500"
                ):
                    ui.label("¿Ya tenés cuenta?")
                    ui.link("Iniciá sesión", "/login").classes(
                        "text-blue-700 font-medium no-underline hover:underline"
                    )
