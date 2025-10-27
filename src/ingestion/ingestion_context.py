from ... import get_logger
from . import CTALStrategy

logger = get_logger(__name__)

class DataCollector:
    def __init__(self):
        self.memory = {}

    def initialize_comtrade_collector(
                                    self,
                                    subscription_key=None,
                                    typeCode='C',
                                    freqCode='A',
                                    clCode='HS',
                                    reporterCode='840',
                                    flowCode='M',
                                    customsCode=None,
                                    motCode=None,
                                    aggregateBy=None,
                                    breakdownMode='classic',
                                    countOnly=None,
                                    includeDesc=True,
    ):
        try:
            self._comtrade_collector = CTALStrategy(
                subscription_key=subscription_key,
                typeCode=typeCode,
                freqCode=freqCode,
                clCode=clCode,
                reporterCode=reporterCode,
                flowCode=flowCode,
                customsCode=customsCode,
                motCode=motCode,
                aggregateBy=aggregateBy,
                breakdownMode=breakdownMode,
                countOnly=countOnly,
                includeDesc=includeDesc
            )

            self.memory['comtrade_collector'] = self._comtrade_collector
            logger.info("Comtrade Data Collector Initialized.")

            return self._comtrade_collector

        except Exception as e:
            logger.exception(f"Initializing Comtrade Data Collector Failed: {e}")
    
