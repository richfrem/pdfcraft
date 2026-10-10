/**
 * Types and data models for the PdfCraft TypeScript SDK (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/types.ts
 * Purpose:
 *   Strongly typed TypeScript definitions mirroring Datalogics APDFL 21 domain models.
 */
// ==============================================================================
// Domain 4: Text, Fonts & Styles
// ==============================================================================
export class Style {
    fontName;
    fontSize;
    color;
    constructor(fontName, fontSize, color = { r: 0, g: 0, b: 0 }) {
        this.fontName = fontName;
        this.fontSize = fontSize;
        this.color = color;
    }
    toString() {
        return `[color=RGB(${this.color.r},${this.color.g},${this.color.b}), fontsize=${this.fontSize}, fontname=${this.fontName}]`;
    }
}
// ==============================================================================
// Domain 6: Forms & Data Exchange
// ==============================================================================
export var AcroFormExportType;
(function (AcroFormExportType) {
    AcroFormExportType[AcroFormExportType["FDF"] = 1] = "FDF";
    AcroFormExportType[AcroFormExportType["XFDF"] = 2] = "XFDF";
    AcroFormExportType[AcroFormExportType["XML"] = 3] = "XML";
    AcroFormExportType[AcroFormExportType["JSON"] = 4] = "JSON";
})(AcroFormExportType || (AcroFormExportType = {}));
