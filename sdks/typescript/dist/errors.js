/**
 * Error hierarchy for the PdfCraft TypeScript SDK.
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/errors.ts
 * Purpose:
 *   Provides structured, typed exceptions mapped cleanly from engine errors
 *   and HTTP RFC 7807 Problem Details.
 */
export class PdfCraftError extends Error {
    statusCode;
    errorCode;
    problem;
    constructor(message, statusCode = 500, errorCode = "ENGINE_ERROR", problem) {
        super(message);
        this.name = "PdfCraftError";
        this.statusCode = statusCode;
        this.errorCode = errorCode;
        this.problem = problem;
    }
}
export class InvalidArgumentError extends PdfCraftError {
    constructor(message, problem) {
        super(message, 400, "INVALID_ARGUMENT", problem);
        this.name = "InvalidArgumentError";
    }
}
export class NotFoundError extends PdfCraftError {
    constructor(message, problem) {
        super(message, 404, "NOT_FOUND", problem);
        this.name = "NotFoundError";
    }
}
export class ConflictError extends PdfCraftError {
    constructor(message, problem) {
        super(message, 409, "CONFLICT", problem);
        this.name = "ConflictError";
    }
}
export class QuotaExceededError extends PdfCraftError {
    constructor(message, problem) {
        super(message, 413, "QUOTA_EXCEEDED", problem);
        this.name = "QuotaExceededError";
    }
}
