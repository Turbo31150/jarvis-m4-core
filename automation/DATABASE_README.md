# Database Module - README

## Overview

Complete, production-ready database layer for the JARVIS Automation System with:

- **16 core tables** covering workflows, tasks, execution, errors, metrics, CRM, content, insights, and audit
- **Async database manager** with connection pooling
- **12 ORM models** using Python dataclasses
- **Query helpers** for common operations
- **40+ comprehensive tests**
- **Full documentation** with examples

## Quick Start

### 1. Initialize Database

```python
import asyncio
from database import DatabaseInit

async def setup():
    db_init = DatabaseInit("automation.db")
    manager = await db_init.initialize()
    return manager

manager = asyncio.run(setup())
```

### 2. Create Workflows

```python
from models import Workflow

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

await db_manager.create_workflow(workflow)
```

### 3. Create and Track Tasks

```python
from models import Task, TaskStatus

task = Task.create(
    workflow_id=workflow.id,
    level=3,
    priority=4,
    input_params={"search_query": "data scientist"},
    timeout_seconds=3600
)

created_task = await db_manager.create_task(task)

# Get pending tasks
pending = await db_manager.get_pending_tasks(level=3, limit=10)

# Update status
await db_manager.update_task_status(task.id, TaskStatus.RUNNING)

# Log execution
log = ExecutionLog.create(task.id, "main_step")
log.complete(ExecutionStatus.SUCCESS, output={"result": "ok"})
await db_manager.create_execution_log(log)
```

### 4. Track Errors and Metrics

```python
from models import ErrorLog, ErrorType, Severity, Metric

# Log errors
error = ErrorLog.create(
    message="API timeout",
    error_type=ErrorType.TIMEOUT,
    severity=Severity.HIGH,
    task_id=task.id
)
await db_manager.create_error_log(error)

# Record metrics
metric = Metric.create(workflow.id)
metric.success_count = 45
metric.failure_count = 5
metric.total_tasks = 50
metric.avg_duration_ms = 1250.5
metric.p95_duration_ms = 3500.0
metric.calculate_rates()
await db_manager.record_metric(metric)
```

### 5. Manage Approvals

```python
from models import Approval, RiskLevel

# Create approval request
approval = Approval.create(
    task_id=task.id,
    action="send_message",
    risk_level=RiskLevel.HIGH,
    rationale="User mention detected"
)
await db_manager.create_approval(approval)

# Get pending approvals
pending_approvals = await db_manager.get_pending_approvals()

# Approve or reject
approval.approve(response_from="user@example.com", notes="Looks good")
await db_manager.update_approval(approval)
```

### 6. Manage CRM Contacts

```python
from models import CRMContact, ContactStatus

# Create contact
contact = CRMContact.create(
    email="prospect@example.com",
    name="John Doe",
    company="Tech Corp"
)
await db_manager.create_contact(contact)

# Update contact
contact.add_tag("vip")
contact.update_score(25)
contact.status = ContactStatus.QUALIFIED
await db_manager.update_contact(contact)

# Query contacts
high_score = await db_manager.get_contacts_by_status(ContactStatus.PROSPECT)
by_email = await db_manager.get_contact_by_email("prospect@example.com")
```

### 7. Manage Content

```python
from models import ContentQueue, ContentType, ContentStatus
from datetime import datetime, timedelta

# Create content
scheduled_time = datetime.utcnow() + timedelta(hours=2)
content = ContentQueue.create(
    content_type=ContentType.LINKEDIN_POST,
    platform="linkedin",
    content="Check this out! #AI #Automation",
    scheduled_for=scheduled_time,
    priority=4
)
await db_manager.create_content(content)

# Get scheduled content
ready = await db_manager.get_scheduled_content()

# Mark as posted
content.mark_posted()
await db_manager.update_content(content)
```

### 8. Track Learning Insights

```python
from models import LearningInsight, InsightType

# Create insight
insight = LearningInsight.create(
    insight_type=InsightType.PATTERN,
    title="LinkedIn engagement pattern",
    data={"best_hours": [9, 14, 19], "best_day": "Tuesday"},
    confidence=0.87
)
await db_manager.create_insight(insight)

# Get unapplied insights
insights = await db_manager.get_unapplied_insights()

# Apply insight
insight.apply(result={"posts_adjusted": 10})
```

### 9. Query Helper Functions

```python
from database.query_helpers import QueryBuilder

queries = QueryBuilder(db_manager)

# Task queries
overdue = await queries.tasks.get_overdue_tasks(timeout_minutes=60)
high_priority = await queries.tasks.get_high_priority_pending(limit=20)
failed = await queries.tasks.get_failed_tasks(hours=24)

# Contact queries
vip_contacts = await queries.contacts.get_high_score_contacts(min_score=70)
inactive = await queries.contacts.get_inactive_contacts(days=30)
tagged = await queries.contacts.get_contacts_with_tag("vip")

# Metrics queries
health = await queries.metrics.get_health_status(workflow.id)
trend = await queries.metrics.get_performance_trend(workflow.id, hours=24)

# Insights queries
actionable = await queries.insights.get_actionable_insights(min_confidence=0.7)

# Dashboard summary
summary = await queries.get_dashboard_summary()
```

### 10. Audit Logging

```python
from models import AuditLog

# Log an action
audit = AuditLog.create(
    actor="user123",
    action="create",
    resource_type="workflow",
    resource_id=workflow.id,
    changes={"name": {"old": None, "new": "linkedin_outreach"}}
)
await db_manager.log_audit(audit)
```

