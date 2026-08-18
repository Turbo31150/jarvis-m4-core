#!/usr/bin/env python3
"""
Database setup and validation script for testing
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from models.models import Workflow, Task, TaskStatus


async def main():
    """Test database setup"""
    print("=" * 70)
    print("DATABASE INITIALIZATION & VALIDATION")
    print("=" * 70)

    # Create temporary database
    db_path = "test_automation.db"
    print(f"\n[1/5] Creating database at: {db_path}")
    
    manager = DatabaseManager(db_path=db_path, pool_size=3)
    
    print("[2/5] Initializing database...")
    await manager.initialize()
    print("✓ Database initialized successfully")

    # Test workflow creation
    print("\n[3/5] Testing workflow creation...")
    workflow = Workflow.create(
        name="test_workflow_validation",
        level=2,
        definition={"steps": [{"name": "test", "action": "test"}]},
        description="Test workflow for validation"
    )
    
    created_wf = await manager.create_workflow(workflow)
    print(f"✓ Created workflow: {created_wf.id}")

    # Test task creation
    print("\n[4/5] Testing task creation...")
    task = Task.create(
        workflow_id=workflow.id,
        level=2,
        priority=3,
        input_params={"test": "data"}
    )
    
    created_task = await manager.create_task(task)
    print(f"✓ Created task: {created_task.id}")
    print(f"  Status: {created_task.status}")
    print(f"  Priority: {created_task.priority}")

    # Retrieve and verify
    print("\n[5/5] Verifying data retrieval...")
    retrieved_wf = await manager.get_workflow(workflow.id)
    retrieved_task = await manager.get_task(task.id)
    
    print(f"✓ Retrieved workflow: {retrieved_wf.name}")
    print(f"✓ Retrieved task: {retrieved_task.id}")

    # Get pending tasks
    pending = await manager.get_pending_tasks()
    print(f"✓ Pending tasks: {len(pending)}")

    # Close
    await manager.close()
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)

    print("\n" + "=" * 70)
    print("✓ ALL VALIDATIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
