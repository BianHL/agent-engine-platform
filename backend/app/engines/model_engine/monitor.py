import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ModelMetrics:
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    last_request_time: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count

    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class ModelMonitor:
    def __init__(self):
        self._metrics: dict[str, ModelMetrics] = defaultdict(ModelMetrics)

    def record_request(self, model: str, latency_ms: float, success: bool):
        m = self._metrics[model]
        m.request_count += 1
        m.total_latency_ms += latency_ms
        m.last_request_time = time.time()
        if not success:
            m.error_count += 1

    def get_metrics(self, model: str) -> ModelMetrics:
        return self._metrics.get(model, ModelMetrics())

    def get_all_metrics(self) -> dict[str, ModelMetrics]:
        return dict(self._metrics)
