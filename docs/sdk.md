# PdfCraft Document Processing SDK & REST Service Guide

The **PdfCraft Document Processing SDK** provides a high-performance, `#![forbid(unsafe_code)]`, memory-safe document processing engine. It serves as an open-source alternative to the proprietary Adobe PDF Library (PDFL) for in-process execution, and pdfRest / Adobe PDF Services for containerized on-premise REST deployments.

---

## 1. Architectural Model: Dual-Transport Execution

PdfCraft provides identical capabilities across two execution modes with 1:1 semantic parity:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Unified Client API Contract                           │
│              merge(...)  │  split(...)  │  render_page(...)                 │
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
        ┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
        │     In-Process Driver       │ │     Remote REST Driver      │
        │       (LocalClient)         │ │        (RestClient)         │
        ├─────────────────────────────┤ ├─────────────────────────────┤
        │ • Zero network overhead     │ │ • HTTP/1.1 Loopback/LAN     │
        │ • In-memory byte buffers    │ │ • Async Job Polling         │
        │ • Native Rust / PyO3 / N-API│ │ • Multi-tenant Bearer Auth  │
        │ • Ephemeral sandbox drop    │ │ • Bounded Worker Semaphore  │
        └──────────────┬──────────────┘ └──────────────┬──────────────┘
                       │                               │
                       ▼                               ▼
        ┌─────────────────────────────┐ ┌─────────────────────────────┐
        │  AutomationEngineAdapter    │ │     pdfcraft-rest Server    │
        └──────────────┬──────────────┘ └──────────────┬──────────────┘
                       │                               │
                       └──────────────►◄───────────────┘
                                       │
                                       ▼
                       ┌──────────────────────────────┐
                       │ pdfcraft-engine / automation │
                       └──────────────────────────────┘
