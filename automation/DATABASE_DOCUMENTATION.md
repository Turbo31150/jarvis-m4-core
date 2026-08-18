# Database Schema & ORM Models - Complete Documentation

## Overview

This module provides a production-ready database layer for the JARVIS Automation System with:

- **SQLite Database** with 16 core tables
- **ORM Models** using Python dataclasses
- **Async DatabaseManager** with connection pooling
- **Query Helpers** for common operations
- **Comprehensive Test Suite** with 40+ test cases

## Architecture

### Database Structure

```
automation.db
├── Core Workflow Tables
│   ├── workflows
│   └── tasks
├── Execution & Monitoring
│   ├── execution_logs
│   ├── error_logs
│   ├── metrics
│   └── performance_trends
├── Approval & Risk Management
│   └── approvals
├── CRM & Contacts
│   ├── crm_contacts
│   └── contact_history
├── Content Management
│   ├── content_queue
│   └── content_analytics
├── AI Learning
│   └── learning_insights
└── Audit & Compliance
    ├── audit_trail
    └── (all operations logged)
```

## File Structure

```
automation/
├── database/
│   ├── __init__.py           # Database initialization
│   ├── schema.sql            # Complete SQL schema (16 tables + indexes)
│   ├── db_manager.py         # Main database manager (1300+ lines)
│   └── query_helpers.py      # Query utilities and helpers
├── models/
│   ├── __init__.py
│   └── models.py             # 12 ORM models with 50+ enums (900 lines)
└── tests/
    ├── __init__.py
    └── test_database.py      # 40+ comprehensive tests
```

## Quick Start

### 1. Initialize Database

```python
import asyncio
from database import DatabaseInit

async def main():
    db_init = DatabaseInit(db_path="automation.db")
    manager = await db_init.initialize()
    # Database is ready for use
    return manager

manager = asyncio.run(main())
```

### 2. Create and Use Models

```python
from models import Workflow, Task, TaskStatus

# Create a workflow
workflow = Workflow.create(
    name="linkedin_outreach",
    level=3,
    definition={
        "steps": [
            {"name": "find_prospects", "action": "search"},
            {"name": "send_message", "action": "message"}
        ]
    }
)

# Create and save
await db_manager.create_workflow(workflow)

# Create a task
task = Task.create(
    workflow_id=workflow.id,
    level=3,
    priority=4,
    input_params={"search_query": "data scientist"}
)

await db_manager.create_task(task)
```

### 3. Query Data

```python
# Get pending tasks
pending = await db_manager.get_pending_tasks(level=3, limit=10)

# Get task details
task = await db_manager.get_task(task_id)

# Update task status
await db_manager.update_task_status(task_id, TaskStatus.RUNNING)

# Get execution logs
logs = await db_manager.get_execution_logs(task_id)
```

## ORM Models

### Core Models

#### Workflow
```python
@dataclass
class Workflow:
    id: str
    name: str
    level: int              # 1-5
    definition: Dict[str, Any]
    description: Optional[str] = None
    enabled: bool = True
    version: int = 1
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"
    updated_by: str = "system"

# Factory method
workflow = Workflow.create(name, level, definition, description)
```

#### Task
```python
@dataclass
class Task:
    id: str
    workflow_id: str
    status: TaskStatus              # pending, running, completed, failed, escalated
    priority: int                   # 1-5
    level: int                      # 1-5
    created_at: datetime
    input_params: Optional[Dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    assigned_to: Optional[str] = None
    timeout_seconds: int = 3600

# Factory method
task = Task.create(workflow_id, level, priority, input_params)

# Helper methods
task.is_running()           # bool
task.is_completed()         # bool
task.can_retry()            # bool
```

#### ExecutionLog
```python
@dataclass
class ExecutionLog:
    id: Optional[int]
    task_id: str
    step_name: str
    status: ExecutionStatus         # pending, running, success, warning, error
    started_at: datetime
    duration_ms: Optional[int] = None
    completed_at: Optional[datetime] = None
    output: Optional[Dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    step_index: Optional[int] = None
    retry_attempt: int = 0

# Create and complete
log = ExecutionLog.create(task_id, step_name)
log.complete(ExecutionStatus.SUCCESS, output={"result": "ok"})
```

