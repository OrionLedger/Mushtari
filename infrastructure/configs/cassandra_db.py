from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
import os

cas_username = os.getenv("CASSANDEA_USERNAME")
cas_password = os.getenv("CASSANDRA_PASSWORD")

class CassandraModule:
    def connect(   
                    self,
                    username = cas_username,
                    password = cas_password, 
                    contact_points=["127.0.0.1"],
                    port = 9042
                ):
        
        if(not username or not password):
            cluster = cluster = Cluster(contact_points, port)
        else:
            auth_provider = PlainTextAuthProvider(
                username,
                password,
            )
            cluster = Cluster(contact_points, port, auth_provider)

        session = cluster.connect()
        self._session = session
        self._cluster = cluster

        return session

    def get_cluster(self):
        return self._cluster