```

1. **In-Process Mode (`LocalClient`)**:
   - Links directly to `pdfcraft-engine` and `pdfcraft-automation` in memory.
   - Zero daemon lifecycle, zero port binding, zero network latency.
   - Ideal for CLI tools, local desktop software, and compute pipelines.

2. **On-Premise REST Mode (`RestClient`)**:
   - Connects over HTTP/HTTPS to a self-hosted `pdfcraft-rest` daemon.
   - Provides durable job state tracking, asynchronous polling, and worker pool governance.
   - Ideal for microservices, web backends, and multi-tenant architectures.

---

## 2. Divisions of Functions Overview

### 2.1 Document Merge (`merge`)
- **Capability**: Combines multiple independent PDF documents into a single unified PDF.
- **Input Types**: File paths (`PathBuf`, `str`, `Path`) or in-memory byte buffers (`Vec<u8>`, `bytes`, `Uint8Array`).
- **Options (`MergeOptions`)**:
  - `output_filename`: Optional virtual filename for output metadata.
  - `pages`: Specific page range selectors (e.g., `["1-3", "5"]`).
- **Memory Safety**: Documents under 10 MB are processed and returned directly in memory. Documents exceeding 10 MB automatically spill to disk returning a file handle.

### 2.2 Document Split & Extraction (`split`)
- **Capability**: Partitions a source document into multiple PDF slices.
- **Split Modes (`SplitMode`)**:
  - `EveryNPages(n)`: Splits the document into chunks of $N$ pages each.
  - `BeforePages(vec![p1, p2])`: Inserts split boundaries before designated page numbers.
  - `AtBookmarks(level)`: Splits at hierarchical outline bookmarks of the specified level.
- **Output**: Returns an array of paths pointing to the partitioned PDF files.

### 2.3 High-DPI Page Rendering (`render_page`)
- **Capability**: Renders a single page of a PDF document to a raster image at an exact physical DPI.
- **DPI Calculation**: Decoupled from monitor or OS PPI (#739); dimensions are computed strictly via:
  $$\text{pixels} = \frac{\text{points} \times \text{dpi}}{72.0}$$
- **Options (`RenderOptions`)**:
  - `dpi`: Physical target resolution (e.g. `72.0` screen, `150.0` tablet, `300.0` print, `600.0` archival).
  - `image_format`: Output raster format (`png` or `jpeg`).
- **Output**: Returns raster image bytes (`image/png` or `image/jpeg`).

### 2.4 Durable Job Lifecycle & State Machine
- **Endpoints**: `GET /v1/jobs/{id}`, `GET /v1/jobs/{id}/result`, `DELETE /v1/jobs/{id}`.
- **State Machine**:
  - `Queued` $\rightarrow$ `Running` $\rightarrow$ `Succeeded` (Terminal)
  - `Queued` / `Running` $\rightarrow$ `Failed` (Terminal)
  - `Queued` / `Running` $\rightarrow$ `Canceled` (Terminal)
- **Terminal Immutability**: Any job reaching a terminal state cannot be transitioned again; attempts return HTTP 409 Conflict.
- **Persistence**: Backed by a crash-resilient disk journal with automatic recovery upon restart.

### 2.5 Error Handling & RFC 7807 Problem Details
All client and server errors map to standardized RFC 7807 Problem Details schemas:
- `400 Bad Request` (`INVALID_ARGUMENT`): Missing files, page index 0, or malformed JSON.
- `401 Unauthorized` (`UNAUTHORIZED`): Missing or invalid Bearer authentication token.
- `404 Not Found` (`NOT_FOUND`): Non-existent document or job ID.
- `409 Conflict` (`CONFLICT`): Invalid state transition or canceling a terminal job.
- `413 / 429 Limit Exceeded` (`QUOTA_EXCEEDED` / `WORKER_POOL_SATURATED`): Input size exceeds quota or worker pool saturated.
- `500 Internal Error` (`ENGINE_ERROR` / `ENGINE_PANIC_CONTAINED`): Contained engine errors.

---

## 3. Language Guide: Rust Developers

### Crate Dependencies (`Cargo.toml`)
```toml
[dependencies]
pdfcraft-sdk = { path = "crates/sdk", version = "0.5.0" }
# Optional: for REST daemon and client
pdfcraft-rest = { path = "crates/rest", version = "0.5.0" }
```

### 3.1 In-Process Execution (`LocalClient`)
```rust
use pdfcraft_sdk::{DocumentSource, LocalClient, MergeOptions, PdfCraftClient, RenderOptions};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = LocalClient::default();

    // 1. Merge in-memory byte buffers
    let doc1 = DocumentSource::from_bytes(b"%PDF-1.4 sample 1".to_vec(), None);
    let doc2 = DocumentSource::from_path("sample-docs/policy.pdf");
    let merged = client.merge(&[doc1, doc2], MergeOptions::default())?;
    println!("Merged MIME: {}, Size: {} bytes", merged.mime_type(), merged.byte_len());

    // 2. High-DPI Page Rendering
    let render = client.render_page(
        &DocumentSource::from_path("sample-docs/schedule.pdf"),
        1,
        RenderOptions { dpi: 300.0, ..Default::default() },
    )?;
    println!("Rendered page 1 at 300 DPI: {} bytes", render.byte_len());

    Ok(())
}
```

### 3.2 Remote REST Daemon & Client (`RestClient`)
```rust
use std::sync::Arc;
use pdfcraft_rest::{BlockingExecutor, ExecutorConfig, HttpServer, InMemoryJobRepository, RestClient, RestService, ServerConfig};
use pdfcraft_sdk::{AutomationEngineAdapter, DocumentSource, MergeOptions, PdfCraftClient};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Start Server on Loopback
    let engine = Arc::new(AutomationEngineAdapter::default());
    let executor = Arc::new(BlockingExecutor::new(engine, ExecutorConfig::default()));
    let repo = Arc::new(InMemoryJobRepository::new());
    let service = Arc::new(RestService::new(executor, repo, Some("secret-token".into())));
    
    let server = HttpServer::start(service, ServerConfig {
        bind_addr: "127.0.0.1:8080".parse()?,
        allow_public_bind: false,
        auth_token: Some("secret-token".into()),
    })?;

    // 2. Connect via RestClient
    let client = RestClient::remote("http://127.0.0.1:8080", Some("secret-token".into()));
    let input = DocumentSource::from_bytes(b"%PDF-doc".to_vec(), None);
    let result = client.merge(&[input], MergeOptions::default())?;
    
    println!("REST Merge completed: {} bytes", result.byte_len());
    Ok(())
}
```

---

## 4. Language Guide: Python Developers

### Package Installation
```bash
pip install ./sdks/python
```

### 4.1 In-Process Execution (`pdfcraft.local.LocalClient`)
```python
from pathlib import Path
from pdfcraft.local import LocalClient
from pdfcraft.types import MergeOptions, RenderOptions

# Initialize in-process client (zero server required)
client = LocalClient()

# 1. Merge documents (accepts paths or bytes)
doc1 = Path("sample-docs/Optional-Car-Wordings-BCAA policy info.pdf")
doc2 = Path("sample-docs/osaka geidai schedule.pdf")

merged = client.merge([doc1, doc2], options=MergeOptions(output_filename="combined.pdf"))
print(f"Merged output size: {len(merged.data):,} bytes (MIME: {merged.mime_type})")

# 2. Split document
split = client.split(doc2, every_n_pages=1)
print(f"Split generated {len(split.files)} files: {[f.name for f in split.files]}")

