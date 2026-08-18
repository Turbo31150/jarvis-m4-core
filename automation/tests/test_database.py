"""
Comprehensive Tests for Database Layer
Tests include happy path, edge cases, error handling, and async operations
"""

import asyncio
import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from models.models import (
    Workflow, Task, ExecutionLog, ErrorLog, Metric, Approval, CRMContact,
    ContactHistory, ContentQueue, ContentAnalytics, LearningInsight, AuditLog,
    TaskStatus, ExecutionStatus, ApprovalStatus, ContactStatus, ContentStatus,
    ContentType, ErrorType, RiskLevel, Severity, InsightType
)
from database.db_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def db_manager(temp_db):
    """Create and initialize database manager"""
    manager = DatabaseManager(db_path=temp_db, pool_size=3)
    await manager.initialize()
    try:
        yield manager
    finally:
        await manager.close()


@pytest.fixture
def sample_workflow():
    """Create a sample workflow"""
    return Workflow.create(
        name="test_workflow",
        level=2,
        definition={
            "steps": [
                {"name": "step1", "action": "api_call"},
                {"name": "step2", "action": "process_data"}
            ]
        },
        description="Test workflow"
    )


@pytest.fixture
def sample_task(sample_workflow):
    """Create a sample task"""
    return Task.create(
        workflow_id=sample_workflow.id,
        level=2,
        priority=3,
        input_params={"key": "value"},
        timeout_seconds=3600
    )


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_workflow(db_manager, sample_workflow):
    """Test creating a workflow"""
    result = await db_manager.create_workflow(sample_workflow)

    assert result.id == sample_workflow.id
    assert result.name == "test_workflow"
    assert result.level == 2
    assert result.enabled is True


@pytest.mark.asyncio
async def test_get_workflow(db_manager, sample_workflow):
    """Test retrieving a workflow"""
    await db_manager.create_workflow(sample_workflow)
    result = await db_manager.get_workflow(sample_workflow.id)

    assert result is not None
    assert result.id == sample_workflow.id
    assert result.name == sample_workflow.name


@pytest.mark.asyncio
async def test_get_workflow_not_found(db_manager):
    """Test retrieving a non-existent workflow"""
    result = await db_manager.get_workflow("nonexistent_id")
    assert result is None


@pytest.mark.asyncio
async def test_get_enabled_workflows(db_manager):
    """Test retrieving enabled workflows"""
    wf1 = Workflow.create("wf1", 1, {"steps": []})
    wf2 = Workflow.create("wf2", 2, {"steps": []})
    wf3 = Workflow.create("wf3", 3, {"steps": []})
    wf3.enabled = False

    await db_manager.create_workflow(wf1)
    await db_manager.create_workflow(wf2)
    await db_manager.create_workflow(wf3)

    results = await db_manager.get_enabled_workflows()

    assert len(results) == 2
    assert all(w.enabled for w in results)


@pytest.mark.asyncio
async def test_update_workflow(db_manager, sample_workflow):
    """Test updating a workflow"""
    await db_manager.create_workflow(sample_workflow)

    sample_workflow.name = "updated_name"
    sample_workflow.version = 2
    sample_workflow.enabled = False

    await db_manager.update_workflow(sample_workflow)

    result = await db_manager.get_workflow(sample_workflow.id)
    assert result.name == "updated_name"
    assert result.version == 2
    assert result.enabled is False


# ============================================================================
# TASK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_task(db_manager, sample_workflow, sample_task):
    """Test creating a task"""
    await db_manager.create_workflow(sample_workflow)
    result = await db_manager.create_task(sample_task)

    assert result.id == sample_task.id
    assert result.workflow_id == sample_workflow.id
    assert result.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_get_task(db_manager, sample_workflow, sample_task):
    """Test retrieving a task"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    result = await db_manager.get_task(sample_task.id)

    assert result is not None
    assert result.id == sample_task.id
    assert result.level == 2


@pytest.mark.asyncio
async def test_update_task_status(db_manager, sample_workflow, sample_task):
    """Test updating task status"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    await db_manager.update_task_status(sample_task.id, TaskStatus.RUNNING)

    result = await db_manager.get_task(sample_task.id)
    assert result.status == TaskStatus.RUNNING


@pytest.mark.asyncio
async def test_get_pending_tasks(db_manager, sample_workflow):
    """Test retrieving pending tasks"""
    await db_manager.create_workflow(sample_workflow)

    # Create multiple tasks
    for i in range(5):
        task = Task.create(
            workflow_id=sample_workflow.id,
            level=2,
            priority=i % 3,
            input_params={"index": i}
        )
        await db_manager.create_task(task)

    # Get only level 2 or lower
    results = await db_manager.get_pending_tasks(level=2, limit=10)

    assert len(results) == 5
    assert all(t.status == TaskStatus.PENDING for t in results)


