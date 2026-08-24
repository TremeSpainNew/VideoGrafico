from __future__ import annotations

"""
Renderizado de los elementos del videográfico sobre un `tk.Canvas`.

Puntos principales que se pueden tocar en este archivo:

1. Colores genéricos por estado:
   `STATE_COLORS`

2. Aspectos específicos de señales NAS 816:
   `SIGNAL_ASPECTS`

3. Render global del lienzo:
   `draw_grid()` y `render_diagram()`

4. Render por tipo de elemento:
   `render_element()`

5. Geometría detallada de las señales:
   `_render_signal()`

Guía rápida para modificaciones frecuentes:

- Cambiar colores de señales según norma:
  editar `SIGNAL_ASPECTS`

- Añadir un nuevo aspecto de señal:
  crear una nueva entrada en `SIGNAL_ASPECTS` y hacer que el editor/runtime
  la expongan en sus listas de selección

- Cambiar el tamaño visual del símbolo de señal:
  ajustar `w` y `h` por defecto en `model.py` y luego refinar proporciones
  en `_render_signal()`

- Cambiar la silueta de la señal:
  tocar los cálculos `zone2_w`, `zone3_w`, `zone4_bar_w`, `zone4_stem_w`,
  `zone4_stem_h`, `body_size`, `gap`

- Cambiar cómo se representa una vía, aguja o bloqueo:
  tocar el bloque correspondiente dentro de `render_element()`
"""

import tkinter as tk

from .model import Diagram, GraphicElement


# Colores genéricos de trabajo para elementos que usan un estado simple.
# Esto afecta a vías, agujas, bloqueos y al color de texto por defecto.
STATE_COLORS = {
    "normal": dict(stroke="#E6E6E6", fill="", accent="#E6E6E6"),
    "active": dict(stroke="#50FA7B", fill="#163B24", accent="#50FA7B"),
    "warning": dict(stroke="#F1C40F", fill="#4B3B0A", accent="#F1C40F"),
    "alarm": dict(stroke="#FF5C57", fill="#4F1717", accent="#FF5C57"),
    "locked": dict(stroke="#4AA3FF", fill="#132C4B", accent="#4AA3FF"),
}

# Catálogo de aspectos de señal de trabajo inspirado en NAS 816 5.4.1.
#
# Claves de cada aspecto:
# - z1: cabeza de señal
# - z2: foco auxiliar azul/blanco cuando existe
# - z3: cuerpo central
# - z4: pie/brazo izquierdo
# - triangle: si la cabeza se dibuja triangular en lugar de circular
# - flash: aplica tramado para simular aspecto intermitente
# - flash_aux: tramado en cuerpo/foco auxiliar
# - fused_head: fuerza cabeza blanca en algunos casos de foco fundido
#
# Para añadir un aspecto nuevo, lo normal es duplicar uno parecido y cambiar
# zonas y banderas.
SIGNAL_ASPECTS = {
    "no_data": {"z1": "#FF0000", "z2": "#FF0000", "z3": "#FF0000", "z4": "#FF0000", "triangle": False, "flash": True},
    "stop": {"z1": "#FF0000", "z2": "#FF0000", "z3": "#FF0000", "z4": "#FF0000", "triangle": False},
    "white": {"z1": "#FFFFFF", "z2": None, "z3": "#FFFFFF", "z4": "#FFFFFF", "triangle": False},
    "white_fused": {"z1": "#FFFFFF", "z2": None, "z3": "#FF0000", "z4": "#FF0000", "triangle": True, "flash": True},
    "dark_fused": {"z1": "#9A9A9A", "z2": None, "z3": "#9A9A9A", "z4": "#9A9A9A", "triangle": False},
    "red_fused": {"z1": "#FF0000", "z2": "#FF0000", "z3": "#FF0000", "z4": "#FF0000", "triangle": False, "fused_head": True},
    "announce_stop": {"z1": "#FFD400", "z2": None, "z3": "#FFD400", "z4": "#FFD400", "triangle": False},
    "yellow_fused": {"z1": "#FF0000", "z2": None, "z3": "#FFD400", "z4": "#FFD400", "triangle": True, "flash": True},
    "announce_caution": {"z1": "#00FF00", "z2": None, "z3": "#FFD400", "z4": "#FFD400", "triangle": False},
    "clear": {"z1": "#00FF00", "z2": None, "z3": "#00FF00", "z4": "#00FF00", "triangle": False},
    "conditional_clear": {"z1": "#00FF00", "z2": None, "z3": "#00FF00", "z4": "#00FF00", "triangle": False, "flash": True},
    "green_fused": {"z1": "#FF0000", "z2": None, "z3": "#00FF00", "z4": "#00FF00", "triangle": True, "flash": True},
    "rebase_maneuver": {"z1": "#FF0000", "z2": "#FFFFFF", "z3": "#FFFFFF", "z4": "#FF0000", "triangle": False},
    "rebase_authorized": {"z1": "#FF0000", "z2": "#FFFFFF", "z3": "#FFFFFF", "z4": "#FF0000", "triangle": False, "flash_aux": True},
    "selective_stop_n2": {"z1": "#FF0000", "z2": "#2D8CFF", "z3": "#2D8CFF", "z4": "#FF0000", "triangle": False},
    "selective_stop_n1_n2": {"z1": "#FF0000", "z2": "#2D8CFF", "z3": "#2D8CFF", "z4": "#FF0000", "triangle": False, "flash_aux": True},
}


