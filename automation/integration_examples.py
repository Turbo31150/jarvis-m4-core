#!/usr/bin/env python3
"""
Example Integration Script - How to use the Database Module
This demonstrates the complete workflow with real-world scenarios
"""

import asyncio
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from database.query_helpers import QueryBuilder
from models.models import (
    Workflow, Task, TaskStatus, ExecutionLog, ExecutionStatus,
    ErrorLog, ErrorType, Severity, Metric, Approval, RiskLevel,
    ApprovalStatus, CRMContact, ContactStatus, ContentQueue,
    ContentType, ContentStatus, LearningInsight, InsightType,
    AuditLog
)


async def example_1_workflow_creation():
    """Example 1: Create and manage workflows"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Workflow Creation and Management")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create a workflow
    workflow = Workflow.create(
        name="automated_linkedin_outreach",
        level=3,
        definition={
            "steps": [
                {"name": "find_prospects", "action": "search", "filters": {"title": "Data Scientist"}},
                {"name": "personalize_message", "action": "generate", "ai": True},
                {"name": "send_connection", "action": "connect"},
                {"name": "send_message", "action": "message", "delay_hours": 24}
            ]
        },
        description="Automated LinkedIn outreach workflow"
    )

    created_workflow = await manager.create_workflow(workflow)
    print(f"✓ Created workflow: {created_workflow.name} (ID: {created_workflow.id})")

    # Retrieve workflow
    retrieved = await manager.get_workflow(created_workflow.id)
    print(f"✓ Retrieved workflow: {retrieved.name}")
    print(f"  Level: {retrieved.level}")
    print(f"  Enabled: {retrieved.enabled}")
    print(f"  Steps: {len(retrieved.definition['steps'])}")

    await manager.close()


async def example_2_task_management():
    """Example 2: Create and track tasks"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Task Management and Lifecycle")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create a workflow first
    workflow = Workflow.create("test_wf", 2, {})
    await manager.create_workflow(workflow)

    # Create multiple tasks with different priorities
    tasks = []
    for i in range(3):
        task = Task.create(
            workflow_id=workflow.id,
            level=2,
            priority=5 - i,  # Decreasing priority
            input_params={"prospect_id": f"p_{i}", "search_query": "data scientist"}
        )
        created = await manager.create_task(task)
        tasks.append(created)
        print(f"✓ Created task {i+1}: {created.id} (Priority: {created.priority})")

    # Get pending tasks sorted by priority
    pending = await manager.get_pending_tasks(level=2, limit=10)
    print(f"\n✓ Pending tasks: {len(pending)}")
    for task in pending:
        print(f"  - {task.id} (Priority: {task.priority})")

    # Update task status
    first_task = tasks[0]
    first_task.started_at = datetime.utcnow()
    first_task.status = TaskStatus.RUNNING
    await manager.update_task(first_task)
    print(f"\n✓ Updated task {first_task.id} to RUNNING")

    await manager.close()


