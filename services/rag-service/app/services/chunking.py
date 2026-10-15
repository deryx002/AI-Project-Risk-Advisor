import re
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> List[str]:
    """
    Intelligently splits text into semantic overlapping chunks.
    Preserves paragraph and sentence boundaries wherever possible.
    """
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    # 1. Normalize line endings
    cleaned_text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Split text into primary atomic paragraphs
    paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]

    # If document has no paragraph breaks, split by lines or sentences
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in cleaned_text.split("\n") if p.strip()]

    # Further break down any oversized paragraphs by sentences
    units = []
    for p in paragraphs:
        if len(p) <= chunk_size:
            units.append(p)
        else:
            # Split by sentence terminators
            sentences = re.split(r"(?<=[.!?])\s+", p)
            curr = ""
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if len(curr) + len(s) + 1 <= chunk_size:
                    curr = f"{curr} {s}".strip() if curr else s
                else:
                    if curr:
                        units.append(curr)
                    # If a single sentence exceeds chunk_size, cut with word boundary
                    if len(s) > chunk_size:
                        words = s.split()
                        w_chunk = ""
                        for w in words:
                            if len(w_chunk) + len(w) + 1 <= chunk_size:
                                w_chunk = f"{w_chunk} {w}".strip() if w_chunk else w
                            else:
                                if w_chunk:
                                    units.append(w_chunk)
                                w_chunk = w
                        if w_chunk:
                            units.append(w_chunk)
                        curr = ""
                    else:
                        curr = s
            if curr:
                units.append(curr)

    if not units:
        return []

    # 3. Assemble units into target chunks with specified overlap
    chunks = []
    current_chunk = ""

    for unit in units:
        if not current_chunk:
            current_chunk = unit
        elif len(current_chunk) + len(unit) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{unit}"
        else:
            chunks.append(current_chunk.strip())
            # Calculate overlap from the end of current_chunk
            if overlap > 0 and len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:].strip()
                # Find the first whitespace to avoid half words in overlap
                space_idx = overlap_text.find(" ")
                if space_idx != -1:
                    overlap_text = overlap_text[space_idx:].strip()
                current_chunk = f"{overlap_text}\n\n{unit}" if overlap_text else unit
            else:
                current_chunk = unit

    if current_chunk and (not chunks or chunks[-1] != current_chunk.strip()):
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c.strip()]
