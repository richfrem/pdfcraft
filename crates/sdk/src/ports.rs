//! Application ports decoupling client facades from concrete engine execution.
//!
//! # Architecture Reference
//! Module: crates/sdk/src/ports.rs
//! Purpose:
//!   Enforces Hexagonal / Ports-and-Adapters boundary so `LocalClient` depends
//!   on an abstract `OperationExecutor` rather than concrete engine structs.

use std::sync::Arc;
use crate::error::SdkError;
use crate::types::{DocumentResult, DocumentSource, MergeOptions, RenderOptions, SplitMode, SplitResult};

/// Strongly typed document command for execution by an engine adapter.
#[derive(Debug)]
pub enum OperationCommand {
    Merge {
        sources: Vec<DocumentSource>,
        options: MergeOptions,
    },
    Split {
        source: DocumentSource,
        mode: SplitMode,
    },
    RenderPage {
        source: DocumentSource,
        page: usize,
        options: RenderOptions,
    },
}

/// Abstract engine executor port.
pub trait OperationExecutor: Send + Sync {
    /// Executes a document command and returns a result or a structured SdkError.
    fn execute_merge(&self, sources: &[DocumentSource], options: &MergeOptions) -> Result<DocumentResult, SdkError>;
    fn execute_split(&self, source: &DocumentSource, mode: &SplitMode) -> Result<SplitResult, SdkError>;
    fn execute_render(&self, source: &DocumentSource, page: usize, options: &RenderOptions) -> Result<DocumentResult, SdkError>;
}