#### ErrorLog
```python
@dataclass
class ErrorLog:
    id: Optional[int]
    task_id: Optional[str]
    workflow_id: Optional[str]
    timestamp: datetime
    error_type: ErrorType            # timeout, api_error, validation, system, etc.
    severity: Severity               # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    stack_trace: Optional[str] = None
    recovery_strategy: Optional[str] = None
    recovery_success: Optional[bool] = None
    recovery_timestamp: Optional[datetime] = None

# Factory method
error = ErrorLog.create(
    message="API timeout",
    error_type=ErrorType.TIMEOUT,
    severity=Severity.HIGH,
    task_id=task_id
)
```

#### Metric
```python
@dataclass
class Metric:
    id: Optional[int]
    workflow_id: str
    timestamp: datetime
    period_minutes: int = 60
    success_count: int = 0
    failure_count: int = 0
    total_tasks: int = 0
    avg_duration_ms: Optional[float] = None
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None
    p50_duration_ms: Optional[float] = None
    p95_duration_ms: Optional[float] = None
    p99_duration_ms: Optional[float] = None
    success_rate: Optional[float] = None
    error_rate: Optional[float] = None

# Create and calculate
metric = Metric.create(workflow_id)
metric.success_count = 45
metric.failure_count = 5
metric.total_tasks = 50
metric.calculate_rates()  # Calculates success_rate, error_rate
```

#### Approval
```python
@dataclass
class Approval:
    id: str
    task_id: str
    action: str
    risk_level: RiskLevel           # LOW, MEDIUM, HIGH, CRITICAL
    proposed_by: str
    status: ApprovalStatus          # pending, approved, rejected, auto_approved
    requested_at: datetime
    rationale: Optional[str] = None
    responded_at: Optional[datetime] = None
    response_from: Optional[str] = None
    approval_notes: Optional[str] = None

# Factory and operations
approval = Approval.create(task_id, "send_message", RiskLevel.HIGH)
approval.approve(response_from="user@example.com", notes="Approved")
approval.reject(response_from="user@example.com", notes="Too risky")
```

#### CRMContact
```python
@dataclass
class CRMContact:
    id: str
    email: str
    name: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    status: ContactStatus = ContactStatus.PROSPECT
    source: Optional[str] = None
    score: int = 0              # 0-100
    last_contact: Optional[datetime] = None
    last_contacted_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

# Operations
contact = CRMContact.create(email, name, company)
contact.add_tag("vip")
contact.remove_tag("vip")
contact.update_score(25)  # +25 points
```

#### ContentQueue
```python
@dataclass
class ContentQueue:
    id: str
    type: ContentType               # linkedin_post, twitter, instagram, email, blog, newsletter
    platform: str
    content: str
    scheduled_for: datetime
    status: ContentStatus = ContentStatus.DRAFT
    priority: int = 3
    media_paths: List[str] = field(default_factory=list)
    campaign_id: Optional[str] = None
    target_audience: List[str] = field(default_factory=list)
    created_at: datetime
    published_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_by: str = "system"
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)

# Factory and operations
content = ContentQueue.create(ContentType.LINKEDIN_POST, "linkedin", "Check this out!", scheduled_time)
content.mark_posted()
content.mark_failed("Rate limit exceeded")
```

#### LearningInsight
```python
@dataclass
class LearningInsight:
    id: Optional[int]
    type: InsightType               # pattern, suggestion, optimization, anomaly, trend
    category: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    priority: int = 3
    recommended_action: Optional[str] = None
    generated_at: datetime
    applied: bool = False
    applied_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

# Factory and operations
insight = LearningInsight.create(
    InsightType.PATTERN,
    "LinkedIn engagement by time",
    {"best_hours": [9, 14, 19]}
)
insight.apply({"posts_adjusted": 10})
```

## DatabaseManager API

### Workflow Operations

```python
# Create
workflow = await db_manager.create_workflow(workflow: Workflow) -> Workflow

# Retrieve
workflow = await db_manager.get_workflow(workflow_id: str) -> Optional[Workflow]
workflows = await db_manager.get_enabled_workflows() -> List[Workflow]

# Update
await db_manager.update_workflow(workflow: Workflow) -> None
```

### Task Operations

