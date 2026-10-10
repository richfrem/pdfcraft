//! lib.rs — Unified Document Processing SDK for PdfCraft (Issue #872).
//! =========================================================================
//!
//! Purpose:
//!     Main entry point for pdfcraft-sdk. Defines the unified PdfCraftClient trait
//!     and re-exports domain models, error hierarchies, engine adapters, and the LocalClient.
//!
//! Layer:
//!     Core SDK Root
//!
//! Key Input Dependencies:
//!     - pdfcraft-automation
//!     - pdfcraft-engine
//!
//! Usage Examples:
//!     ```rust
//!     use pdfcraft_sdk::{LocalClient, PdfCraftClient, DocumentSource, MergeOptions};
//!     let client = LocalClient::default();
//!     let doc = DocumentSource::from_bytes(b"%PDF-1.4...".to_vec(), None);
//!     let res = client.merge(&[doc], MergeOptions::default());
//!     ```
//!
//! Key Types & Functions Index:
//!     - PdfCraftClient: Unified document processing client trait (merge, split, render_page)
//!     - LocalClient: In-process client facade
//!     - AutomationEngineAdapter: Concrete engine adapter implementing OperationExecutor
//!     - SdkError: Strongly typed error enum
//!     - DocumentSource: Input abstraction (Path or Bytes)
//!     - DocumentResult: Output abstraction (Memory or File)

#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

pub mod error;
pub mod engine_adapter;
pub mod local;
pub mod ports;
pub mod types;

pub use engine_adapter::AutomationEngineAdapter;
pub use error::SdkError;
pub use local::LocalClient;
pub use ports::OperationExecutor;
pub use types::{
    DocumentResult, DocumentSource, ImageFormat, MergeOptions, RenderOptions, ResourceLimits, SplitMode, SplitResult,
};

/// Unified document processing client trait shared across in-process and remote transports.
pub trait PdfCraftClient {
    /// Merges multiple PDF files into a single output PDF.
    fn merge(&self, files: &[DocumentSource], options: MergeOptions) -> Result<DocumentResult, SdkError>;

    /// Splits a PDF file into multiple PDF documents based on the specified split mode.
    fn split(&self, file: &DocumentSource, mode: SplitMode) -> Result<SplitResult, SdkError>;

    /// Renders a single page of a PDF document to an image at the specified physical DPI.
    fn render_page(&self, file: &DocumentSource, page: usize, options: RenderOptions) -> Result<DocumentResult, SdkError>;
}
