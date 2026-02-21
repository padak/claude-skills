# Example Plan: Task Management API

## Contents
- Phase 1: Database Schema and Base Models (solo)
- Phase 2: User CRUD API (parallel, depends on 1)
- Phase 3: Task CRUD API (parallel, depends on 1)
- Phase 4: Dashboard Statistics (solo, depends on 2+3)

A complete example demonstrating plan structure with solo phases, parallel phases, dependencies, and all required sections.

**Execution groups:** [1], [2, 3], [4]
- Group 1: Phase 1 (solo) — foundation
- Group 2: Phases 2 + 3 (parallel) — independent features branching from Phase 1
- Group 3: Phase 4 (solo) — integration depending on both 2 and 3

---

<!-- PHASE:1 -->
## Phase 1: Database Schema and Base Models

### Branch
`phase-1-db-schema`

### Scope
Set up the database schema for a task management system. Create SQLAlchemy models for tasks, users, and task assignments. Include Alembic migration.

Pseudocode:
```
class User(Base):
    id: UUID, primary key
    email: str, unique, not null
    name: str, not null
    created_at: datetime, default now

class Task(Base):
    id: UUID, primary key
    title: str, not null
    description: text, nullable
    status: enum(pending, in_progress, done), default pending
    priority: enum(low, medium, high), default medium
    created_by: FK -> User.id, not null
    assigned_to: FK -> User.id, nullable
    due_date: datetime, nullable
    created_at: datetime, default now
    updated_at: datetime, on update now
```

### Files to Create/Modify
- `src/models/user.py` — User SQLAlchemy model
- `src/models/task.py` — Task SQLAlchemy model with enums
- `src/models/__init__.py` — re-export models
- `alembic/versions/001_initial_schema.py` — migration
- `src/db.py` — engine, session factory, Base

### Acceptance Criteria
- [ ] User model has id (UUID), email (unique), name, created_at
- [ ] Task model has id, title, description, status enum, priority enum, created_by FK, assigned_to FK, due_date, timestamps
- [ ] Alembic migration creates both tables with proper constraints
- [ ] `alembic upgrade head` runs without errors on a clean database
- [ ] Foreign keys enforce referential integrity (CASCADE on user delete)

### Tests Required
- `tests/test_models.py::test_create_user` — insert and retrieve user
- `tests/test_models.py::test_create_task_with_assignment` — task with FK to user
- `tests/test_models.py::test_task_status_enum_validation` — reject invalid status
- `tests/test_models.py::test_user_email_uniqueness` — duplicate email raises IntegrityError
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
## Phase 2: User CRUD API

### Branch
`phase-2-user-api`

### Scope
REST API for user management. Uses models from Phase 1.

Pseudocode:
```
router = APIRouter(prefix="/users")

POST   /users          — create user (email, name) -> 201 + user
GET    /users           — list users (pagination: skip, limit) -> 200 + list
GET    /users/{id}      — get user by id -> 200 + user | 404
PUT    /users/{id}      — update user (name, email) -> 200 + user | 404
DELETE /users/{id}      — delete user -> 204 | 404

Pydantic schemas:
  UserCreate(email: EmailStr, name: str)
  UserUpdate(name: str | None, email: EmailStr | None)
  UserResponse(id: UUID, email: str, name: str, created_at: datetime)
```

### Files to Create/Modify
- `src/routers/users.py` — FastAPI router with all 5 endpoints
- `src/schemas/user.py` — Pydantic request/response schemas
- `src/services/user.py` — business logic (CRUD operations)

### Acceptance Criteria
- [ ] POST /users creates user and returns 201 with UserResponse
- [ ] GET /users returns paginated list (default limit from config)
- [ ] GET /users/{id} returns 404 with detail message for non-existent user
- [ ] PUT /users/{id} allows partial update (only provided fields change)
- [ ] DELETE /users/{id} returns 204 on success
- [ ] Email validation rejects malformed emails (422)
- [ ] Duplicate email returns 409 Conflict

### Tests Required
- `tests/test_users_api.py::test_create_user` — POST 201 + response body
- `tests/test_users_api.py::test_create_user_duplicate_email` — POST 409
- `tests/test_users_api.py::test_list_users_pagination` — GET with skip/limit
- `tests/test_users_api.py::test_get_user_not_found` — GET 404
- `tests/test_users_api.py::test_update_user_partial` — PUT only changes provided fields
- `tests/test_users_api.py::test_delete_user` — DELETE 204, subsequent GET 404
<!-- /PHASE:2 -->

