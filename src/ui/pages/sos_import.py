"""SOS Import dialog — upload Excel, preview rows, confirm import, show results."""

from collections.abc import Callable

from nicegui import ui

from src.application.services.excel_parser import ParsedRow, parse_excel
from src.infrastructure.container import get_container


def importar_gestiones_dialog(on_success: Callable[[], None] | None = None) -> None:
    """Open a dialog to import SOS claims from an Excel file.

    Args:
        on_success: Optional callback invoked after successful import.
    """

    with ui.dialog() as dlg, ui.card().classes("w-[800px] max-w-full"):
        ui.label("Importar Gestiones SOS").classes("text-2xl font-bold mb-4")

        parsed_rows: list[ParsedRow] = []
        preview_area = ui.column().classes("w-full")
        result_area = ui.column().classes("w-full")

        async def handle_upload(e) -> None:
            nonlocal parsed_rows
            result_area.clear()

            name = e.file.name or ""
            if not name.lower().endswith(".xlsx"):
                ui.notify(
                    "Formato no soportado. Seleccione un archivo .xlsx.",
                    type="negative",
                )
                return

            content = await e.file.read()
            try:
                parsed_rows = parse_excel(content)
            except ValueError as exc:
                ui.notify(str(exc), type="negative")
                return
            except Exception as exc:
                ui.notify(f"Error al leer el archivo: {exc}", type="negative")
                return

            if not parsed_rows:
                ui.notify(
                    "No se encontraron filas con datos en el archivo.",
                    type="warning",
                )
                return

            _render_preview(parsed_rows, preview_area)
            import_btn.set_visibility(True)
            ui.notify(
                f"Se parsearon {len(parsed_rows)} filas correctamente.",
                type="positive",
            )

        ui.upload(
            label="Seleccionar archivo .xlsx",
            on_upload=handle_upload,
            auto_upload=True,
            max_file_size=10_000_000,
        ).props("accept=.xlsx").classes("w-full max-w-md")

        async def do_import() -> None:
            if not parsed_rows:
                return

            import_btn.set_visibility(False)
            import_btn.disable()

            container = get_container()
            use_case = container.importar_gestiones_sos
            result = use_case.execute(parsed_rows)

            _render_results(result, result_area)
            ui.notify("Importación finalizada.", type="positive")

            if on_success:
                on_success()

        import_btn = ui.button(
            "Importar",
            icon="cloud_upload",
            on_click=do_import,
        ).props('color="positive"')
        import_btn.set_visibility(False)

        with ui.row().classes("gap-2 justify-end mt-4"):
            ui.button("Cerrar", on_click=dlg.close).props("flat")

    dlg.open()


# ── Rendering helpers ─────────────────────────────────────────────────────────


def _render_preview(rows: list[ParsedRow], area: ui.column) -> None:
    area.clear()
    with area:
        ui.label(f"Vista previa — {len(rows)} filas").classes(
            "text-lg font-semibold mt-4 mb-2"
        )

        columns = [
            {"name": "gestion", "label": "N° Gestión", "field": "gestion", "sortable": True},
            {"name": "fecha", "label": "Fecha", "field": "fecha", "sortable": True},
            {"name": "asegurado", "label": "Asegurado", "field": "asegurado", "sortable": True},
            {"name": "poliza", "label": "Póliza", "field": "poliza", "sortable": True},
            {"name": "patente", "label": "Patente", "field": "patente", "sortable": True},
            {"name": "categoria", "label": "Categoría", "field": "categoria", "sortable": True},
            {"name": "motivo", "label": "Motivo", "field": "motivo", "sortable": True},
            {"name": "estado", "label": "Estado", "field": "estado", "sortable": True},
            {"name": "carga", "label": "Carga", "field": "carga", "sortable": True},
            {"name": "responde", "label": "Responde", "field": "responde", "sortable": True},
            {"name": "itr", "label": "ITR", "field": "itr", "sortable": True},
        ]

        rows_data = [
            {
                "gestion": r.gestion,
                "fecha": r.created_at.isoformat() if r.created_at else "",
                "asegurado": r.claimer_name,
                "poliza": r.policy_number,
                "patente": r.plate,
                "categoria": r.category,
                "motivo": r.reason,
                "estado": r.status,
                "carga": r.load_user,
                "responde": r.response_user,
                "itr": r.itr,
            }
            for r in rows
        ]

        ui.table(columns=columns, rows=rows_data).classes("w-full")


def _render_results(result, area: ui.column) -> None:
    area.clear()
    with area:
        with ui.card().classes("w-full p-4 mt-4"):
            ui.label("Resultado de la Importación").classes("text-xl font-bold")

            with ui.row().classes("gap-4 mt-2"):
                ui.label(f"Creados: {result.created}").classes(
                    "text-green-400 font-semibold"
                )
                ui.label(f"Actualizados: {result.updated}").classes(
                    "text-blue-400 font-semibold"
                )
                ui.label(f"Errores: {len(result.errors)}").classes(
                    "text-red-400 font-semibold"
                )

            if result.errors:
                ui.label("Detalle de errores:").classes("text-lg font-bold mt-4")
                columns = [
                    {"name": "row", "label": "Fila", "field": "row", "sortable": True},
                    {"name": "gestion", "label": "Gestión", "field": "gestion", "sortable": True},
                    {"name": "error", "label": "Error", "field": "error", "sortable": True},
                ]
                rows_data = [
                    {
                        "row": e.row_index + 2,
                        "gestion": str(e.gestion) if e.gestion is not None else "-",
                        "error": e.message,
                    }
                    for e in result.errors
                ]
                ui.table(columns=columns, rows=rows_data).classes("w-full")
