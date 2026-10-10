# PdfCraft SDK API Reference Manual

This document provides the exhaustive, domain-by-domain function reference for the **PdfCraft Document Processing SDK** and **REST Service**. It documents all available operations, parameters, return types, error conditions, and multi-language code examples across **Rust**, **Python**, and **TypeScript**.

---

## Table of Contents

- [Domain 1: Document Assembly & Merging (`merge`)](#domain-1-document-assembly--merging)
- [Domain 2: Page Organization & Splitting (`split`)](#domain-2-page-organization--splitting)
- [Domain 3: Visual Rasterization & Previews (`render_page`)](#domain-3-visual-rasterization--previews)
- [Domain 4: Core Value Objects (`DocumentSource` & `DocumentResult`)](#domain-4-core-value-objects)
- [Domain 5: Asynchronous Job Lifecycle & Governance (REST Service)](#domain-5-asynchronous-job-lifecycle--governance)
- [Domain 6: Client Configuration & Resource Quotas](#domain-6-client-configuration--resource-quotas)
- [Domain 7: Error Taxonomy & Exception Handling](#domain-7-error-taxonomy--exception-handling)

---

## Domain 1: Document Assembly & Merging

### `merge` / `mergeDocuments`

Combines two or more distinct PDF documents into a single unified document. Supports mixing in-memory byte buffers and filesystem paths, selective page range inclusion, and virtual output filenames. Automatically spills the result to temporary disk storage if the generated output exceeds the memory quota (default 10 MB).

#### Signatures by Language

| Language | Client | Method Signature |
|---|---|---|
| **Rust** | `LocalClient` / `RestClient` | `fn merge(&self, sources: &[DocumentSource], options: MergeOptions) -> Result<DocumentResult, SdkError>` |
| **Python** | `LocalClient` / `RestClient` | `def merge(self, sources: List[Union[str, Path, bytes, DocumentSource]], options: Optional[MergeOptions] = None) -> DocumentResult` |
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `mergeDocuments(sources: (string \| Buffer \| DocumentSource)[], options?: MergeOptions): Promise<DocumentResult>` |
| **REST** | HTTP Daemon | `POST /v1/merged-pdf` (Header: `Prefer: respond-async` for 202 Job response) |

#### Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `sources` | `Array` / `List` | **Yes** | — | Ordered collection of PDF document sources (minimum 1 item). Rejects empty input. |
| `options.output_filename` | `String` | No | `None` | Virtual filename for the generated output metadata or HTTP `Content-Disposition`. |
| `options.pages` | `List[String]` | No | `None` | Optional page range selectors (e.g. `["1-3", "5"]`). 1-based indexing. |

#### Return Value (`DocumentResult`)
- **`data` / `bytes`**: In-memory byte slice containing the compiled PDF document.
- **`mime_type`**: MIME type string (`"application/pdf"`).
- **`is_spilled()`**: Boolean indicating if the result was automatically written to disk due to size threshold.
- **`save_to_path(path)`**: Helper method to persist output directly to disk atomically.

#### Error Conditions
- `INVALID_ARGUMENT`: Input `sources` array is empty, or specified page numbers are $\le 0$.
- `NOT_FOUND`: A filesystem path provided in `sources` does not exist on disk.
- `QUOTA_EXCEEDED`: Total input size exceeds `max_input_bytes` (128 MB default).
- `ENGINE_ERROR`: One or more input files are severely corrupted and cannot be repaired.

#### Code Examples

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

fn main() -> Result<(), SdkError> {
    let client = LocalClient::default();

    let sources = vec![
        DocumentSource::from_path("cover.pdf"),
        DocumentSource::from_bytes(b"%PDF-1.4...".to_vec(), Some("section1.pdf".into())),
        DocumentSource::from_path("appendix.pdf"),
    ];

    let options = MergeOptions {
        output_filename: Some("combined_report.pdf".into()),
        pages: Some(vec!["1-5".into(), "10".into()]),
    };

    let result = client.merge(&sources, options)?;
    println!("Merged PDF: {} bytes (Spilled: {})", result.byte_len(), result.is_spilled());
    result.save_to_path("final.pdf")?;
    Ok(())
}
```

##### Python
```python
from pathlib import Path
from pdfcraft.local import LocalClient
from pdfcraft.types import DocumentSource, MergeOptions

client = LocalClient()

sources = [
    Path("cover.pdf"),
    b"%PDF-1.4 in-memory bytes",
    "appendix.pdf",
]

options = MergeOptions(output_filename="combined_report.pdf")
result = client.merge(sources, options=options)

print(f"Merged PDF size: {len(result.data):,} bytes (MIME: {result.mime_type})")
result.save_to_path("final.pdf")
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
    outputFilename: "combined_report.pdf",
  });

  console.log(`Merged PDF: ${result.data.length} bytes`);
  await result.saveToPath("final.pdf");
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
| **Python** | `LocalClient` / `RestClient` | `def split(self, source: Union[str, Path, bytes, DocumentSource], every_n_pages: Optional[int] = None, before_pages: Optional[List[int]] = None, at_bookmarks: Optional[int] = None) -> SplitResult` |
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `splitDocument(source: string \| Buffer \| DocumentSource, options?: SplitOptions): Promise<SplitResult>` |
| **REST** | HTTP Daemon | `POST /v1/split-pdf` |

#### Partitioning Modes (`SplitMode`)

| Mode | Options Key | Arguments | Description |
|---|---|---|---|
| **Every N Pages** | `every_n_pages` | `n: usize` | Partitions document into consecutive chunks of $N$ pages each. |
| **Before Pages** | `before_pages` | `pages: Vec<usize>` | Inserts cut-points immediately before specified 1-based page indices. |
| **At Bookmarks** | `at_bookmarks` | `level: usize` | Splits at outline / table-of-contents bookmarks matching the hierarchy level. |

#### Return Value (`SplitResult`)
- **`files`**: Array/List of filesystem paths (`Vec<PathBuf>` / `List[Path]` / `string[]`) pointing to generated PDF parts.
- **`count()`**: Total number of partitioned files generated.

#### Error Conditions
- `INVALID_ARGUMENT`: Source document is empty, chunk size is $0$, or split page cut-point is $\le 0$.
- `NOT_FOUND`: Source document file path does not exist.
- `ENGINE_ERROR`: Source document contains malformed cross-reference tables that prevent page tree extraction.

#### Code Examples

##### Rust
```rust
use pdfcraft_sdk::prelude::*;

fn main() -> Result<(), SdkError> {
    let client = LocalClient::default();
    let source = DocumentSource::from_path("large_document.pdf");

    // Mode A: Split every 2 pages
    let result = client.split(&source, &SplitMode::EveryNPages(2))?;
    println!("Generated {} partitions: {:?}", result.files.len(), result.files);

    // Mode B: Split before page 5 and page 10
    let custom_split = client.split(&source, &SplitMode::BeforePages(vec![5, 10]))?;
    println!("Cut at boundaries: {:?}", custom_split.files);
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

# Split before specific pages
custom = client.split("large_document.pdf", before_pages=[3, 7])
print(f"Custom partitions: {[f.name for f in custom.files]}")
```

##### TypeScript
```typescript
import { PdfCraftLocalClient } from "@pdfcraft/sdk";

async function main() {
  const client = new PdfCraftLocalClient();

  // Split every 2 pages
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
| **TypeScript** | `PdfCraftLocalClient` / `PdfCraftRestClient` | `renderPagePreview(source: string \| Buffer \| DocumentSource, page: number, maxSide?: number): Promise<DocumentResult>` |
| **REST** | HTTP Daemon | `POST /v1/page-preview` |

#### Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `source` | `DocumentSource` | **Yes** | — | Input PDF document (path or in-memory byte buffer). |
| `page` / `page_number` | `Integer` | **Yes** | — | 1-based page index. Rejects $0$ with `INVALID_ARGUMENT`. |
| `options.dpi` | `Float` | No | `150.0` | Physical target DPI (screen `72.0`, tablet `150.0`, print `300.0`, archival `600.0`). |
| `options.image_format` | `String` | No | `"png"` | Target raster format (`"png"` or `"jpeg"`). |
| `options.max_side` | `Integer` | No | `None` | Bounding-box constraint in pixels (clamps longest dimension, 1–4096 px). |

#### Return Value (`DocumentResult`)
- **`data` / `png_bytes`**: Raw raster image bytes (PNG or JPEG).
- **`mime_type`**: MIME type string (`"image/png"` or `"image/jpeg"`).
- **`save_to_path(path)`**: Persists the raster image directly to disk.

#### Error Conditions
- `INVALID_ARGUMENT`: Page number is $\le 0$, or requested page exceeds the total page count.
- `QUOTA_EXCEEDED`: Target DPI exceeds the configured limit (default 600.0 DPI).
- `ENGINE_ERROR`: Font rendering failure or corrupted content stream on designated page.

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
  const preview = await client.renderPagePreview("specimen.pdf", 1, 1024);
  console.log(`Rendered preview: ${preview.data.length} bytes (MIME: ${preview.mimeType})`);
  await preview.saveToPath("preview.png");
}

main().catch(console.error);
```

---

## Domain 4: Core Value Objects

### `DocumentSource`

Represents an input PDF document, decoupling SDK calls from raw filesystem dependencies and enabling transparent in-memory or streamed execution.

| Method / Constructor | Language | Description |
|---|---|---|
| `DocumentSource::from_path(path)` | Rust, Python, TS | Wraps a filesystem path without loading full content into memory immediately. |
| `DocumentSource::from_bytes(data, name)` | Rust, Python, TS | Wraps raw in-memory PDF byte buffers with an optional virtual filename. |
| `source.byte_len()` | Rust, Python, TS | Returns known in-memory byte length, or reads file metadata. |
| `source.name()` | Rust, Python, TS | Returns virtual or file name. |

### `DocumentResult`

Represents the generated binary output of an SDK operation, encapsulating automatic disk spillover when outputs exceed memory thresholds.

| Method / Property | Language | Description |
|---|---|---|
| `result.data()` / `.data` | Rust, Python, TS | Returns raw bytes in memory (reading from temporary file if spilled). |
| `result.save_to_path(path)` | Rust, Python, TS | Atomically writes the result to disk without redundant memory reallocation. |
| `result.is_spilled()` | Rust, Python, TS | Returns `true` if output automatically spilled to disk (> 10 MB threshold). |
| `result.mime_type()` | Rust, Python, TS | Returns content MIME type (`"application/pdf"`, `"image/png"`). |

---

## Domain 5: Asynchronous Job Lifecycle & Governance

For high-volume server operations or microservice architectures, `pdfcraft-rest` provides an asynchronous job state machine with crash-safe file journaling.

### Job State Transitions

```text
       ┌───────────┐
       │  Queued   │
       └─────┬─────┘
             │ (Worker dequeues)
             ▼
       ┌───────────┐
       │  Running  │
       └─────┬─────┘
             │
 ┌───────────┼───────────┐
 │ (Success) │ (Failure) │ (Client cancel)
 ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Succeeded│ │ Failed  │ │Canceled │  <-- Terminal States (Immutable)
└─────────┘ └─────────┘ └─────────┘
```

### Job Operations & Endpoints

| Operation | HTTP Route | Method | Description |
|---|---|---|---|
| **Submit Job** | `POST /v1/{operation}` | POST | Submit with `Prefer: respond-async` header. Returns `202 Accepted` + Job ID. |
| **Get Status** | `GET /v1/jobs/{id}` | GET | Returns current state (`Queued`, `Running`, `Succeeded`, `Failed`, `Canceled`). |
| **Get Result** | `GET /v1/jobs/{id}/result`| GET | Downloads completed binary artifact if `Succeeded`. Returns 409 if still Running. |
| **Cancel Job** | `DELETE /v1/jobs/{id}` | DELETE | Cancels a Queued or Running job. Rejects terminal jobs with 409 Conflict. |

#### Code Examples

##### Python (Asynchronous Job Polling)
```python
from pdfcraft.rest import RestClient

client = RestClient(base_url="http://127.0.0.1:8080", auth_token="secret-token")

# Submit asynchronous merge job
job = client.merge_async(["large1.pdf", "large2.pdf"])
print(f"Submitted job ID: {job.job_id}")

# Poll with timeout
result = job.wait_for_completion(timeout_secs=120)
print(f"Job completed: {len(result.data):,} bytes")
result.save_to_path("merged_output.pdf")
```

##### TypeScript (Asynchronous Job Polling)
```typescript
import { PdfCraftRestClient } from "@pdfcraft/sdk";

const client = new PdfCraftRestClient({
  baseUrl: "http://127.0.0.1:8080",
  authToken: "secret-token",
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

### Resource Limits Specification

Configurable resource constraints guard against out-of-memory crashes and resource starvation:

| Configuration Property | Type | Default | Description |
|---|---|---|---|
| `max_memory_bytes` | `usize` | `10 * 1024 * 1024` (10 MB) | Memory threshold before outputs automatically spill to temporary disk files. |
| `max_input_bytes` | `usize` | `128 * 1024 * 1024` (128 MB) | Maximum accepted single payload size before fast rejection. |
| `max_render_dpi` | `f32` | `600.0` | Upper limit for raster rendering resolution. |
| `max_workers` | `usize` | CPU core count | Bounded worker semaphore pool size for the REST daemon. |
| `job_retention_secs` | `u64` | `86400` (24 hours) | Duration to retain finished job artifacts in disk storage. |

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
| `ENGINE_ERROR` | 500 | `SdkError::EngineError` | `PdfCraftError` | `PdfCraftError` | PDF syntax corruption or unrecoverable object error |
| `ENGINE_PANIC_CONTAINED`| 500 | `SdkError::EnginePanic` | `PdfCraftError` | `PdfCraftError` | Escaped internal panic safely caught by `catch_unwind` |

#### Exception Handling Example

```python
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
