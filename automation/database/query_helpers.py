"""
Query helpers for common database operations
Provides high-level functions for frequently used queries
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from models.models import (
    Task, TaskStatus, ContactStatus, ContentStatus, Severity, InsightType
)


class TaskQueries:
    """Task-specific query helpers"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_overdue_tasks(self, timeout_minutes: int = 60) -> List[Task]:
        """Get tasks that have exceeded their timeout"""
        running_tasks = await self.db.get_running_tasks()
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        overdue = [
            t for t in running_tasks
            if t.started_at and t.started_at < cutoff_time
        ]

        return overdue

    async def get_high_priority_pending(self, limit: int = 20) -> List[Task]:
        """Get high priority pending tasks"""
        pending = await self.db.get_pending_tasks(limit=limit)
        return sorted(pending, key=lambda t: t.priority, reverse=True)[:limit]

    async def get_failed_tasks(self, hours: int = 24) -> List[Task]:
        """Get failed tasks from last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        errors = await self.db.get_error_logs()

        failed_task_ids = set()
        for error in errors:
            if error.task_id and error.timestamp > cutoff:
                failed_task_ids.add(error.task_id)

        failed_tasks = []
        for task_id in failed_task_ids:
            task = await self.db.get_task(task_id)
            if task:
                failed_tasks.append(task)

        return failed_tasks

    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status"""
        if status == TaskStatus.PENDING:
            return await self.db.get_pending_tasks()

        query = """
        SELECT * FROM tasks WHERE status = ?
        ORDER BY priority DESC, created_at DESC
        """
        # Note: This would require adding a query method to DatabaseManager
        # Placeholder for demonstration
        return []

    async def get_retry_candidates(self) -> List[Task]:
        """Get tasks eligible for retry"""
        pending = await self.db.get_pending_tasks()
        return [t for t in pending if t.can_retry()]


class ContactQueries:
    """Contact-specific query helpers"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_high_score_contacts(self, min_score: int = 70) -> List:
        """Get contacts with high engagement scores"""
        prospects = await self.db.get_contacts_by_status(ContactStatus.PROSPECT)
        qualified = await self.db.get_contacts_by_status(ContactStatus.QUALIFIED)

        all_contacts = prospects + qualified
        return [c for c in all_contacts if c.score >= min_score]

    async def get_inactive_contacts(self, days: int = 30) -> List:
        """Get contacts not contacted in N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        prospects = await self.db.get_contacts_by_status(ContactStatus.PROSPECT)
        qualified = await self.db.get_contacts_by_status(ContactStatus.QUALIFIED)

        all_contacts = prospects + qualified
        return [
            c for c in all_contacts
            if c.last_contact is None or c.last_contact < cutoff
        ]

    async def get_contacts_with_tag(self, tag: str) -> List:
        """Get contacts with a specific tag"""
        prospects = await self.db.get_contacts_by_status(ContactStatus.PROSPECT)
        qualified = await self.db.get_contacts_by_status(ContactStatus.QUALIFIED)

        all_contacts = prospects + qualified
        return [c for c in all_contacts if tag in c.tags]


class ContentQueries:
    """Content-specific query helpers"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_ready_to_publish(self) -> List:
        """Get content ready to publish (scheduled and past due)"""
        return await self.db.get_scheduled_content()

    async def get_high_engagement_content(self, platform: Optional[str] = None) -> List:
        """Get content with high engagement"""
        # This would require additional queries to analytics table
        scheduled = await self.db.get_scheduled_content()
        return sorted(
            scheduled,
            key=lambda c: c.engagement_metrics.get('likes', 0) +
                         c.engagement_metrics.get('shares', 0),
            reverse=True
        )


class MetricsQueries:
    """Metrics-specific query helpers"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_health_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get overall health status of a workflow"""
        metrics = await self.db.get_aggregated_metrics(workflow_id, hours=24)
        errors = await self.db.get_error_logs()

        critical_errors = [e for e in errors if e.severity == Severity.CRITICAL]

        status = "healthy"
        if metrics['success_rate'] < 0.8:
            status = "degraded"
        if critical_errors:
            status = "critical"

        return {
            "status": status,
            "metrics": metrics,
            "critical_errors": len(critical_errors),
            "checked_at": datetime.utcnow().isoformat()
        }

    async def get_performance_trend(self, workflow_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance trend for a workflow"""
        metrics = await self.db.get_workflow_metrics(workflow_id, hours=hours)

        if len(metrics) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend
        latest = metrics[0]
        previous = metrics[-1]

        if latest.success_rate is None or previous.success_rate is None:
            trend = "neutral"
        elif latest.success_rate > previous.success_rate:
            trend = "improving"
        elif latest.success_rate < previous.success_rate:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "current_success_rate": latest.success_rate,
            "previous_success_rate": previous.success_rate,
            "period_hours": hours
        }


class InsightQueries:
    """Learning insight query helpers"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_actionable_insights(self, min_confidence: float = 0.7) -> List:
        """Get insights worth acting on"""
        insights = await self.db.get_unapplied_insights()
        return [
            i for i in insights
            if i.confidence >= min_confidence
            and i.recommended_action is not None
        ]

    async def get_high_priority_insights(self, limit: int = 10) -> List:
        """Get high priority insights"""
        insights = await self.db.get_unapplied_insights(limit=limit*2)
        return sorted(
            insights,
            key=lambda i: (i.priority, i.confidence),
            reverse=True
        )[:limit]


class QueryBuilder:
    """Helper to build complex queries"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.tasks = TaskQueries(db)
        self.contacts = ContactQueries(db)
        self.content = ContentQueries(db)
        self.metrics = MetricsQueries(db)
        self.insights = InsightQueries(db)

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard"""
        return {
            "pending_tasks": len(await self.db.get_pending_tasks()),
            "running_tasks": len(await self.db.get_running_tasks()),
            "pending_approvals": len(await self.db.get_pending_approvals()),
            "scheduled_content": len(await self.db.get_scheduled_content()),
            "unapplied_insights": len(await self.db.get_unapplied_insights()),
            "generated_at": datetime.utcnow().isoformat()
        }


# Convenience functions
async def build_queries(db: DatabaseManager) -> QueryBuilder:
    """Create a query builder instance"""
    return QueryBuilder(db)
