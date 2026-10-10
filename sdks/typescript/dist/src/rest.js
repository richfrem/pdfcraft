"use strict";
/**
 * Remote REST SDK Client for PdfCraft (Issue #872).
 *
 * # Architecture Reference
 * Module: sdks/typescript/src/rest.ts
 * Purpose:
 *   Fetch-based client communicating with an on-premise PdfCraft REST daemon,
 *   providing 1:1 semantic parity with PdfCraftLocalClient.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PdfCraftRestClient = void 0;
const errors_js_1 = require("./errors.js");
class PdfCraftRestClient {
    baseUrl;
    authToken;
    timeoutMs;
    constructor(options) {
        this.baseUrl = (options?.baseUrl ?? "http://127.0.0.1:8080").replace(/\/+$/, "");
        this.authToken = options?.authToken;
        this.timeoutMs = options?.timeoutMs ?? 60000;
    }
    async request(method, path, body, expectedStatus = 200) {
        const url = `${this.baseUrl}${path}`;
        const headers = {
            "Content-Type": "application/json",
        };
        if (this.authToken) {
            headers["Authorization"] = `Bearer ${this.authToken}`;
        }
        const response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
        });
        const status = response.status;
        const arrayBuffer = await response.arrayBuffer();
        const data = new Uint8Array(arrayBuffer);
        if (status !== expectedStatus && status !== 200 && status !== 202) {
            this.handleErrorResponse(data, status);
        }
        return { status, headers: response.headers, data };
    }
    handleErrorResponse(data, status) {
        let problem;
        try {
            problem = JSON.parse(new TextDecoder().decode(data));
        }
        catch {
            problem = {
                type: "about:blank",
                title: "HTTP Error",
                status,
                detail: `HTTP request failed with status ${status}`,
                code: "HTTP_ERROR",
            };
        }
        if (status === 400) {
            throw new errors_js_1.InvalidArgumentError(problem.detail, problem);
        }
        if (status === 404) {
            throw new errors_js_1.NotFoundError(problem.detail, problem);
        }
        if (status === 409) {
            throw new errors_js_1.ConflictError(problem.detail, problem);
        }
        if (status === 413 || status === 429) {
            throw new errors_js_1.QuotaExceededError(problem.detail, problem);
        }
        throw new errors_js_1.PdfCraftError(problem.detail, status, problem.code, problem);
    }
    /**
     * Merges multiple PDF documents via the REST daemon.
     */
    async merge(sources, options, asyncJob = false) {
        if (!sources || sources.length === 0) {
            throw new errors_js_1.InvalidArgumentError("Cannot merge zero files");
        }
        const filesPayload = sources.map((s) => {
            if (typeof s === "string") {
                return { path: s };
            }
            if (s instanceof Uint8Array) {
                return { data_base64: Buffer.from(s).toString("base64") };
            }
            if ("data" in s) {
                return { data_base64: Buffer.from(s.data).toString("base64"), name: s.name };
            }
            return { path: s.path };
        });
        const payload = {
            files: filesPayload,
            options: {
                output_filename: options?.outputFilename,
                pages: options?.pages,
            },
            async_job: asyncJob,
        };
        const res = await this.request("POST", "/v1/merged-pdf", payload, asyncJob ? 202 : 200);
        if (asyncJob) {
            const job = JSON.parse(new TextDecoder().decode(res.data));
            return this.pollJob(job.id);
        }
        const mime = res.headers.get("content-type") ?? "application/pdf";
        return {
            type: "memory",
            data: res.data,
            mimeType: mime,
        };
    }
    /**
     * Splits a PDF document via the REST daemon.
     */
    async split(source, mode) {
        let filePayload;
        if (typeof source === "string") {
            filePayload = { path: source };
        }
        else if (source instanceof Uint8Array) {
            filePayload = { data_base64: Buffer.from(source).toString("base64") };
        }
        else if ("data" in source) {
            filePayload = { data_base64: Buffer.from(source.data).toString("base64"), name: source.name };
        }
        else {
            filePayload = { path: source.path };
        }
        const payload = {
            file: filePayload,
            mode: mode ?? { EveryNPages: 1 },
            async_job: false,
        };
        const res = await this.request("POST", "/v1/split-pdf", payload);
        return JSON.parse(new TextDecoder().decode(res.data));
    }
    /**
     * Renders a PDF page to image via the REST daemon.
     */
    async renderPage(source, page, options) {
        if (page < 1) {
            throw new errors_js_1.InvalidArgumentError("Page index must be >= 1 (1-based index)");
        }
        let filePayload;
        if (typeof source === "string") {
            filePayload = { path: source };
        }
        else if (source instanceof Uint8Array) {
            filePayload = { data_base64: Buffer.from(source).toString("base64") };
        }
        else if ("data" in source) {
            filePayload = { data_base64: Buffer.from(source.data).toString("base64"), name: source.name };
        }
        else {
            filePayload = { path: source.path };
        }
        const payload = {
            file: filePayload,
            page,
            options: {
                dpi: options?.dpi ?? 150.0,
                format: options?.imageFormat ?? "png",
            },
            async_job: false,
        };
        const res = await this.request("POST", "/v1/page-preview", payload);
        const mime = res.headers.get("content-type") ?? "image/png";
        return {
            type: "memory",
            data: res.data,
            mimeType: mime,
        };
    }
    async pollJob(jobId) {
        const deadline = Date.now() + this.timeoutMs;
        while (Date.now() < deadline) {
            const res = await this.request("GET", `/v1/jobs/${jobId}`);
            const job = JSON.parse(new TextDecoder().decode(res.data));
            if (job.status === "succeeded") {
                const resultRes = await this.request("GET", `/v1/jobs/${jobId}/result`);
                const mime = resultRes.headers.get("content-type") ?? "application/pdf";
                return {
                    type: "memory",
                    data: resultRes.data,
                    mimeType: mime,
                };
            }
            if (job.status === "failed" || job.status === "canceled") {
                throw new errors_js_1.PdfCraftError(job.error ?? `Job ended in status ${job.status}`);
            }
            await new Promise((r) => setTimeout(r, 50));
        }
        throw new errors_js_1.PdfCraftError("Job polling timeout exceeded");
    }
}
exports.PdfCraftRestClient = PdfCraftRestClient;
