import os
from prometheus_client import Counter, Histogram, Gauge, push_to_gateway

# Initialize metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total count of API requests',
    ['endpoint', 'method', 'status_code']
)

report_generation_duration = Histogram(
    'report_generation_duration_seconds',
    'Time spent generating reports',
    ['template_type', 'success'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

active_reports_gauge = Gauge(
    'active_reports',
    'Number of reports currently being generated'
)

api_errors_total = Counter(
    'api_errors_total',
    'Total count of API errors',
    ['endpoint', 'error_type']
)

llm_api_calls_total = Counter(
    'llm_api_calls_total',
    'Total count of LLM API calls',
    ['service', 'model', 'success']
)

llm_api_duration = Histogram(
    'llm_api_duration_seconds',
    'Time spent on LLM API calls',
    ['service', 'model'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60)
)

llm_token_usage = Counter(
    'llm_token_usage_total',
    'Total token usage for LLM API calls',
    ['service', 'model', 'type']  # type can be 'prompt' or 'completion'
)


def setup_metrics(app=None):
    """Set up metrics collection for the application.

    Args:
        app: FastAPI app to set up metrics for (optional)
    """
    # Get environment variables
    enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    if not enable_metrics:
        return
        
    if app:
        from prometheus_client import make_asgi_app
        
        # Create metrics endpoint for scraping
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        
        @app.middleware("http")
        async def metrics_middleware(request, call_next):
            # Track request count
            endpoint = request.url.path
            method = request.method
            
            try:
                response = await call_next(request)
                status_code = response.status_code
                api_requests_total.labels(endpoint=endpoint, method=method, status_code=status_code).inc()
                return response
            except Exception as e:
                # Track API errors
                error_type = type(e).__name__
                api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()
                raise