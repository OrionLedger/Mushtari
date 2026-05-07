import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from repo import get_repository
from etl.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger("InfrastructureDeployment")

def deploy_postgres():
    """Reads and executes the SQL schema for PostgreSQL."""
    logger.info("Starting PostgreSQL infrastructure deployment...")
    sql_path = Path(__file__).resolve().parent / "init_postgres.sql"
    
    if not sql_path.exists():
        logger.error(f"SQL file not found at {sql_path}")
        return False

    with open(sql_path, "r") as f:
        sql_content = f.read()

    settings = get_settings().extract.postgres
    repo = get_repository(
        "postgres",
        user=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        dbname=settings.dbname
    )

    success = repo.execute_script(sql_content)
    if success:
        logger.info("PostgreSQL schema deployed successfully.")
    else:
        logger.error("PostgreSQL deployment failed.")
    
    repo.close()
    return success

def deploy_cassandra():
    """Reads and executes the CQL schema for Cassandra."""
    logger.info("Starting Cassandra infrastructure deployment...")
    cql_path = Path(__file__).resolve().parent / "init_cassandra.cql"
    
    if not cql_path.exists():
        logger.error(f"CQL file not found at {cql_path}")
        return False

    with open(cql_path, "r") as f:
        cql_content = f.read()

    settings = get_settings().extract.cassandra
    repo = get_repository(
        "cassandra",
        username=settings.username,
        password=settings.password,
        contact_points=settings.contact_points,
        port=settings.port,
        keyspace=None # Initial deployment shouldn't assume keyspace exists
    )

    success = repo.execute_script(cql_content)
    if success:
        logger.info("Cassandra schema deployed successfully.")
    else:
        logger.error("Cassandra deployment failed.")
    
    repo.close()
    return success

def verify_system_health():
    """Performs a sanity check on both repositories."""
    logger.info("Verifying system health across both repositories...")
    
    # Check Postgres
    try:
        settings = get_settings().extract.postgres
        with get_repository("postgres", **vars(settings)) as repo:
            if repo.table_exists("products"):
                logger.info("POSTGRES: Sanity check passed (Table 'products' exists).")
            else:
                logger.warning("POSTGRES: Table 'products' not found.")
    except Exception as e:
        logger.error(f"POSTGRES: Health check failed: {e}")

    # Check Cassandra
    try:
        settings = get_settings().extract.cassandra
        # We need to explicitly check if connection works with keyspace now
        with get_repository("cassandra", **vars(settings)) as repo:
            if repo.table_exists("sales"):
                logger.info("CASSANDRA: Sanity check passed (Table 'sales' exists).")
            else:
                logger.warning("CASSANDRA: Table 'sales' not found.")
    except Exception as e:
        logger.error(f"CASSANDRA: Health check failed: {e}")

if __name__ == "__main__":
    pg_ok = deploy_postgres()
    cs_ok = deploy_cassandra()
    
    if pg_ok and cs_ok:
        verify_system_health()
        logger.info("Infrastructure deployment COMPLETE.")
    else:
        logger.error("Infrastructure deployment partial or failed.")
        sys.exit(1)
