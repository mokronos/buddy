from typing import Any

from a2a.types import DataPart, Part, TextPart


def simple_text_part(text: str) -> Part:
    return Part(root=TextPart(text=text))


def simple_data_part(data: dict[str, Any]) -> Part:
    return Part(root=DataPart(data=data))