def _shape_kwargs(spec: dict, key: str) -> dict:
    """Devuelve opciones extra de dibujo para simular parpadeo con tramado."""
    kwargs = {}
    if spec.get(key):
        kwargs["stipple"] = "gray50"
    return kwargs


def draw_grid(canvas: tk.Canvas, diagram: Diagram) -> None:
    """Dibuja la retícula base del editor/runtime."""
    grid = diagram.grid_size
    for x in range(0, diagram.width + 1, grid):
        canvas.create_line(x, 0, x, diagram.height, fill="#132235")
    for y in range(0, diagram.height + 1, grid):
        canvas.create_line(0, y, diagram.width, y, fill="#132235")


def render_diagram(canvas: tk.Canvas, diagram: Diagram, selected_id: str | None = None) -> None:
    """Redibuja por completo el videográfico en el canvas."""
    canvas.delete("all")
    canvas.configure(bg=diagram.background, width=diagram.width, height=diagram.height)
    draw_grid(canvas, diagram)
    for element in diagram.elements:
        if element.visible:
            render_element(canvas, element, selected=(element.id == selected_id))


def _style_for(element: GraphicElement) -> dict:
    """Resuelve el estilo final de un elemento a partir de su estado y overrides."""
    state_style = STATE_COLORS.get(element.state, STATE_COLORS["normal"])
    stroke = element.style.stroke if element.style.stroke else state_style["stroke"]
    fill = element.style.fill if element.style.fill else state_style["fill"]
    text = element.style.text if element.style.text else state_style["accent"]
    return {"stroke": stroke, "fill": fill, "text": text}


