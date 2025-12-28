from ... import CassandraModule

def connect(module = CassandraModule()):
    return module.connect()