```python
# Create
task = await db_manager.create_task(task: Task) -> Task

# Retrieve
task = await db_manager.get_task(task_id: str) -> Optional[Task]
tasks = await db_manager.get_pending_tasks(level: Optional[int] = None, limit: int = 100) -> List[Task]
tasks = await db_manager.get_tasks_by_workflow(workflow_id: str) -> List[Task]
tasks = await db_manager.get_running_tasks() -> List[Task]

# Update
await db_manager.update_task_status(task_id: str, status: TaskStatus) -> None
await db_manager.update_task(task: Task) -> None
```

### Execution Log Operations

```python
# Create
log = await db_manager.create_execution_log(log: ExecutionLog) -> ExecutionLog

# Retrieve
logs = await db_manager.get_execution_logs(task_id: str) -> List[ExecutionLog]
```

### Error Log Operations

```python
# Create
error = await db_manager.create_error_log(error: ErrorLog) -> ErrorLog

# Retrieve
errors = await db_manager.get_error_logs(task_id: Optional[str] = None, limit: int = 100) -> List[ErrorLog]
errors = await db_manager.get_critical_errors(hours: int = 24) -> List[ErrorLog]
```

### Metric Operations

```python
# Record
metric = await db_manager.record_metric(metric: Metric) -> Metric

# Retrieve
metrics = await db_manager.get_workflow_metrics(workflow_id: str, hours: int = 24) -> List[Metric]
agg = await db_manager.get_aggregated_metrics(workflow_id: str, hours: int = 24) -> Dict[str, Any]
```

### Approval Operations

```python
# Create
approval = await db_manager.create_approval(approval: Approval) -> Approval

# Retrieve
approvals = await db_manager.get_pending_approvals(risk_level: Optional[RiskLevel] = None) -> List[Approval]

# Update
await db_manager.update_approval(approval: Approval) -> None
```

### CRM Contact Operations

```python
# Create
contact = await db_manager.create_contact(contact: CRMContact) -> CRMContact

# Retrieve
contact = await db_manager.get_contact(contact_id: str) -> Optional[CRMContact]
contact = await db_manager.get_contact_by_email(email: str) -> Optional[CRMContact]
contacts = await db_manager.get_contacts_by_status(status: ContactStatus) -> List[CRMContact]

# Update
await db_manager.update_contact(contact: CRMContact) -> None
```

### Content Operations

```python
# Create
content = await db_manager.create_content(content: ContentQueue) -> ContentQueue

# Retrieve
content = await db_manager.get_scheduled_content(limit: int = 50) -> List[ContentQueue]

# Update
await db_manager.update_content(content: ContentQueue) -> None
```

### Learning Insight Operations

```python
# Create
insight = await db_manager.create_insight(insight: LearningInsight) -> LearningInsight

# Retrieve
insights = await db_manager.get_unapplied_insights(limit: int = 50) -> List[LearningInsight]
```

### Audit Log Operations

```python
# Log
audit = await db_manager.log_audit(audit: AuditLog) -> AuditLog
```

## Query Helpers

The `query_helpers.py` module provides high-level query builders:

```python
from database.query_helpers import QueryBuilder

queries = QueryBuilder(db_manager)

# Task queries
tasks = await queries.tasks.get_overdue_tasks(timeout_minutes=60)
tasks = await queries.tasks.get_high_priority_pending(limit=20)
tasks = await queries.tasks.get_failed_tasks(hours=24)

# Contact queries
contacts = await queries.contacts.get_high_score_contacts(min_score=70)
contacts = await queries.contacts.get_inactive_contacts(days=30)
contacts = await queries.contacts.get_contacts_with_tag("vip")

# Content queries
content = await queries.content.get_ready_to_publish()

# Metrics queries
health = await queries.metrics.get_health_status(workflow_id)
trend = await queries.metrics.get_performance_trend(workflow_id, hours=24)

# Insights queries
insights = await queries.insights.get_actionable_insights(min_confidence=0.7)

# Dashboard
summary = await queries.get_dashboard_summary()
```

## Enums

### TaskStatus
- PENDING: Waiting to be executed
- RUNNING: Currently executing
- COMPLETED: Successfully completed
- FAILED: Execution failed
- ESCALATED: Requires manual intervention
- CANCELLED: Was cancelled before execution

### ExecutionStatus
- PENDING: Step not started
- RUNNING: Step in progress
- SUCCESS: Step completed successfully
- WARNING: Step completed with warnings
- ERROR: Step failed

### ApprovalStatus
- PENDING: Awaiting approval
- APPROVED: Approved
- REJECTED: Rejected
- AUTO_APPROVED: Auto-approved based on criteria

