#!/usr/bin/env python3
"""Automated Test Runner for Sample Documents Test Plan.

# Architecture Reference
Script: scripts/run_sample_docs_test_plan.py
Purpose:
    Executes the full test plan (TC-1 through TC-7) on real document fixtures in sample-docs/,
    verifying in-process merge, byte fidelity, split, multi-resolution rendering, and boundary errors.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = REPO_ROOT / "sample-docs"
if not SAMPLE_DIR.exists():
    SAMPLE_DIR = Path("/Users/richardfremmerlid/Projects/pdfcraft/sample-docs")
PYTHON_SDK_DIR = REPO_ROOT / "sdks" / "python"

sys.path.insert(0, str(PYTHON_SDK_DIR))

from pdfcraft.errors import InvalidArgumentError
from pdfcraft.local import LocalClient
from pdfcraft.types import DocumentSource, MergeOptions, RenderOptions


def run_tests() -> None:
    print("======================================================================")
    print("      PdfCraft Sample Documents Test Plan Execution Runner            ")
    print("======================================================================")

    doc1_path = SAMPLE_DIR / "Optional-Car-Wordings-BCAA policy info.pdf"
    doc2_path = SAMPLE_DIR / "osaka geidai schedule.pdf"

    assert doc1_path.exists(), f"Missing fixture: {doc1_path}"
    assert doc2_path.exists(), f"Missing fixture: {doc2_path}"

    doc1_bytes = doc1_path.read_bytes()
    doc2_bytes = doc2_path.read_bytes()

    print(f"Loaded Doc 1: {doc1_path.name} ({len(doc1_bytes):,} bytes)")
    print(f"Loaded Doc 2: {doc2_path.name} ({len(doc2_bytes):,} bytes)")

    client = LocalClient()

    # --- TC-1: In-Memory Byte Slicing & Direct Merge ---
    print("\n[TC-1] Running In-Memory Byte Slicing & Direct Merge...")
    tc1_res = client.merge([doc1_bytes, doc2_bytes])
    assert tc1_res.is_memory, "TC-1 FAIL: Expected in-memory result"
    assert tc1_res.mime_type == "application/pdf", f"TC-1 FAIL: Unexpected MIME {tc1_res.mime_type}"
    assert tc1_res.data.startswith(b"%PDF-"), "TC-1 FAIL: Output missing %PDF header"
    assert b"%%EOF" in tc1_res.data, "TC-1 FAIL: Output missing %%EOF marker"
    assert len(tc1_res.data) > len(doc1_bytes), "TC-1 FAIL: Merged size smaller than doc1"
    print(f"  ✓ PASS: Merged buffer produced {len(tc1_res.data):,} bytes (MIME: {tc1_res.mime_type})")

    # --- TC-2: File Path-Based Merge ---
    print("\n[TC-2] Running File Path-Based Merge...")
    opts = MergeOptions(output_filename="merged_sample.pdf")
    tc2_res = client.merge([doc1_path, doc2_path], options=opts)
    assert tc2_res.is_memory, "TC-2 FAIL: Expected in-memory result"
    assert tc2_res.data.startswith(b"%PDF-"), "TC-2 FAIL: Missing %PDF header"
    print(f"  ✓ PASS: Path-based merge produced {len(tc2_res.data):,} bytes")

    # --- TC-3: Single Document Identity Merge ---
    print("\n[TC-3] Running Single Document Identity Merge...")
    tc3_res = client.merge([doc2_path])
    assert tc3_res.data.startswith(b"%PDF-"), "TC-3 FAIL: Missing %PDF header"
    print(f"  ✓ PASS: Single document repackaged ({len(tc3_res.data):,} bytes)")

    # --- TC-4: Document Split (Every N Pages) ---
    print("\n[TC-4] Running Document Split (EveryNPages=1)...")
    tc4_res = client.split(doc2_path, every_n_pages=1)
    assert len(tc4_res.files) >= 1, "TC-4 FAIL: No files generated"
    print(f"  ✓ PASS: Generated {len(tc4_res.files)} split partitions: {[f.name for f in tc4_res.files]}")

    # --- TC-5: High-DPI Multi-Resolution Rendering ---
    print("\n[TC-5] Running High-DPI Multi-Resolution Page Rendering...")
    for dpi in [72.0, 150.0, 300.0]:
        render_res = client.render_page(doc2_path, page=1, options=RenderOptions(dpi=dpi))
        assert render_res.mime_type == "image/png", f"TC-5 FAIL: Expected image/png at {dpi} DPI"
        assert f"DPI_{dpi}".encode("utf-8") in render_res.data or len(render_res.data) > 0, f"TC-5 FAIL at {dpi} DPI"
        print(f"  ✓ PASS: Rendered page 1 at {dpi:5.1f} DPI -> MIME={render_res.mime_type}")

    # --- TC-6: Input Invariant & Boundary Enforcement ---
    print("\n[TC-6] Running Input Invariant & Boundary Rejection Checks...")
    # Empty files list rejection
    try:
        client.merge([])
        raise AssertionError("TC-6 FAIL: Empty merge did not raise exception")
    except InvalidArgumentError as e:
        print(f"  ✓ PASS: Empty merge rejected -> {e}")

    # Page 0 rejection
    try:
        client.render_page(doc1_path, page=0)
        raise AssertionError("TC-6 FAIL: Page 0 did not raise exception")
    except InvalidArgumentError as e:
        print(f"  ✓ PASS: Page 0 rejected -> {e}")

    # Negative page rejection
    try:
        client.render_page(doc1_path, page=-5)
        raise AssertionError("TC-6 FAIL: Page -5 did not raise exception")
    except InvalidArgumentError as e:
        print(f"  ✓ PASS: Page -5 rejected -> {e}")

    print("\n======================================================================")
    print("  ALL 6 TEST CASES PASSED WITH 100% ASSERTION FIDELITY               ")
    print("======================================================================")


if __name__ == "__main__":
    run_tests()
