#!/usr/bin/env python3
"""PdfCraft README Showcase Document Generator (Python SDK).

Programmatically generates a multi-page PDF specimen demonstrating the
exact features and design capabilities showcased in the main README:
  • Page 1: Showcase Cover & ArtCraft Workbench Brand
  • Page 2: Scripts of the World & Typography (World scripts & vertical Japanese)
  • Page 3: Editorial Layout & Two-Column Read Mode (Drop cap & pull quotes)
  • Page 4: Interactive Forms & Digital Signatures (Fields & values)
  • Page 5: Review & Markup (Threaded comments, APPROVED stamp & DRAFT watermark)

Usage:
  python3 docs/sdk/examples/python/readme_showcase_builder.py
  python3 docs/sdk/examples/python/readme_showcase_builder.py --output dist/readme_showcase.pdf --render-previews
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Automatically add local SDK package to sys.path so the example runs out of the box
REPO_ROOT = Path(__file__).resolve().parents[4]
SDK_PYTHON_DIR = REPO_ROOT / "sdks" / "python"
if str(SDK_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_DIR))

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install pillow", file=sys.stderr)
    sys.exit(1)

from pdfcraft import (
    Color,
    DocumentSession,
    Rect,
    Style,
    StyleTransition,
)


def create_artcraft_badge(width: int = 140, height: int = 140) -> bytes:
    """Generates an in-memory ArtCraft palette icon badge."""
    img = Image.new("RGB", (width, height), color=(10, 117, 99))  # Emerald #0a7563
    for x in range(width):
        for y in range(height):
            # Concentric rings & geometric lines
            dist_sq = (x - 70) ** 2 + (y - 70) ** 2
            if 3600 <= dist_sq <= 4200 or 1200 <= dist_sq <= 1600 or (x == y and 40 <= x <= 100):
                img.putpixel((x, y), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_readme_showcase_document(output_pdf: Path) -> DocumentSession:
    """Constructs the complete 5-page specimen PDF."""
    session = DocumentSession.create()

    # Shared palette colors
    c_navy = Color.rgb(0.06, 0.16, 0.32)
    c_emerald = Color.rgb(0.04, 0.46, 0.39)  # ArtCraft signature emerald
    c_slate = Color.rgb(0.35, 0.40, 0.48)
    c_charcoal = Color.rgb(0.15, 0.15, 0.18)
    c_card_bg = Color.rgb(0.96, 0.98, 0.99)
    c_card_border = Color.rgb(0.80, 0.85, 0.90)

    # ==========================================================================
    # Page 1: Showcase Cover & Viewer (README §Highlights)
    # ==========================================================================
    session.add_page(width=612.0, height=792.0)

    # Top Brand Ribbon
    session.add_rect(1, Rect(40.0, 720.0, 532.0, 36.0), fill_color=c_emerald)
    ribbon_style = Style(font_name="Helvetica-Bold", font_size=14.0, color=Color.white())
    session.add_text(1, "ARTCRAFT  |  PdfCraft Workbench Specimen", 56.0, 733.0, ribbon_style)

    # Hero Cover Title
    cover_title = Style(font_name="Helvetica-Bold", font_size=28.0, color=c_navy)
    session.add_text(1, "PdfCraft Showcase", 56.0, 660.0, cover_title)

    cover_sub = Style(font_name="Helvetica", font_size=13.0, color=c_slate)
    session.add_text(1, "Clean-Room Reimplementation of Adobe Acrobat in Pure Safe Rust", 56.0, 638.0, cover_sub)

    # Embedded Brand Badge
    badge_data = create_artcraft_badge(140, 140)
    session.add_image(1, badge_data, Rect(390.0, 470.0, 140.0, 140.0), image_id="ArtCraftBadge")

    # Three Core Highlights Cards (Faithful, Fearless, Yours from README)
    cards = [
        ("FAITHFUL", "World scripts, vertical Japanese, gradients, soft masks, and blend modes render as intended."),
        ("FEARLESS", "Atomic writes, deep undo history, zero crashes across the entire pdf.js corpus."),
        ("YOURS", "No telemetry, no cloud accounts, offline-first execution, and 100% open-source safe Rust."),
    ]
    y_card = 520.0
    for title, desc in cards:
        session.add_rect(1, Rect(56.0, y_card, 310.0, 48.0), fill_color=c_card_bg, stroke_color=c_card_border, line_width=1.0)
        session.add_text(1, title, 68.0, y_card + 30.0, Style(font_name="Helvetica-Bold", font_size=10.0, color=c_emerald))
        session.add_text(1, desc, 68.0, y_card + 12.0, Style(font_name="Helvetica", font_size=8.5, color=c_charcoal))
        y_card -= 60.0

    # Specification Metadata Box
    session.add_rect(1, Rect(56.0, 180.0, 500.0, 120.0), fill_color=Color.rgb(0.94, 0.96, 0.98), stroke_color=c_card_border, line_width=1.0)
    meta_h = Style(font_name="Helvetica-Bold", font_size=11.0, color=c_navy)
    session.add_text(1, "DOCUMENT PROPERTIES & SPECIFICATION", 70.0, 275.0, meta_h)

    meta_items = [
        ("PDF Specification:", "ISO 32000-2 (PDF 2.0) Compliant"),
        ("Safety & Security:", "#![forbid(unsafe_code)] · AES-256 SASLprep Handler"),
        ("Headless Parity:", "Full tool catalog reachable via CLI, MCP, and Native SDK"),
        ("Asset Governance:", "Zero Adobe proprietary assets · OFL / MIT open licenses"),
    ]
    y_meta = 250.0
    for k, v in meta_items:
        session.add_text(1, k, 70.0, y_meta, Style(font_name="Helvetica-Bold", font_size=9.0, color=c_slate))
        session.add_text(1, v, 200.0, y_meta, Style(font_name="Courier", font_size=9.0, color=c_navy))
        y_meta -= 20.0

    # ==========================================================================
    # Page 2: Scripts of the World & Typography (README §Read anything, beautifully)
    # ==========================================================================
    section_title = Style(font_name="Helvetica-Bold", font_size=20.0, color=c_navy)
    session.add_page(width=612.0, height=792.0)

    session.add_text(2, "Scripts of the World & Typographical Engine", 40.0, 725.0, section_title)
    session.add_text(2, "Real-world typography: vertical Japanese margins, world alphabets, and glyph layout", 40.0, 700.0, cover_sub)

    # Vertical Japanese simulated margin strip (README: vertical Japanese in right margin)
    session.add_rect(2, Rect(510.0, 100.0, 48.0, 570.0), fill_color=Color.rgb(0.95, 0.97, 0.96), stroke_color=c_emerald, line_width=1.0)
    jp_chars = ["大", "阪", "芸", "術", "大", "学", "・", "工", "芸", "研", "究", "所", "・", "縦", "組", "組", "版"]
    y_jp = 640.0
    for ch in jp_chars:
        session.add_text(2, ch, 526.0, y_jp, Style(font_name="Helvetica", font_size=11.0, color=c_navy))
        y_jp -= 28.0

    # Multi-language type specimens
    specimens = [
        ("Latin Proportional (Helvetica)", "All human beings are born free and equal in dignity and rights."),
        ("Latin Serif (Times-Roman)", "Quo usque tandem abutere, Catilina, patientia nostra?"),
        ("Monospace Code (Courier)", "let session = DocumentSession::create().unwrap();"),
        ("Greek Alphabet Sample", "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa"),
        ("Cyrillic Script Sample", "Bse lyudi rozhdayutsya svobodnymi i ravnymi v svoyem dostoinstve."),
    ]
    y_spec = 620.0
    for label, text in specimens:
        session.add_rect(2, Rect(40.0, y_spec - 10.0, 450.0, 55.0), fill_color=c_card_bg, stroke_color=c_card_border, line_width=0.8)
        session.add_text(2, label, 52.0, y_spec + 25.0, Style(font_name="Helvetica-Bold", font_size=10.0, color=c_emerald))
        session.add_text(2, text, 52.0, y_spec + 5.0, Style(font_name="Times-Roman", font_size=11.0, color=c_charcoal))
        y_spec -= 75.0

    # ==========================================================================
    # Page 3: Two-Up Editorial Layout (README §Read mode, two-up)
    # ==========================================================================
    session.add_page(width=612.0, height=792.0)

    session.add_text(3, "Setting Text & Editorial Layout", 40.0, 725.0, section_title)
    session.add_text(3, "Read mode layout: large initial drop cap, two-column flow, and pull quote callout", 40.0, 700.0, cover_sub)

    # Large Drop Cap 'P'
    drop_cap_style = Style(font_name="Helvetica-Bold", font_size=42.0, color=c_emerald)
    session.add_text(3, "P", 44.0, 630.0, drop_cap_style)

    # Column 1 Paragraphs next to drop cap
    body_style = Style(font_name="Times-Roman", font_size=10.0, color=c_charcoal)
    session.add_text(3, "dfCraft renders documents with care", 78.0, 655.0, body_style)
    session.add_text(3, "for details that make complex typography", 78.0, 640.0, body_style)
    session.add_text(3, "feel right: ligatures, soft masks & curves.", 78.0, 625.0, body_style)

    col1_lines = [
        "Every page renders in safe isolation,",
        "protected by panic guards and memory",
        "budgets. Damaged files are repaired",
        "incrementally without destroying revisions.",
        "Corrupt trailers and damaged offsets are",
        "restored safely without losing edits.",
    ]
    y_col1 = 605.0
    for l in col1_lines:
        session.add_text(3, l, 44.0, y_col1, body_style)
        y_col1 -= 15.0

    # Column 2 Paragraphs (x = 310)
    col2_lines = [
        "In contrast to legacy C++ engines, PdfCraft is pure",
        "safe Rust. No buffer overflows, no use-after-free",
        "vulnerabilities, and zero proprietary closed-source",
        "blobs. Documents stay yours, with offline-first",
        "privacy and zero cloud telemetry dependencies.",
        "Every action is completely undoable via history.",
    ]
    y_col2 = 655.0
    for l in col2_lines:
        session.add_text(3, l, 310.0, y_col2, body_style)
        y_col2 -= 15.0

    # Pull Quote Callout Box
    session.add_rect(3, Rect(44.0, 420.0, 524.0, 70.0), fill_color=Color.rgb(0.92, 0.96, 0.98), stroke_color=c_emerald, line_width=2.0)
    quote_style = Style(font_name="Helvetica-Bold", font_size=12.0, color=c_navy)
    session.add_text(3, "\"Fearless: Every save appends changes and leaves original bytes untouched.", 60.0, 460.0, quote_style)
    session.add_text(3, "Writes are atomic, undo runs deep, and nothing is lost if closed by mistake.\"", 60.0, 440.0, quote_style)

    # Syntax-Colored Monospace Listing (README §Code and Images chapter)
    session.add_rect(3, Rect(44.0, 200.0, 524.0, 190.0), fill_color=Color.rgb(0.12, 0.14, 0.18), stroke_color=Color.rgb(0.2, 0.25, 0.3), line_width=1.0)
    session.add_text(3, "// Safe Rust In-Process API Example", 60.0, 365.0, Style(font_name="Courier", font_size=9.5, color=Color.rgb(0.5, 0.6, 0.7)))
    code_lines = [
        "use pdfcraft_sdk::{DocumentSession, Style, Color, Rect};",
        "",
        "fn main() -> Result<(), Box<dyn std::error::Error>> {",
        "    let mut session = DocumentSession::create();",
        "    let page = session.add_page(612.0, 792.0, 0)?;",
        "    session.add_text(1, \"Hello PdfCraft\", 40.0, 700.0, Style::default())?;",
        "    session.save(\"output.pdf\")?;",
        "    Ok(())",
        "}",
    ]
    y_code = 345.0
    for cl in code_lines:
        c_code = Color.rgb(0.4, 0.85, 0.6) if "let" in cl or "fn" in cl or "use" in cl else Color.rgb(0.9, 0.9, 0.95)
        session.add_text(3, cl, 60.0, y_code, Style(font_name="Courier", font_size=9.5, color=c_code))
        y_code -= 15.0

    # ==========================================================================
    # Page 4: Interactive Forms & Digital Signatures (README §Forms & layers)
    # ==========================================================================
    session.add_page(width=612.0, height=792.0)

    session.add_text(4, "Interactive Forms & Data Exchange (AcroForms)", 40.0, 725.0, section_title)
    session.add_text(4, "Interactive form fields, appearance streams, checkboxes, and signature containers", 40.0, 700.0, cover_sub)

    # Form Fields
    session.add_form_field_view(4, "Full Name / Policyholder:", Rect(44.0, 610.0, 240.0, 24.0), value="Jane Doe, P.Eng.", field_type="text")
    session.add_form_field_view(4, "Policy Number:", Rect(310.0, 610.0, 240.0, 24.0), value="BCAA-OPT-2024-99812", field_type="text")

    session.add_form_field_view(4, "Vehicle Identification Number (VIN):", Rect(44.0, 540.0, 506.0, 24.0), value="2HGFC2F69MH512390", field_type="text")

    session.add_form_field_view(4, "Comprehensive Collision Coverage Included", Rect(44.0, 485.0, 20.0, 20.0), value="true", field_type="checkbox")
    session.add_form_field_view(4, "Rental Vehicle Reimbursement Endorsement", Rect(44.0, 445.0, 20.0, 20.0), value="true", field_type="checkbox")
    session.add_form_field_view(4, "Third-Party Excess Liability Extended to $5,000,000", Rect(44.0, 405.0, 20.0, 20.0), value="false", field_type="checkbox")

    # Digital Signature Block
    session.add_rect(4, Rect(44.0, 240.0, 506.0, 120.0), fill_color=Color.rgb(0.97, 0.99, 0.98), stroke_color=c_emerald, line_width=1.5)
    sig_header = Style(font_name="Helvetica-Bold", font_size=11.0, color=c_emerald)
    session.add_text(4, "DIGITAL SIGNATURE CONTAINER (PKCS#7 / P12)", 60.0, 335.0, sig_header)

    sig_info = [
        "Signer:        Jane Doe <jane.doe@storytold.internal>",
        "Certificate:   CN=Storytold Enterprise CA, O=ArtCraft Team",
        "Algorithm:     RSA-4096 / SHA-256 with PSS Padding",
        "Status:        Cryptographically Validated (Integrity Intact)",
    ]
    y_sig = 310.0
    for s in sig_info:
        session.add_text(4, s, 60.0, y_sig, Style(font_name="Courier", font_size=9.0, color=c_navy))
        y_sig -= 18.0

    # ==========================================================================
    # Page 5: Review & Markup (README §Comments, forms, layers)
    # ==========================================================================
    session.add_page(width=612.0, height=792.0)

    session.add_text(5, "Review, Markup & Annotations", 40.0, 725.0, section_title)
    session.add_text(5, "Threaded comment panels, vector highlights, stamps, and draft watermarks", 40.0, 700.0, cover_sub)

    # DRAFT Watermark (diagonal amber stroke across page)
    session.add_stamp(5, "DRAFT WATERMARK", Rect(60.0, 460.0, 290.0, 55.0), color=Color.rgb(0.9, 0.55, 0.15))

    # APPROVED Official Stamp (emerald green)
    session.add_stamp(5, "APPROVED - READY TO SHIP", Rect(60.0, 380.0, 290.0, 50.0), color=c_emerald)

    # Main text with simulated yellow highlight annotation
    session.add_rect(5, Rect(44.0, 578.0, 320.0, 18.0), fill_color=Color.rgb(1.0, 0.96, 0.6))
    session.add_text(5, "All tools are accessible headlessly via CLI and native SDK.", 46.0, 582.0, Style(font_name="Helvetica-Bold", font_size=10.5, color=c_navy))

    session.add_rect(5, Rect(44.0, 548.0, 280.0, 18.0), fill_color=Color.rgb(1.0, 0.88, 0.88))
    session.add_text(5, "Zero crash guarantee: pure safe Rust without unsafe blobs.", 46.0, 552.0, Style(font_name="Helvetica-Bold", font_size=10.5, color=Color.rgb(0.7, 0.15, 0.15)))

    # Threaded Comments Panel on Right Side (README: 20 threaded comments on the right)
    session.add_comment_card(
        5,
        author="Richard Fremmerlid (Staff Lead)",
        comment="Approved: Parity aligns with APDFL 21 domain hierarchy.",
        rect=Rect(380.0, 560.0, 185.0, 65.0),
    )
    session.add_comment_card(
        5,
        author="Astra (Staff Architect)",
        comment="Boundary verified: COS AST isolated behind lowlevel.",
        rect=Rect(380.0, 480.0, 185.0, 65.0),
    )
    session.add_comment_card(
        5,
        author="QA Bot (Automation)",
        comment="All 24 test suites pass with 0 regressions.",
        rect=Rect(380.0, 400.0, 185.0, 65.0),
    )

    # Save to disk
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    res = session.save(output_pdf)
    print(f"✓ Saved 5-page README Showcase PDF: {output_pdf.resolve()} ({res.size_bytes:,} bytes)")
    return session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PdfCraft README Showcase Document Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("dist/readme_showcase_specimen.pdf"),
        help="Path where the generated PDF document will be written",
    )
    parser.add_argument(
        "--render-previews",
        "-r",
        action="store_true",
        default=True,
        help="Render preview PNG images for each page",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Rendering resolution for previews",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Building PdfCraft README Level Showcase Document")
    print("=" * 70)

    session = build_readme_showcase_document(args.output)

    if args.render_previews:
        print("\nRendering Page Previews via pdftoppm...")
        preview_dir = args.output.parent / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        for p in range(1, session.num_pages + 1):
            out_img = preview_dir / f"showcase_page_{p}.png"
            try:
                session.render_page(p, out_img, dpi=float(args.dpi))
                print(f"  • Rendered Page {p}: {out_img.resolve()} ({out_img.stat().st_size:,} bytes)")
            except Exception as e:
                print(f"  ⚠ Page {p} preview skipped: {e}")

    print("\n" + "=" * 70)
    print("Showcase Document Generation Complete!")
    print(f"Output PDF: {args.output.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
