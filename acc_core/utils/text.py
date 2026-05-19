import tiktoken

_ENC = None


def _get_encoder():
    global _ENC
    if _ENC is None:
        _ENC = tiktoken.get_encoding("cl100k_base")
    return _ENC


def estimate_tokens(text: str) -> int:
    return len(_get_encoder().encode(text))


def truncate_xml(xml: str, max_elements: int = 80) -> str:
    """Truncate a UI hierarchy XML to the most relevant elements."""
    import re
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return xml[:8000]

    nodes = []
    for el in root.iter():
        if el.tag == "node":
            text = el.attrib.get("text", "")
            clazz = el.attrib.get("class", "")
            bounds = el.attrib.get("bounds", "")
            clickable = el.attrib.get("clickable", "false") == "true"
            focused = el.attrib.get("focused", "false") == "true"
            visible = el.attrib.get("visible-to-user", "true") != "false"
            score = 0
            if text:
                score += 5
            if clickable:
                score += 3
            if focused:
                score += 10
            if not visible:
                score -= 100
            if clazz:
                score += 1
            nodes.append((el, score))

    nodes.sort(key=lambda x: x[1], reverse=True)
    kept = nodes[:max_elements]

    lines = []
    for el, _score in sorted(kept, key=lambda x: _element_order(x[0])):
        attrs = {
            k: v
            for k, v in el.attrib.items()
            if k in ("text", "class", "bounds", "clickable", "focused", "content-desc", "resource-id")
        }
        lines.append(str(attrs))
    return "\n".join(lines)


def _element_order(el) -> int:
    """Extract z-order position from element bounds for sorting."""
    import re
    bounds = el.attrib.get("bounds", "[0,0][0,0]")
    m = re.match(r"\[(\d+),(\d+)\]", bounds)
    if m:
        return int(m.group(2)) * 10000 + int(m.group(1))
    return 0
