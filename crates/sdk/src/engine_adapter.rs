//! Concrete `OperationExecutor` adapter connecting `crates/sdk` to `pdfcraft_automation`.
//!
//! # Architecture Reference
//! Module: crates/sdk/src/engine_adapter.rs
//! Purpose:
//!   Executes document transformations headlessly through `pdfcraft_automation::Automation`
//!   inside an ephemeral sandbox with:
//!   - Panic containment (`std::panic::catch_unwind`) converting engine panics to `SdkError::EnginePanic`
//!   - Strict path containment within a temporary directory
//!   - High-DPI physical rendering calculation decoupled from display PPI (#739)

use std::fs;
use std::panic::{AssertUnwindSafe, catch_unwind};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use tempfile::TempDir;

use crate::error::SdkError;
use crate::ports::OperationExecutor;
use crate::types::{
    DocumentResult, DocumentSource, ImageFormat, MergeOptions, RenderOptions, SplitMode, SplitResult,
};
use pdfcraft_automation::Automation;
use serde_json::{json, Value};

static COUNTER: AtomicU64 = AtomicU64::new(1);

/// Execution sandbox managing ephemeral disk isolation and cleanup.
pub struct ExecutionSandbox {
    temp_dir: TempDir,
    root: PathBuf,
}

impl ExecutionSandbox {
    pub fn new() -> Result<Self, SdkError> {
        let temp_dir = tempfile::Builder::new()
            .prefix("pdfcraft-sandbox-")
            .tempdir()
            .map_err(SdkError::Io)?;
        let root = temp_dir.path().to_path_buf();
        Ok(Self { temp_dir, root })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Materializes a `DocumentSource` into the sandbox, returning its relative filename.
    pub fn materialize_source(&self, source: &DocumentSource, index: usize) -> Result<String, SdkError> {
        match source {
            DocumentSource::Path(p) => {
                if !p.exists() {
                    return Err(SdkError::FileNotFound {
                        path: p.display().to_string(),
                    });
                }
                let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("pdf");
                let file_name = format!("input_{index}.{ext}");
                let dest = self.root.join(&file_name);
                fs::copy(p, dest).map_err(SdkError::Io)?;
                Ok(file_name)
            }
            DocumentSource::Bytes { data, name } => {
                let file_name = name.clone().unwrap_or_else(|| format!("input_{index}.pdf"));
                let dest = self.root.join(&file_name);
                fs::write(dest, data).map_err(SdkError::Io)?;
                Ok(file_name)
            }
        }
    }
}

/// Concrete engine adapter delegating to `pdfcraft_automation::Automation`.
pub struct AutomationEngineAdapter {
    max_memory_bytes: u64,
}

impl Default for AutomationEngineAdapter {
    fn default() -> Self {
        Self {
            max_memory_bytes: 10 * 1024 * 1024, // 10 MB threshold to spill to disk
        }
    }
}

impl AutomationEngineAdapter {
    pub fn new(max_memory_bytes: u64) -> Self {
        Self { max_memory_bytes }
    }

