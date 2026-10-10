//! RFC 7807 Problem Details serialization for HTTP error responses.
//!
//! # Architecture Reference
//! Module: crates/rest/src/problem.rs
//! Purpose:
//!   Formats errors as standardized application/problem+json payloads conforming to RFC 7807.

use serde::{Deserialize, Serialize};
use pdfcraft_sdk::SdkError;

/// RFC 7807 Problem Details object.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProblemDetails {
    #[serde(rename = "type")]
    pub problem_type: String,
    pub title: String,
    pub status: u16,
    pub detail: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub instance: Option<String>,
    pub code: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub invalid_params: Option<Vec<InvalidParam>>,
}

/// Description of an invalid request parameter.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct InvalidParam {
    pub name: String,
    pub reason: String,
}

impl ProblemDetails {
    pub fn new(status: u16, title: impl Into<String>, detail: impl Into<String>, code: impl Into<String>) -> Self {
        let code_str = code.into();
        Self {
            problem_type: format!("https://pdfcraft.storytold.org/errors/{}", code_str.to_lowercase().replace('_', "-")),
            title: title.into(),
            status,
            detail: detail.into(),
            instance: None,
            code: code_str,
            invalid_params: None,
        }
    }

    pub fn with_instance(mut self, instance: impl Into<String>) -> Self {
        self.instance = Some(instance.into());
        self
    }

    pub fn with_invalid_param(mut self, name: impl Into<String>, reason: impl Into<String>) -> Self {
        let param = InvalidParam {
            name: name.into(),
            reason: reason.into(),
        };
        match &mut self.invalid_params {
            Some(params) => params.push(param),
            None => self.invalid_params = Some(vec![param]),
        }
        self
    }

    pub fn bad_request(detail: impl Into<String>) -> Self {
        Self::new(400, "Bad Request", detail, "BAD_REQUEST")
    }

    pub fn unauthorized(detail: impl Into<String>) -> Self {
        Self::new(401, "Unauthorized", detail, "UNAUTHORIZED")
    }

    pub fn not_found(detail: impl Into<String>) -> Self {
        Self::new(404, "Not Found", detail, "NOT_FOUND")
    }

    pub fn conflict(detail: impl Into<String>) -> Self {
        Self::new(409, "Conflict", detail, "CONFLICT")
    }

    pub fn payload_too_large(detail: impl Into<String>) -> Self {
        Self::new(413, "Payload Too Large", detail, "QUOTA_EXCEEDED")
    }

    pub fn too_many_requests(detail: impl Into<String>) -> Self {
        Self::new(429, "Too Many Requests", detail, "CONCURRENCY_LIMIT_EXCEEDED")
    }

    pub fn internal_error(detail: impl Into<String>) -> Self {
        Self::new(500, "Internal Server Error", detail, "INTERNAL_SERVER_ERROR")
    }

    pub fn not_implemented(detail: impl Into<String>) -> Self {
        Self::new(501, "Not Implemented", detail, "NOT_IMPLEMENTED")
    }

    pub fn service_unavailable(detail: impl Into<String>) -> Self {
        Self::new(503, "Service Unavailable", detail, "SERVICE_UNAVAILABLE")
    }
}

impl From<SdkError> for ProblemDetails {
    fn from(err: SdkError) -> Self {
        let status = err.http_status();
        let code = err.error_code();
        let title = match status {
            400 => "Bad Request",
            404 => "Resource Not Found",
            413 => "Payload Too Large",
            501 => "Not Implemented",
            _ => "Processing Failure",
        };
        Self::new(status, title, err.to_string(), code)
    }
}
