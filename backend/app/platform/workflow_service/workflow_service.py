"""Workflow execution state persistence service (W-013).

Manages saving and restoring workflow execution state, enabling crash
recovery and pause/resume of long-running workflows.
Also manages workflow version history.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import (
    WorkflowExecutionModel,
    WorkflowModel,
    WorkflowVersionModel,
)


class WorkflowExecutionService:
    """Persist and retrieve workflow execution state via SQLAlchemy async session."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_execution(
        self,
        workflow_id: str,
        tenant_id: str,
        variables: Optional[dict] = None,
    ) -> dict:
        """Create a new workflow execution record and return its metadata."""
        try:
            execution = WorkflowExecutionModel(
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                status="running",
                node_states={},
                variables=variables or {},
                execution_log=[],
            )
            self.db.add(execution)
            await self.db.flush()
            return self._to_dict(execution)
        except Exception as e:
            raise ValueError(f"Failed to start execution: {str(e)}")

    async def get_execution(self, execution_id: str, tenant_id: str) -> Optional[dict]:
        """Retrieve a single execution by id, scoped to a tenant."""
        stmt = select(WorkflowExecutionModel).where(
            and_(
                WorkflowExecutionModel.id == execution_id,
                WorkflowExecutionModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        if execution is None:
            return None
        return self._to_dict(execution)

    async def update_node_status(
        self,
        execution_id: str,
        tenant_id: str,
        node_id: str,
        node_status: str,
        node_output: Optional[dict] = None,
    ) -> dict:
        """Update the status (and optional output) of a single node inside
        an execution's node_states JSON field.
        """
        stmt = select(WorkflowExecutionModel).where(
            and_(
                WorkflowExecutionModel.id == execution_id,
                WorkflowExecutionModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        if execution is None:
            raise ValueError(f"Execution {execution_id} not found")

        node_states = dict(execution.node_states or {})
        node_states[node_id] = {
            "status": node_status,
            "output": node_output,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        execution.node_states = node_states
        execution.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return self._to_dict(execution)

    async def update_execution_status(
        self,
        execution_id: str,
        tenant_id: str,
        status: str,
        variables: Optional[dict] = None,
        execution_log: Optional[list] = None,
        error_message: Optional[str] = None,
        trace_id: Optional[str] = None,
        node_logs: Optional[list] = None,
        trace_tree: Optional[dict] = None,
    ) -> dict:
        """Update top-level execution fields: status, variables, log, error, trace."""
        stmt = select(WorkflowExecutionModel).where(
            and_(
                WorkflowExecutionModel.id == execution_id,
                WorkflowExecutionModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        if execution is None:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = status
        if variables is not None:
            execution.variables = variables
        if execution_log is not None:
            execution.execution_log = execution_log
        if error_message is not None:
            execution.error_message = error_message
        if trace_id is not None:
            execution.trace_id = trace_id
        if node_logs is not None:
            execution.node_logs = node_logs
        if trace_tree is not None:
            execution.trace_tree = trace_tree
        execution.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return self._to_dict(execution)

    async def resume_execution(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> dict:
        """Load a paused/failed execution so the engine can continue from
        where it left off.

        Returns the persisted state that the caller should feed back into
        WorkflowEngine.execute() (or a custom resume path).
        """
        stmt = select(WorkflowExecutionModel).where(
            and_(
                WorkflowExecutionModel.id == execution_id,
                WorkflowExecutionModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()
        if execution is None:
            raise ValueError(f"Execution {execution_id} not found")

        # Mark as running again
        execution.status = "running"
        execution.error_message = None
        execution.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        return self._to_dict(execution)

    # ------------------------------------------------------------------
    @staticmethod
    def _to_dict(execution: WorkflowExecutionModel) -> dict:
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "tenant_id": execution.tenant_id,
            "status": execution.status,
            "node_states": execution.node_states or {},
            "variables": execution.variables or {},
            "execution_log": execution.execution_log or [],
            "error_message": execution.error_message,
            "trace_id": execution.trace_id,
            "node_logs": execution.node_logs or [],
            "trace_tree": execution.trace_tree or {},
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
        }


class WorkflowVersionService:
    """Manage workflow version history: snapshot, list, and rollback."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def snapshot_version(
        self,
        workflow_id: str,
        version: int,
        dag_config: dict,
        created_by: Optional[str] = None,
    ) -> dict:
        """Save a snapshot of the current DAG config as a versioned record."""
        wf_version = WorkflowVersionModel(
            workflow_id=workflow_id,
            version=version,
            dag_config=dag_config,
            created_by=created_by,
        )
        self.db.add(wf_version)
        await self.db.flush()
        return self._to_dict(wf_version)

    async def list_versions(self, workflow_id: str) -> list[dict]:
        """List all versions for a workflow, ordered by version number."""
        stmt = (
            select(WorkflowVersionModel)
            .where(WorkflowVersionModel.workflow_id == workflow_id)
            .order_by(WorkflowVersionModel.version.desc())
        )
        result = await self.db.execute(stmt)
        versions = result.scalars().all()
        return [self._to_dict(v) for v in versions]

    async def get_version(self, workflow_id: str, version: int) -> Optional[dict]:
        """Get a specific version's config snapshot."""
        stmt = select(WorkflowVersionModel).where(
            and_(
                WorkflowVersionModel.workflow_id == workflow_id,
                WorkflowVersionModel.version == version,
            )
        )
        result = await self.db.execute(stmt)
        wf_version = result.scalar_one_or_none()
        if wf_version is None:
            return None
        return self._to_dict(wf_version)

    async def rollback_to_version(
        self,
        workflow_id: str,
        version: int,
        user_id: Optional[str] = None,
    ) -> dict:
        """Restore a workflow to a previous version.

        1. Snapshot the current config as a new version
        2. Overwrite the workflow's dag_config with the target version's config
        3. Increment the workflow version
        """
        try:
            # Fetch the target version snapshot
            target = await self.get_version(workflow_id, version)
            if target is None:
                raise ValueError(f"Version {version} not found for workflow {workflow_id}")

            # Fetch the workflow
            stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
            result = await self.db.execute(stmt)
            workflow = result.scalar_one_or_none()
            if workflow is None:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Snapshot current state before overwriting
            current_version = workflow.version
            await self.snapshot_version(
                workflow_id=workflow_id,
                version=current_version,
                dag_config=workflow.dag_config or {},
                created_by=user_id,
            )

            # Apply the target version's config
            new_version = current_version + 1
            workflow.dag_config = target["dag_config"]
            workflow.version = new_version
            workflow.updated_at = datetime.now(timezone.utc)

            # Snapshot the restored config as the new version
            await self.snapshot_version(
                workflow_id=workflow_id,
                version=new_version,
                dag_config=target["dag_config"],
                created_by=user_id,
            )

            await self.db.flush()
            return {
                "id": workflow.id,
                "name": workflow.name,
                "version": new_version,
                "dag_config": target["dag_config"],
                "restored_from_version": version,
            }
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to rollback workflow: {str(e)}")

    @staticmethod
    def _to_dict(wf_version: WorkflowVersionModel) -> dict:
        return {
            "id": wf_version.id,
            "workflow_id": wf_version.workflow_id,
            "version": wf_version.version,
            "dag_config": wf_version.dag_config or {},
            "created_at": wf_version.created_at.isoformat() if wf_version.created_at else None,
            "created_by": wf_version.created_by,
        }
