
from sqlalchemy import create_engine, text
from etl.config.settings import get_settings

def migrate_alerts_to_postgres():
    settings = get_settings().extract.postgres
    uri = f"postgresql://{settings.user}:{settings.password}@{settings.host}:{settings.port}/{settings.dbname}"
    engine = create_engine(uri)
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_alerts (
                id SERIAL PRIMARY KEY,
                alert_id UUID UNIQUE NOT NULL,
                severity VARCHAR(50) NOT NULL,
                event_type VARCHAR(100),
                alert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message TEXT,
                is_resolved BOOLEAN DEFAULT FALSE
            );
        """))
        conn.commit()
    print("Postgres system_alerts table initialized.")

if __name__ == "__main__":
    migrate_alerts_to_postgres()
