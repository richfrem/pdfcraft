# PdfCraft SDK API Reference Manual

This document provides the exhaustive, domain-by-domain function reference for the **PdfCraft Document Processing SDK** and **REST Service**. It documents all available operations, parameters, return types, edge cases, resource boundaries, and multi-language code examples across **Rust**, **Python**, and **TypeScript**.

---

## Table of Contents

- [Architectural Conventions & Cross-Language Casing](#architectural-conventions--cross-language-casing)
- [Domain 1: Document Assembly & Merging (`merge`)](#domain-1-document-assembly--merging)
- [Domain 2: Page Organization & Splitting (`split`)](#domain-2-page-organization--splitting)
- [Domain 3: Visual Rasterization & Previews (`render_page`)](#domain-3-visual-rasterization--previews)
- [Domain 4: Core Value Objects (`DocumentSource` & `DocumentResult`)](#domain-4-core-value-objects)
- [Domain 5: Asynchronous Job Lifecycle & Governance (REST Service)](#domain-5-asynchronous-job-lifecycle--governance)
- [Domain 6: Client Configuration & Resource Quotas](#domain-6-client-configuration--resource-quotas)
- [Domain 7: Error Taxonomy & Exception Handling](#domain-7-error-taxonomy--exception-handling)

---

## Architectural Conventions & Cross-Language Casing

PdfCraft maintains a unified operation vocabulary across transports and languages. The table below defines the mechanical mapping conventions applied across SDK bindings:

| Logical Concept | Rust (`pdfcraft-sdk`) | Python (`pdfcraft`) | TypeScript (`@pdfcraft/sdk`) | REST OpenAPI Field |
|---|---|---|---|---|
| Merge Operation | `client.merge(...)` | `client.merge(...)` | `client.mergeDocuments(...)`| `POST /v1/merged-pdf` |
| Split Operation | `client.split(...)` | `client.split(...)` | `client.splitDocument(...)` | `POST /v1/split-pdf` |
| Render Operation| `client.render_page(...)` | `client.render_page(...)` | `client.renderPagePreview(...)`| `POST /v1/page-preview` |
| Output Filename | `options.output_filename` | `options.output_filename` | `options.outputFilename` | `output_filename` |
| Target DPI | `options.dpi` | `options.dpi` | `options.dpi` | `dpi` |
| Max Side (Px) | `options.max_side` | `options.max_side` | `options.maxSide` | `max_side` |
| Image Format | `options.image_format` | `options.image_format` | `options.imageFormat` | `image_format` |
| Page Number | `page: usize` (1-based) | `page_number: int` (1-based) | `page: number` (1-based) | `page` |

All paths and endpoints are strictly environment-independent. Code examples use environment variables or explicit placeholders (`$PDFCRAFT_BASE_URL`, `$PDFCRAFT_AUTH_TOKEN`) rather than hardcoded credentials or host assumptions.

---

## Domain 1: Document Assembly & Merging

### `merge` / `mergeDocuments`

Combines one or more distinct PDF documents into a single unified document. Supports mixing in-memory byte buffers and filesystem paths, selective page range inclusion, and virtual output filenames. Automatically spills the result to temporary disk storage if the generated output exceeds the memory quota (default 10 MB) to protect host processes from out-of-memory errors.

#### Signatures by Language

| Language | Client | Method Signature |
|---|---|---|
| **Rust** | `LocalClient` / `RestClient` | `fn merge(&self, sources: &[DocumentSource], options: MergeOptions) -> Result<DocumentResult, SdkError>` |
| **Python** | `LocalClient` / `RestClient` | `def merge(self, sources: List[Union[str, Path, bytes, DocumentSource]], options: Optional[MergeOptions] = None) -> DocumentResult` |
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `mergeDocuments(sources: (string \| Buffer \| DocumentSource)[], options?: MergeOptions): Promise<DocumentResult>` |
| **REST** | HTTP Daemon | `POST /v1/merged-pdf` (Header: `Prefer: respond-async` for 202 Job response) |

#### Parameters & Options (`MergeOptions`)

| Parameter | Type | Required | Default | Validation & Edge-Case Rules |
|---|---|---|---|---|
| `sources` | `Array` / `List` | **Yes** | — | Minimum 1 source. Rejects empty list with `INVALID_ARGUMENT`. Single source acts as passthrough re-encryption/repair. |
| `options.output_filename` | `String` | No | `None` | Virtual filename for generated metadata or HTTP `Content-Disposition`. |
| `options.pages` | `List[String]` | No | `None` | Optional page range selectors (e.g. `["1-3", "5"]`). 1-based indexing. Grammar: `positive_int` or `start "-" end` where `start <= end`. Out-of-bounds pages return `INVALID_ARGUMENT`. |

#### Return Value (`DocumentResult`)
- **`data` / `bytes`**: Raw bytes in memory. *(Note: for spilled artifacts $> 10$ MB, reading `.data` re-reads from disk; use `.save_to_path()` for zero-allocation disk streaming).*
- **`mime_type`**: MIME type string (`"application/pdf"`).
- **`is_spilled()`**: Boolean indicating if the result automatically spilled to disk.
- **`save_to_path(path)`**: Atomically writes output to disk using a write-then-rename protocol.

#### Code Examples

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

fn main() -> Result<(), SdkError> {
    let client = LocalClient::default();

    let sources = vec![
        DocumentSource::from_path("cover.pdf"),
        DocumentSource::from_bytes(b"%PDF-1.4 sample content".to_vec(), Some("section1.pdf".into())),
        DocumentSource::from_path("appendix.pdf"),
    ];

    let options = MergeOptions {
        output_filename: Some("report.pdf".into()),
        pages: Some(vec!["1-5".into(), "10".into()]),
    };

    let result = client.merge(&sources, options)?;
    println!("Merged PDF: {} bytes (Spilled to disk: {})", result.byte_len(), result.is_spilled());
    result.save_to_path("final_report.pdf")?;
    Ok(())
}
```

##### Python
```python
import os
from pathlib import Path
from pdfcraft.local import LocalClient
from pdfcraft.types import DocumentSource, MergeOptions

client = LocalClient()

sources = [
    Path("cover.pdf"),
    b"%PDF-1.4 in-memory bytes",
    "appendix.pdf",
]

options = MergeOptions(output_filename="report.pdf")
result = client.merge(sources, options=options)

print(f"Merged PDF size: {len(result.data):,} bytes (MIME: {result.mime_type})")
result.save_to_path("final_report.pdf")
```

##### TypeScript
```typescript
import { PdfCraftLocalClient, DocumentSource } from "@pdfcraft/sdk";
import * as fs from "node:fs";

async function main() {
  const client = new PdfCraftLocalClient();

  const sources = [
    "cover.pdf",
    fs.readFileSync("section1.pdf"),
    DocumentSource.fromPath("appendix.pdf"),
  ];

  const result = await client.mergeDocuments(sources, {
    outputFilename: "report.pdf",
  });

  console.log(`Merged PDF: ${result.data.length} bytes (Spilled: ${result.isSpilled})`);
  await result.saveToPath("final_report.pdf");
}

main().catch(console.error);
```

---

## Domain 2: Page Organization & Splitting

### `split` / `splitDocument`

Partitions an input PDF document into multiple discrete PDF files using one of three partitioning strategies: chunking into fixed-size page groups, cutting before specific page numbers, or splitting at outline bookmark headings.

#### Signatures by Language

| Language | Client | Method Signature |
|---|---|---|
| **Rust** | `LocalClient` / `RestClient` | `fn split(&self, source: &DocumentSource, mode: &SplitMode) -> Result<SplitResult, SdkError>` |
| **Python** | `LocalClient` / `RestClient` | `def split(self, source: Union[str, Path, bytes, DocumentSource], every_n_pages: Optional[int] = None, before_pages: Optional[List[int]] = None, bookmark_level: Optional[int] = None) -> SplitResult` |
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `splitDocument(source: string \| Buffer \| DocumentSource, options?: SplitOptions): Promise<SplitResult>` |
| **REST** | HTTP Daemon | `POST /v1/split-pdf` |

#### Partitioning Modes (`SplitMode` / `SplitOptions`)

| Mode | Field Name | Argument Type | Validation & Invariant Rules |
|---|---|---|---|
| **Every N Pages** | `every_n_pages` / `everyNPages` | `usize` / `int` | Partitions document into consecutive chunks of $N$ pages each ($N \ge 1$). Rejects $N=0$ with `INVALID_ARGUMENT`. |
| **Before Pages** | `before_pages` / `beforePages` | `List[usize]` | Inserts cut-points immediately before specified 1-based page indices. Cut points are automatically sorted and deduplicated. Rejects cut points $\le 1$ or $> \text{page\_count}$. |
| **At Bookmarks** | `bookmark_level` / `bookmarkLevel` | `usize` / `int` | Splits at outline bookmarks matching the hierarchy level ($1$-based). If document has no matching bookmarks, returns single partition containing full document. |

#### Return Value (`SplitResult`)
- **`files`**: Collection of filesystem paths (`Vec<PathBuf>` / `List[Path]` / `string[]`) pointing to generated PDF parts.
- **`count()`**: Total number of partitioned files generated.
- **Lifecycle & Cleanup:** Local client partitions are created in the configured working directory; caller owns file disposal.

#### Code Examples

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

fn main() -> Result<(), SdkError> {
    let client = LocalClient::default();
    let source = DocumentSource::from_path("large_document.pdf");

    // Partition every 2 pages
    let result = client.split(&source, &SplitMode::EveryNPages(2))?;
    println!("Generated {} partitions: {:?}", result.files.len(), result.files);

    // Custom boundary split: cut before pages 5 and 10
    let custom = client.split(&source, &SplitMode::BeforePages(vec![5, 10]))?;
    println!("Partitions: {:?}", custom.files);
    Ok(())
}
```

##### Python
```python
from pdfcraft.local import LocalClient

client = LocalClient()

# Split every 5 pages
result = client.split("large_document.pdf", every_n_pages=5)
for file_path in result.files:
    print(f"Generated partition: {file_path.name}")

# Split before specific page numbers
custom = client.split("large_document.pdf", before_pages=[3, 7])
print(f"Custom partitions: {[f.name for f in custom.files]}")
```

##### TypeScript
```typescript
import { PdfCraftLocalClient } from "@pdfcraft/sdk";

async function main() {
  const client = new PdfCraftLocalClient();

  const result = await client.splitDocument("large_document.pdf", {
    everyNPages: 2,
  });

  console.log(`Generated ${result.files.length} partitions:`);
  result.files.forEach((file) => console.log(` - ${file}`));
}

main().catch(console.error);
```

---

## Domain 3: Visual Rasterization & Previews

### `render_page` / `renderPagePreview`

Renders an exact page of a PDF document into a raster image (PNG or JPEG) at a precise physical resolution. Physical resolution is strictly decoupled from host operating system display scaling (#739), calculating dimensions strictly via:

$$\text{pixels} = \frac{\text{points} \times \text{dpi}}{72.0}$$

#### Signatures by Language

| Language | Client | Method Signature |
|---|---|---|
| **Rust** | `LocalClient` / `RestClient` | `fn render_page(&self, source: &DocumentSource, page: usize, options: &RenderOptions) -> Result<DocumentResult, SdkError>` |
| **Python** | `LocalClient` / `RestClient` | `def render_page(self, source: Union[str, Path, bytes, DocumentSource], page_number: int, options: Optional[RenderOptions] = None) -> DocumentResult` |
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `renderPagePreview(source: string \| Buffer \| DocumentSource, page: number, options?: RenderOptions): Promise<DocumentResult>` |
| **REST** | HTTP Daemon | `POST /v1/page-preview` |

#### Parameters & Options (`RenderOptions`)

| Parameter | Type | Required | Default | Description & Bounds |
|---|---|---|---|---|
| `source` | `DocumentSource` | **Yes** | — | Input PDF document (path or in-memory byte buffer). |
| `page` / `page_number` | `Integer` | **Yes** | — | 1-based page index. Rejects $\le 0$ or $> \text{page\_count}$ with `INVALID_ARGUMENT`. |
| `options.dpi` | `Float` | No | `150.0` | Physical target DPI (screen `72.0`, tablet `150.0`, print `300.0`, archival `600.0`). Capped at `max_render_dpi` (600.0). |
| `options.image_format` | `String` | No | `"png"` | Target raster format (`"png"` with alpha or `"jpeg"` with white composited background). |
| `options.max_side` | `Integer` | No | `None` | Bounding-box constraint in pixels (clamps longest dimension, 1–4096 px). Preserves aspect ratio. |

#### Deterministic Rasterization Guarantees
- Fractional pixel dimensions are rounded to the nearest integer using standard round-half-up.
- Non-opaque background pages composite over an opaque `#FFFFFF` white matte when rendering to JPEG.
- If calculated raster dimensions exceed `max_render_pixels` ($16,384 \times 16,384$ px), operation fails fast with `QUOTA_EXCEEDED`.

#### Code Examples

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

fn main() -> Result<(), SdkError> {
    let client = LocalClient::default();
    let source = DocumentSource::from_path("specimen.pdf");

    // Render Page 1 at print-quality 300 DPI
    let image = client.render_page(&source, 1, &RenderOptions {
        dpi: 300.0,
        image_format: "png".into(),
        max_side: None,
    })?;

    println!("Rendered PNG: {} bytes", image.byte_len());
    image.save_to_path("page1_300dpi.png")?;
    Ok(())
}
```

##### Python
```python
from pdfcraft.local import LocalClient
from pdfcraft.types import RenderOptions

client = LocalClient()

# Render page 1 at 300 DPI
preview = client.render_page(
    "specimen.pdf",
    page_number=1,
    options=RenderOptions(dpi=300.0, image_format="png"),
)

with open("page1_300dpi.png", "wb") as f:
    f.write(preview.png_bytes)
```

##### TypeScript
```typescript
import { PdfCraftLocalClient } from "@pdfcraft/sdk";

async function main() {
  const client = new PdfCraftLocalClient();

  // Render page 1 preview clamped to max 1024px side
  const preview = await client.renderPagePreview("specimen.pdf", 1, {
    dpi: 150.0,
    maxSide: 1024,
    imageFormat: "png",
  });

  console.log(`Rendered preview: ${preview.data.length} bytes (MIME: ${preview.mimeType})`);
  await preview.saveToPath("preview.png");
}

main().catch(console.error);
```

---

## Domain 4: Core Value Objects

### `DocumentSource`

Represents an input PDF document, decoupling SDK calls from raw filesystem dependencies and enabling transparent in-memory or streamed execution.

| Method / Constructor | Language | Description & Invariants |
|---|---|---|
| `DocumentSource::from_path(path)` | Rust, Python, TS | Wraps a filesystem path lazily. Validates file existence and readability at execution time. |
| `DocumentSource::from_bytes(data, name)` | Rust, Python, TS | Wraps raw in-memory PDF byte buffers with an optional virtual filename. Zero-copy buffer slice where supported. |
| `source.byte_len()` | Rust, Python, TS | Returns known in-memory byte length, or reads filesystem metadata. |
| `source.name()` | Rust, Python, TS | Returns virtual filename or basename of the path. |

### `DocumentResult`

Represents the generated binary output of an SDK operation, encapsulating automatic disk spillover when outputs exceed memory thresholds.

| Method / Property | Language | Description & Resource Behavior |
|---|---|---|
| `result.data()` / `.data` | Rust, Python, TS | Returns raw bytes in memory. *(Note: For spilled results, reading `.data` allocates full memory. For large files, use `.save_to_path()`)*. |
| `result.save_to_path(path)` | Rust, Python, TS | Atomically writes result to destination using a temporary write-then-rename protocol. Never leaves partial files on failure. |
| `result.is_spilled()` | Rust, Python, TS | Returns `true` if output automatically spilled to disk (> 10 MB threshold). |
| `result.mime_type()` | Rust, Python, TS | Returns content MIME type (`"application/pdf"`, `"image/png"`, `"image/jpeg"`). |

---

## Domain 5: Asynchronous Job Lifecycle & Governance (REST Service)

For high-volume server operations or microservice fleets, `pdfcraft-rest` provides an asynchronous job state machine backed by atomic CAS state transitions and crash-resilient disk journaling.

### Job State Machine

```text
       ┌───────────┐
       │  Queued   │
       └─────┬─────┘
             │ (Worker dequeues)
             ▼
       ┌───────────┐
       │  Running   │
       └─────┬─────┘
             │
 ┌───────────┼───────────┐
 │ (Success) │ (Failure) │ (Client cancel)
 ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Succeeded│ │ Failed  │ │Canceled │  <-- Terminal States (Immutable)
└─────────┘ └─────────┘ └─────────┘
```

### State Transition & Concurrency Invariants
- **Atomic CAS Transitions:** State changes occur via atomic Compare-And-Swap (`transition(expected, target)`).
- **Terminal Immutability:** Once a job reaches `Succeeded`, `Failed`, or `Canceled`, its state is permanently frozen. Subsequent state transition requests return HTTP `409 Conflict`.
- **Cancellation Race Invariant:** If cancellation is requested while a job is transitioning to `Succeeded`, the successful artifact is preserved and cancellation returns `409 Conflict`.
- **Artifact Expiration:** Finished artifacts are retained for `job_retention_secs` (default 24h). Requesting an expired job result returns HTTP `410 Gone`.

### REST Endpoints Summary

| Operation | Route | Method | Success Code | Error Codes |
|---|---|---|---|---|
| **Submit Async Job** | `POST /v1/{operation}` | POST | `202 Accepted` | 400, 401, 413, 429 |
| **Get Job Status** | `GET /v1/jobs/{id}` | GET | `200 OK` | 401, 404 |
| **Download Result** | `GET /v1/jobs/{id}/result` | GET | `200 OK` | 401, 404, 409 (still running), 410 (expired) |
| **Cancel Job** | `DELETE /v1/jobs/{id}` | DELETE | `204 No Content` | 401, 404, 409 (already terminal) |

#### Code Examples (Asynchronous Polling with Environment Variables)

##### Python
```python
import os
from pdfcraft.rest import RestClient

base_url = os.environ.get("PDFCRAFT_BASE_URL", "http://127.0.0.1:8080")
auth_token = os.environ.get("PDFCRAFT_AUTH_TOKEN", "test-token")

client = RestClient(base_url=base_url, auth_token=auth_token)

# Submit asynchronous job
job = client.merge_async(["large1.pdf", "large2.pdf"])
print(f"Submitted Job ID: {job.job_id}")

# Poll with timeout
result = job.wait_for_completion(timeout_secs=120)
print(f"Job completed: {len(result.data):,} bytes")
result.save_to_path("merged_output.pdf")
```

##### TypeScript
```typescript
import { PdfCraftRestClient } from "@pdfcraft/sdk";

const client = new PdfCraftRestClient({
  baseUrl: process.env.PDFCRAFT_BASE_URL ?? "http://127.0.0.1:8080",
  authToken: process.env.PDFCRAFT_AUTH_TOKEN ?? "test-token",
});

async function run() {
  const job = await client.submitMergeJob(["large1.pdf", "large2.pdf"]);
  console.log(`Submitted Job ID: ${job.jobId}`);

  const result = await job.waitForCompletion(120000);
  console.log(`Job finished: ${result.data.length} bytes`);
  await result.saveToPath("merged_output.pdf");
}

run().catch(console.error);
```

---

## Domain 6: Client Configuration & Resource Quotas

Resource limits prevent memory ballooning, worker starvation, and denial-of-service crashes:

| Configuration Property | Target Layer | Default Value | Description & Enforcement |
|---|---|---|---|
| `max_memory_bytes` | Local Client | `10 * 1024 * 1024` (10 MB) | Memory threshold before outputs automatically spill to temporary disk files. |
| `max_input_bytes` | Local & REST | `128 * 1024 * 1024` (128 MB) | Maximum accepted single payload size before fast rejection with `QUOTA_EXCEEDED` (413). |
| `max_render_dpi` | Local & REST | `600.0` | Upper limit for raster rendering resolution. Rejects higher values with `INVALID_ARGUMENT`. |
| `max_workers` | REST Daemon | CPU core count | Bounded worker semaphore pool size. Rejects queue overflow with `WORKER_POOL_SATURATED` (429). |
| `job_retention_secs` | REST Daemon | `86400` (24 hours) | Duration to retain finished job artifacts in disk storage before cleanup. |

#### Configuration Example

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

let client = LocalClient::builder()
    .max_memory_bytes(64 * 1024 * 1024)   // 64 MB memory threshold
    .max_input_bytes(256 * 1024 * 1024)   // 256 MB max document budget
    .build()?;
```

---

## Domain 7: Error Taxonomy & Exception Handling

All client and server errors map to standardized error categories across transports:

| Error Category | HTTP Code | Rust Enum | Python Exception | TypeScript Class | Trigger Condition |
|---|---|---|---|---|---|
| `INVALID_ARGUMENT` | 400 | `SdkError::InvalidArgument` | `InvalidArgumentError` | `InvalidArgumentError` | Empty sources, page index 0, malformed options |
| `UNAUTHORIZED` | 401 | `SdkError::Unauthorized` | `UnauthorizedError` | `UnauthorizedError` | Missing or invalid Bearer token |
| `NOT_FOUND` | 404 | `SdkError::NotFound` | `NotFoundError` | `NotFoundError` | Input file or Job ID does not exist |
| `CONFLICT` | 409 | `SdkError::Conflict` | `ConflictError` | `ConflictError` | Invalid state transition, canceling terminal job |
| `QUOTA_EXCEEDED` | 413 | `SdkError::QuotaExceeded` | `QuotaExceededError` | `QuotaExceededError` | Payload exceeds max size or DPI exceeds 600 |
| `WORKER_POOL_SATURATED` | 429 | `SdkError::PoolSaturated` | `PoolSaturatedError` | `PoolSaturatedError` | Server worker queue full under heavy compute load |
| `GONE` | 410 | `SdkError::Gone` | `ArtifactExpiredError` | `ArtifactExpiredError` | Finished job artifact has exceeded retention time |
| `ENGINE_ERROR` | 500 | `SdkError::EngineError` | `PdfCraftError` | `PdfCraftError` | PDF syntax corruption or unrecoverable object error |
| `ENGINE_PANIC_CONTAINED`| 500 | `SdkError::EnginePanic` | `PdfCraftError` | `PdfCraftError` | Escaped internal panic safely caught by `catch_unwind` |

#### Normative Exception Handling Example

```python
import os
from pdfcraft.local import LocalClient
from pdfcraft.errors import InvalidArgumentError, QuotaExceededError, PdfCraftError

client = LocalClient()

try:
    result = client.merge([])
except InvalidArgumentError as e:
    print(f"Validation failed (HTTP 400 equivalent): {e}")
except QuotaExceededError as e:
    print(f"Resource quota exceeded (HTTP 413 equivalent): {e}")
except PdfCraftError as e:
    print(f"General engine error (HTTP 500 equivalent): {e}")
```
