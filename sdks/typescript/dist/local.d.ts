/**
 * In-process Local SDK Client for PdfCraft (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/local.ts
 * Purpose:
 *   In-process document processing client linking to pdfcraft-engine via N-API addon,
 *   providing zero-network, zero-daemon PDF processing (PDFL alternative).
 */
import { DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode, SplitResult } from "./types.js";
export declare class PdfCraftLocalClient {
    private nativeBinding;
    constructor();
    /**
     * Merges multiple PDF documents into a single document in-process.
     */
    merge(sources: (DocumentSource | string | Uint8Array)[], options?: MergeOptions): Promise<DocumentResult>;
    /**
     * Splits a PDF document into multiple documents.
     */
    split(source: DocumentSource | string | Uint8Array, mode?: SplitMode): Promise<SplitResult>;
    /**
     * Renders a single page of a PDF document to an image at the specified physical DPI.
     */
    renderPage(source: DocumentSource | string | Uint8Array, page: number, options?: RenderOptions): Promise<DocumentResult>;
}
