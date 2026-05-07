"""
serving/services/identity_manager.py

Centralized Identity & Access Management (IAM) service. 
Interfaces with PostgreSQL to manage users, roles, and authentication.
"""

import bcrypt
import jwt
import datetime
from typing import Optional, Dict, Any, List
from infrastructure.logging.logger import get_logger
from repo import get_repository
from etl.config.settings import get_settings

logger = get_logger(__name__)

# Move this to .env in production
SECRET_KEY = "orion_ledger_secret_99" 
ALGORITHM = "HS256"

class IdentityManager:
    @staticmethod
    def _get_postgres():
        settings = get_settings().extract.postgres
        return get_repository("postgres", **vars(settings))

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @classmethod
    def create_user(cls, email: str, password: str, full_name: str, role_names: List[str] = None):
        """
        Registers a new user in PostgreSQL and assigns roles.
        """
        repo = cls._get_postgres()
        hashed = cls.hash_password(password)
        
        user_record = {
            "email": email,
            "password_hash": hashed,
            "full_name": full_name,
            "is_active": True
        }
        
        try:
            with repo:
                # 1. Insert user
                repo.add_record("users", user_record)
                
                # 2. Assign Roles if provided
                if role_names:
                    # Fetch user ID (Postgres auto-generates UUID)
                    user = repo.get_record("users", filters={"email": email})[0]
                    user_id = user['id']
                    
                    # Fetch Role IDs
                    all_roles = repo.get_record("roles")
                    role_map = {r['name']: r['id'] for r in all_roles}
                    
                    for r_name in role_names:
                        if r_name in role_map:
                            repo.add_record("user_roles", {
                                "user_id": user_id,
                                "role_id": role_map[r_name]
                            })
                
                logger.info(f"User {email} created successfully.")
                return True
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verifies credentials and returns a user summary + JWT.
        """
        repo = cls._get_postgres()
        try:
            with repo:
                users = repo.get_record("users", filters={"email": email})
                if not users:
                    return None
                
                user = users[0]
                if not cls.verify_password(password, user['password_hash']):
                    return None
                
                # Success - Create Token
                token = jwt.encode({
                    "sub": str(user['id']),
                    "email": user['email'],
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, SECRET_KEY, algorithm=ALGORITHM)
                
                return {
                    "id": str(user['id']),
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "access_token": token
                }
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None
