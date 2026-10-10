/**
 * Remote REST SDK Client for PdfCraft (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/rest.ts
 * Purpose:
 *   Fetch-based client communicating with an on-premise PdfCraft REST daemon,
 *   providing 1:1 semantic parity with PdfCraftLocalClient.
 */
import { DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode, SplitResult } from "./types.js";
export interface RestClientOptions {
    baseUrl?: string;
    authToken?: string;
    timeoutMs?: number;
}
export declare class PdfCraftRestClient {
    readonly baseUrl: string;
    readonly authToken?: string;
    readonly timeoutMs: number;
    constructor(options?: RestClientOptions);
    private request;
    private handleErrorResponse;
    /**
     * Merges multiple PDF documents via the REST daemon.
     */
    merge(sources: (DocumentSource | string | Uint8Array)[], options?: MergeOptions, asyncJob?: boolean): Promise<DocumentResult>;
    /**
     * Splits a PDF document via the REST daemon.
     */
    split(source: DocumentSource | string | Uint8Array, mode?: SplitMode): Promise<SplitResult>;
    /**
     * Renders a PDF page to image via the REST daemon.
     */
    renderPage(source: DocumentSource | string | Uint8Array, page: number, options?: RenderOptions): Promise<DocumentResult>;
    private pollJob;
}
