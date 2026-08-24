from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from .model import Diagram
from .render import render_diagram
from .storage import load_diagram


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "nas816_demo.json"
STATES = ["normal", "active", "warning", "alarm", "locked"]
SIGNAL_VARIANTS = ["without_aux_focus", "with_aux_focus"]
SIGNAL_ASPECTS = [
    "no_data",
    "stop",
    "white",
    "white_fused",
    "dark_fused",
    "red_fused",
    "announce_stop",
    "yellow_fused",
    "announce_caution",
    "clear",
    "conditional_clear",
    "green_fused",
    "rebase_maneuver",
    "rebase_authorized",
    "selective_stop_n2",
    "selective_stop_n1_n2",
]


class RuntimeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("VideoGrafico Explotación")
        self.diagram = load_diagram(DEFAULT_PATH) if DEFAULT_PATH.exists() else Diagram()
        self.current_path = DEFAULT_PATH
        self.selected_id: str | None = None

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self.root.geometry("1500x900")
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        panel = ttk.Frame(self.root, padding=12)
        panel.grid(row=0, column=0, sticky="ns")

        canvas_frame = ttk.Frame(self.root, padding=12)
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        ttk.Button(panel, text="Abrir proyecto", command=self.open_diagram).grid(row=0, column=0, sticky="ew")
        ttk.Label(panel, text="Elementos").grid(row=1, column=0, sticky="w", pady=(12, 4))

        self.listbox = tk.Listbox(panel, width=32, height=24)
        self.listbox.grid(row=2, column=0, sticky="ns")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        ttk.Label(panel, text="Estado operativo").grid(row=3, column=0, sticky="w", pady=(12, 4))
        self.state_var = tk.StringVar(value="normal")
        ttk.Combobox(panel, textvariable=self.state_var, values=STATES, state="readonly").grid(row=4, column=0, sticky="ew")
        ttk.Button(panel, text="Aplicar estado", command=self.apply_state).grid(row=5, column=0, sticky="ew", pady=(8, 0))

        ttk.Label(panel, text="Variante señal").grid(row=6, column=0, sticky="w", pady=(12, 4))
        self.signal_variant_var = tk.StringVar(value="without_aux_focus")
        ttk.Combobox(panel, textvariable=self.signal_variant_var, values=SIGNAL_VARIANTS, state="readonly").grid(row=7, column=0, sticky="ew")
        ttk.Label(panel, text="Aspecto señal").grid(row=8, column=0, sticky="w", pady=(12, 4))
        self.signal_aspect_var = tk.StringVar(value="stop")
        ttk.Combobox(panel, textvariable=self.signal_aspect_var, values=SIGNAL_ASPECTS, state="readonly").grid(row=9, column=0, sticky="ew")
        ttk.Button(panel, text="Aplicar señal", command=self.apply_signal_config).grid(row=10, column=0, sticky="ew", pady=(8, 0))

        ttk.Label(panel, text="Acciones rápidas").grid(row=11, column=0, sticky="w", pady=(12, 4))
        ttk.Button(panel, text="Normalizar todo", command=self.normalize_all).grid(row=12, column=0, sticky="ew")
        ttk.Button(panel, text="Simular alarma", command=lambda: self.apply_quick_state("alarm")).grid(row=13, column=0, sticky="ew", pady=4)
        ttk.Button(panel, text="Simular ruta", command=lambda: self.apply_quick_state("active")).grid(row=14, column=0, sticky="ew")

        self.info_var = tk.StringVar(value="Carga un videográfico y selecciona un elemento.")
        ttk.Label(panel, textvariable=self.info_var, wraplength=240).grid(row=15, column=0, sticky="ew", pady=(12, 0))

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def _refresh(self) -> None:
        self._reload_list()
        render_diagram(self.canvas, self.diagram, self.selected_id)
        self.root.title(f"VideoGrafico Explotación - {self.diagram.name}")

    def _reload_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for element in self.diagram.elements:
            self.listbox.insert(tk.END, f"{element.kind}: {element.label} [{element.state}]")

    def _select_index(self, index: int) -> None:
        if index < 0 or index >= len(self.diagram.elements):
            return
        self.selected_id = self.diagram.elements[index].id
        self.state_var.set(self.diagram.elements[index].state)
        self.signal_variant_var.set(self.diagram.elements[index].signal_variant)
        self.signal_aspect_var.set(self.diagram.elements[index].signal_aspect)
        self.info_var.set(f"Seleccionado: {self.diagram.elements[index].label}")
        self._refresh()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)

    def _index_from_id(self, element_id: str | None) -> int | None:
        if not element_id:
            return None
        for index, element in enumerate(self.diagram.elements):
            if element.id == element_id:
                return index
        return None

    def open_diagram(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Abrir videográfico",
            filetypes=[("JSON", "*.json")],
            initialdir=str(DEFAULT_PATH.parent),
        )
        if not file_path:
            return
        self.diagram = load_diagram(file_path)
        self.current_path = Path(file_path)
        self.selected_id = None
        self.info_var.set(f"Proyecto cargado: {self.current_path.name}")
        self._refresh()

    def on_select(self, _event: tk.Event) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self._select_index(selection[0])

    def on_canvas_click(self, event: tk.Event) -> None:
        x, y = int(event.x), int(event.y)
        for index, element in enumerate(reversed(self.diagram.elements)):
            if element.x <= x <= element.x + element.w and element.y <= y <= element.y + element.h:
                real_index = len(self.diagram.elements) - 1 - index
                self._select_index(real_index)
                return

    def apply_state(self) -> None:
        element = self.diagram.get_element(self.selected_id) if self.selected_id else None
        if not element:
            self.info_var.set("Selecciona un elemento.")
            return
        element.state = self.state_var.get()
        self.info_var.set(f"Estado aplicado a {element.label}: {element.state}")
        self._refresh()

    def apply_signal_config(self) -> None:
        element = self.diagram.get_element(self.selected_id) if self.selected_id else None
        if not element:
            self.info_var.set("Selecciona un elemento.")
            return
        if element.kind != "signal":
            self.info_var.set("El elemento seleccionado no es una señal.")
            return
        element.signal_variant = self.signal_variant_var.get()
        element.signal_aspect = self.signal_aspect_var.get()
        self.info_var.set(f"Señal actualizada: {element.label} -> {element.signal_aspect}")
        self._refresh()

    def apply_quick_state(self, state: str) -> None:
        element = self.diagram.get_element(self.selected_id) if self.selected_id else None
        if not element:
            self.info_var.set("Selecciona un elemento.")
            return
        element.state = state
        self.state_var.set(state)
        self.info_var.set(f"Estado rápido aplicado a {element.label}: {state}")
        self._refresh()

    def normalize_all(self) -> None:
        for element in self.diagram.elements:
            element.state = "normal"
        self.info_var.set("Todos los elementos han vuelto a estado normal.")
        self._refresh()


def main() -> None:
    root = tk.Tk()
    RuntimeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