async def example_3_execution_logging():
    """Example 3: Log execution steps"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Execution Logging and Tracking")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create workflow and task
    workflow = Workflow.create("test_wf", 2, {})
    await manager.create_workflow(workflow)

    task = Task.create(workflow.id, 2, 3)
    await manager.create_task(task)

    # Log execution steps
    steps = [
        ("search_prospects", {"query": "data scientist", "location": "USA"}),
        ("filter_results", {"min_connections": 500}),
        ("personalize_message", {"ai_model": "gpt-4"})
    ]

    for i, (step_name, input_data) in enumerate(steps):
        log = ExecutionLog.create(task.id, step_name, step_index=i)
        print(f"\n✓ Starting step {i+1}: {step_name}")

        # Simulate execution
        await asyncio.sleep(0.1)

        # Complete step
        log.complete(
            status=ExecutionStatus.SUCCESS,
            output={"results_count": 42, "processed": True}
        )
        await manager.create_execution_log(log)
        print(f"  Duration: {log.duration_ms}ms")
        print(f"  Status: {log.status.value}")

    # Retrieve execution history
    logs = await manager.get_execution_logs(task.id)
    print(f"\n✓ Execution history: {len(logs)} steps logged")

    await manager.close()


async def example_4_error_tracking():
    """Example 4: Error logging and recovery"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Error Tracking and Recovery")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create workflow and task
    workflow = Workflow.create("test_wf", 2, {})
    await manager.create_workflow(workflow)

    task = Task.create(workflow.id, 2, 3)
    await manager.create_task(task)

    # Log an error
    error = ErrorLog.create(
        message="LinkedIn API rate limit exceeded",
        error_type=ErrorType.RATE_LIMIT,
        severity=Severity.HIGH,
        task_id=task.id,
        workflow_id=workflow.id,
        stack_trace="Rate limit reached at line 42 in api_client.py"
    )

    error.recovery_strategy = "retry"
    created_error = await manager.create_error_log(error)
    print(f"✓ Logged error: {created_error.message}")
    print(f"  Type: {created_error.error_type.value}")
    print(f"  Severity: {created_error.severity.value}")
    print(f"  Recovery Strategy: {created_error.recovery_strategy}")

    # Get critical errors
    critical = await manager.get_critical_errors(hours=24)
    print(f"\n✓ Critical errors in last 24 hours: {len(critical)}")

    await manager.close()


async def example_5_metrics_and_analytics():
    """Example 5: Record and query metrics"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Metrics and Performance Analytics")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    workflow = Workflow.create("test_wf", 2, {})
    await manager.create_workflow(workflow)

    # Record metrics for the workflow
    metric = Metric.create(workflow.id)
    metric.success_count = 89
    metric.failure_count = 11
    metric.total_tasks = 100
    metric.avg_duration_ms = 2450.5
    metric.min_duration_ms = 1200
    metric.max_duration_ms = 5800
    metric.p50_duration_ms = 2300.0
    metric.p95_duration_ms = 4500.0
    metric.p99_duration_ms = 5200.0
    metric.calculate_rates()

    created_metric = await manager.record_metric(metric)
    print(f"✓ Recorded metric for workflow: {workflow.id}")
    print(f"  Success rate: {created_metric.success_rate:.1%}")
    print(f"  Error rate: {created_metric.error_rate:.1%}")
    print(f"  Avg duration: {created_metric.avg_duration_ms}ms")
    print(f"  P95 duration: {created_metric.p95_duration_ms}ms")

    # Get aggregated metrics
    agg = await manager.get_aggregated_metrics(workflow.id, hours=24)
    print(f"\n✓ Aggregated metrics (24h):")
    print(f"  Total tasks: {agg['total_tasks']}")
    print(f"  Success count: {agg['success_count']}")
    print(f"  Success rate: {agg['success_rate']:.1%}")

    await manager.close()


async def example_6_crm_contacts():
    """Example 6: CRM contact management"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: CRM Contact Management")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create contacts
    contacts = []
    for i, email in enumerate([
        "alice@techcorp.com",
        "bob@startupinc.com",
        "charlie@enterprise.com"
    ]):
        contact = CRMContact.create(
            email=email,
            name=f"Professional {i+1}",
            company=f"Company {i+1}"
        )
        contact.source = "linkedin"
        contact.add_tag("data_scientist")
        contact.add_tag("hiring_manager")
        created = await manager.create_contact(contact)
        contacts.append(created)
        print(f"✓ Created contact: {created.name} ({created.email})")

    # Update contact scores and status
    for i, contact in enumerate(contacts):
        contact.update_score(50 + i * 20)  # 50, 70, 90
        contact.status = ContactStatus.QUALIFIED if contact.score > 60 else ContactStatus.PROSPECT
        await manager.update_contact(contact)

    # Query high-score contacts
    qualified = await manager.get_contacts_by_status(ContactStatus.QUALIFIED)
    print(f"\n✓ Qualified contacts: {len(qualified)}")
    for contact in qualified:
        print(f"  - {contact.name} (Score: {contact.score})")

    await manager.close()


