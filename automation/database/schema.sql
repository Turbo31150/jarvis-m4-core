-- ============================================================================
-- JARVIS Automation System - Database Schema
-- Production-Ready SQLite Schema with Full Audit & Monitoring
-- ============================================================================

-- ============================================================================
-- CORE WORKFLOW TABLES
-- ============================================================================

-- Workflows: Master definitions for automation sequences
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
    definition JSON NOT NULL,  -- Full YAML definition in JSON format
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system'
);

-- Tasks: Individual task executions within workflows
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed', 'escalated', 'cancelled')),
    priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5) DEFAULT 3,
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    input_params JSON,
    output_data JSON,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    assigned_to TEXT,
    timeout_seconds INTEGER DEFAULT 3600,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- ============================================================================
-- EXECUTION & MONITORING TABLES
-- ============================================================================

-- Execution Logs: Detailed step-by-step execution records
CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'warning', 'error')),
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_ms INTEGER,
    output JSON,
    error TEXT,
    error_code TEXT,
    retry_attempt INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Error Logs: Centralized error tracking and recovery
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    workflow_id TEXT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_type TEXT NOT NULL,  -- 'timeout', 'api_error', 'validation', 'system', etc.
    severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    message TEXT NOT NULL,
    stack_trace TEXT,
    recovery_strategy TEXT,  -- 'retry', 'escalate', 'skip', 'manual'
    recovery_success BOOLEAN,
    recovery_timestamp DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE SET NULL
);

-- Metrics: Performance and health metrics
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    period_minutes INTEGER DEFAULT 60,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    total_tasks INTEGER NOT NULL DEFAULT 0,
    avg_duration_ms FLOAT,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    p50_duration_ms FLOAT,
    p95_duration_ms FLOAT,
    p99_duration_ms FLOAT,
    success_rate FLOAT,
    error_rate FLOAT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- ============================================================================
-- APPROVAL & RISK MANAGEMENT TABLES
-- ============================================================================

-- Approvals: Risk-based approval workflow
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- e.g., 'execute_action', 'send_message', 'make_post'
    risk_level TEXT NOT NULL CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    proposed_by TEXT NOT NULL DEFAULT 'ai_orchestrator',
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'auto_approved')),
    rationale TEXT,
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    response_from TEXT,
    approval_notes TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ============================================================================
-- CRM & CONTACT MANAGEMENT TABLES
-- ============================================================================

-- CRM Contacts: Prospect and customer database
CREATE TABLE IF NOT EXISTS crm_contacts (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    company TEXT,
    job_title TEXT,
    phone TEXT,
    status TEXT NOT NULL CHECK(status IN ('prospect', 'contacted', 'qualified', 'won', 'lost', 'archived')),
    source TEXT,  -- 'linkedin', 'email', 'manual', 'api', etc.
    score INTEGER DEFAULT 0 CHECK(score BETWEEN 0 AND 100),
    last_contact DATETIME,
    last_contacted_by TEXT,
    tags JSON,  -- Array of string tags
    metadata JSON,  -- Custom metadata
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system'
);

-- Contact History: Interaction timeline
CREATE TABLE IF NOT EXISTS contact_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,  -- 'message', 'email', 'call', 'meeting', 'post_like', etc.
    platform TEXT,  -- 'linkedin', 'email', 'twitter', etc.
    message TEXT,
    success BOOLEAN,
    metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES crm_contacts(id) ON DELETE CASCADE
);

-- ============================================================================
-- CONTENT MANAGEMENT TABLES
-- ============================================================================

-- Content Queue: Scheduled content for publishing
CREATE TABLE IF NOT EXISTS content_queue (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('linkedin_post', 'twitter', 'instagram', 'email', 'blog', 'newsletter')),
    platform TEXT NOT NULL,
    content TEXT NOT NULL,
    media_paths JSON,  -- Array of file paths or URLs
    scheduled_for DATETIME NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('draft', 'pending', 'scheduled', 'posted', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 3,
    campaign_id TEXT,
    target_audience JSON,  -- Tags or segments
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    failed_at DATETIME,
    failure_reason TEXT,
    created_by TEXT DEFAULT 'system',
    engagement_metrics JSON  -- Likes, shares, comments, etc.
);