### RiskLevel
- LOW: Low risk operation
- MEDIUM: Medium risk
- HIGH: High risk
- CRITICAL: Critical risk

### Severity
- LOW: Low severity error
- MEDIUM: Medium severity
- HIGH: High severity
- CRITICAL: Critical error

### ErrorType
- TIMEOUT: Operation timeout
- API_ERROR: API call failed
- VALIDATION: Input validation failed
- SYSTEM: System error
- RATE_LIMIT: Rate limited
- AUTHENTICATION: Auth failed
- DATABASE: Database error
- UNKNOWN: Unknown error type

### ContactStatus
- PROSPECT: New prospect
- CONTACTED: Initial contact made
- QUALIFIED: Sales qualified
- WON: Customer won
- LOST: Lead lost
- ARCHIVED: Archived

### ContentType
- LINKEDIN_POST: LinkedIn post
- TWITTER: Twitter post
- INSTAGRAM: Instagram post
- EMAIL: Email content
- BLOG: Blog post
- NEWSLETTER: Newsletter

### ContentStatus
- DRAFT: Draft state
- PENDING: Pending publication
- SCHEDULED: Scheduled for publication
- POSTED: Successfully posted
- FAILED: Publication failed
- CANCELLED: Cancelled

### InsightType
- PATTERN: Identified pattern
- SUGGESTION: Recommendation
- OPTIMIZATION: Optimization opportunity
- ANOMALY: Anomalous behavior
- TREND: Trend detection

## Database Indexes

The schema creates 25+ indexes for performance optimization:

```sql
-- Tasks
idx_tasks_status
idx_tasks_workflow
idx_tasks_created
idx_tasks_assigned
idx_tasks_level
idx_tasks_status_level

-- Execution Logs
idx_execution_logs_task
idx_execution_logs_timestamp
idx_execution_logs_status

-- Error Logs
idx_error_logs_task
idx_error_logs_timestamp
idx_error_logs_severity
idx_error_logs_type

-- CRM
idx_crm_contacts_email
idx_crm_contacts_company
idx_crm_contacts_status
idx_crm_contacts_score

-- Content
idx_content_queue_scheduled
idx_content_queue_status
idx_content_queue_platform
idx_content_queue_created

-- Metrics
idx_metrics_workflow_time
idx_metrics_timestamp

-- And more...
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest tests/test_database.py -v

# Run specific test
pytest tests/test_database.py::test_create_workflow -v

# Run with coverage
pytest tests/test_database.py --cov=database --cov=models

# Run in parallel
pytest tests/test_database.py -n auto
```

### Test Coverage

- 40+ test cases covering all major operations
- Happy path tests
- Error handling tests
- Edge case tests
- Integration tests
- Concurrent operation tests

## Connection Pooling

The database manager includes async connection pooling:

```python
# Configured in DatabaseManager
pool = DatabaseConnectionPool(
    db_path="automation.db",
    pool_size=5,          # Number of connections
    timeout=30            # Connection timeout in seconds
)

# Automatic connection reuse and management
async with pool.get_connection() as conn:
    # Use connection
    pass
```

## Performance Considerations

1. **Connection Pooling**: Reuses connections efficiently
2. **Async Operations**: Non-blocking database access
3. **Indexes**: 25+ indexes for fast queries
4. **JSON Storage**: Flexible data storage in JSON columns
5. **Batch Operations**: Support for concurrent operations

## Security

- **Foreign Key Constraints**: Referential integrity enforced
- **Input Validation**: Enums prevent invalid states
- **Audit Trail**: All operations logged
- **Type Safety**: Dataclass-based models with type hints

## Best Practices

1. Always use factory methods (e.g., `Task.create()`)
2. Check `task.can_retry()` before retrying
3. Use query helpers for complex operations
4. Log all important state changes
5. Monitor error logs regularly
6. Track metrics for workflow optimization
7. Use audit logs for compliance

## Migration from Existing Systems

The schema supports:
- JSON storage for flexible data
- NULL values for optional fields
- Foreign key cascading for data consistency
- Audit trails for audit tracking

## Next Steps

1. Initialize database on application startup
2. Create workflows in application configuration
3. Use ORM models for all database operations
4. Monitor metrics and logs
5. Apply learning insights automatically