def render_element(canvas: tk.Canvas, element: GraphicElement, selected: bool = False) -> None:
    """
    Dibuja un elemento individual.

    Sitios típicos para tocar:
    - `track`: grosor y proporción de la banda del CV
    - `switch`: geometría de la aguja
    - `block`: marco, flechas y estados del bloqueo
    - `signal`: delega en `_render_signal()`
    """
    style = _style_for(element)
    x1, y1 = element.x, element.y
    x2, y2 = element.x + element.w, element.y + element.h
    dash = (4, 4) if selected else None
    selection = "#FFFFFF" if selected else style["stroke"]

    if element.kind == "track":
        # NAS 816 representa el CV como una banda rectangular sobre fondo negro.
        # `inset` controla el grosor de la banda útil dentro del bloque negro.
        canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="#000000")
        inset = max(2, int(element.h * 0.18))
        canvas.create_rectangle(x1, y1 + inset, x2, y2 - inset, fill=style["stroke"], outline=style["stroke"])
        if element.label:
            canvas.create_text((x1 + x2) / 2, y1 - 10, text=element.label, fill=style["text"], font=("Helvetica", 10))
        if selected:
            canvas.create_rectangle(x1 - 4, y1 - 4, x2 + 4, y2 + 4, outline="#FFFFFF", dash=dash)

    elif element.kind == "signal":
        _render_signal(canvas, element, selected, style, dash, selection)

    elif element.kind == "switch":
        # Geometría segmentada inspirada en la figura 13 de la NAS 816.
        # Si quieres una aguja más abierta o más compacta, toca `join_x`, `seg`
        # y la línea oblicua.
        base_y = y2 - max(8, int(element.h * 0.22))
        join_x = x1 + max(14, int(element.w * 0.40))
        seg = max(12, int(element.w * 0.22))
        canvas.create_line(x1, base_y, join_x, base_y, fill=selection, width=3, dash=dash)
        canvas.create_line(join_x, base_y, x2, base_y, fill=selection, width=3, dash=dash)
        canvas.create_line(join_x, base_y, x2 - 6, y1 + 6, fill=selection, width=3, dash=dash)
        canvas.create_line(join_x - 8, base_y, join_x - 8, base_y - 10, fill="#E6E6E6", width=2)
        for marker_x in (x1 + seg, join_x, join_x + seg):
            canvas.create_line(marker_x, base_y - 6, marker_x, base_y + 6, fill=selection, width=1)
        canvas.create_text(x1, y2 + 10, text=element.label, anchor="w", fill=style["text"], font=("Helvetica", 10))

    elif element.kind == "label":
        canvas.create_text(x1, y1, text=element.label, anchor="nw", fill=style["text"], font=("Helvetica", 12, "bold"))
        if selected:
            canvas.create_rectangle(x1 - 4, y1 - 4, x1 + element.w, y1 + element.h, outline="#FFFFFF", dash=(4, 4))

    elif element.kind == "block":
        # NAS 816: recuadro blanco con interior activo y flechas de estado.
        # `inset` controla el margen entre marco exterior e interior.
        canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="#FFFFFF" if selected else "#E6E6E6", width=2, dash=dash)
        inset = 7
        canvas.create_rectangle(x1 + inset, y1 + inset, x2 - inset, y2 - inset, fill="#000000", outline=selection, width=2)
        state = element.state
        if state in {"active", "warning", "alarm"}:
            arrow_color = {"active": "#00FF00", "warning": "#FF0000", "alarm": "#FF0000"}[state]
            arrow_points = [
                x2 - inset - 18,
                y1 + inset + 6,
                x2 - inset - 18,
                y2 - inset - 6,
                x2 - inset - 4,
                (y1 + y2) / 2,
            ]
            canvas.create_polygon(arrow_points, fill=arrow_color, outline=arrow_color)
        elif state == "locked":
            canvas.create_rectangle(x1 + inset, y1 + inset, x2 - inset, y2 - inset, fill="#FFFFFF", outline=selection, width=2)
        canvas.create_text((x1 + x2) / 2, y2 + 12, text=element.label, fill=style["text"], font=("Helvetica", 10, "bold"))

    if selected and element.kind != "label":
        canvas.create_rectangle(x1 - 4, y1 - 4, x2 + 4, y2 + 4, outline="#FFFFFF", dash=(4, 4))


