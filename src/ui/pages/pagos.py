"""Placeholder page for pagos list view."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_pagos_page() -> None:
    @ui.page("/pagos")
    def pagos_page() -> None:
        with AppShell():
            ui.label("Pagos").classes("text-2xl font-bold")
            ui.label("Próximamente — control de pagos.").classes("text-gray-400 mt-2")
