from dataclasses import dataclass


@dataclass
class Slider:
    id: int
    title: str
    subtitle: str | None
    image: str
    link: str | None
    button_text: str | None
    position: int
    is_active: bool
