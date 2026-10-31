# Building and Running PdfCraft & SDK

This guide covers how to build and run all components in this repository: the **desktop GUI app**, the **headless CLI**, the **minimal in-process Rust SDK**, the **HTTP REST microservice**, and the **Python / TypeScript bindings**.

---

## 📋 Prerequisites

- **Rust:** Rust 1.95+ (`rustup update stable`).
- **C Compiler (Optional for PyO3/Node):** `clang` or `gcc`.
- **Python (Optional):** Python 3.10+ for `sdks/python`.
- **Node.js (Optional):** Node.js 18+ for `sdks/typescript`.

---

## 🖥️ 1. Desktop GUI Application (`pdfcraft`)

The desktop app provides the full native viewer and editor (built with `egui` and `wgpu`).

### Running via Cargo
```bash
# Launch the empty app in debug mode
cargo run -p pdfcraft

# Open a specific PDF
cargo run -p pdfcraft -- path/to/document.pdf

# High-performance release mode (smoother zooming & rendering)
cargo run --release -p pdfcraft -- path/to/document.pdf
```

### Running the Pre-Compiled Binary Directly
Cargo only needs to compile on the first run or when source code changes. Once built, you can bypass Cargo and start the binary instantly:
```bash
# Debug binary
./target/debug/pdfcraft [path/to/document.pdf]

# Release binary (if compiled with --release)
./target/release/pdfcraft [path/to/document.pdf]
```

---

## ⚡ 2. Minimal In-Process SDK (`crates/sdk`)

If you only need headless programmatic PDF capabilities (merge, split, forms, annotations, rendering), you **do not need to compile the desktop app**. The SDK completely skips the windowing, GUI, and GPU stack (`egui`, `wgpu`, `winit`).

### Ultra-Fast Syntax / Type Check (~2 seconds)
```bash
cargo check -p pdfcraft-sdk
```

### Build the Rust SDK Crate
```bash
cargo build -p pdfcraft-sdk
```

### Run the SDK Capability Tour Example
```bash
cargo run -p pdfcraft-sdk --example sdk_capability_tour
```

### Using in Your Own Rust Project
Add to your `Cargo.toml`:
```toml
[dependencies]
pdfcraft-sdk = { path = "path/to/pdfcraft/crates/sdk" }
```
```rust
use pdfcraft_sdk::{DocumentSource, LocalPdfClient, PdfClient};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = LocalPdfClient::new()?;
    let merged = client.merge(vec![
        DocumentSource::from_path("part1.pdf")?,
        DocumentSource::from_path("part2.pdf")?,
    ])?;
    std::fs::write("merged.pdf", merged.into_bytes()?)?;
    Ok(())
}
```

---

## 🌐 3. Self-Hosted REST Microservice (`crates/rest`)

The REST microservice runs headless as a background daemon or containerized service, providing synchronous endpoints and an asynchronous job queue.

### Launch the Daemon
```bash
# Start on default port 8080 with bearer authentication
cargo run -p pdfcraft-rest -- --port 8080 --auth-token "your-secret-token"

# Or run the compiled release binary directly
cargo build --release -p pdfcraft-rest
./target/release/pdfcraft-rest --port 8080 --auth-token "your-secret-token"
```

### Test via curl
```bash
# Synchronous document merge
curl -X POST http://localhost:8080/v1/merged-pdf \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"sources": [{"path": "a.pdf"}, {"path": "b.pdf"}]}' \
  --output merged.pdf

# High-DPI page preview
curl -X POST http://localhost:8080/v1/page-preview \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"source": {"path": "doc.pdf"}, "page": 1, "max_dimension": 1024}' \
  --output page_1.png
```

---

## 💻 4. Command-Line Interface (`pdfcraft-cli`)

The CLI drives the headless engine and automation tools from terminal scripts:
```bash
# Display CLI help
cargo run -p pdfcraft-cli -- --help

# List all 123 automation tools
cargo run -p pdfcraft-cli -- tools

# Execute an automation script headlessly
cargo run -p pdfcraft-cli -- run --script steps.json --root ./
```

---

## 🐍 5. Language SDKs (Python & TypeScript)

### Python Package (`sdks/python`)
Native PyO3 extension + async HTTP client:
```bash
cd sdks/python

# Install in editable mode
pip install -e .

# Run test suite
pytest
```

### TypeScript / Node.js Package (`sdks/typescript`)
N-API native addon + typed HTTP client:
```bash
cd sdks/typescript

# Install dependencies and compile
npm install
npm run build

# Run test suite
npm test
```

---

## 📦 6. Consuming in External Repositories

To use PdfCraft programmatically inside other repositories and projects:

| Language / Platform | Dependency Declaration / Installation Command |
| :--- | :--- |
| **Rust (`Cargo.toml`)** | `pdfcraft-sdk = { git = "https://github.com/richfrem/pdfcraft.git", branch = "main" }` |
| **Python (`pip`)** | `pip install "git+https://github.com/richfrem/pdfcraft.git#subdirectory=sdks/python"` |
| **TypeScript / Node (`npm`)** | `npm install "github:richfrem/pdfcraft#subdirectory=sdks/typescript"` |
| **REST Microservice** | Launch daemon: `cargo run -p pdfcraft-rest -- --port 8080 --auth-token "your-token"` |
| **Other Languages (Go, C#, Java)** | Generate typed client from [`sdks/openapi.json`](sdks/openapi.json) via `openapi-generator-cli` |

---

## 🧪 7. Verification and Testing

Run test suites across components:
```bash
# Run SDK and REST test suite (76 tests)
cargo test -p pdfcraft-sdk -p pdfcraft-rest

# Verify 100% OpenAPI, Rust, Python, and TypeScript contract alignment
python3 sdks/check_contract_drift.py

# Verify architecture layering compliance
cargo run -p xtask -- layers
```

---

## 📚 Related Documentation
- [**Main Project README**](README.md): Product highlights, architecture diagram, and APDFL feature parity.
- [**Syncing with Upstream**](SYNC_UPSTREAM.md): How to merge updates from upstream while protecting your code.
- [**Multi-Language SDKs**](sdks/README.md): Detailed package matrix and OpenAPI spec.
- [**SDK Architecture Guide**](docs/sdk/README.md): In-depth control planes, concurrency, and memory bounds.
