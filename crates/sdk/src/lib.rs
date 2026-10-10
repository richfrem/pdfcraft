//! pdfcraft-sdk — Unified Document Processing SDK for PdfCraft (Issue #872).
//!
//! Provides dual execution modes:
//! 1. `LocalClient`: In-process execution linking directly to `pdfcraft-engine` and `pdfcraft-automation`
//!    through the `OperationExecutor` port (open-source alternative to Adobe PDF Library / PDFL).
//! 2. `RestClient`: Connects over HTTP/HTTPS to an on-premise `pdfcraft-rest` service.

#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

pub mod error;
pub mod local;
pub mod ports;
pub mod types;

pub use error::SdkError;
pub use local::LocalClient;
pub use ports::OperationExecutor;
pub use types::{
    DocumentResult, DocumentSource, ImageFormat, MergeOptions, RenderOptions, SplitMode, SplitResult,
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
