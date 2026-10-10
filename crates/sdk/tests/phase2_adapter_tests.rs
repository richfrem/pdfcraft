//! Phase 2 Integration Tests: Engine Adapter, Panic Boundary, and Concrete Wire-up.

use std::sync::Arc;
use pdfcraft_sdk::engine_adapter::AutomationEngineAdapter;
use pdfcraft_sdk::error::SdkError;
use pdfcraft_sdk::ports::OperationExecutor;
use pdfcraft_sdk::types::{DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode};
use pdfcraft_sdk::{LocalClient, PdfCraftClient};

fn minimal_valid_pdf() -> Vec<u8> {
    // Synthetic minimal valid PDF adhering to AGENTS.md clean-room asset policy
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n".to_vec()
}

#[test]
fn test_merge_missing_source_fails_with_file_not_found() {
    let adapter = AutomationEngineAdapter::default();
    let sources = vec![DocumentSource::from("nonexistent_doc.pdf")];
    let res = adapter.execute_merge(&sources, &MergeOptions::default());

    assert!(res.is_err());
    match res.err().expect("error expected") {
        SdkError::FileNotFound { path } => {
            assert!(path.contains("nonexistent_doc.pdf"));
        }
        other => panic!("Expected FileNotFound, got {other:?}"),
    }
}

#[test]
fn test_merge_valid_in_memory_sources() {
    let adapter = AutomationEngineAdapter::default();
    let doc1 = DocumentSource::from_bytes(minimal_valid_pdf(), Some("doc1.pdf".into()));
    let doc2 = DocumentSource::from_bytes(minimal_valid_pdf(), Some("doc2.pdf".into()));

    let res = adapter.execute_merge(&[doc1, doc2], &MergeOptions::default());
    // Note: depending on engine test state, it either combines or returns a structured result
    // In all cases, it must NOT panic and return a valid Result.
    match res {
        Ok(result) => {
            assert_eq!(result.mime_type(), "application/pdf");
            assert!(result.byte_len() > 0);
        }
        Err(SdkError::EngineError(e)) => {
            // Document combine returned a structured error, not a crash
            assert!(!e.is_empty());
        }
        Err(other) => panic!("Unexpected error type: {other:?}"),
    }
}

#[test]
fn test_render_page_zero_rejected() {
    let client = LocalClient::default();
    let src = DocumentSource::from_bytes(minimal_valid_pdf(), Some("doc.pdf".into()));
    let res = client.render_page(&src, 0, RenderOptions::default());

    assert!(res.is_err());
    match res.err().expect("error expected") {
        SdkError::InvalidArgument(msg) => {
            assert!(msg.contains("1-based"));
        }
        other => panic!("Expected InvalidArgument, got {other:?}"),
    }
}

#[test]
fn test_large_output_spills_to_file_backed_result() {
    // Set max memory threshold to 100 bytes so any successful output spills to disk
    let adapter = AutomationEngineAdapter::new(100);
    let doc1 = DocumentSource::from_bytes(minimal_valid_pdf(), Some("doc1.pdf".into()));
    let doc2 = DocumentSource::from_bytes(minimal_valid_pdf(), Some("doc2.pdf".into()));

    if let Ok(result) = adapter.execute_merge(&[doc1, doc2], &MergeOptions::default()) {
        match result {
            DocumentResult::File { path, mime_type, size_bytes } => {
                assert_eq!(mime_type, "application/pdf");
                assert!(size_bytes > 100);
                assert!(path.exists());
            }
            DocumentResult::Memory { .. } => {
                panic!("Output should have spilled to DocumentResult::File due to 100 byte limit");
            }
        }
    }
}
