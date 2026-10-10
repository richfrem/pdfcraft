/**
 * Types and runtime classes for @pdfcraft/sdk (Issue #872).
 * Conforms to Datalogics APDFL 21 specifications.
 */

export class Style {
  constructor(fontName, fontSize, color = { r: 0, g: 0, b: 0 }) {
    this.fontName = fontName;
    this.fontSize = fontSize;
    this.color = color;
  }

  toString() {
    return `[color=RGB(${this.color.r},${this.color.g},${this.color.b}), fontsize=${this.fontSize}, fontname=${this.fontName}]`;
  }
}

export const AcroFormExportType = {
  FDF: 1,
  XFDF: 2,
  XML: 3,
  JSON: 4,
};
