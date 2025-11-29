from src.pdfqa.utils import structure_pdf_content

def test_structure_basic():
    text = "INTRODUCTION\nThis is an intro.\nSECTION ONE\nContent A\nMore content.\nConclusion\nFinal notes."
    sections = structure_pdf_content(text)
    assert "INTRODUCTION" in sections or "Introduction" in sections
    # ensure some content extracted
    assert any(len(v) > 0 for v in sections.values())
