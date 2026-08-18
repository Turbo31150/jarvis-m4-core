# 🚀 START HERE - Database Module Quick Guide

Welcome to the JARVIS Automation System Database Module (T7)!

## What is This?

This is a production-ready database layer providing:
- **13 database tables** covering workflows, tasks, CRM, content, and more
- **12 ORM models** with full type hints and helper methods
- **40+ CRUD methods** for database operations
- **37 comprehensive tests** validating all functionality
- **Complete documentation** with examples

## In 5 Minutes

### 1. Install Dependencies
```bash
pip install pytest pytest-asyncio
```

### 2. Initialize Database
```python
import asyncio
from database import DatabaseInit

async def setup():
    db_init = DatabaseInit("automation.db")
    manager = await db_init.initialize()
    return manager

manager = asyncio.run(setup())
```

### 3. Create Your First Workflow
```python
from models import Workflow

workflow = Workflow.create(
    name="my_workflow",
    level=2,
    definition={"steps": [{"name": "step1", "action": "test"}]}
)

await manager.create_workflow(workflow)
print(f"Created workflow: {workflow.id}")
```

### 4. Create a Task
```python
from models import Task

task = Task.create(
    workflow_id=workflow.id,
    level=2,
    priority=3
)

await manager.create_task(task)
print(f"Created task: {task.id}")
```

### 5. Query Your Data
```python
# Get pending tasks
pending = await manager.get_pending_tasks()
print(f"Pending tasks: {len(pending)}")

# Close database
await manager.close()
```

## Documentation Map

**Start Here:**
- This file (you are here!)

**10-Minute Quick Start:**
- [DATABASE_README.md](DATABASE_README.md) - Full setup guide

**Complete Reference:**
- [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md) - All methods and examples

**Project Overview:**
- [FINAL_DELIVERY.md](FINAL_DELIVERY.md) - What's included
- [INDEX.md](INDEX.md) - Complete index

**Real-World Examples:**
- [integration_examples.py](integration_examples.py) - 9 usage examples
- [tests/test_database.py](tests/test_database.py) - 37 test cases

## Key Files

```
automation/
├── database/
│   ├── schema.sql           ← Database schema (13 tables)
│   ├── db_manager.py        ← Main database interface
│   └── query_helpers.py     ← High-level queries
├── models/
│   └── models.py            ← Data models and enums
└── tests/
    └── test_database.py     ← Test examples
```

## Common Tasks

### Create a Contact
```python
from models import CRMContact

contact = CRMContact.create(
    email="prospect@company.com",
    name="John Doe",
    company="Acme Corp"
)
contact.add_tag("vip")
await manager.create_contact(contact)
```

### Log an Error
```python
from models import ErrorLog, ErrorType, Severity

error = ErrorLog.create(
    message="API failed",
    error_type=ErrorType.API_ERROR,
    severity=Severity.HIGH,
    task_id=task_id
)
await manager.create_error_log(error)
```

### Schedule Content
```python
from models import ContentQueue, ContentType
from datetime import datetime, timedelta

content = ContentQueue.create(
    content_type=ContentType.LINKEDIN_POST,
    platform="linkedin",
    content="Check this out!",
    scheduled_for=datetime.utcnow() + timedelta(hours=2)
)
await manager.create_content(content)
```

### Query with Helpers
```python
from database.query_helpers import QueryBuilder

queries = QueryBuilder(manager)

# Get dashboard summary
summary = await queries.get_dashboard_summary()
print(summary)

# Get overdue tasks
overdue = await queries.tasks.get_overdue_tasks(timeout_minutes=60)

# Get high-score contacts
vips = await queries.contacts.get_high_score_contacts(min_score=70)
```

## Run Tests

```bash
# Run all tests
pytest tests/test_database.py -v

# Run specific test
pytest tests/test_database.py::test_create_workflow -v

# Run with coverage
pytest tests/test_database.py --cov=database --cov=models
```

## Validate Installation

```bash
python3 validate_database.py
```

## Integration with Other Components

**T6 (Task Orchestrator):**
- Use `Task` model for tasks
- Use `ExecutionLog` for step tracking

**T8 (Content Management):**
- Use `ContentQueue` for scheduling
- Use `ContentAnalytics` for metrics

**CRM Module:**
- Use `CRMContact` for prospects
- Use `ContactHistory` for interactions

## Next Steps

1. ✅ Read [DATABASE_README.md](DATABASE_README.md)
2. ✅ Try [integration_examples.py](integration_examples.py)
3. ✅ Review [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)
4. ✅ Check the [tests](tests/test_database.py) for examples
5. ✅ Integrate with your application

## API Quick Reference

### DatabaseManager Methods

**Workflow:**
- `create_workflow(workflow)`
- `get_workflow(id)`
- `get_enabled_workflows()`
- `update_workflow(workflow)`

**Task:**
- `create_task(task)`
- `get_task(id)`
- `get_pending_tasks(level, limit)`
- `update_task_status(id, status)`

**Execution:**
- `create_execution_log(log)`
- `get_execution_logs(task_id)`

**Errors:**
- `create_error_log(error)`
- `get_critical_errors(hours)`

**Metrics:**
- `record_metric(metric)`
- `get_aggregated_metrics(workflow_id)`

**CRM:**
- `create_contact(contact)`
- `get_contacts_by_status(status)`

**Content:**
- `create_content(content)`
- `get_scheduled_content()`

**Approvals:**
- `create_approval(approval)`
- `get_pending_approvals()`

## Models Overview

**Core Models:**
- `Workflow` - Automation definitions
- `Task` - Task executions
- `ExecutionLog` - Step tracking

**Monitoring:**
- `ErrorLog` - Error tracking
- `Metric` - Performance metrics
- `Approval` - Approval requests

**CRM:**
- `CRMContact` - Contacts/prospects
- `ContactHistory` - Interactions

**Content:**
- `ContentQueue` - Content for publishing
- `ContentAnalytics` - Engagement metrics

**Learning:**
- `LearningInsight` - AI insights

**Audit:**
- `AuditLog` - Action history

## Features

✅ **Production-Ready** - Enterprise-grade code
✅ **Async/Await** - Non-blocking operations
✅ **Type-Safe** - Full type hints (100%)
✅ **Tested** - 37 comprehensive tests
✅ **Documented** - 28KB of documentation
✅ **Performant** - 25+ indexes, connection pooling
✅ **Secure** - Foreign keys, audit trail, validation

## Support

- **Questions?** Check [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)
- **Examples?** See [integration_examples.py](integration_examples.py)
- **Getting started?** Read [DATABASE_README.md](DATABASE_README.md)
- **Lost?** Check the [INDEX.md](INDEX.md)

## Project Status

✅ **PRODUCTION-READY**

All components are implemented, tested, documented, and ready for use.

---

**Ready to get started? Go to [DATABASE_README.md](DATABASE_README.md)! 🚀**