-- Content Analytics: Track performance metrics
CREATE TABLE IF NOT EXISTS content_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    platform TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    sentiment_score FLOAT,
    FOREIGN KEY (content_id) REFERENCES content_queue(id) ON DELETE CASCADE
);

-- ============================================================================
-- AI LEARNING & INSIGHTS TABLES
-- ============================================================================

-- Learning Insights: AI-generated patterns and recommendations
CREATE TABLE IF NOT EXISTS learning_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('pattern', 'suggestion', 'optimization', 'anomaly', 'trend')),
    category TEXT,  -- 'performance', 'engagement', 'efficiency', etc.
    title TEXT NOT NULL,
    description TEXT,
    data JSON NOT NULL,
    confidence FLOAT CHECK(confidence BETWEEN 0.0 AND 1.0),
    priority INTEGER DEFAULT 3,
    recommended_action TEXT,
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied BOOLEAN DEFAULT 0,
    applied_at DATETIME,
    result JSON,
    created_by TEXT DEFAULT 'ai_engine'
);

-- Performance Trends: Aggregated trend data
CREATE TABLE IF NOT EXISTS performance_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT,
    metric_name TEXT NOT NULL,  -- 'success_rate', 'avg_duration', 'error_count', etc.
    timestamp DATETIME NOT NULL,
    value FLOAT NOT NULL,
    trend_direction TEXT,  -- 'up', 'down', 'stable'
    forecast_value FLOAT,
    confidence FLOAT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE SET NULL
);

-- ============================================================================
-- AUDIT & COMPLIANCE TABLES
-- ============================================================================

-- Audit Trail: Complete audit log for compliance
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor TEXT NOT NULL,  -- 'system', 'user', 'ai', 'scheduled'
    action TEXT NOT NULL,  -- 'create', 'update', 'delete', 'approve', 'execute'
    resource_type TEXT NOT NULL,  -- 'workflow', 'task', 'contact', 'content'
    resource_id TEXT NOT NULL,
    changes JSON,  -- Before/after values
    metadata JSON,
    ip_address TEXT,
    user_agent TEXT
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_level ON tasks(level);
CREATE INDEX IF NOT EXISTS idx_tasks_status_level ON tasks(status, level);

-- Execution Logs indexes
CREATE INDEX IF NOT EXISTS idx_execution_logs_task ON execution_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_logs_status ON execution_logs(status);

-- Error Logs indexes
CREATE INDEX IF NOT EXISTS idx_error_logs_task ON error_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type);

-- CRM indexes
CREATE INDEX IF NOT EXISTS idx_crm_contacts_email ON crm_contacts(email);
CREATE INDEX IF NOT EXISTS idx_crm_contacts_company ON crm_contacts(company);
CREATE INDEX IF NOT EXISTS idx_crm_contacts_status ON crm_contacts(status);
CREATE INDEX IF NOT EXISTS idx_crm_contacts_score ON crm_contacts(score DESC);

-- Content Queue indexes
CREATE INDEX IF NOT EXISTS idx_content_queue_scheduled ON content_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_content_queue_status ON content_queue(status);
CREATE INDEX IF NOT EXISTS idx_content_queue_platform ON content_queue(platform);
CREATE INDEX IF NOT EXISTS idx_content_queue_created ON content_queue(created_at DESC);

-- Metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_workflow_time ON metrics(workflow_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);

-- Approvals indexes
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_task ON approvals(task_id);
CREATE INDEX IF NOT EXISTS idx_approvals_risk_level ON approvals(risk_level);

-- Learning insights indexes
CREATE INDEX IF NOT EXISTS idx_learning_insights_type ON learning_insights(type);
CREATE INDEX IF NOT EXISTS idx_learning_insights_applied ON learning_insights(applied);
CREATE INDEX IF NOT EXISTS idx_learning_insights_generated ON learning_insights(generated_at DESC);

-- Audit Trail indexes
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_actor ON audit_trail(actor);
CREATE INDEX IF NOT EXISTS idx_audit_trail_resource ON audit_trail(resource_type, resource_id);

-- Contact History indexes
CREATE INDEX IF NOT EXISTS idx_contact_history_contact ON contact_history(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_history_timestamp ON contact_history(created_at DESC);

-- Content Analytics indexes
CREATE INDEX IF NOT EXISTS idx_content_analytics_content ON content_analytics(content_id);
CREATE INDEX IF NOT EXISTS idx_content_analytics_timestamp ON content_analytics(timestamp DESC);
