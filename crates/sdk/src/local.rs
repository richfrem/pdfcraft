//! In-process engine driver executing operations through an injected `OperationExecutor`.

use std::sync::Arc;
use crate::error::SdkError;
use crate::ports::OperationExecutor;
use crate::types::{DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode, SplitResult};
use crate::PdfCraftClient;

/// Local in-process client for running document transformations without an HTTP server.
pub struct LocalClient {
    executor: Arc<dyn OperationExecutor>,
}

impl LocalClient {
    /// Creates a new `LocalClient` with the provided engine executor implementation.
    pub fn new(executor: Arc<dyn OperationExecutor>) -> Self {
        Self { executor }
    }
}

impl PdfCraftClient for LocalClient {
    fn merge(&self, files: &[DocumentSource], options: MergeOptions) -> Result<DocumentResult, SdkError> {
        if files.is_empty() {
            return Err(SdkError::InvalidArgument("files list cannot be empty".into()));
        }
        self.executor.execute_merge(files, &options)
    }

    fn split(&self, file: &DocumentSource, mode: SplitMode) -> Result<SplitResult, SdkError> {
        self.executor.execute_split(file, &mode)
    }

    fn render_page(&self, file: &DocumentSource, page: usize, options: RenderOptions) -> Result<DocumentResult, SdkError> {
        if page == 0 {
            return Err(SdkError::InvalidArgument("Page number must be 1-based (greater than 0)".into()));
        }
        self.executor.execute_render(file, page, &options)
    }
}