def _render_signal(
    canvas: tk.Canvas,
    element: GraphicElement,
    selected: bool,
    style: dict,
    dash: tuple[int, int] | None,
    selection: str,
) -> None:
    """
    Dibuja la señal NAS 816 de salida/entrada/trayecto.

    Composición visual actual:
    - zona 4: poste/brazo izquierdo
    - zona 3: cuerpo principal
    - zona 2: foco auxiliar, solo si `signal_variant == with_aux_focus`
    - zona 1: cabeza circular o triangular
    - zona 5: recuadro exterior auxiliar para GRP/ARS

    Parámetros geométricos más importantes:
    - `pad`: margen interior total del icono
    - `body_size`: tamaño base del cuerpo y de la cabeza
    - `zone2_w`: ancho del foco auxiliar
    - `zone3_w`: ancho del cuerpo central
    - `zone4_bar_w`: longitud del brazo izquierdo
    - `zone4_stem_w`: ancho del poste izquierdo
    - `zone4_stem_h`: alto del poste izquierdo
    - `gap`: separación entre zonas

    Si el icono se ve demasiado grande o pequeño:
    - primero cambia el tamaño del elemento en `model.py`
    - después ajusta aquí `pad` y `body_size`

    Si la silueta no coincide con la norma:
    - toca los anchos/altos `zone*`
    - no cambies `SIGNAL_ASPECTS` para eso; esa tabla es solo color/estado
    """
    x1, y1 = element.x, element.y
    x2, y2 = element.x + element.w, element.y + element.h
    spec = SIGNAL_ASPECTS.get(element.signal_aspect, SIGNAL_ASPECTS["stop"])
    aux_visible = element.signal_variant == "with_aux_focus"

    canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="")

    z1 = spec["z1"]
    z2 = spec["z2"] if aux_visible else None
    z3 = spec["z3"]
    z4 = spec["z4"]

    # Escala general del icono dentro de su caja.
    # Subir `pad` lo hace visualmente más pequeño.
    pad = 5
    total_h = max(20, element.h - 2 * pad)
    # Tamaño base de la cabeza y del cuerpo.
    body_size = max(12, int(total_h * 0.48))
    body_y = y1 + (element.h - body_size) / 2

    head_d = body_size
    head_y = body_y

    # Proporciones internas de cada zona del símbolo.
    zone2_w = max(0, int(body_size * 0.46)) if aux_visible else 0
    zone3_w = max(10, int(body_size * 0.74))
    zone4_bar_w = max(10, int(body_size * 0.95))
    zone4_stem_w = max(4, int(body_size * 0.22))
    zone4_stem_h = max(10, int(body_size * 0.82))
    gap = 2

    content_w = zone4_bar_w + gap + zone3_w + (gap + zone2_w if aux_visible else 0) + gap + head_d
    start_x = x1 + max(4, int((element.w - content_w) / 2))

    # Zona 4: pie/poste izquierdo en horizontal, como en la tabla del 5.4.1
    zone4_y = y1 + (element.h - zone4_stem_h) / 2
    stem_x = start_x
    arm_y = zone4_y + (zone4_stem_h - zone4_stem_w) / 2
    canvas.create_rectangle(
        stem_x,
        zone4_y,
        stem_x + zone4_stem_w,
        zone4_y + zone4_stem_h,
        fill=z4 or "#000000",
        outline=selection,
        width=2,
        **_shape_kwargs(spec, "flash"),
    )
    canvas.create_rectangle(
        stem_x + zone4_stem_w,
        arm_y,
        stem_x + zone4_bar_w,
        arm_y + zone4_stem_w,
        fill=z4 or "#000000",
        outline=selection,
        width=2,
        **_shape_kwargs(spec, "flash"),
    )

    # Zona 3: cuerpo principal
    zone3_x = stem_x + zone4_bar_w + gap
    canvas.create_rectangle(
        zone3_x,
        body_y,
        zone3_x + zone3_w,
        body_y + body_size,
        fill=z3 or "#000000",
        outline=selection,
        width=2,
        **_shape_kwargs(spec, "flash_aux"),
    )

    # Zona 2: foco azul/blanco intermedio
    head_x = zone3_x + zone3_w + gap
    if aux_visible:
        canvas.create_rectangle(
            head_x,
            body_y,
            head_x + zone2_w,
            body_y + body_size,
            fill=z2 or "#000000",
            outline=selection,
            width=2,
            **_shape_kwargs(spec, "flash_aux"),
        )
        head_x += zone2_w + gap

    # Zona 1: cabeza circular o triangular
    if spec["triangle"]:
        canvas.create_polygon(
            head_x,
            head_y + head_d,
            head_x + head_d,
            head_y + head_d,
            head_x + head_d / 2,
            head_y,
            fill=z1 or "#000000",
            outline=selection,
            width=2,
            **_shape_kwargs(spec, "flash"),
        )
    else:
        canvas.create_oval(
            head_x,
            head_y,
            head_x + head_d,
            head_y + head_d,
            fill=("#FFFFFF" if spec.get("fused_head") else (z1 or "#000000")),
            outline=selection,
            width=2,
            **_shape_kwargs(spec, "flash"),
        )

    # Zona 5: recuadro auxiliar para GRP/ARS.
    # Hoy se reaprovecha `element.state`:
    # - `locked` -> recuadro amarillo
    # - `active` -> recuadro azul
    #
    # Si luego quieres fidelidad completa con refs. 87/88, lo ideal es sacar
    # esta información a un atributo propio del modelo de señal.
    if element.state == "locked":
        canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, outline="#FFD400", width=2)
    elif element.state == "active":
        canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, outline="#2D8CFF", width=2)

    canvas.create_text(x1, y2 + 8, text=element.label, anchor="w", fill=style["text"], font=("Helvetica", 10))

    if selected:
        canvas.create_rectangle(x1 - 4, y1 - 4, x2 + 4, y2 + 4, outline="#FFFFFF", dash=dash)
