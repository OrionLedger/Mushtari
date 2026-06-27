"""
serving/services/inference_logger.py

Unified logging logic for AI model inferences. Persists every prediction
result into the Cassandra fact-store for historical tracking and 
accuracy drift analysis.
"""

import uuid
import time
from typing import Any, Dict, Optional
from infrastructure.logging.logger import get_logger
from repo.current import get_active_repository

logger = get_logger(__name__)

class InferenceLogger:
    @classmethod
    def log_inference(
        cls,
        product_id: int,
        prediction: float,
        model_version: str = "v1.0.0",
        features: Optional[Dict[str, float]] = None,
        latency_ms: Optional[float] = None
    ) -> str:
        """
        Persists a single inference record into the active repository.
        """
        inference_id = uuid.uuid4()
        from datetime import datetime
        timestamp = datetime.now()
        
        record = {
            "inference_id": str(inference_id),
            "product_id": int(product_id),
            "model_version": model_version,
            "prediction_result": float(prediction),
            "inference_ts": timestamp,
            "latency_ms": float(latency_ms or 0.0),
            "input_features": features or {}
        }

        try:
            repo = get_active_repository()
            repo.add_record("inference_logs", record)
            logger.debug(f"[Log] Inference {inference_id} archived for Product #{product_id}")
            return str(inference_id)
        except Exception as e:
            logger.error(f"Failed to log inference: {e}")
            return ""

def log_prediction(product_id: int, result: float, **kwargs):
    """Convenience helper for inference logging."""
    return InferenceLogger.log_inference(product_id, result, **kwargs)
