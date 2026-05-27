from pydantic import BaseModel, ConfigDict


class SliderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    subtitle: str | None
    image: str
    link: str | None
    button_text: str | None
    position: int


class SliderCreateSchema(BaseModel):
    title: str
    subtitle: str | None = None
    image: str
    link: str | None = None
    button_text: str | None = None
    position: int = 0
    is_active: bool = True


class SliderUpdateSchema(BaseModel):
    title: str
    subtitle: str | None = None
    image: str
    link: str | None = None
    button_text: str | None = None
    position: int = 0
    is_active: bool = True


class SliderReorderSchema(BaseModel):
    position: int