@pytest.mark.asyncio
async def test_get_pending_tasks_by_level(db_manager, sample_workflow):
    """Test retrieving tasks filtered by level"""
    await db_manager.create_workflow(sample_workflow)

    # Create tasks at different levels
    for level in [1, 2, 3, 4, 5]:
        task = Task.create(
            workflow_id=sample_workflow.id,
            level=level,
            priority=3
        )
        await db_manager.create_task(task)

    # Get only level 2 or lower
    results = await db_manager.get_pending_tasks(level=2)

    assert all(t.level <= 2 for t in results)


@pytest.mark.asyncio
async def test_get_tasks_by_workflow(db_manager, sample_workflow):
    """Test retrieving all tasks for a workflow"""
    await db_manager.create_workflow(sample_workflow)

    for i in range(3):
        task = Task.create(
            workflow_id=sample_workflow.id,
            level=2,
            priority=3
        )
        await db_manager.create_task(task)

    results = await db_manager.get_tasks_by_workflow(sample_workflow.id)

    assert len(results) == 3
    assert all(t.workflow_id == sample_workflow.id for t in results)


@pytest.mark.asyncio
async def test_task_can_retry(db_manager, sample_workflow, sample_task):
    """Test task retry logic"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    assert sample_task.can_retry() is True

    # Max out retries
    sample_task.retry_count = sample_task.max_retries
    assert sample_task.can_retry() is False


# ============================================================================
# EXECUTION LOG TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_execution_log(db_manager, sample_workflow, sample_task):
    """Test creating an execution log"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    log = ExecutionLog.create(
        task_id=sample_task.id,
        step_name="process_step",
        step_index=0
    )

    result = await db_manager.create_execution_log(log)

    assert result.id is not None
    assert result.task_id == sample_task.id
    assert result.status == ExecutionStatus.PENDING


@pytest.mark.asyncio
async def test_execution_log_complete(db_manager, sample_workflow, sample_task):
    """Test completing an execution log"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    log = ExecutionLog.create(sample_task.id, "process_step")
    await db_manager.create_execution_log(log)

    # Simulate some work
    await asyncio.sleep(0.1)

    log.complete(
        status=ExecutionStatus.SUCCESS,
        output={"result": "success"}
    )

    assert log.status == ExecutionStatus.SUCCESS
    assert log.duration_ms > 0


@pytest.mark.asyncio
async def test_get_execution_logs(db_manager, sample_workflow, sample_task):
    """Test retrieving execution logs"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    # Create multiple logs
    for i in range(3):
        log = ExecutionLog.create(sample_task.id, f"step_{i}", step_index=i)
        await db_manager.create_execution_log(log)

    results = await db_manager.get_execution_logs(sample_task.id)

    assert len(results) == 3
    assert all(log.task_id == sample_task.id for log in results)


