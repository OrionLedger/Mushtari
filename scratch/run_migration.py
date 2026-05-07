
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from repo.postgres_repo import PostgresRepository
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    uri = os.getenv("POSTGRES_URI")
    print(f"Connecting to: {uri}")
    repo = PostgresRepository(connection_uri=uri)
    
    with open("scripts/init_order_schema.sql", "r") as f:
        sql = f.read()
    
    print("Executing migration script...")
    success = repo.execute_script(sql)
    
    if success:
        print("✓ Migration successful.")
    else:
        print("✗ Migration failed.")

if __name__ == "__main__":
    run_migration()
