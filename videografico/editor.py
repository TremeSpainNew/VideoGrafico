from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .model import Diagram, ElementKind
from .render import render_diagram
from .storage import load_diagram, save_diagram


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "nas816_demo.json"
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


class EditorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("VideoGrafico Editor")
        self.diagram = load_diagram(DEFAULT_PATH) if DEFAULT_PATH.exists() else Diagram()
        self.current_path = DEFAULT_PATH
        self.selected_id: str | None = None
        self.current_tool = tk.StringVar(value="select")

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self.root.geometry("1500x900")
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self.root, padding=12)
        sidebar.grid(row=0, column=0, sticky="ns")

        canvas_frame = ttk.Frame(self.root, padding=12)
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text="Herramienta").grid(row=0, column=0, sticky="w")
        tools: list[tuple[str, str]] = [
            ("Seleccionar", "select"),
            ("Vía", "track"),
            ("Señal", "signal"),
            ("Aguja", "switch"),
            ("Bloqueo", "block"),
            ("Texto", "label"),
        ]
        for index, (label, value) in enumerate(tools, start=1):
            ttk.Radiobutton(sidebar, text=label, value=value, variable=self.current_tool).grid(row=index, column=0, sticky="w")

        actions_row = len(tools) + 2
        ttk.Button(sidebar, text="Nuevo", command=self.new_diagram).grid(row=actions_row, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(sidebar, text="Abrir", command=self.open_diagram).grid(row=actions_row + 1, column=0, sticky="ew", pady=4)
        ttk.Button(sidebar, text="Guardar", command=self.save_current).grid(row=actions_row + 2, column=0, sticky="ew", pady=4)
        ttk.Button(sidebar, text="Guardar como", command=self.save_as).grid(row=actions_row + 3, column=0, sticky="ew", pady=4)
        ttk.Button(sidebar, text="Eliminar elemento", command=self.delete_selected).grid(row=actions_row + 4, column=0, sticky="ew", pady=(12, 0))

        props_row = actions_row + 6
        ttk.Label(sidebar, text="Propiedades").grid(row=props_row, column=0, sticky="w", pady=(12, 4))

        self.name_var = tk.StringVar()
        self.x_var = tk.IntVar(value=0)
        self.y_var = tk.IntVar(value=0)
        self.w_var = tk.IntVar(value=0)
        self.h_var = tk.IntVar(value=0)
        self.label_var = tk.StringVar()
        self.state_var = tk.StringVar(value="normal")
        self.signal_variant_var = tk.StringVar(value="without_aux_focus")
        self.signal_aspect_var = tk.StringVar(value="stop")
        self.visible_var = tk.BooleanVar(value=True)

        fields = [
            ("Etiqueta", self.label_var),
            ("X", self.x_var),
            ("Y", self.y_var),
            ("Ancho", self.w_var),
            ("Alto", self.h_var),
        ]
        cursor = props_row + 1
        for field_label, variable in fields:
            ttk.Label(sidebar, text=field_label).grid(row=cursor, column=0, sticky="w")
            ttk.Entry(sidebar, textvariable=variable, width=18).grid(row=cursor + 1, column=0, sticky="ew", pady=(0, 4))
            cursor += 2

        ttk.Label(sidebar, text="Estado").grid(row=cursor, column=0, sticky="w")
        ttk.Combobox(sidebar, textvariable=self.state_var, values=["normal", "active", "warning", "alarm", "locked"], state="readonly").grid(
            row=cursor + 1, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Label(sidebar, text="Variante señal").grid(row=cursor + 2, column=0, sticky="w")
        ttk.Combobox(sidebar, textvariable=self.signal_variant_var, values=SIGNAL_VARIANTS, state="readonly").grid(
            row=cursor + 3, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Label(sidebar, text="Aspecto señal").grid(row=cursor + 4, column=0, sticky="w")
        ttk.Combobox(sidebar, textvariable=self.signal_aspect_var, values=SIGNAL_ASPECTS, state="readonly").grid(
            row=cursor + 5, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Checkbutton(sidebar, text="Visible", variable=self.visible_var).grid(row=cursor + 6, column=0, sticky="w")
        ttk.Button(sidebar, text="Aplicar cambios", command=self.apply_properties).grid(row=cursor + 7, column=0, sticky="ew", pady=(8, 0))

        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(sidebar, textvariable=self.status_var, wraplength=240).grid(row=cursor + 8, column=0, sticky="ew", pady=(12, 0))

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def _refresh(self) -> None:
        render_diagram(self.canvas, self.diagram, self.selected_id)
        self.root.title(f"VideoGrafico Editor - {self.diagram.name}")

    def _hit_test(self, x: int, y: int) -> str | None:
        for element in reversed(self.diagram.elements):
            if element.x <= x <= element.x + element.w and element.y <= y <= element.y + element.h:
                return element.id
        return None

    def on_canvas_click(self, event: tk.Event) -> None:
        x, y = int(event.x), int(event.y)
        tool = self.current_tool.get()
        if tool == "select":
            self.selected_id = self._hit_test(x, y)
            self._load_selected_properties()
            self.status_var.set("Elemento seleccionado" if self.selected_id else "Sin selección")
        else:
            label = f"{tool.upper()}_{len(self.diagram.elements) + 1}"
            element = self.diagram.add_element(tool, x, y, label)
            self.selected_id = element.id
            self._load_selected_properties()
            self.status_var.set(f"Elemento {tool} creado")
        self._refresh()

    def _load_selected_properties(self) -> None:
        element = self.diagram.get_element(self.selected_id) if self.selected_id else None
        if not element:
            self.label_var.set("")
            self.x_var.set(0)
            self.y_var.set(0)
            self.w_var.set(0)
            self.h_var.set(0)
            self.state_var.set("normal")
            self.signal_variant_var.set("without_aux_focus")
            self.signal_aspect_var.set("stop")
            self.visible_var.set(True)
            return
        self.label_var.set(element.label)
        self.x_var.set(element.x)
        self.y_var.set(element.y)
        self.w_var.set(element.w)
        self.h_var.set(element.h)
        self.state_var.set(element.state)
        self.signal_variant_var.set(element.signal_variant)
        self.signal_aspect_var.set(element.signal_aspect)
        self.visible_var.set(element.visible)

    def apply_properties(self) -> None:
        element = self.diagram.get_element(self.selected_id) if self.selected_id else None
        if not element:
            messagebox.showinfo("Sin selección", "Selecciona un elemento para editarlo.")
            return
        element.label = self.label_var.get()
        element.x = self.x_var.get()
        element.y = self.y_var.get()
        element.w = max(10, self.w_var.get())
        element.h = max(10, self.h_var.get())
        element.state = self.state_var.get()
        element.signal_variant = self.signal_variant_var.get()
        element.signal_aspect = self.signal_aspect_var.get()
        element.visible = self.visible_var.get()
        self.status_var.set("Cambios aplicados")
        self._refresh()

    def delete_selected(self) -> None:
        if not self.selected_id:
            return
        self.diagram.remove_element(self.selected_id)
        self.selected_id = None
        self._load_selected_properties()
        self.status_var.set("Elemento eliminado")
        self._refresh()

    def new_diagram(self) -> None:
        self.diagram = Diagram(name="Nuevo videografico")
        self.selected_id = None
        self.current_path = DEFAULT_PATH
        self._load_selected_properties()
        self.status_var.set("Nuevo proyecto creado")
        self._refresh()

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
        self._load_selected_properties()
        self.status_var.set(f"Proyecto cargado: {self.current_path.name}")
        self._refresh()

    def save_current(self) -> None:
        save_diagram(self.diagram, self.current_path)
        self.status_var.set(f"Proyecto guardado en {self.current_path}")

    def save_as(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="Guardar videográfico",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir=str(DEFAULT_PATH.parent),
        )
        if not file_path:
            return
        self.current_path = Path(file_path)
        self.save_current()


def main() -> None:
    root = tk.Tk()
    EditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
