"""
Database Manager - Production-Ready Database Operations
Handles all CRUD operations with connection pooling, transaction management, and error handling
"""

import sqlite3
import asyncio
import logging
import json
from typing import Optional, List, Dict, Any, Callable, Coroutine
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from dataclasses import asdict

from models.models import (
    Workflow, Task, ExecutionLog, ErrorLog, Metric, Approval, CRMContact,
    ContactHistory, ContentQueue, ContentAnalytics, LearningInsight, AuditLog,
    TaskStatus, ExecutionStatus, ApprovalStatus, ContactStatus, ContentStatus,
    ErrorType, RiskLevel, Severity
)


logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Simple SQLite connection pool for async operations"""

    def __init__(self, db_path: str, pool_size: int = 5, timeout: int = 30):
        """
        Initialize connection pool

        Args:
            db_path: Path to SQLite database
            pool_size: Number of connections to maintain
            timeout: Connection timeout in seconds
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.connections: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return

        for _ in range(self.pool_size):
            conn = await self._create_connection()
            await self.connections.put(conn)
        self._initialized = True
        logger.info(f"Database pool initialized with {self.pool_size} connections")

    async def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._sync_create_connection
        )

    def _sync_create_connection(self) -> sqlite3.Connection:
        """Synchronous connection creation"""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for getting a connection from the pool"""
        conn = await asyncio.wait_for(self.connections.get(), timeout=self.timeout)
        try:
            yield conn
        finally:
            await self.connections.put(conn)

    async def close_all(self):
        """Close all connections in the pool"""
        loop = asyncio.get_event_loop()
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                await loop.run_in_executor(None, lambda c=conn: c.close())
            except asyncio.QueueEmpty:
                break
        self._initialized = False
        logger.info("Database pool closed")


class DatabaseManager:
    """Main database manager with full CRUD operations"""

    def __init__(self, db_path: str = "automation.db", pool_size: int = 5):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database
            pool_size: Number of connections in pool
        """
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, pool_size=pool_size)
        self._initialized = False

    async def initialize(self):
        """Initialize database and connection pool"""
        if self._initialized:
            return

        # Create database file if it doesn't exist
        Path(self.db_path).touch()

        # Initialize pool
        await self.pool.initialize()

        # Load schema
        await self._load_schema()

        self._initialized = True
        logger.info(f"Database manager initialized: {self.db_path}")

    async def _load_schema(self):
        """Load and execute database schema"""
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"

        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.executescript(schema_sql)
            )
        logger.info("Database schema loaded successfully")

    # ========================================================================
    # WORKFLOW OPERATIONS
    # ========================================================================

    async def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow"""
        query = """
        INSERT INTO workflows 
        (id, name, level, definition, description, enabled, version, created_at, updated_at, created_by, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        workflow.id,
                        workflow.name,
                        workflow.level,
                        json.dumps(workflow.definition),
                        workflow.description,
                        workflow.enabled,
                        workflow.version,
                        workflow.created_at,
                        workflow.updated_at,
                        workflow.created_by,
                        workflow.updated_by
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
        logger.info(f"Created workflow: {workflow.id}")
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        query = "SELECT * FROM workflows WHERE id = ?"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            row = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (workflow_id,)).fetchone()
            )

        if not row:
            return None

        return self._parse_workflow_row(row)

    async def get_enabled_workflows(self) -> List[Workflow]:
        """Get all enabled workflows"""
        query = "SELECT * FROM workflows WHERE enabled = 1"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query).fetchall()
            )

        return [self._parse_workflow_row(row) for row in rows]

    async def update_workflow(self, workflow: Workflow) -> None:
        """Update an existing workflow"""
        query = """
        UPDATE workflows
        SET name = ?, level = ?, definition = ?, description = ?, enabled = ?, 
            version = ?, updated_at = ?, updated_by = ?
        WHERE id = ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        workflow.name,
                        workflow.level,
                        json.dumps(workflow.definition),
                        workflow.description,
                        workflow.enabled,
                        workflow.version,
                        datetime.utcnow(),
                        workflow.updated_by,
                        workflow.id
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
        logger.info(f"Updated workflow: {workflow.id}")

    # ========================================================================
    # TASK OPERATIONS
    # ========================================================================

    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        query = """
        INSERT INTO tasks 
        (id, workflow_id, status, priority, level, created_at, started_at, completed_at,
         input_params, output_data, error_message, retry_count, max_retries, assigned_to, timeout_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        task.id,
                        task.workflow_id,
                        task.status.value,
                        task.priority,
                        task.level,
                        task.created_at,
                        task.started_at,
                        task.completed_at,
                        json.dumps(task.input_params) if task.input_params else None,
                        json.dumps(task.output_data) if task.output_data else None,
                        task.error_message,
                        task.retry_count,
                        task.max_retries,
                        task.assigned_to,
                        task.timeout_seconds
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
        logger.info(f"Created task: {task.id}")
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        query = "SELECT * FROM tasks WHERE id = ?"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            row = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (task_id,)).fetchone()
            )

        if not row:
            return None

        return self._parse_task_row(row)

    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        query = "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (status.value, datetime.utcnow(), task_id))
            )
            await loop.run_in_executor(None, conn.commit)
        logger.info(f"Updated task {task_id} status to {status.value}")

    async def get_pending_tasks(self, level: Optional[int] = None, limit: int = 100) -> List[Task]:
        """Get pending tasks, optionally filtered by level"""
        if level:
            query = "SELECT * FROM tasks WHERE status = ? AND level <= ? ORDER BY priority DESC LIMIT ?"
            params = (TaskStatus.PENDING.value, level, limit)
        else:
            query = "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC LIMIT ?"
            params = (TaskStatus.PENDING.value, limit)

        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, params).fetchall()
            )

        return [self._parse_task_row(row) for row in rows]

    async def get_tasks_by_workflow(self, workflow_id: str) -> List[Task]:
        """Get all tasks for a workflow"""
        query = "SELECT * FROM tasks WHERE workflow_id = ? ORDER BY created_at DESC"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (workflow_id,)).fetchall()
            )

        return [self._parse_task_row(row) for row in rows]

    async def get_running_tasks(self) -> List[Task]:
        """Get all currently running tasks"""
        query = "SELECT * FROM tasks WHERE status = ? ORDER BY started_at"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (TaskStatus.RUNNING.value,)).fetchall()
            )

        return [self._parse_task_row(row) for row in rows]

    async def update_task(self, task: Task) -> None:
        """Update entire task record"""
        query = """
        UPDATE tasks
        SET workflow_id = ?, status = ?, priority = ?, level = ?, started_at = ?, 
            completed_at = ?, input_params = ?, output_data = ?, error_message = ?, 
            retry_count = ?, max_retries = ?, assigned_to = ?, timeout_seconds = ?
        WHERE id = ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        task.workflow_id,
                        task.status.value,
                        task.priority,
                        task.level,
                        task.started_at,
                        task.completed_at,
                        json.dumps(task.input_params) if task.input_params else None,
                        json.dumps(task.output_data) if task.output_data else None,
                        task.error_message,
                        task.retry_count,
                        task.max_retries,
                        task.assigned_to,
                        task.timeout_seconds,
                        task.id
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
        logger.info(f"Updated task: {task.id}")

    # ========================================================================
    # EXECUTION LOG OPERATIONS
    # ========================================================================

    async def create_execution_log(self, log: ExecutionLog) -> ExecutionLog:
        """Create a new execution log"""
        query = """
        INSERT INTO execution_logs 
        (task_id, step_name, step_index, status, started_at, completed_at, duration_ms, 
         output, error, error_code, retry_attempt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        log.task_id,
                        log.step_name,
                        log.step_index,
                        log.status.value,
                        log.started_at,
                        log.completed_at,
                        log.duration_ms,
                        json.dumps(log.output) if log.output else None,
                        log.error,
                        log.error_code,
                        log.retry_attempt
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
            log.id = cursor.lastrowid

        logger.info(f"Created execution log for task: {log.task_id}")
        return log

    async def get_execution_logs(self, task_id: str) -> List[ExecutionLog]:
        """Get all execution logs for a task"""
        query = "SELECT * FROM execution_logs WHERE task_id = ? ORDER BY started_at"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (task_id,)).fetchall()
            )

        return [self._parse_execution_log_row(row) for row in rows]

    # ========================================================================
    # ERROR LOG OPERATIONS
    # ========================================================================

    async def create_error_log(self, error: ErrorLog) -> ErrorLog:
        """Create a new error log"""
        query = """
        INSERT INTO error_logs 
        (task_id, workflow_id, timestamp, error_type, severity, message, stack_trace, 
         recovery_strategy, recovery_success, recovery_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        error.task_id,
                        error.workflow_id,
                        error.timestamp,
                        error.error_type.value,
                        error.severity.value,
                        error.message,
                        error.stack_trace,
                        error.recovery_strategy,
                        error.recovery_success,
                        error.recovery_timestamp
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
            error.id = cursor.lastrowid

        logger.warning(f"Created error log: {error.error_type.value} - {error.message}")
        return error

    async def get_error_logs(self, task_id: Optional[str] = None, limit: int = 100) -> List[ErrorLog]:
        """Get error logs, optionally filtered by task"""
        if task_id:
            query = "SELECT * FROM error_logs WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?"
            params = (task_id, limit)
        else:
            query = "SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)

        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, params).fetchall()
            )

        return [self._parse_error_log_row(row) for row in rows]

    async def get_critical_errors(self, hours: int = 24) -> List[ErrorLog]:
        """Get critical errors from the last N hours"""
        timestamp_filter = datetime.utcnow() - timedelta(hours=hours)
        query = """
        SELECT * FROM error_logs 
        WHERE severity = ? AND timestamp > ?
        ORDER BY timestamp DESC
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (Severity.CRITICAL.value, timestamp_filter)).fetchall()
            )

        return [self._parse_error_log_row(row) for row in rows]

    # ========================================================================
    # METRIC OPERATIONS
    # ========================================================================

    async def record_metric(self, metric: Metric) -> Metric:
        """Record a workflow metric"""
        query = """
        INSERT INTO metrics 
        (workflow_id, timestamp, period_minutes, success_count, failure_count, total_tasks,
         avg_duration_ms, min_duration_ms, max_duration_ms, p50_duration_ms, 
         p95_duration_ms, p99_duration_ms, success_rate, error_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        metric.workflow_id,
                        metric.timestamp,
                        metric.period_minutes,
                        metric.success_count,
                        metric.failure_count,
                        metric.total_tasks,
                        metric.avg_duration_ms,
                        metric.min_duration_ms,
                        metric.max_duration_ms,
                        metric.p50_duration_ms,
                        metric.p95_duration_ms,
                        metric.p99_duration_ms,
                        metric.success_rate,
                        metric.error_rate
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
            metric.id = cursor.lastrowid

        logger.debug(f"Recorded metric for workflow: {metric.workflow_id}")
        return metric

    async def get_workflow_metrics(self, workflow_id: str, hours: int = 24) -> List[Metric]:
        """Get metrics for a workflow from the last N hours"""
        timestamp_filter = datetime.utcnow() - timedelta(hours=hours)
        query = """
        SELECT * FROM metrics 
        WHERE workflow_id = ? AND timestamp > ?
        ORDER BY timestamp DESC
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (workflow_id, timestamp_filter)).fetchall()
            )

        return [self._parse_metric_row(row) for row in rows]

    async def get_aggregated_metrics(self, workflow_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated metrics for a workflow"""
        metrics = await self.get_workflow_metrics(workflow_id, hours)

        if not metrics:
            return {
                'workflow_id': workflow_id,
                'period_hours': hours,
                'total_tasks': 0,
                'success_count': 0,
                'failure_count': 0,
                'avg_duration_ms': 0,
                'p95_duration_ms': 0,
                'success_rate': 0
            }

        total_success = sum(m.success_count for m in metrics)
        total_failure = sum(m.failure_count for m in metrics)
        total_tasks = total_success + total_failure
        avg_durations = [m.avg_duration_ms for m in metrics if m.avg_duration_ms]

        return {
            'workflow_id': workflow_id,
            'period_hours': hours,
            'total_tasks': total_tasks,
            'success_count': total_success,
            'failure_count': total_failure,
            'avg_duration_ms': sum(avg_durations) / len(avg_durations) if avg_durations else 0,
            'p95_duration_ms': max([m.p95_duration_ms for m in metrics if m.p95_duration_ms], default=0),
            'success_rate': total_success / total_tasks if total_tasks > 0 else 0
        }

    # ========================================================================
    # APPROVAL OPERATIONS
    # ========================================================================

    async def create_approval(self, approval: Approval) -> Approval:
        """Create a new approval request"""
        query = """
        INSERT INTO approvals 
        (id, task_id, action, risk_level, proposed_by, status, rationale, 
         requested_at, responded_at, response_from, approval_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        approval.id,
                        approval.task_id,
                        approval.action,
                        approval.risk_level.value,
                        approval.proposed_by,
                        approval.status.value,
                        approval.rationale,
                        approval.requested_at,
                        approval.responded_at,
                        approval.response_from,
                        approval.approval_notes
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Created approval request: {approval.id}")
        return approval

    async def get_pending_approvals(self, risk_level: Optional[RiskLevel] = None) -> List[Approval]:
        """Get pending approval requests"""
        if risk_level:
            query = """
            SELECT * FROM approvals 
            WHERE status = ? AND risk_level = ?
            ORDER BY requested_at
            """
            params = (ApprovalStatus.PENDING.value, risk_level.value)
        else:
            query = """
            SELECT * FROM approvals 
            WHERE status = ?
            ORDER BY requested_at
            """
            params = (ApprovalStatus.PENDING.value,)

        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, params).fetchall()
            )

        return [self._parse_approval_row(row) for row in rows]

    async def update_approval(self, approval: Approval) -> None:
        """Update an approval request"""
        query = """
        UPDATE approvals
        SET status = ?, responded_at = ?, response_from = ?, approval_notes = ?
        WHERE id = ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        approval.status.value,
                        approval.responded_at,
                        approval.response_from,
                        approval.approval_notes,
                        approval.id
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Updated approval: {approval.id} - {approval.status.value}")

    # ========================================================================
    # CRM OPERATIONS
    # ========================================================================

    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new CRM contact"""
        query = """
        INSERT INTO crm_contacts 
        (id, email, name, company, job_title, phone, status, source, score, last_contact,
         last_contacted_by, tags, metadata, created_at, updated_at, created_by, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        contact.id,
                        contact.email,
                        contact.name,
                        contact.company,
                        contact.job_title,
                        contact.phone,
                        contact.status.value,
                        contact.source,
                        contact.score,
                        contact.last_contact,
                        contact.last_contacted_by,
                        json.dumps(contact.tags),
                        json.dumps(contact.metadata),
                        contact.created_at,
                        contact.updated_at,
                        contact.created_by,
                        contact.updated_by
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Created contact: {contact.id}")
        return contact

    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get a contact by ID"""
        query = "SELECT * FROM crm_contacts WHERE id = ?"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            row = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (contact_id,)).fetchone()
            )

        return self._parse_contact_row(row) if row else None

    async def get_contact_by_email(self, email: str) -> Optional[CRMContact]:
        """Get a contact by email"""
        query = "SELECT * FROM crm_contacts WHERE email = ?"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            row = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (email,)).fetchone()
            )

        return self._parse_contact_row(row) if row else None

    async def get_contacts_by_status(self, status: ContactStatus) -> List[CRMContact]:
        """Get contacts by status"""
        query = "SELECT * FROM crm_contacts WHERE status = ? ORDER BY score DESC"
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (status.value,)).fetchall()
            )

        return [self._parse_contact_row(row) for row in rows]

    async def update_contact(self, contact: CRMContact) -> None:
        """Update a contact"""
        query = """
        UPDATE crm_contacts
        SET email = ?, name = ?, company = ?, job_title = ?, phone = ?, status = ?,
            source = ?, score = ?, last_contact = ?, last_contacted_by = ?, 
            tags = ?, metadata = ?, updated_at = ?, updated_by = ?
        WHERE id = ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        contact.email,
                        contact.name,
                        contact.company,
                        contact.job_title,
                        contact.phone,
                        contact.status.value,
                        contact.source,
                        contact.score,
                        contact.last_contact,
                        contact.last_contacted_by,
                        json.dumps(contact.tags),
                        json.dumps(contact.metadata),
                        datetime.utcnow(),
                        contact.updated_by,
                        contact.id
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Updated contact: {contact.id}")

    # ========================================================================
    # CONTENT OPERATIONS
    # ========================================================================

    async def create_content(self, content: ContentQueue) -> ContentQueue:
        """Create a new content queue item"""
        query = """
        INSERT INTO content_queue 
        (id, type, platform, content, media_paths, scheduled_for, status, priority,
         campaign_id, target_audience, created_at, published_at, failed_at, 
         failure_reason, created_by, engagement_metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        content.id,
                        content.type.value,
                        content.platform,
                        content.content,
                        json.dumps(content.media_paths),
                        content.scheduled_for,
                        content.status.value,
                        content.priority,
                        content.campaign_id,
                        json.dumps(content.target_audience),
                        content.created_at,
                        content.published_at,
                        content.failed_at,
                        content.failure_reason,
                        content.created_by,
                        json.dumps(content.engagement_metrics)
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Created content: {content.id}")
        return content

    async def get_scheduled_content(self, limit: int = 50) -> List[ContentQueue]:
        """Get pending scheduled content"""
        query = """
        SELECT * FROM content_queue 
        WHERE status = ? AND scheduled_for <= ?
        ORDER BY priority DESC, scheduled_for ASC
        LIMIT ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (ContentStatus.SCHEDULED.value, datetime.utcnow(), limit)
                ).fetchall()
            )

        return [self._parse_content_row(row) for row in rows]

    async def update_content(self, content: ContentQueue) -> None:
        """Update a content item"""
        query = """
        UPDATE content_queue
        SET type = ?, platform = ?, content = ?, media_paths = ?, scheduled_for = ?,
            status = ?, priority = ?, campaign_id = ?, target_audience = ?, 
            published_at = ?, failed_at = ?, failure_reason = ?, engagement_metrics = ?
        WHERE id = ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        content.type.value,
                        content.platform,
                        content.content,
                        json.dumps(content.media_paths),
                        content.scheduled_for,
                        content.status.value,
                        content.priority,
                        content.campaign_id,
                        json.dumps(content.target_audience),
                        content.published_at,
                        content.failed_at,
                        content.failure_reason,
                        json.dumps(content.engagement_metrics),
                        content.id
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)

        logger.info(f"Updated content: {content.id}")

    # ========================================================================
    # LEARNING INSIGHTS OPERATIONS
    # ========================================================================

    async def create_insight(self, insight: LearningInsight) -> LearningInsight:
        """Create a new learning insight"""
        query = """
        INSERT INTO learning_insights 
        (type, category, title, description, data, confidence, priority, 
         recommended_action, generated_at, applied, applied_at, result, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        insight.type.value,
                        insight.category,
                        insight.title,
                        insight.description,
                        json.dumps(insight.data),
                        insight.confidence,
                        insight.priority,
                        insight.recommended_action,
                        insight.generated_at,
                        insight.applied,
                        insight.applied_at,
                        json.dumps(insight.result) if insight.result else None,
                        insight.created_by
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
            insight.id = cursor.lastrowid

        logger.info(f"Created insight: {insight.id}")
        return insight

    async def get_unapplied_insights(self, limit: int = 50) -> List[LearningInsight]:
        """Get unapplied insights"""
        query = """
        SELECT * FROM learning_insights 
        WHERE applied = 0
        ORDER BY confidence DESC, priority DESC, generated_at DESC
        LIMIT ?
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: conn.execute(query, (limit,)).fetchall()
            )

        return [self._parse_insight_row(row) for row in rows]

    # ========================================================================
    # AUDIT OPERATIONS
    # ========================================================================

    async def log_audit(self, audit: AuditLog) -> AuditLog:
        """Create an audit log entry"""
        query = """
        INSERT INTO audit_trail 
        (timestamp, actor, action, resource_type, resource_id, changes, metadata, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.pool.get_connection() as conn:
            loop = asyncio.get_event_loop()
            cursor = await loop.run_in_executor(
                None,
                lambda: conn.execute(
                    query,
                    (
                        audit.timestamp,
                        audit.actor,
                        audit.action,
                        audit.resource_type,
                        audit.resource_id,
                        json.dumps(audit.changes) if audit.changes else None,
                        json.dumps(audit.metadata) if audit.metadata else None,
                        audit.ip_address,
                        audit.user_agent
                    )
                )
            )
            await loop.run_in_executor(None, conn.commit)
            audit.id = cursor.lastrowid

        logger.info(f"Audit: {audit.actor} {audit.action} {audit.resource_type}/{audit.resource_id}")
        return audit

    # ========================================================================
    # PARSING HELPERS
    # ========================================================================

    def _parse_workflow_row(self, row) -> Workflow:
        """Parse a workflow row into model"""
        definition = json.loads(row['definition']) if isinstance(row['definition'], str) else row['definition']
        return Workflow(
            id=row['id'],
            name=row['name'],
            level=row['level'],
            definition=definition,
            description=row['description'],
            enabled=bool(row['enabled']),
            version=row['version'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            created_by=row['created_by'],
            updated_by=row['updated_by']
        )

    def _parse_task_row(self, row) -> Task:
        """Parse a task row into model"""
        input_params = json.loads(row['input_params']) if row['input_params'] else None
        output_data = json.loads(row['output_data']) if row['output_data'] else None
        return Task(
            id=row['id'],
            workflow_id=row['workflow_id'],
            status=TaskStatus(row['status']),
            priority=row['priority'],
            level=row['level'],
            created_at=datetime.fromisoformat(row['created_at']),
            input_params=input_params,
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            output_data=output_data,
            error_message=row['error_message'],
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            assigned_to=row['assigned_to'],
            timeout_seconds=row['timeout_seconds']
        )

    def _parse_execution_log_row(self, row) -> ExecutionLog:
        """Parse an execution log row"""
        output = json.loads(row['output']) if row['output'] else None
        return ExecutionLog(
            id=row['id'],
            task_id=row['task_id'],
            step_name=row['step_name'],
            status=ExecutionStatus(row['status']),
            started_at=datetime.fromisoformat(row['started_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            duration_ms=row['duration_ms'],
            output=output,
            error=row['error'],
            error_code=row['error_code'],
            step_index=row['step_index'],
            retry_attempt=row['retry_attempt']
        )

    def _parse_error_log_row(self, row) -> ErrorLog:
        """Parse an error log row"""
        return ErrorLog(
            id=row['id'],
            task_id=row['task_id'],
            workflow_id=row['workflow_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            error_type=ErrorType(row['error_type']),
            severity=Severity(row['severity']),
            message=row['message'],
            stack_trace=row['stack_trace'],
            recovery_strategy=row['recovery_strategy'],
            recovery_success=row['recovery_success'],
            recovery_timestamp=datetime.fromisoformat(row['recovery_timestamp']) if row['recovery_timestamp'] else None
        )

    def _parse_metric_row(self, row) -> Metric:
        """Parse a metric row"""
        return Metric(
            id=row['id'],
            workflow_id=row['workflow_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            period_minutes=row['period_minutes'],
            success_count=row['success_count'],
            failure_count=row['failure_count'],
            total_tasks=row['total_tasks'],
            avg_duration_ms=row['avg_duration_ms'],
            min_duration_ms=row['min_duration_ms'],
            max_duration_ms=row['max_duration_ms'],
            p50_duration_ms=row['p50_duration_ms'],
            p95_duration_ms=row['p95_duration_ms'],
            p99_duration_ms=row['p99_duration_ms'],
            success_rate=row['success_rate'],
            error_rate=row['error_rate']
        )

    def _parse_approval_row(self, row) -> Approval:
        """Parse an approval row"""
        return Approval(
            id=row['id'],
            task_id=row['task_id'],
            action=row['action'],
            risk_level=RiskLevel(row['risk_level']),
            proposed_by=row['proposed_by'],
            status=ApprovalStatus(row['status']),
            rationale=row['rationale'],
            requested_at=datetime.fromisoformat(row['requested_at']),
            responded_at=datetime.fromisoformat(row['responded_at']) if row['responded_at'] else None,
            response_from=row['response_from'],
            approval_notes=row['approval_notes']
        )

    def _parse_contact_row(self, row) -> CRMContact:
        """Parse a contact row"""
        tags = json.loads(row['tags']) if row['tags'] else []
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        return CRMContact(
            id=row['id'],
            email=row['email'],
            name=row['name'],
            company=row['company'],
            job_title=row['job_title'],
            phone=row['phone'],
            status=ContactStatus(row['status']),
            source=row['source'],
            score=row['score'],
            last_contact=datetime.fromisoformat(row['last_contact']) if row['last_contact'] else None,
            last_contacted_by=row['last_contacted_by'],
            tags=tags,
            metadata=metadata,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            created_by=row['created_by'],
            updated_by=row['updated_by']
        )

    def _parse_content_row(self, row) -> ContentQueue:
        """Parse a content row"""
        media_paths = json.loads(row['media_paths']) if row['media_paths'] else []
        target_audience = json.loads(row['target_audience']) if row['target_audience'] else []
        engagement_metrics = json.loads(row['engagement_metrics']) if row['engagement_metrics'] else {}
        return ContentQueue(
            id=row['id'],
            type=ContentType(row['type']),
            platform=row['platform'],
            content=row['content'],
            scheduled_for=datetime.fromisoformat(row['scheduled_for']),
            status=ContentStatus(row['status']),
            priority=row['priority'],
            media_paths=media_paths,
            campaign_id=row['campaign_id'],
            target_audience=target_audience,
            created_at=datetime.fromisoformat(row['created_at']),
            published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None,
            failed_at=datetime.fromisoformat(row['failed_at']) if row['failed_at'] else None,
            failure_reason=row['failure_reason'],
            created_by=row['created_by'],
            engagement_metrics=engagement_metrics
        )

    def _parse_insight_row(self, row) -> LearningInsight:
        """Parse a learning insight row"""
        data = json.loads(row['data']) if row['data'] else {}
        result = json.loads(row['result']) if row['result'] else None
        return LearningInsight(
            id=row['id'],
            type=InsightType(row['type']),
            category=row['category'],
            title=row['title'],
            description=row['description'],
            data=data,
            confidence=row['confidence'],
            priority=row['priority'],
            recommended_action=row['recommended_action'],
            generated_at=datetime.fromisoformat(row['generated_at']),
            applied=bool(row['applied']),
            applied_at=datetime.fromisoformat(row['applied_at']) if row['applied_at'] else None,
            result=result,
            created_by=row['created_by']
        )

    async def close(self):
        """Close database connections"""
        await self.pool.close_all()
        self._initialized = False
        logger.info("Database manager closed")
