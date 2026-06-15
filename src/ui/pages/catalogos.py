"""Catalogos page — inline-editable view of agents, payment vias, and claim kinds."""

from copy import deepcopy
from uuid import UUID

from nicegui import ui

from src.domain.models.entities import Agent, ClaimKind, PaymentVia
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell


def register_catalogos_page() -> None:
    @ui.page("/catalogos")
    def catalogos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Catálogos").classes("text-2xl font-bold")

            with ui.tabs().classes("mt-4") as tabs:
                ui.tab("Agentes", icon="people")
                ui.tab("Medios de Pago", icon="payments")
                ui.tab("Tipos de Siniestro", icon="category")

            with ui.tab_panels(tabs, value="Agentes").classes("w-full"):
                with ui.tab_panel("Agentes"):
                    _render_tab(container.agent_repo, "agente", Agent)
                with ui.tab_panel("Medios de Pago"):
                    _render_tab(container.payment_via_repo, "medio de pago", PaymentVia)
                with ui.tab_panel("Tipos de Siniestro"):
                    _render_tab(
                        container.claim_kind_repo, "tipo de siniestro", ClaimKind
                    )


def _render_tab(repo, entity_name: str, entity_cls) -> None:
    """Render an inline-editable catalog tab."""

    def _build(name: str):
        """Create a new entity with the given name and defaults."""
        return entity_cls(name=name)

    def _clone_with_name(item, new_name: str):
        """Clone entity with updated name, preserving everything else."""
        kwargs = {"name": new_name}
        for field in entity_cls.model_fields:
            if field == "name":
                continue
            kwargs[field] = deepcopy(getattr(item, field))
        return entity_cls(**kwargs)

    def _entity_id(item):
        for attr in ("agent_id", "payment_via_id", "claim_kind_id"):
            val = getattr(item, attr, None)
            if val is not None:
                return val
        return item.get_id() if hasattr(item, "get_id") else UUID(int=0)

    # ── Create form ──────────────────────────────────────────────────────
    new_input = (
        ui.input(
            label=f"Nuevo {entity_name}",
            placeholder=f"Ingrese nombre del {entity_name}...",
        )
        .props("dense outlined")
        .classes("min-w-[250px]")
    )

    async def _add() -> None:
        name = (new_input.value or "").strip()
        if not name:
            ui.notify("El nombre no puede estar vacío", type="warning")
            return
        if repo.exists({"name": name}):
            ui.notify(f"Ya existe un {entity_name} con ese nombre", type="warning")
            return
        repo.add(_build(name))
        new_input.value = ""
        new_input.update()
        _refresh.refresh()

    with ui.row().classes("items-center gap-2"):
        ui.button("Agregar", icon="add", on_click=_add).props("flat")

    ui.separator().classes("my-2")

    # ── Catalog list ─────────────────────────────────────────────────────
    @ui.refreshable
    def _refresh() -> None:
        items = repo.get_all()
        if not items:
            ui.label("Sin elementos").classes("text-gray-400 italic")
            return

        for item in items:
            eid = _entity_id(item)

            with ui.row().classes("items-center gap-2 w-full py-1"):
                # Inline name editor
                inp = (
                    ui.input(value=item.name)
                    .classes("flex-grow min-w-[200px]")
                    .props("dense outlined")
                )

                async def _save(inp=inp, eid=eid, orig=item.name) -> None:
                    val = (inp.value or "").strip()
                    if not val:
                        ui.notify("El nombre no puede estar vacío", type="warning")
                        inp.value = orig
                        inp.update()
                        return
                    if val != orig and repo.exists({"name": val}):
                        ui.notify(
                            f"Ya existe un {entity_name} con ese nombre",
                            type="warning",
                        )
                        inp.value = orig
                        inp.update()
                        return
                    if val == orig:
                        return
                    existing = repo.get_by_id(eid)
                    if existing is not None:
                        repo.update(eid, _clone_with_name(existing, val))
                    _refresh.refresh()

                inp.on("blur", _save)
                inp.on("keydown.enter", _save)

                # Active/inactive toggle
                sw = ui.switch(value=item.active).props("dense")

                async def _toggle(sw=sw, eid=eid) -> None:
                    if sw.value:
                        repo.activate(eid)
                    else:
                        repo.inactivate(eid)
                    _refresh.refresh()

                sw.on("update:model-value", _toggle)

                # Delete with confirmation dialog
                with ui.dialog() as dlg, ui.card():
                    ui.label(f"¿Eliminar {entity_name}?").classes("text-lg")
                    ui.label(f"¿Está seguro de eliminar '{item.name}'?")
                    with ui.row().classes("gap-2 justify-end mt-2"):
                        ui.button("Cancelar", on_click=dlg.close).props("flat")

                        async def _delete(eid=eid, dlg=dlg) -> None:
                            repo.delete(eid)
                            dlg.close()
                            _refresh.refresh()

                        ui.button("Eliminar", on_click=_delete).props("color=negative")

                ui.button(
                    icon="delete",
                    on_click=dlg.open,
                ).props("flat dense round color=negative")

    _refresh()
