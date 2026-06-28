"""Reusable UI components for table refactoring."""

from enum import Enum

from nicegui import ui


class BadgeColor(str, Enum):
    """Standard color palette for status badges."""
    GREEN = 'bg-green-600'
    RED = 'bg-red-600'
    YELLOW = 'bg-yellow-600'
    BLUE = 'bg-blue-600'
    GRAY = 'bg-gray-600'
    ORANGE = 'bg-orange-600'
    PURPLE = 'bg-purple-600'


def Badge(
    text: str,
    color: BadgeColor = BadgeColor.GRAY,
    size: str = 'text-xs'
) -> ui.label:
    """
    Render a status badge with consistent styling.
    
    Args:
        text: Badge label text
        color: BadgeColor enum value
        size: Tailwind text size class
    
    Returns:
        ui.label configured as badge
    """
    return ui.label(text).classes(
        f'{size} font-bold px-2 py-0.5 rounded-full {color.value} text-white text-center'
    )


def ActionButton(
    icon: str,
    label: str = '',
    on_click=None,
    color: str = '',
    disabled: bool = False,
    tooltip_position: str = 'top'
) -> ui.button:
    """
    Render a consistent action button (edit, delete, toggle, etc.).
    
    Args:
        icon: Material Design icon name
        label: Optional tooltip label
        on_click: Click handler function
        color: Optional color class (e.g., 'text-red-500')
        disabled: Disable button if True
        tooltip_position: Position of tooltip
    
    Returns:
        ui.button configured as action button
    """
    btn = ui.button(icon=icon, on_click=on_click)
    btn.props('flat dense round size=sm')
    if color:
        btn.classes(color)
    if label:
        btn.tooltip(label)
        if tooltip_position != 'top':
            btn.props(f'position={tooltip_position}')
    if disabled:
        btn.enabled = False
    return btn
