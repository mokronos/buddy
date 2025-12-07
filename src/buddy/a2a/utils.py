from a2a.types import Part, TextPart

def simple_text_part(text: str) -> Part:
    return Part(root=TextPart(text=text))
