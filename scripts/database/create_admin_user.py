"""
scripts/database/create_admin_user.py

One-off script to create the initial administrative user in PostgreSQL.
"""

import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from serving.services.identity_manager import IdentityManager
from infrastructure.logging.logger import get_logger

logger = get_logger("CreateAdmin")

def create():
    email = os.getenv("ADMIN_EMAIL", "admin@orionledger.com")
    pw = os.getenv("ADMIN_PASSWORD", "orion_admin_secure")
    full_name = "System Administrator"

    logger.info(f"Creating Primary Admin User: {email}...")

    # IdentityManager handles password hashing and role assignment
    success = IdentityManager.create_user(
        email=email,
        password=pw,
        full_name=full_name,
        role_names=["Admin", "Analyst"]
    )

    if success:
        logger.info("✓ Admin user created successfully. Use these credentials to login.")
    else:
        logger.error("✗ Failed to create admin user. Ensure PostgreSQL is reachable and roles are seeded.")

if __name__ == "__main__":
    create()