# 3. High-DPI page render
rendered = client.render_page(doc2, page=1, options=RenderOptions(dpi=300.0))
print(f"Rendered page 1 at 300 DPI: {len(rendered.data):,} bytes")
```

### 4.2 Remote REST Client (`pdfcraft.rest.RestClient`)
```python
from pdfcraft.rest import RestClient
from pdfcraft.errors import InvalidArgumentError, PdfCraftError

client = RestClient(base_url="http://127.0.0.1:8080", auth_token="secret-token")

# 1. Synchronous Merge
try:
    result = client.merge(["doc1.pdf", "doc2.pdf"])
    print(f"Sync merge: {len(result.data)} bytes")
except InvalidArgumentError as e:
    print(f"Invalid input: {e}")

# 2. Asynchronous Merge (Background Job)
async_result = client.merge(["large_doc1.pdf", "large_doc2.pdf"], async_job=True)
print(f"Async job finished: {len(async_result.data)} bytes")
```

---

## 5. Language Guide: TypeScript / Node.js Developers

### Package Installation
```bash
npm install ./sdks/typescript
```

### 5.1 In-Process Execution (`PdfCraftLocalClient`)
```typescript
import * as fs from "node:fs";
import { PdfCraftLocalClient } from "@pdfcraft/sdk";

const local = new PdfCraftLocalClient();

async function run() {
  // 1. Merge files by path or Buffer
  const buf1 = fs.readFileSync("sample-docs/policy.pdf");
  const buf2 = fs.readFileSync("sample-docs/schedule.pdf");

  const merged = await local.merge([buf1, buf2]);
  console.log(`Merged ${merged.data.length} bytes (MIME: ${merged.mimeType})`);

  // 2. Split document
  const split = await local.split("sample-docs/schedule.pdf");
  console.log(`Split files: ${split.files.join(", ")}`);

  // 3. Render page at 300 DPI
  const pageImage = await local.renderPage("sample-docs/schedule.pdf", 1, { dpi: 300 });
  console.log(`Rendered page image: ${pageImage.data.length} bytes`);
}

run().catch(console.error);
```

### 5.2 Remote REST Client (`PdfCraftRestClient`)
```typescript
import { PdfCraftRestClient, InvalidArgumentError } from "@pdfcraft/sdk";

const client = new PdfCraftRestClient({
  baseUrl: "http://127.0.0.1:8080",
  authToken: "secret-token",
  timeoutMs: 30000,
});

async function run() {
  try {
    // Synchronous execution
    const result = await client.merge(["docA.pdf", "docB.pdf"]);
    console.log(`Merge completed: ${result.data.length} bytes`);

    // Asynchronous background job with automatic polling
    const asyncResult = await client.merge(["docA.pdf", "docB.pdf"], undefined, true);
    console.log(`Background job completed: ${asyncResult.data.length} bytes`);
  } catch (err) {
    if (err instanceof InvalidArgumentError) {
      console.error("Validation error:", err.message);
    }
  }
}

run().catch(console.error);
```

---

## 6. Where Documents Belong in the Repository

| Document Type | Recommended Path | Tracked in Git? | Description |
|---|---|---|---|
| **Public User Guide** | [`docs/sdk.md`](file:///Users/richardfremmerlid/Projects/pdfcraft/docs/sdk.md) | **Yes** | Comprehensive public developer documentation for all three languages. |
| **Package READMEs** | `sdks/python/README.md`<br>`sdks/typescript/README.md`<br>`crates/sdk/README.md` | **Yes** | Package-specific guides for npm, PyPI, and crates.io. |
| **Architecture Specification** | [`docs/plans/pdfcraft-rest-sdk-plan.md`](file:///Users/richardfremmerlid/Projects/pdfcraft/docs/plans/pdfcraft-rest-sdk-plan.md) | **No** (Gitignored) | 1,120-line technical architecture and design document. |
| **Implementation Tasks** | [`docs/plans/tasks.md`](file:///Users/richardfremmerlid/Projects/pdfcraft/docs/plans/tasks.md) | **No** (Gitignored) | Engineering task breakdown across Phases 1–5. |
| **File Inventory** | [`docs/plans/file-inventory.md`](file:///Users/richardfremmerlid/Projects/pdfcraft/docs/plans/file-inventory.md) | **No** (Gitignored) | Detailed catalog of all internal files and symbols. |
| **Fixture Test Plan** | [`docs/plans/sample-docs-test-plan.md`](file:///Users/richardfremmerlid/Projects/pdfcraft/docs/plans/sample-docs-test-plan.md) | **No** (Gitignored) | Real customer documents test plan and verification results. |
| **Customer PDF Fixtures** | `/sample-docs/` | **No** (Gitignored) | Real customer documents per `AGENTS.md` §1 asset policy. |
