"""Document Lifecycle Session for PdfCraft Python SDK (APDFL Parity).

# Architecture Reference
Module: sdks/python/pdfcraft/session.py
Purpose:
    Provides an end-to-end programmatic document manipulation session
    implementing the full APDFL lifecycle:
      1. Create blank document
      2. Page management (add, remove, modify rotation/dimensions)
      3. Text extraction & styled insertion with Style / StyleTransition
      4. Image management (embed raster, locate, remove/replace)
      5. Save to disk and render preview images
"""

from __future__ import annotations

import io
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

from pdfcraft.errors import InvalidArgumentError, PdfCraftError
from pdfcraft.types import (
    Color,
    DocTextFinderConfig,
    DocTextFinderMatch,
    DocumentResult,
    Page,
    Quad,
    Rect,
    Style,
    StyleTransition,
    Word,
)


@dataclass
class _TextElement:
    """Internal record of placed styled text."""

    text: str
    x: float
    y: float
    style: Style


@dataclass
class _ImageElement:
    """Internal record of placed image XObject."""

    image_id: str
    raw_rgb: bytes
    width: int
    height: int
    rect: Rect


class DocumentSession:
    """High-level in-process document editing session adhering to APDFL patterns."""

    def __init__(self) -> None:
        """Creates an empty DocumentSession."""
        self._pages: List[Page] = []
        self._text_elements: Dict[int, List[_TextElement]] = {}
        self._image_elements: Dict[int, List[_ImageElement]] = {}

    @classmethod
    def create(cls) -> DocumentSession:
        """Factory method to start a new document session."""
        return cls()

    @property
    def num_pages(self) -> int:
        """Returns the total number of pages in the session."""
        return len(self._pages)

    @property
    def pages(self) -> List[Page]:
        """Returns a copy of the page list."""
        return list(self._pages)

    def add_page(
        self,
        width: float = 612.0,
        height: float = 792.0,
        rotation_degrees: int = 0,
    ) -> Page:
        """Appends a new page with the specified dimensions and rotation."""
        if width <= 0 or height <= 0:
            raise InvalidArgumentError(f"Page dimensions must be positive: ({width}, {height})")
        if rotation_degrees % 90 != 0:
            raise InvalidArgumentError(f"Rotation must be multiple of 90 degrees: {rotation_degrees}")

        page_num = len(self._pages) + 1
        page = Page(
            page_number=page_num,
            media_box=Rect(0.0, 0.0, width, height),
            crop_box=Rect(0.0, 0.0, width, height),
            rotation_degrees=rotation_degrees % 360,
        )
        self._pages.append(page)
        self._text_elements[page_num] = []
        self._image_elements[page_num] = []
        return page

    def get_page(self, page_number: int) -> Page:
        """Retrieves page metadata by 1-based page index."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds (1..{len(self._pages)})")
        return self._pages[page_number - 1]

    def modify_page(
        self,
        page_number: int,
        rotation_degrees: Optional[int] = None,
        media_box: Optional[Rect] = None,
    ) -> Page:
        """Modifies page geometry or rotation."""
        page = self.get_page(page_number)
        if rotation_degrees is not None:
            if rotation_degrees % 90 != 0:
                raise InvalidArgumentError(f"Rotation must be multiple of 90: {rotation_degrees}")
            page.rotation_degrees = rotation_degrees % 360
        if media_box is not None:
            if media_box.width <= 0 or media_box.height <= 0:
                raise InvalidArgumentError("Media box width and height must be positive")
            page.media_box = media_box
            page.crop_box = media_box
        return page

    def remove_page(self, page_number: int) -> Page:
        """Removes a page at 1-based index and re-indexes remaining pages."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds (1..{len(self._pages)})")

        removed = self._pages.pop(page_number - 1)

        # Shift elements dictionary down
        new_text: Dict[int, List[_TextElement]] = {}
        new_img: Dict[int, List[_ImageElement]] = {}

        for i, p in enumerate(self._pages, start=1):
            old_idx = p.page_number
            p.page_number = i
            new_text[i] = self._text_elements.get(old_idx, [])
            new_img[i] = self._image_elements.get(old_idx, [])

        self._text_elements = new_text
        self._image_elements = new_img
        return removed

    def add_text(
        self,
        page_number: int,
        text: str,
        x: float,
        y: float,
        style: Optional[Style] = None,
    ) -> None:
        """Adds text at (x, y) with typographical styling."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds (1..{len(self._pages)})")

        st = style or Style(font_name="Helvetica", font_size=12.0, color=Color.black())
        elem = _TextElement(text=text, x=x, y=y, style=st)
        self._text_elements[page_number].append(elem)

    def add_styled_line(
        self,
        page_number: int,
        x: float,
        y: float,
        base_text: str,
        transitions: List[StyleTransition],
    ) -> None:
        """Places text using style transitions (APDFL StyleTransition pattern)."""
        if not transitions:
            self.add_text(page_number, base_text, x, y)
            return

        sorted_trans = sorted(transitions, key=lambda t: t.char_index)
        cur_x = x
        for i, t in enumerate(sorted_trans):
            start = t.char_index
            end = sorted_trans[i + 1].char_index if i + 1 < len(sorted_trans) else len(base_text)
            segment = base_text[start:end]
            if segment:
                self.add_text(page_number, segment, cur_x, y, t.style)
                # Compute advance width based on character properties
                is_bold = "bold" in t.style.font_name.lower()
                is_mono = "courier" in t.style.font_name.lower()
                seg_width = 0.0
                for ch in segment:
                    if is_mono:
                        seg_width += t.style.font_size * 0.60
                    elif ch == ' ':
                        seg_width += t.style.font_size * 0.30
                    elif ch in 'il.,:;!\'':
                        seg_width += t.style.font_size * (0.32 if is_bold else 0.26)
                    elif ch.isupper() or ch in 'mwMW':
                        seg_width += t.style.font_size * (0.76 if is_bold else 0.70)
                    else:
                        seg_width += t.style.font_size * (0.58 if is_bold else 0.52)
                cur_x += seg_width

    def find_text(
        self,
        query: str,
        config: Optional[DocTextFinderConfig] = None,
    ) -> List[DocTextFinderMatch]:
        """Searches for text pattern across all pages matching APDFL DocTextFinder."""
        if not query:
            return []

        cfg = config or DocTextFinderConfig()
        flags = 0 if cfg.case_sensitive else re.IGNORECASE
        pattern = re.escape(query) if not cfg.regex else query
        if cfg.whole_words_only:
            pattern = rf"\b{pattern}\b"

        regex = re.compile(pattern, flags)
        matches: List[DocTextFinderMatch] = []

        for p_num, elems in self._text_elements.items():
            for elem in elems:
                for match in regex.finditer(elem.text):
                    m_text = match.group(0)
                    start_char = match.start()
                    char_offset = start_char * (elem.style.font_size * 0.52)
                    match_width = len(m_text) * (elem.style.font_size * 0.52)
                    match_height = elem.style.font_size

                    box = Rect(
                        x=elem.x + char_offset,
                        y=elem.y,
                        width=match_width,
                        height=match_height,
                    )
                    matches.append(
                        DocTextFinderMatch(
                            page_number=p_num,
                            matched_text=m_text,
                            bounding_box=box,
                            quads=[Quad.from_rect(box)],
                        )
                    )

        return matches

    def add_image(
        self,
        page_number: int,
        image_source: Union[bytes, str, Path],
        rect: Rect,
        image_id: Optional[str] = None,
    ) -> str:
        """Embeds a raster image into the specified page."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds")

        if isinstance(image_source, (str, Path)):
            with open(image_source, "rb") as f:
                raw_data = f.read()
        else:
            raw_data = image_source

        # Parse raster image with PIL to normalize to RGB
        pil_img = Image.open(io.BytesIO(raw_data)).convert("RGB")
        w, h = pil_img.size
        rgb_bytes = pil_img.tobytes()

        assigned_id = image_id or f"Im{len(self._image_elements[page_number]) + 1}"
        elem = _ImageElement(
            image_id=assigned_id,
            raw_rgb=rgb_bytes,
            width=w,
            height=h,
            rect=rect,
        )
        self._image_elements[page_number].append(elem)
        return assigned_id

    def remove_image(self, page_number: int, image_id: str) -> bool:
        """Removes an embedded image XObject from the specified page."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds")

        images = self._image_elements[page_number]
        initial_len = len(images)
        self._image_elements[page_number] = [img for img in images if img.image_id != image_id]
        return len(self._image_elements[page_number]) < initial_len

    def get_images(self, page_number: int) -> List[Dict[str, Any]]:
        """Returns metadata of images placed on a page."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds")

        return [
            {
                "image_id": img.image_id,
                "width": img.width,
                "height": img.height,
                "rect": img.rect,
            }
            for img in self._image_elements[page_number]
        ]

    def save(self, target_path: Union[str, Path]) -> DocumentResult:
        """Serializes the document session to a standard compliant PDF file."""
        if not self._pages:
            raise PdfCraftError("Cannot save empty document with zero pages")

        out_path = Path(target_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        writer = PdfWriter()

        font_map: Dict[str, str] = {
            "Helvetica": "Helvetica",
            "Helvetica-Bold": "Helvetica-Bold",
            "Times-Roman": "Times-Roman",
            "Times-Bold": "Times-Bold",
            "Courier": "Courier",
            "Courier-Bold": "Courier-Bold",
        }

        for p_idx, page_model in enumerate(self._pages, start=1):
            writer_page = writer.add_blank_page(
                width=page_model.media_box.width,
                height=page_model.media_box.height,
            )
            if page_model.rotation_degrees != 0:
                writer_page.rotate(page_model.rotation_degrees)

            # Build content stream commands
            stream_chunks: List[str] = []

            # 1. Background grid / border decoration for visible structure
            stream_chunks.append(
                f"0.92 0.94 0.96 rg 20 20 {page_model.media_box.width - 40} {page_model.media_box.height - 40} re f\n"
                f"0.75 0.80 0.85 RG 2 w 20 20 {page_model.media_box.width - 40} {page_model.media_box.height - 40} re S\n"
            )

            # 2. Text elements
            fonts_used: Dict[str, str] = {}
            for t_elem in self._text_elements.get(p_idx, []):
                font_name = t_elem.style.font_name
                canonical_font = font_map.get(font_name, "Helvetica")
                font_alias = f"F_{canonical_font.replace('-', '_')}"
                fonts_used[font_alias] = canonical_font

                r = max(0.0, min(1.0, t_elem.style.color.r))
                g = max(0.0, min(1.0, t_elem.style.color.g))
                b = max(0.0, min(1.0, t_elem.style.color.b))

                # Escape text for PDF literal string
                escaped = (
                    t_elem.text.replace("\\", "\\\\")
                    .replace("(", "\\(")
                    .replace(")", "\\)")
                )

                stream_chunks.append(
                    f"BT /{font_alias} {t_elem.style.font_size} Tf "
                    f"{r:.3f} {g:.3f} {b:.3f} rg "
                    f"{t_elem.x:.2f} {t_elem.y:.2f} Td ({escaped}) Tj ET\n"
                )

            # 3. Image elements
            images_used: Dict[str, _ImageElement] = {}
            for img_elem in self._image_elements.get(p_idx, []):
                img_key = f"Im_{img_elem.image_id}"
                images_used[img_key] = img_elem

                # q width 0 0 height x y cm /Im Do Q
                stream_chunks.append(
                    f"q {img_elem.rect.width:.2f} 0 0 {img_elem.rect.height:.2f} "
                    f"{img_elem.rect.x:.2f} {img_elem.rect.y:.2f} cm /{img_key} Do Q\n"
                )

            # Stream object registration
            content_stream = DecodedStreamObject()
            content_stream.set_data("".join(stream_chunks).encode("utf-8"))
            stream_ref = writer._add_object(content_stream)
            writer_page[NameObject("/Contents")] = stream_ref

            # Resource dictionaries
            res_dict = DictionaryObject()

            if fonts_used:
                font_dict = DictionaryObject()
                for alias, base_name in fonts_used.items():
                    f_obj = DictionaryObject({
                        NameObject("/Type"): NameObject("/Font"),
                        NameObject("/Subtype"): NameObject("/Type1"),
                        NameObject("/BaseFont"): NameObject(f"/{base_name}"),
                    })
                    f_ref = writer._add_object(f_obj)
                    font_dict[NameObject(f"/{alias}")] = f_ref
                res_dict[NameObject("/Font")] = font_dict

            if images_used:
                xobj_dict = DictionaryObject()
                for alias, img_data in images_used.items():
                    x_obj = DecodedStreamObject()
                    x_obj.set_data(img_data.raw_rgb)
                    x_obj[NameObject("/Type")] = NameObject("/XObject")
                    x_obj[NameObject("/Subtype")] = NameObject("/Image")
                    x_obj[NameObject("/Width")] = NumberObject(img_data.width)
                    x_obj[NameObject("/Height")] = NumberObject(img_data.height)
                    x_obj[NameObject("/ColorSpace")] = NameObject("/DeviceRGB")
                    x_obj[NameObject("/BitsPerComponent")] = NumberObject(8)
                    x_ref = writer._add_object(x_obj)
                    xobj_dict[NameObject(f"/{alias}")] = x_ref
                res_dict[NameObject("/XObject")] = xobj_dict

            writer_page[NameObject("/Resources")] = res_dict

        with open(out_path, "wb") as f:
            writer.write(f)

        size = out_path.stat().st_size
        return DocumentResult(path=out_path, size_bytes=size)

    def render_page(
        self,
        page_number: int,
        output_path: Union[str, Path],
        dpi: float = 150.0,
    ) -> Path:
        """Renders the rendered page to a raster PNG image file."""
        if page_number < 1 or page_number > len(self._pages):
            raise InvalidArgumentError(f"Page index {page_number} out of bounds")

        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        temp_pdf = dest.with_suffix(".tmp.pdf")
        self.save(temp_pdf)

        try:
            prefix = dest.parent / f"{dest.stem}_temp_render"
            cmd = [
                "pdftoppm",
                "-png",
                "-r",
                str(int(dpi)),
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                str(temp_pdf),
                str(prefix),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # pdftoppm appends -1.png or -01.png
            candidates = sorted(dest.parent.glob(f"{dest.stem}_temp_render*.png"))
            if not candidates:
                raise PdfCraftError("pdftoppm did not generate output image")

            rendered_file = candidates[0]
            shutil.move(rendered_file, dest)
            return dest
        finally:
            if temp_pdf.exists():
                temp_pdf.unlink()
