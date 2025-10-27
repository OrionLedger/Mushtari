import comtradeapicall
from ... import get_logger

logger = get_logger(__name__)

class CTALStrategy:
    def __init__(   self,
                    subscription_key,
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
                    includeDesc=True
                ):
        self.subscription_key = subscription_key
        self.typeCode = typeCode
        self.freqCode = freqCode
        self.clCode = clCode
        self.reporterCode = reporterCode
        self.flowCode = flowCode
        self.customsCode = customsCode
        self.motCode = motCode
        self.aggregateBy = aggregateBy
        self.breakdownMode = breakdownMode
        self.countOnly = countOnly
        self.includeDesc = includeDesc

    def collect_sample_data(self, 
                    period='202201', 
                    cmdCode=None, 
                    partnerCode=None, 
                    partner2Code=None,
                    maxRecords=500,
                    format_output='JSON',
    ):
        try:
            data = comtradeapicall.previewFinalData(
                typeCode=self.typeCode,
                freqCode=self.freqCode,
                clCode=self.clCode,
                reporterCode=self.reporterCode,
                period=period,
                cmdCode=cmdCode,
                flowCode=self.flowCode,
                partnerCode=partnerCode,
                partner2Code=partner2Code,
                customsCode=self.customsCode,
                motCode=self.motCode,
                maxRecords=maxRecords,
                format_output=format_output,
                aggregateBy=self.aggregateBy,
                breakdownMode=self.breakdownMode,
                countOnly=self.countOnly,
                includeDesc=self.includeDesc,
            )
            logger.info("Comtrade API samples data collection completed.")
            return data
        except Exception as e:
            logger.exception(f"Data collection failed: {e}")
