from typing import TypedDict, Optional, Literal, List

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


Dialog = List[Message]


class RenderObj(TypedDict):
    content: str
    image_base64: Optional[str]
    lang: str
    sender: str


class ImageResult:
    def __init__(self, class_name, plant_name, disease_name: Optional, description: Optional):
        self.class_name = class_name
        self.plant_name = plant_name
        self.disease_name = None if isinstance(disease_name, float) else disease_name
        self.description = None if isinstance(description, float) else description

    def __str__(self) -> str:
        out_str = f"Image contains {self.plant_name.replace('_', ' ').lower()} "
        if self.disease_name is not None:
            disease_name = self.disease_name.replace("_", " ").lower()
            out_str += f"with {disease_name} disease\n"
        else:
            out_str += "without any disease\n"
        if self.description is not None:
            out_str += f"image description: {self.description}\n"
        return out_str
