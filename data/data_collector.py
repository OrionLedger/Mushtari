from .. import get_logger

logger = get_logger(__name__)

class data_collector:
    def __init__(self, collecting_context):
        self._collecting_context = collecting_context

    def collect_data(self):
        try:
            self._collecting_context.collect_data()
            logger.info("Collecting data...")
        except Exception as e:
            logger.exception(f"Data collection failed: {e}")
