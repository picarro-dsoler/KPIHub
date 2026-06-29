from locallib.picarrodb import *
from locallib.query import *
from locallib.pandas import *

from ..config import *

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(INGESTER_LOG_PATH)
    ]
)
#Class used to get any data inside the data KPI HUb database
# The inggester focuses on a single table at a time

#Add sanity checks to ensure that all what you have on P-Cubed are the same things you have on KPIHUb
class Ingester:
    def __init__(self, arguments):
        name = self.__class__.__name__
        self.logger = logging.getLogger(name)
        self.arguments = arguments
        self.logger.info(f"{name} initialized")

    def query_data(self):
        self.logger.info(f"Querying data for {self.name}")
        pass

    def process_data(self):
        self.logger.info(f"Transforming data for {self.name}")
        pass

    def load_data(self):
        self.logger.info(f"Loading data for {self.name}")
        pass

    def sanity_check(self):
        self.logger.info(f"Sanity checking data for {self.name}")
        pass

class ReportIngester(Ingester):
    def __init__(self, arguments):
        super().__init__(arguments)
        
    def query_data(self):
        super().query_data()
        query = f"SELECT * FROM KPI_ReportSummary"
        q = Query(query = query)
        return q.execute(self.arguments['conn'])

    def pull_data(self):
        pass

class EmissionSourceIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass

class SurveyIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass

class LeakIngester(Ingester):
    def __init__(self, resource):
        super().__init__(resource)

    def pull_data(self):
        pass