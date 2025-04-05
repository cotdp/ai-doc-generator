# AI Document Generator API Reference

## Overview
This document provides a comprehensive reference for all API endpoints in the AI Document Generator system. The API follows RESTful principles and returns responses in JSON format.

## Base URL
By default, the API is accessible at: `http://localhost:8000`

## Authentication
Currently, the API doesn't require authentication for local development. For production, authentication should be implemented.

## Endpoints

### Health Check
```
GET /health
```

**Description**: Simple endpoint to verify the API is running.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Generate Report
```
POST /generate-report
```

**Description**: Start the generation of a new report.

**Request Body**:
```json
{
  "topic": "Your research topic",           // Required: The topic to research
  "template_type": "standard",            // Optional: Report template (standard, academic, business)
  "max_pages": 10,                        // Optional: Maximum pages (1-50)
  "include_images": true,                 // Optional: Whether to include images
  "max_concurrent_tasks": 10             // Optional: Maximum concurrent tasks (1-20)
}
```

**Response**:
```json
{
  "task_id": "uuid-string",                // The unique ID for tracking this task
  "status": "accepted",                   // Initial status (always "accepted")
  "message": "Report generation started for topic: Topic Name with concurrency: 10"
}
```

**Error Responses**:
- `500 Internal Server Error`: If the request could not be processed

### Report Status
```
GET /report-status/{task_id}
```

**Description**: Check the status of a report generation task.

**Path Parameters**:
- `task_id`: The UUID returned from the generate-report call

**Response**:
```json
{
  "id": "uuid-string",
  "status": "in_progress",               // One of: "in_progress", "completed", "failed"
  "topic": "Your research topic",
  "error": null,                         // Error message if status is "failed"
  "progress": 0.65                       // Progress from 0.0 to 1.0
}
```

**Error Responses**:
- `404 Not Found`: If the task ID doesn't exist

### Download Report
```
GET /download-report/{task_id}
```

**Description**: Download the generated report file (DOCX format).

**Path Parameters**:
- `task_id`: The UUID returned from the generate-report call

**Response**:
- The DOCX file as an attachment

**Error Responses**:
- `404 Not Found`: If the task ID doesn't exist or the report file wasn't found
- `400 Bad Request`: If the report generation is not complete yet

## Response Status Codes

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid or cannot be served
- `404 Not Found`: The requested resource doesn't exist
- `500 Internal Server Error`: An error occurred on the server

## Rate Limiting

The API currently doesn't implement rate limiting, but excessive requests may be throttled by the underlying LLM providers (OpenAI, Perplexity).

## Versioning

API versioning is currently handled through the application version. Future updates may include versioned endpoints (e.g., `/v1/generate-report`).
