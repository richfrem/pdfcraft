/**
 * Types and data models for the PdfCraft TypeScript SDK (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/types.ts
 * Purpose:
 *   Strongly typed TypeScript definitions mirroring the Rust SDK domain models.
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
export interface RenderOptions {
    dpi?: number;
    imageFormat?: "png" | "jpeg";
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
