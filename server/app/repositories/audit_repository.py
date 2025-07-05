"""
Audit Repository for TMS API.
Handles all database operations related to audit logging.
"""

from typing import Dict, Any, Optional
from .base import PostgresRepository


class AuditRepository(PostgresRepository):
    """Repository for audit log operations"""

    async def log_action(self, table_name: str, record_id: str, action: str, changed_data: Dict[str, Any], user_id: Optional[str] = None):
        """Insert an audit log entry"""
        query = """
        INSERT INTO audit_logs (table_name, record_id, action, changed_data, user_id)
        VALUES ($1, $2, $3, $4, $5)
        """
        await self.execute_command(query, table_name, record_id, action, changed_data, user_id)
