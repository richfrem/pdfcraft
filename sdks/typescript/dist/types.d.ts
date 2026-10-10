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
