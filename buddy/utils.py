import re

def insert_links(text: str, docs: list) -> str:
    pattern = r"<cite>(\d+)</cite>"
    
    def replace_match(match):
        index = int(match.group(1))
        if 0 <= index < len(docs):
            return f"[{index}]({docs[index]['link']})"
        return ""
    
    return re.sub(pattern, replace_match, text)
