/**
 * Error hierarchy for the PdfCraft TypeScript SDK.
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/errors.ts
 * Purpose:
 *   Provides structured, typed exceptions mapped cleanly from engine errors
 *   and HTTP RFC 7807 Problem Details.
 */
import { ProblemDetails } from "./types.js";
export declare class PdfCraftError extends Error {
    readonly statusCode: number;
    readonly errorCode: string;
    readonly problem?: ProblemDetails;
    constructor(message: string, statusCode?: number, errorCode?: string, problem?: ProblemDetails);
}
export declare class InvalidArgumentError extends PdfCraftError {
    constructor(message: string, problem?: ProblemDetails);
}
export declare class NotFoundError extends PdfCraftError {
    constructor(message: string, problem?: ProblemDetails);
}
export declare class ConflictError extends PdfCraftError {
    constructor(message: string, problem?: ProblemDetails);
}
export declare class QuotaExceededError extends PdfCraftError {
    constructor(message: string, problem?: ProblemDetails);
}
