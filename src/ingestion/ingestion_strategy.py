from ... import get_logger

logger = get_logger(__name__)

class DataCollector:
    def __init__(self):
        pass

    def collect_data(self, data_collecting_context):
        try:
            data_collecting_context.collect_data()
            logger.info("Collecting data...")
        except Exception as e:
            logger.exception(f"Data collection failed: {e}")