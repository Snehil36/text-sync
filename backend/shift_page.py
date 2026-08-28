import pymupdf
import re
 
 
def get_level(title):
    """
    Detects the hierarchy level of a TOC entry from its numbering prefix.
 
    Examples:
        "1 The Foundations"        → level 1  (no dots)
        "1.1 Propositional Logic"  → level 2  (one dot)
        "1.1.1 Some Subsection"    → level 3  (two dots)
        "Preface"                  → level 1  (no number prefix, default)
    """
    match = re.match(r'^(\d+(\.\d+)*)', title.strip())
    if match:
        dots = match.group(1).count(".")
        return dots + 1
    return 1  # default to top level if no number prefix found
 
 
def apply_toc_metadata(pdf_path, offset, toc, output_path="corrected_output.pdf"):
    """
    Writes a new PDF where the built-in bookmark/outline tree (the clickable
    TOC visible in any PDF viewer's sidebar) is populated with the correct
    chapter and section titles mapped to their true PDF page numbers.
 
    Levels are inferred automatically from the numbering prefix in each title
    (e.g. "1.1" = level 2, "1.1.1" = level 3) — no changes to the Gemini
    prompt or parse_result.py are needed.
 
    Args:
        pdf_path:    path to the original PDF
        offset:      the offset calculated by parse_result.py
        toc:         dictionary of {chapter_title: corrected_pdf_page}
                     as returned by parse_result.py (offset already applied)
        output_path: where to save the corrected PDF
    """
    doc = pymupdf.open(pdf_path)
 
    toc_list = []
    for title, pdf_page in toc.items():
        level = get_level(title)
        toc_list.append([level, title, pdf_page])
 
    doc.set_toc(toc_list)
    doc.save(output_path)
 
    print(f"Saved corrected PDF to: {output_path}")
    print(f"Wrote {len(toc_list)} TOC entries into PDF metadata")
    for entry in toc_list:
        print(f"  Level {entry[0]}: {entry[1]} → PDF page {entry[2]}")
 
    return output_path
 
 
if __name__ == "__main__":
    # Quick standalone test
    test_toc = {
        "1 The Foundations: Logic and Proofs": 6,
        "1.1 Propositional Logic": 6,
        "1.2 Applications of Propositional Logic": 21,
        "2 Basic Structures": 120,
        "2.1 Sets": 120,
    }
    apply_toc_metadata("/Users/snehil/Documents/pdf_page_editor/final/test_pdfs/182 Textbook.pdf", offset=5, toc=test_toc)