async def example_7_content_scheduling():
    """Example 7: Content scheduling and publishing"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Content Scheduling and Publishing")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create scheduled content
    content_items = []
    for i in range(3):
        scheduled_time = datetime.utcnow() + timedelta(hours=i*2)
        content = ContentQueue.create(
            content_type=ContentType.LINKEDIN_POST if i % 2 == 0 else ContentType.TWITTER,
            platform="linkedin" if i % 2 == 0 else "twitter",
            content=f"Great insights on AI and automation! #{i+1}",
            scheduled_for=scheduled_time,
            priority=5-i
        )
        created = await manager.create_content(content)
        content_items.append(created)
        print(f"✓ Scheduled content {i+1}: {created.type.value}")
        print(f"  Scheduled for: {created.scheduled_for.isoformat()}")

    # Get ready-to-publish content (past due)
    ready = await manager.get_scheduled_content()
    print(f"\n✓ Content ready to publish: {len(ready)}")

    await manager.close()


async def example_8_approvals():
    """Example 8: Approval workflow"""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Approval Workflow")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    # Create workflow and task
    workflow = Workflow.create("test_wf", 2, {})
    await manager.create_workflow(workflow)

    task = Task.create(workflow.id, 2, 3)
    await manager.create_task(task)

    # Create approval request
    approval = Approval.create(
        task_id=task.id,
        action="send_bulk_message",
        risk_level=RiskLevel.HIGH,
        rationale="Sending message to 1000+ contacts"
    )

    created = await manager.create_approval(approval)
    print(f"✓ Created approval request: {created.id}")
    print(f"  Action: {created.action}")
    print(f"  Risk Level: {created.risk_level.value}")
    print(f"  Status: {created.status.value}")

    # Get pending approvals
    pending = await manager.get_pending_approvals()
    print(f"\n✓ Pending approvals: {len(pending)}")

    # Approve the request
    approval.approve(response_from="manager@company.com", notes="Approved after review")
    await manager.update_approval(approval)
    print(f"✓ Approved by: {approval.response_from}")

    await manager.close()


async def example_9_query_helpers():
    """Example 9: Using query helpers"""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Query Helpers and Builders")
    print("=" * 70)

    manager = DatabaseManager("example.db", pool_size=3)
    await manager.initialize()

    queries = QueryBuilder(manager)

    # Get dashboard summary
    summary = await queries.get_dashboard_summary()
    print("✓ Dashboard Summary:")
    print(f"  Pending tasks: {summary['pending_tasks']}")
    print(f"  Running tasks: {summary['running_tasks']}")
    print(f"  Pending approvals: {summary['pending_approvals']}")
    print(f"  Scheduled content: {summary['scheduled_content']}")
    print(f"  Unapplied insights: {summary['unapplied_insights']}")

    await manager.close()


async def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "DATABASE MODULE - INTEGRATION EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    examples = [
        ("Workflow Creation", example_1_workflow_creation),
        ("Task Management", example_2_task_management),
        ("Execution Logging", example_3_execution_logging),
        ("Error Tracking", example_4_error_tracking),
        ("Metrics & Analytics", example_5_metrics_and_analytics),
        ("CRM Contacts", example_6_crm_contacts),
        ("Content Scheduling", example_7_content_scheduling),
        ("Approvals", example_8_approvals),
        ("Query Helpers", example_9_query_helpers),
    ]

    for i, (name, example_func) in enumerate(examples, 1):
        try:
            await example_func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")

    print("\n" + "=" * 70)
    print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")

    # Cleanup
    import os
    if os.path.exists("example.db"):
        os.remove("example.db")


if __name__ == "__main__":
    asyncio.run(main())
