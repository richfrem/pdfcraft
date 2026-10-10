//! domain_tests.rs — Unit tests verifying SDK Domain Models and Port Contracts.
//! ==============================================================================
//!
//! Purpose:
//!     Verifies DocumentSource (Path & Bytes), DocumentResult (Memory & File),
//!     MergeOptions, SplitMode, and OperationExecutor port delegation.
//!
//! Layer:
//!     Test Suite / SDK Domain Tests


use std::path::PathBuf;
use std::sync::Arc;
use pdfcraft_sdk::error::SdkError;
use pdfcraft_sdk::ports::OperationExecutor;
use pdfcraft_sdk::types::{
    DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode, SplitResult,
};
use pdfcraft_sdk::{LocalClient, PdfCraftClient};

/// Test fake executor for contract verification.
struct FakeExecutor;

impl OperationExecutor for FakeExecutor {
    fn execute_merge(&self, sources: &[DocumentSource], _options: &MergeOptions) -> Result<DocumentResult, SdkError> {
        if sources.is_empty() {
            return Err(SdkError::InvalidArgument("sources cannot be empty".into()));
        }
        Ok(DocumentResult::memory(b"%PDF-1.7 merged".to_vec(), "application/pdf"))
    }

    fn execute_split(&self, _source: &DocumentSource, _mode: &SplitMode) -> Result<SplitResult, SdkError> {
        Ok(SplitResult {
            files: vec![PathBuf::from("part_1.pdf"), PathBuf::from("part_2.pdf")],
        })
    }

    fn execute_render(&self, _source: &DocumentSource, page: usize, _options: &RenderOptions) -> Result<DocumentResult, SdkError> {
        if page == 0 {
            return Err(SdkError::InvalidArgument("page must be 1-based".into()));
        }
        Ok(DocumentResult::memory(b"PNG_BYTES".to_vec(), "image/png"))
    }
}

#[test]
fn test_document_source_constructors() {
    let from_str = DocumentSource::from("sample.pdf");
    assert_eq!(from_str, DocumentSource::Path(PathBuf::from("sample.pdf")));

    let bytes = vec![1, 2, 3];
    let from_bytes = DocumentSource::from(bytes.clone());
    assert_eq!(from_bytes, DocumentSource::Bytes { data: bytes, name: None });
    assert_eq!(from_bytes.byte_len(), Some(3));
}

#[test]
fn test_document_result_variants() {
    let mem = DocumentResult::memory(vec![1, 2, 3], "application/pdf");
    assert_eq!(mem.byte_len(), 3);
    assert_eq!(mem.mime_type(), "application/pdf");

    let file = DocumentResult::file(PathBuf::from("/tmp/doc.pdf"), "application/pdf", 1024);
    assert_eq!(file.byte_len(), 1024);
    assert_eq!(file.mime_type(), "application/pdf");
}

#[test]
fn test_sdk_error_http_status_mapping() {
    let err_arg = SdkError::InvalidArgument("bad".into());
    assert_eq!(err_arg.http_status(), 400);
    assert_eq!(err_arg.error_code(), "INVALID_ARGUMENT");

    let err_quota = SdkError::QuotaExceeded("limit".into());
    assert_eq!(err_quota.http_status(), 413);
    assert_eq!(err_quota.error_code(), "QUOTA_EXCEEDED");

    let err_panic = SdkError::EnginePanic("panic caught".into());
    assert_eq!(err_panic.http_status(), 500);
    assert_eq!(err_panic.error_code(), "ENGINE_PANIC_CONTAINED");
}

#[test]
fn test_local_client_delegates_to_executor() {
    let executor = Arc::new(FakeExecutor);
    let client = LocalClient::new(executor);

    // Merge validation
    let empty_sources: Vec<DocumentSource> = vec![];
    assert!(client.merge(&empty_sources, MergeOptions::default()).is_err());

    let sources = vec![DocumentSource::from("a.pdf"), DocumentSource::from("b.pdf")];
    let res = client.merge(&sources, MergeOptions::default()).expect("merge ok");
    assert_eq!(res.mime_type(), "application/pdf");

    // Render validation
    assert!(client.render_page(&DocumentSource::from("a.pdf"), 0, RenderOptions::default()).is_err());
    let render_res = client.render_page(&DocumentSource::from("a.pdf"), 1, RenderOptions::default()).expect("render ok");
    assert_eq!(render_res.mime_type(), "image/png");
}
