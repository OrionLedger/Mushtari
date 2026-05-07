from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import sys

def test_conn():
    print("Connecting to 127.0.0.1:9042...")
    auth = PlainTextAuthProvider(username='cassandra', password='cassandra')
    try:
        cluster = Cluster(['127.0.0.1'], port=9042, auth_provider=None) # Try without auth first
        session = cluster.connect()
        print("Connected successfully without auth!")
        print(f"Metadata: {cluster.metadata.cluster_name}")
        cluster.shutdown()
        return
    except Exception as e:
        print(f"Failed without auth: {e}")

    try:
        cluster = Cluster(['127.0.0.1'], port=9042, auth_provider=auth)
        session = cluster.connect()
        print("Connected successfully with auth!")
        cluster.shutdown()
    except Exception as e:
        print(f"Failed with auth: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_conn()