<!-- PHASE:3 DEPENDS:1 -->
## Phase 3: Task CRUD API

### Branch
`phase-3-task-api`

### Scope
REST API for task management. Uses models from Phase 1. Independent of Phase 2 (no shared files).

Pseudocode:
```
router = APIRouter(prefix="/tasks")

POST   /tasks           — create task (title, description?, priority?, assigned_to?) -> 201
GET    /tasks           — list tasks (filters: status, priority, assigned_to; pagination) -> 200
GET    /tasks/{id}      — get task -> 200 | 404
PUT    /tasks/{id}      — update task -> 200 | 404
PATCH  /tasks/{id}/status — transition status (pending->in_progress->done) -> 200 | 422
DELETE /tasks/{id}      — delete task -> 204 | 404

Status transitions enforced:
  pending -> in_progress (only)
  in_progress -> done (only)
  done -> (no further transitions)
```

### Files to Create/Modify
- `src/routers/tasks.py` — FastAPI router with 6 endpoints
- `src/schemas/task.py` — Pydantic schemas including status transition
- `src/services/task.py` — business logic with status state machine

### Acceptance Criteria
- [ ] POST /tasks creates task with created_by from auth context
- [ ] GET /tasks supports filtering by status, priority, assigned_to
- [ ] PATCH /tasks/{id}/status enforces valid transitions (pending->in_progress->done)
- [ ] PATCH /tasks/{id}/status returns 422 for invalid transition (e.g., done->pending)
- [ ] Task listing returns assigned user info (id + name) via join
- [ ] Assigning to non-existent user returns 422

### Tests Required
- `tests/test_tasks_api.py::test_create_task` — POST 201
- `tests/test_tasks_api.py::test_list_tasks_filter_by_status` — GET with status=done
- `tests/test_tasks_api.py::test_status_transition_valid` — pending->in_progress 200
- `tests/test_tasks_api.py::test_status_transition_invalid` — done->pending 422
- `tests/test_tasks_api.py::test_assign_to_nonexistent_user` — 422
- `tests/test_tasks_api.py::test_delete_task` — DELETE 204
<!-- /PHASE:3 -->

<!-- PHASE:4 DEPENDS:2,3 -->
## Phase 4: Dashboard Statistics Endpoint

### Branch
`phase-4-dashboard`

### Scope
Aggregation endpoint combining user and task data. Depends on both Phase 2 and Phase 3 because it queries both users and tasks.
Also registers all routers (users, tasks, dashboard) in the main app.

Pseudocode:
```
router = APIRouter(prefix="/dashboard")

GET /dashboard/stats -> {
    total_users: int,
    total_tasks: int,
    tasks_by_status: {pending: int, in_progress: int, done: int},
    tasks_by_priority: {low: int, medium: int, high: int},
    top_assignees: [{user_id, user_name, task_count}]  # top 5
    overdue_tasks: int  # due_date < now AND status != done
}

Single DB query using window functions for efficiency.
```

### Files to Create/Modify
- `src/routers/dashboard.py` — FastAPI router with stats endpoint
- `src/schemas/dashboard.py` — Pydantic response schema
- `src/services/dashboard.py` — aggregation queries
- `src/main.py` — register users, tasks, and dashboard routers

### Acceptance Criteria
- [ ] GET /dashboard/stats returns all fields with correct counts
- [ ] tasks_by_status counts match actual task distribution
- [ ] top_assignees returns max 5 users sorted by task count desc
- [ ] overdue_tasks only counts tasks where due_date < now AND status != done
- [ ] Endpoint responds under 200ms with 1000 tasks (query optimization)

### Tests Required
- `tests/test_dashboard_api.py::test_stats_empty_db` — all zeros
- `tests/test_dashboard_api.py::test_stats_with_data` — seed 10 users, 50 tasks, verify counts
- `tests/test_dashboard_api.py::test_top_assignees_limit` — verify max 5 returned
- `tests/test_dashboard_api.py::test_overdue_calculation` — task with past due_date + status pending = overdue
<!-- /PHASE:4 -->
