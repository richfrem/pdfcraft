//! pdfcraft-rest — On-Premise REST Service for PdfCraft Document Processing (Issue #872).
//!
//! Provides durable background processing, bounded blocking worker governance,
//! RFC 7807 Problem Details serialization, and 100% semantic parity with `LocalClient`.

#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

pub mod client;
pub mod executor;
pub mod models;
pub mod problem;
pub mod routes;
pub mod server;
pub mod storage;

pub use client::RestClient;
pub use executor::{BlockingExecutor, ExecutionError, ExecutorConfig};
pub use models::{
    JobId, JobRecord, JobResponse, JobState, MergePayload, RenderPayload, SourcePayload, SplitPayload,
};
pub use problem::{InvalidParam, ProblemDetails};
pub use routes::{HttpRequest, HttpResponse, RestService};
pub use server::{HttpServer, ServerConfig};
pub use storage::{DurableFileJobRepository, InMemoryJobRepository, JobError, JobRepository};