# ============================================================================
# ERROR LOG TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_error_log(db_manager, sample_workflow, sample_task):
    """Test creating an error log"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    error = ErrorLog.create(
        message="API timeout",
        error_type=ErrorType.TIMEOUT,
        severity=Severity.HIGH,
        task_id=sample_task.id,
        workflow_id=sample_workflow.id
    )

    result = await db_manager.create_error_log(error)

    assert result.id is not None
    assert result.message == "API timeout"
    assert result.error_type == ErrorType.TIMEOUT


@pytest.mark.asyncio
async def test_get_critical_errors(db_manager):
    """Test retrieving critical errors"""
    # Create errors with different severities
    for i in range(3):
        error = ErrorLog.create(
            message=f"Error {i}",
            error_type=ErrorType.SYSTEM if i % 2 == 0 else ErrorType.API_ERROR,
            severity=Severity.CRITICAL if i == 0 else Severity.HIGH,
            timestamp=datetime.utcnow() - timedelta(hours=i)
        )
        await db_manager.create_error_log(error)

    results = await db_manager.get_critical_errors(hours=24)

    assert len(results) >= 1
    assert all(e.severity == Severity.CRITICAL for e in results)


# ============================================================================
# METRIC TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_record_metric(db_manager, sample_workflow):
    """Test recording a metric"""
    await db_manager.create_workflow(sample_workflow)

    metric = Metric.create(sample_workflow.id)
    metric.success_count = 10
    metric.failure_count = 2
    metric.total_tasks = 12
    metric.avg_duration_ms = 150.5
    metric.p95_duration_ms = 300.0
    metric.calculate_rates()

    result = await db_manager.record_metric(metric)

    assert result.id is not None
    assert result.success_rate == 10 / 12


@pytest.mark.asyncio
async def test_get_workflow_metrics(db_manager, sample_workflow):
    """Test retrieving workflow metrics"""
    await db_manager.create_workflow(sample_workflow)

    # Create multiple metrics
    for i in range(5):
        metric = Metric.create(sample_workflow.id)
        metric.success_count = 10 - i
        metric.failure_count = i
        metric.total_tasks = 10
        metric.timestamp = datetime.utcnow() - timedelta(hours=i)
        await db_manager.record_metric(metric)

    results = await db_manager.get_workflow_metrics(sample_workflow.id, hours=24)

    assert len(results) == 5


@pytest.mark.asyncio
async def test_get_aggregated_metrics(db_manager, sample_workflow):
    """Test getting aggregated metrics"""
    await db_manager.create_workflow(sample_workflow)

    # Create several metrics
    for i in range(3):
        metric = Metric.create(sample_workflow.id)
        metric.success_count = 10
        metric.failure_count = 2
        metric.total_tasks = 12
        metric.avg_duration_ms = 100.0 + i * 50
        metric.p95_duration_ms = 250.0 + i * 50
        await db_manager.record_metric(metric)

    agg = await db_manager.get_aggregated_metrics(sample_workflow.id)

    assert agg['total_tasks'] == 36
    assert agg['success_count'] == 30
    assert agg['failure_count'] == 6


# ============================================================================
# APPROVAL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_approval(db_manager, sample_workflow, sample_task):
    """Test creating an approval request"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    approval = Approval.create(
        task_id=sample_task.id,
        action="send_message",
        risk_level=RiskLevel.HIGH,
        rationale="User mention detected"
    )

    result = await db_manager.create_approval(approval)

    assert result.id is not None
    assert result.status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_get_pending_approvals(db_manager, sample_workflow, sample_task):
    """Test retrieving pending approvals"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    # Create multiple approvals
    for i in range(3):
        approval = Approval.create(
            task_id=sample_task.id,
            action=f"action_{i}",
            risk_level=RiskLevel.MEDIUM if i % 2 == 0 else RiskLevel.HIGH
        )
        await db_manager.create_approval(approval)

    results = await db_manager.get_pending_approvals()

    assert len(results) == 3
    assert all(a.status == ApprovalStatus.PENDING for a in results)


@pytest.mark.asyncio
async def test_approve_request(db_manager, sample_workflow, sample_task):
    """Test approving a request"""
    await db_manager.create_workflow(sample_workflow)
    await db_manager.create_task(sample_task)

    approval = Approval.create(
        task_id=sample_task.id,
        action="send_message",
        risk_level=RiskLevel.MEDIUM
    )

    approval = await db_manager.create_approval(approval)

    approval.approve(response_from="user@example.com", notes="Looks good")
    await db_manager.update_approval(approval)

    result = await db_manager.get_pending_approvals()
    assert len(result) == 0  # No more pending approvals


# ============================================================================
# CRM TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_contact(db_manager):
    """Test creating a contact"""
    contact = CRMContact.create(
        email="test@example.com",
        name="Test User",
        company="Test Corp"
    )

    result = await db_manager.create_contact(contact)

    assert result.id == contact.id
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_contact(db_manager):
    """Test retrieving a contact"""
    contact = CRMContact.create(
        email="test@example.com",
        name="Test User"
    )
    await db_manager.create_contact(contact)

    result = await db_manager.get_contact(contact.id)

    assert result is not None
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_email(db_manager):
    """Test retrieving a contact by email"""
    contact = CRMContact.create(
        email="test@example.com",
        name="Test User"
    )
    await db_manager.create_contact(contact)

    result = await db_manager.get_contact_by_email("test@example.com")

    assert result is not None
    assert result.name == "Test User"


@pytest.mark.asyncio
async def test_get_contact_by_status(db_manager):
    """Test retrieving contacts by status"""
    for i in range(3):
        contact = CRMContact.create(
            email=f"test{i}@example.com",
            name=f"User {i}"
        )
        contact.status = ContactStatus.PROSPECT if i % 2 == 0 else ContactStatus.QUALIFIED
        await db_manager.create_contact(contact)

    results = await db_manager.get_contacts_by_status(ContactStatus.PROSPECT)

    assert len(results) >= 1
    assert all(c.status == ContactStatus.PROSPECT for c in results)


@pytest.mark.asyncio
async def test_contact_tags(db_manager):
    """Test adding and removing tags from a contact"""
    contact = CRMContact.create(
        email="test@example.com",
        name="Test User"
    )

    contact.add_tag("vip")
    contact.add_tag("enterprise")

    assert "vip" in contact.tags
    assert "enterprise" in contact.tags

    contact.remove_tag("vip")
    assert "vip" not in contact.tags


@pytest.mark.asyncio
async def test_contact_score(db_manager):
    """Test updating contact score"""
    contact = CRMContact.create(
        email="test@example.com",
        name="Test User"
    )

    assert contact.score == 0

    contact.update_score(25)
    assert contact.score == 25

    contact.update_score(30)
    assert contact.score == 55

    # Score shouldn't exceed 100
    contact.update_score(100)
    assert contact.score == 100


# ============================================================================
# CONTENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_content(db_manager):
    """Test creating content"""
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    content = ContentQueue.create(
        content_type=ContentType.LINKEDIN_POST,
        platform="linkedin",
        content="Test post content",
        scheduled_for=scheduled_time
    )

    result = await db_manager.create_content(content)

    assert result.id == content.id
    assert result.status == ContentStatus.DRAFT


@pytest.mark.asyncio
async def test_get_scheduled_content(db_manager):
    """Test retrieving scheduled content"""
    now = datetime.utcnow()

    # Create content scheduled in the past (should be retrieved)
    past_content = ContentQueue.create(
        content_type=ContentType.TWITTER,
        platform="twitter",
        content="Past content",
        scheduled_for=now - timedelta(hours=1)
    )
    past_content.status = ContentStatus.SCHEDULED
    await db_manager.create_content(past_content)

    # Create content scheduled in the future (should not be retrieved yet)
    future_content = ContentQueue.create(
        content_type=ContentType.TWITTER,
        platform="twitter",
        content="Future content",
        scheduled_for=now + timedelta(hours=2)
    )
    future_content.status = ContentStatus.SCHEDULED
    await db_manager.create_content(future_content)

    results = await db_manager.get_scheduled_content()

    assert any(c.id == past_content.id for c in results)
    assert not any(c.id == future_content.id for c in results)


@pytest.mark.asyncio
async def test_content_posted(db_manager):
    """Test marking content as posted"""
    content = ContentQueue.create(
        content_type=ContentType.LINKEDIN_POST,
        platform="linkedin",
        content="Test content",
        scheduled_for=datetime.utcnow()
    )

    await db_manager.create_content(content)

    content.mark_posted()
    assert content.status == ContentStatus.POSTED
    assert content.published_at is not None


# ============================================================================
# LEARNING INSIGHTS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_insight(db_manager):
    """Test creating a learning insight"""
    insight = LearningInsight.create(
        insight_type=InsightType.PATTERN,
        title="High engagement pattern",
        data={"pattern": "morning_posts_perform_better"},
        confidence=0.85
    )

    result = await db_manager.create_insight(insight)

    assert result.id is not None
    assert result.type == InsightType.PATTERN


@pytest.mark.asyncio
async def test_get_unapplied_insights(db_manager):
    """Test retrieving unapplied insights"""
    for i in range(3):
        insight = LearningInsight.create(
            insight_type=InsightType.SUGGESTION if i % 2 == 0 else InsightType.OPTIMIZATION,
            title=f"Insight {i}",
            data={"index": i},
            confidence=0.5 + i * 0.1
        )
        await db_manager.create_insight(insight)

    results = await db_manager.get_unapplied_insights()

    assert len(results) == 3
    assert all(not i.applied for i in results)


# ============================================================================
# AUDIT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_log_audit(db_manager):
    """Test creating audit log"""
    audit = AuditLog.create(
        actor="user123",
        action="create",
        resource_type="workflow",
        resource_id="wf_123",
        changes={"name": {"old": None, "new": "new_workflow"}}
    )

    result = await db_manager.log_audit(audit)

    assert result.id is not None
    assert result.actor == "user123"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_task_lifecycle(db_manager):
    """Test complete task lifecycle"""
    # Create workflow
    workflow = Workflow.create("full_test", 2, {"steps": []})
    await db_manager.create_workflow(workflow)

    # Create task
    task = Task.create(workflow.id, level=2, input_params={"data": "test"})
    await db_manager.create_task(task)

    # Start task
    task.started_at = datetime.utcnow()
    task.status = TaskStatus.RUNNING
    await db_manager.update_task(task)

    # Log execution
    log = ExecutionLog.create(task.id, "main_step")
    await db_manager.create_execution_log(log)

    # Complete task
    task.completed_at = datetime.utcnow()
    task.status = TaskStatus.COMPLETED
    task.output_data = {"result": "success"}
    await db_manager.update_task(task)

    # Verify final state
    final_task = await db_manager.get_task(task.id)
    assert final_task.status == TaskStatus.COMPLETED
    assert final_task.output_data is not None


@pytest.mark.asyncio
async def test_concurrent_task_operations(db_manager):
    """Test concurrent task operations"""
    workflow = Workflow.create("concurrent_test", 1, {"steps": []})
    await db_manager.create_workflow(workflow)

    # Create tasks concurrently
    tasks = [
        Task.create(workflow.id, level=1)
        for _ in range(10)
    ]

    await asyncio.gather(*[db_manager.create_task(t) for t in tasks])

    # Query pending tasks
    results = await db_manager.get_pending_tasks()

    assert len(results) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