    /// Helper executing an engine closure under an `AssertUnwindSafe` panic boundary.
    fn with_automation<F, R>(&self, sandbox: &ExecutionSandbox, f: F) -> Result<R, SdkError>
    where
        F: FnOnce(&mut Automation) -> Result<R, SdkError>,
    {
        let mut automation = Automation::new()
            .with_root(sandbox.root())
            .map_err(|e| SdkError::EngineError(format!("Failed to configure automation root: {e}")))?;

        let result = catch_unwind(AssertUnwindSafe(|| f(&mut automation)));

        match result {
            Ok(inner_res) => inner_res,
            Err(panic_err) => {
                let msg = if let Some(s) = panic_err.downcast_ref::<&str>() {
                    s.to_string()
                } else if let Some(s) = panic_err.downcast_ref::<String>() {
                    s.clone()
                } else {
                    "Unknown engine panic".to_string()
                };
                Err(SdkError::EnginePanic(msg))
            }
        }
    }
}

impl OperationExecutor for AutomationEngineAdapter {
    fn execute_merge(&self, sources: &[DocumentSource], options: &MergeOptions) -> Result<DocumentResult, SdkError> {
        if sources.is_empty() {
            return Err(SdkError::InvalidArgument("No input documents provided for merge".into()));
        }

        let sandbox = ExecutionSandbox::new()?;
        let mut materialized_paths = Vec::with_capacity(sources.len());
        for (i, src) in sources.iter().enumerate() {
            materialized_paths.push(sandbox.materialize_source(src, i)?);
        }

        let out_name = options.output_filename.clone().unwrap_or_else(|| {
            let id = COUNTER.fetch_add(1, Ordering::Relaxed);
            format!("merged_{id}.pdf")
        });

        self.with_automation(&sandbox, |automation| {
            let args = json!({
                "paths": materialized_paths,
                "pages": options.pages,
                "passwords": options.passwords,
                "out": out_name,
            });

            automation.call("doc_combine", &args)
                .map_err(|e| SdkError::EngineError(format!("Merge failed: {e}")))?;

            let out_path = sandbox.root().join(&out_name);
            let metadata = fs::metadata(&out_path).map_err(SdkError::Io)?;
            let size = metadata.len();

            if size > self.max_memory_bytes {
                Ok(DocumentResult::file(out_path, "application/pdf", size))
            } else {
                let bytes = fs::read(&out_path).map_err(SdkError::Io)?;
                Ok(DocumentResult::memory(bytes, "application/pdf"))
            }
        })
    }

    fn execute_split(&self, source: &DocumentSource, mode: &SplitMode) -> Result<SplitResult, SdkError> {
        let sandbox = ExecutionSandbox::new()?;
        let file_name = sandbox.materialize_source(source, 0)?;

        self.with_automation(&sandbox, |automation| {
            let open_res = automation.call("doc_open", &json!({ "path": file_name }))
                .map_err(|e| SdkError::EngineError(format!("Failed to open document: {e}")))?;

            let doc_id = open_res.first()
                .and_then(|c| c.as_json())
                .and_then(|v| v.get("doc"))
                .and_then(Value::as_i64)
                .ok_or_else(|| SdkError::EngineError("Invalid doc id returned".into()))?;

            let out_dir = "parts";
            let mut split_args = json!({
                "doc": doc_id,
                "out_dir": out_dir,
            });

            match mode {
                SplitMode::EveryNPages(every) => split_args["every"] = json!(every),
                SplitMode::BeforePages(pages) => split_args["before"] = json!(pages),
                SplitMode::AtBookmarks => split_args["bookmarks"] = json!(true),
                SplitMode::MaxFileSizeMb(mb) => split_args["max_mb"] = json!(mb),
            }

            let res = automation.call("doc_split", &split_args)
                .map_err(|e| SdkError::EngineError(format!("Split failed: {e}")))?;

            let raw_files = res.first()
                .and_then(|c| c.as_json())
                .and_then(|v| v.get("files"))
                .and_then(Value::as_array)
                .map(|arr| arr.iter().filter_map(|v| v.as_str().map(PathBuf::from)).collect())
                .unwrap_or_default();

            Ok(SplitResult { files: raw_files })
        })
    }

    fn execute_render(&self, source: &DocumentSource, page: usize, options: &RenderOptions) -> Result<DocumentResult, SdkError> {
        if page == 0 {
            return Err(SdkError::InvalidArgument("Page number must be 1-based".into()));
        }

        let sandbox = ExecutionSandbox::new()?;
        let file_name = sandbox.materialize_source(source, 0)?;

        self.with_automation(&sandbox, |automation| {
            // Strictly compute DPI without coupling to monitor display PPI (#739)
            let args = json!({
                "path": file_name,
                "page": page,
                "dpi": options.dpi,
            });

            let res = automation.call("page_render", &args)
                .map_err(|e| SdkError::EngineError(format!("Render failed: {e}")))?;

            let img_bytes = res.first()
                .and_then(|c| c.as_bytes())
                .map(|b| b.to_vec())
                .ok_or_else(|| SdkError::EngineError("Render produced no image bytes".into()))?;

            let mime = match options.format {
                ImageFormat::Png => "image/png",
                ImageFormat::Jpeg => "image/jpeg",
            };

            Ok(DocumentResult::memory(img_bytes, mime))
        })
    }
}
