/**
 * Types and data models for the PdfCraft TypeScript SDK (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/types.ts
 * Purpose:
 *   Strongly typed TypeScript definitions mirroring Datalogics APDFL 21 domain models.
 */
export type DocumentSource = {
    path: string;
} | {
    data: Uint8Array;
    name?: string;
};
export type DocumentResult = {
    type: "memory";
    data: Uint8Array;
    mimeType: string;
} | {
    type: "file";
    path: string;
    mimeType: string;
    sizeBytes: number;
};
export interface MergeOptions {
    outputFilename?: string;
    pages?: (string | null)[];
}
export type SplitMode = {
    everyNPages: number;
} | {
    beforePages: number[];
} | {
    atBookmarks: number;
};
export interface SplitResult {
    files: string[];
}
export type ImageFormat = "png" | "jpeg" | "webp" | "tiff";
export interface RenderOptions {
    dpi?: number;
    imageFormat?: ImageFormat;
}
export interface Point {
    x: number;
    y: number;
}
export interface Rect {
    x: number;
    y: number;
    width: number;
    height: number;
}
export interface Quad {
    topLeft: Point;
    topRight: Point;
    bottomLeft: Point;
    bottomRight: Point;
}
export interface Matrix {
    a: number;
    b: number;
    c: number;
    d: number;
    tx: number;
    ty: number;
}
export interface Color {
    r: number;
    g: number;
    b: number;
}
export type ColorSpace = "DeviceRGB" | "DeviceCMYK" | "DeviceGray" | "ICCBased";
export type BlendMode = "Normal" | "Multiply" | "Screen" | "Overlay";
export type FitMode = "XYZ" | "Fit" | "FitH" | "FitV" | "FitR";
export interface ViewDestination {
    pageNumber: number;
    fitMode?: FitMode;
    zoom?: number;
    rect?: Rect;
}
export interface Bookmark {
    title: string;
    destination?: ViewDestination;
    children?: Bookmark[];
    isOpen?: boolean;
}
export interface Page {
    pageNumber: number;
    mediaBox: Rect;
    cropBox?: Rect;
    rotationDegrees?: number;
}
export interface Document {
    numPages: number;
    version?: string;
    isEncrypted?: boolean;
    linearized?: boolean;
    bookmarks?: Bookmark[];
}
export declare class Style {
    fontName: string;
    fontSize: number;
    color: Color;
    constructor(fontName: string, fontSize: number, color?: Color);
    toString(): string;
}
export interface StyleTransition {
    charIndex: number;
    style: Style;
}
export interface Word {
    text: string;
    boundingBox: Rect;
    quads?: Quad[];
    styles?: StyleTransition[];
}
export interface WordFinderConfig {
    preserveLigatures?: boolean;
    preciseQuads?: boolean;
    decomposeHyphenatedWords?: boolean;
}
export interface DocTextFinderConfig {
    caseSensitive?: boolean;
    wholeWordsOnly?: boolean;
    regex?: boolean;
}
export interface DocTextFinderMatch {
    pageNumber: number;
    matchedText: string;
    boundingBox: Rect;
    quads?: Quad[];
}
export interface GoToAction {
    destination: ViewDestination;
}
export interface URIAction {
    uri: string;
    isMap?: boolean;
}
export type Action = {
    type: "GoTo";
    action: GoToAction;
} | {
    type: "URI";
    action: URIAction;
};
export interface HighlightAnnotation {
    quads: Quad[];
    color?: Color;
}
export interface Redaction {
    quads: Quad[];
    overlayText?: string;
    fillColor?: Color;
}
export interface Annotation {
    rect: Rect;
    contents?: string;
    color?: Color;
    opacity?: number;
    action?: Action;
    highlight?: HighlightAnnotation;
    redaction?: Redaction;
}
export declare enum AcroFormExportType {
    FDF = 1,
    XFDF = 2,
    XML = 3,
    JSON = 4
}
export interface TextField {
    multiline?: boolean;
    password?: boolean;
}
export interface ButtonField {
    isCheckbox?: boolean;
    isRadio?: boolean;
    checked?: boolean;
}
export interface Field {
    name: string;
    pageNumber: number;
    rect: Rect;
    value?: string;
    textField?: TextField;
    buttonField?: ButtonField;
}
export interface SignDoc {
    certP12Bytes: Uint8Array;
    password?: string;
    signerName?: string;
    reason?: string;
    location?: string;
}
export interface PermissionsFlags {
    allowPrint?: boolean;
    allowModify?: boolean;
    allowCopy?: boolean;
    allowAnnotate?: boolean;
}
export interface OptimizationParams {
    compressStreams?: boolean;
    removeUnreferencedObjects?: boolean;
    downsampleImages?: boolean;
    linearize?: boolean;
}
export interface JobResponse {
    id: string;
    operation: string;
    status: "queued" | "running" | "succeeded" | "failed" | "canceled";
    progress: number;
    createdAt: number;
    updatedAt: number;
    error?: string;
    resultUrl?: string;
}
export interface ProblemDetails {
    type: string;
    title: string;
    status: number;
    detail: string;
    code: string;
    instance?: string;
    invalidParams?: {
        name: string;
        reason: string;
    }[];
}
export interface DocumentSession {
    numPages: number;
    pages: Page[];
    addPage(width?: number, height?: number, rotationDegrees?: number): Page;
    getPage(pageNumber: number): Page;
    modifyPage(pageNumber: number, rotationDegrees?: number, mediaBox?: Rect): Page;
    removePage(pageNumber: number): Page;
    addText(pageNumber: number, text: string, x: number, y: number, style?: Style): void;
    addStyledLine(pageNumber: number, x: number, y: number, baseText: string, transitions: StyleTransition[]): void;
    findText(query: string, config?: DocTextFinderConfig): DocTextFinderMatch[];
    addImage(pageNumber: number, imageSource: Uint8Array, rect: Rect, imageId?: string): string;
    removeImage(pageNumber: number, imageId: string): boolean;
    save(targetPath: string): Promise<DocumentResult>;
    renderPage(pageNumber: number, outputPath: string, dpi?: number): Promise<string>;
}
