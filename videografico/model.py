from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal
from uuid import uuid4


ElementKind = Literal["track", "signal", "switch", "label", "block"]
ElementState = Literal["normal", "active", "warning", "alarm", "locked"]
SignalVariant = Literal["with_aux_focus", "without_aux_focus"]
SignalAspect = Literal[
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


@dataclass
class ElementStyle:
    stroke: str = "#E6E6E6"
    fill: str = ""
    text: str = "#E6E6E6"
    width: int = 3


@dataclass
class GraphicElement:
    id: str
    kind: ElementKind
    x: int
    y: int
    w: int = 80
    h: int = 20
    label: str = ""
    state: ElementState = "normal"
    signal_variant: SignalVariant = "without_aux_focus"
    signal_aspect: SignalAspect = "stop"
    rotation: int = 0
    visible: bool = True
    style: ElementStyle = field(default_factory=ElementStyle)

    @staticmethod
    def create(kind: ElementKind, x: int, y: int, label: str = "") -> "GraphicElement":
        defaults = {
            "track": dict(w=120, h=12),
            "signal": dict(w=22, h=34, signal_variant="without_aux_focus", signal_aspect="stop"),
            "switch": dict(w=46, h=28),
            "label": dict(w=110, h=24),
            "block": dict(w=96, h=40),
        }
        return GraphicElement(
            id=str(uuid4()),
            kind=kind,
            x=x,
            y=y,
            label=label or kind.upper(),
            **defaults[kind],
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "GraphicElement":
        style = ElementStyle(**data.get("style", {}))
        base = {k: v for k, v in data.items() if k != "style"}
        return GraphicElement(style=style, **base)


@dataclass
class Diagram:
    name: str = "Videografico"
    width: int = 1280
    height: int = 720
    background: str = "#0B1726"
    grid_size: int = 20
    elements: list[GraphicElement] = field(default_factory=list)

    def add_element(self, kind: ElementKind, x: int, y: int, label: str = "") -> GraphicElement:
        element = GraphicElement.create(kind, x, y, label)
        self.elements.append(element)
        return element

    def get_element(self, element_id: str) -> GraphicElement | None:
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def remove_element(self, element_id: str) -> None:
        self.elements = [element for element in self.elements if element.id != element_id]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "grid_size": self.grid_size,
            "elements": [element.to_dict() for element in self.elements],
        }

    @staticmethod
    def from_dict(data: dict) -> "Diagram":
        return Diagram(
            name=data.get("name", "Videografico"),
            width=data.get("width", 1280),
            height=data.get("height", 720),
            background=data.get("background", "#0B1726"),
            grid_size=data.get("grid_size", 20),
            elements=[GraphicElement.from_dict(item) for item in data.get("elements", [])],
        )
