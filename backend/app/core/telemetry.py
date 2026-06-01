"""OpenTelemetry integration for tracing and metrics."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TelemetryManager:
    """Manages OpenTelemetry tracing and metrics."""
    
    def __init__(self, service_name: str = "agent-engine", enabled: bool = True):
        self._service_name = service_name
        self._enabled = enabled
        self._tracer = None
        self._meter = None
        self._initialized = False
    
    def initialize(self, endpoint: str = None):
        """Initialize OTel providers. Call once at startup."""
        if not self._enabled:
            logger.info("Telemetry disabled")
            return
        
        try:
            from opentelemetry import trace, metrics
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            
            resource = Resource.create({"service.name": self._service_name})
            
            # Tracer
            tracer_provider = TracerProvider(resource=resource)
            if endpoint:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=endpoint)
                tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(tracer_provider)
            self._tracer = trace.get_tracer(self._service_name)
            
            # Meter
            meter_provider = MeterProvider(resource=resource)
            if endpoint:
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
                exporter = OTLPMetricExporter(endpoint=endpoint)
                meter_provider.add_metric_reader(PeriodicExportingMetricReader(exporter))
            metrics.set_meter_provider(meter_provider)
            self._meter = metrics.get_meter(self._service_name)
            
            self._initialized = True
            logger.info(f"Telemetry initialized for {self._service_name}")
        except ImportError:
            logger.warning("opentelemetry packages not installed, telemetry disabled")
        except Exception as e:
            logger.error(f"Telemetry initialization failed: {e}")
    
    @property
    def tracer(self):
        return self._tracer
    
    @property
    def meter(self):
        return self._meter
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized


class LLMMonitor:
    """Monitor LLM requests with tracing and metrics."""
    
    def __init__(self, telemetry: TelemetryManager):
        self._telemetry = telemetry
        self._request_counter = None
        self._latency_histogram = None
        self._token_counter = None
        self._error_counter = None
        
        if telemetry.meter:
            self._request_counter = telemetry.meter.create_counter(
                "llm.requests.total", description="Total LLM requests"
            )
            self._latency_histogram = telemetry.meter.create_histogram(
                "llm.request.duration", description="LLM request latency", unit="ms"
            )
            self._token_counter = telemetry.meter.create_counter(
                "llm.tokens.total", description="Total tokens used"
            )
            self._error_counter = telemetry.meter.create_counter(
                "llm.errors.total", description="Total LLM errors"
            )
    
    async def track_request(
        self,
        model: str,
        messages: list[dict],
        response: dict = None,
        latency_ms: float = 0,
        error: str = None,
        tenant_id: str = None,
    ):
        """Track an LLM request with optional tracing span."""
        attributes = {"model": model}
        if tenant_id:
            attributes["tenant_id"] = tenant_id
        
        # Metrics
        if self._request_counter:
            self._request_counter.add(1, attributes)
        if self._latency_histogram:
            self._latency_histogram.record(latency_ms, attributes)
        
        if response and self._token_counter:
            usage = response.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            if tokens:
                self._token_counter.add(tokens, attributes)
        
        if error and self._error_counter:
            self._error_counter.add(1, {**attributes, "error": error})
        
        # Tracing span
        if self._telemetry.tracer:
            from opentelemetry import trace as otel_trace
            with self._telemetry.tracer.start_as_current_span("llm.request") as span:
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.messages_count", len(messages))
                if latency_ms:
                    span.set_attribute("llm.latency_ms", latency_ms)
                if response:
                    usage = response.get("usage", {})
                    span.set_attribute("llm.tokens.prompt", usage.get("prompt_tokens", 0))
                    span.set_attribute("llm.tokens.completion", usage.get("completion_tokens", 0))
                if error:
                    span.set_attribute("llm.error", error)
                    span.set_status(otel_trace.Status(otel_trace.StatusCode.ERROR, error))


# Global instances
_telemetry: Optional[TelemetryManager] = None
_llm_monitor: Optional[LLMMonitor] = None


def get_telemetry() -> TelemetryManager:
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryManager()
    return _telemetry


def get_llm_monitor() -> LLMMonitor:
    global _llm_monitor
    if _llm_monitor is None:
        _llm_monitor = LLMMonitor(get_telemetry())
    return _llm_monitor


def init_telemetry(service_name: str = "agent-engine", endpoint: str = None, enabled: bool = True):
    """Initialize telemetry. Call from app startup."""
    global _telemetry, _llm_monitor
    _telemetry = TelemetryManager(service_name=service_name, enabled=enabled)
    _telemetry.initialize(endpoint=endpoint)
    _llm_monitor = LLMMonitor(_telemetry)
    return _telemetry
