from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
import os

cas_username = os.getenv("CASSANDEA_USERNAME")
cas_password = os.getenv("CASSANDRA_PASSWORD")

class CassandraModule:
    def __init__(   
                    self,
                    username = cas_username,
                    password = cas_password, 
                    contact_points=["10.0.0.10", "10.0.0.11"],
                ):
        auth_provider = PlainTextAuthProvider(
            username,
            password,
        )

        cluster = Cluster(
            contact_points,
            auth_provider=auth_provider
        )

        session = cluster.connect()
        self._session = session
        self._cluster = cluster
        
        return (cluster, session)


