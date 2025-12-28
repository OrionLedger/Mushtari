from .. import CassandraModule

class Cassandra_Repo:
    def __init__(self):
        (cluster, session) = CassandraModule()
        self._session = session
        self._cluster = cluster

    # Make or Set new Keyspace
    def set_keyspace(
        self,
        keyspace = 'demand'
        ):
        
        self._session.execute("""
                CREATE KEYSPACE IF NOT EXISTS %s
                WITH replication = {
                    'class': 'NetworkTopologyStrategy',
                    'dc1': 3
                }
        """, [keyspace])

        self._session.set_keyspace(keyspace)

    # Create new Table in the keyspace
    

