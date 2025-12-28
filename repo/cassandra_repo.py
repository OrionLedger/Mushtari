from .. import MongoDBModule, CassandraModule

class Cassandra_Repo:
    def __init__(self):
        (cluster, session) = CassandraModule()
        self._session = session
        self._cluster = cluster

    # Making new Keyspace
    def set_keyspace(
                    self,
                    keyspace = 'demand'
                    ):
        
        self._session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS %s
                WITH replication = {
                    'class': 'NetworkTopologyStrategy',
                    'dc1': 3
                }
        """, [keyspace])

        self._session.set_keyspace(keyspace)

    # Make new Table in the keyspace
    def make_table(self,
                   table_name,
                   ):
        
        self._session.execute("""

        """, [table_name])

