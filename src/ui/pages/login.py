from nicegui import app, ui

from src.infrastructure.container import get_container


def register_login_page() -> None:
    @ui.page("/login")
    def login_page() -> None:
        if app.storage.user.get("token"):
            ui.navigate.to("/")
            return

        ui.query("body").classes("bg-gray-100")

        with ui.column().classes("absolute-center items-center gap-0 w-full"):
            # Card
            with ui.card().classes("w-96 shadow-xl rounded-2xl p-8 gap-4"):
                # Header
                with ui.column().classes("items-center gap-1 mb-2"):
                    ui.icon("local_police", size="3rem", color="blue-7")
                    ui.label("Gestiones SOS").classes(
                        "text-2xl font-bold text-blue-800"
                    )
                    ui.label("Ingresá a tu cuenta").classes("text-sm text-gray-500")

                ui.separator()

                # Form
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

                error_label = ui.label("").classes("text-red-600 text-sm hidden")

                def do_login() -> None:
                    error_label.classes(remove="hidden")
                    email = email_input.value.strip()
                    password = password_input.value

                    if not email or not password:
                        error_label.set_text("Completá todos los campos.")
                        return

                    try:
                        container = get_container()
                        result = container.auth_router.login(email, password)
                        app.storage.user.update(
                            {
                                "token": result.token,
                                "user_id": result.user_id,
                                "user_name": result.user_name,
                                "user_email": result.user_email,
                            }
                        )
                        ui.navigate.to("/")
                    except ValueError as e:
                        error_label.set_text(str(e))

                password_input.on("keydown.enter", lambda _: do_login())

                ui.button("Ingresar", on_click=do_login, icon="login").props(
                    "unelevated color=blue-7"
                ).classes("w-full mt-2")

                ui.separator()

                with ui.row().classes(
                    "items-center justify-center gap-1 text-sm text-gray-500"
                ):
                    ui.label("¿No tenés cuenta?")
                    ui.link("Registrate", "/register").classes(
                        "text-blue-700 font-medium no-underline hover:underline"
                    )