## File Structure

```
automation/
├── database/
│   ├── __init__.py              # Database initialization utilities
│   ├── schema.sql               # SQL schema (16 tables + 25+ indexes)
│   ├── db_manager.py            # Main DatabaseManager class (1200+ lines)
│   └── query_helpers.py         # Query builders and helpers
├── models/
│   ├── __init__.py              # Model exports
│   └── models.py                # 12 ORM models + 10 enums (900 lines)
└── tests/
    ├── __init__.py
    └── test_database.py         # 40+ comprehensive tests
```

## Models Overview

### Core Workflow Models
- **Workflow**: Automation workflow definitions
- **Task**: Individual task executions
- **ExecutionLog**: Step-by-step execution tracking

### Monitoring Models
- **ErrorLog**: Error tracking with recovery strategies
- **Metric**: Performance and health metrics
- **PerformanceTrend**: Historical trend data

### Approval Models
- **Approval**: Risk-based approval requests

### CRM Models
- **CRMContact**: Contact/prospect database
- **ContactHistory**: Interaction timeline

### Content Models
- **ContentQueue**: Content scheduling and publishing
- **ContentAnalytics**: Engagement metrics

### Learning Models
- **LearningInsight**: AI-generated patterns and suggestions

### Audit Models
- **AuditLog**: Complete audit trail

## Enums

### Status Enums
- TaskStatus: PENDING, RUNNING, COMPLETED, FAILED, ESCALATED, CANCELLED
- ExecutionStatus: PENDING, RUNNING, SUCCESS, WARNING, ERROR
- ApprovalStatus: PENDING, APPROVED, REJECTED, AUTO_APPROVED
- ContactStatus: PROSPECT, CONTACTED, QUALIFIED, WON, LOST, ARCHIVED
- ContentStatus: DRAFT, PENDING, SCHEDULED, POSTED, FAILED, CANCELLED

### Type Enums
- ErrorType: TIMEOUT, API_ERROR, VALIDATION, SYSTEM, RATE_LIMIT, AUTHENTICATION, DATABASE, UNKNOWN
- ContentType: LINKEDIN_POST, TWITTER, INSTAGRAM, EMAIL, BLOG, NEWSLETTER
- InsightType: PATTERN, SUGGESTION, OPTIMIZATION, ANOMALY, TREND

### Level Enums
- RiskLevel: LOW, MEDIUM, HIGH, CRITICAL
- Severity: LOW, MEDIUM, HIGH, CRITICAL

## Database Tables

1. **workflows** - Automation workflow definitions
2. **tasks** - Task executions and state
3. **execution_logs** - Step-by-step execution records
4. **error_logs** - Error tracking and recovery
5. **metrics** - Performance metrics
6. **performance_trends** - Historical trends
7. **approvals** - Approval requests
8. **crm_contacts** - Contact database
9. **contact_history** - Interaction timeline
10. **content_queue** - Content for publishing
11. **content_analytics** - Engagement metrics
12. **learning_insights** - AI insights and patterns
13. **audit_trail** - Complete audit log

Plus structural support tables and 25+ performance indexes.

## Connection Pooling

- Async connection pool with configurable size
- Default: 5 connections
- Automatic connection reuse
- Thread-safe operations

## Performance Optimizations

- 25+ database indexes
- JSON for flexible data storage
- Connection pooling
- Async/await for non-blocking I/O
- Batch operations support

## Testing

### Run Tests
```bash
cd automation
pytest tests/test_database.py -v
```

### Validate Database
```bash
python3 validate_database.py
```

### Test Coverage
- 40+ test cases
- Happy path testing
- Error handling
- Edge cases
- Concurrent operations
- Integration tests

## API Reference

See [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md) for complete API reference with all methods, parameters, and return types.

## Configuration

### Connection Pool Size
```python
manager = DatabaseManager(db_path="automation.db", pool_size=5)
```

### Database Path
```python
manager = DatabaseManager(db_path="./data/automation.db")
```

### Initialization
```python
await manager.initialize()
```

### Cleanup
```python
await manager.close()
```

## Best Practices

1. **Always use factory methods** for creating models
   ```python
   task = Task.create(...)  # Good
   # task = Task(...)       # Avoid
   ```

2. **Check retry eligibility** before retrying
   ```python
   if task.can_retry():
       # Retry logic
   ```

3. **Log all important operations**
   ```python
   await db_manager.log_audit(audit)
   ```

4. **Monitor error logs**
   ```python
   errors = await db_manager.get_critical_errors()
   ```

5. **Use query helpers** for complex queries
   ```python
   queries = QueryBuilder(db_manager)
   ```

## Error Handling

All database operations handle:
- Connection errors
- Data validation errors
- Concurrency issues
- Timeout errors
- Foreign key violations

## Security

- Foreign key constraints for referential integrity
- Enum-based state management prevents invalid states
- Complete audit trail for compliance
- Input validation through dataclass models

## Future Enhancements

- [ ] Database migrations (Alembic)
- [ ] Query caching layer
- [ ] Replication support
- [ ] Backup/restore utilities
- [ ] Query performance profiling
- [ ] Advanced analytics queries

## Support

For documentation, see:
- [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md) - Complete reference
- [models/models.py](models/models.py) - Model definitions
- [database/db_manager.py](database/db_manager.py) - Manager implementation
- [tests/test_database.py](tests/test_database.py) - Usage examples
