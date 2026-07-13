"""
Workstation Application Service
Coordinates business logic between repositories and domain models.
"""
from typing import List, Optional
from datetime import datetime
from loguru import logger

from database.repositories.workstation_repository      import WorkstationRepository
from database.repositories.device_mapping_repository   import DeviceMappingRepository
from database.repositories.status_history_repository   import StatusHistoryRepository
from database.models.workstation_model              import WorkstationModel
from domain.models.workstation                      import Workstation
from domain.enums.workstation_status                import WorkstationStatus
from domain.enums.audit_action                      import AuditAction
from config.settings                                import AppSettings


def _audit():
    from application.services.audit_service import AuditService
    return AuditService.instance()


class WorkstationService:
    """Service layer for workstation business logic."""

    def __init__(self) -> None:
        self._ws_repo      = WorkstationRepository()
        self._dm_repo      = DeviceMappingRepository()
        self._history_repo = StatusHistoryRepository()
        self._settings     = AppSettings.instance()
        self._cache: dict[int, Workstation] = {}
        self._actor: str = "system"   # set by MainWindow after login

    def set_actor(self, username: str) -> None:
        """Called by MainWindow after login so audit logs show the right user."""
        self._actor = username

    # ─── Startup hydration ──────────────────────────────────────
    def hydrate_cache_from_history(self) -> None:
        """
        Populate the in-memory cache from the most recent StatusHistory
        record for each workstation, so the dashboard shows last-known
        status immediately on launch instead of 'Disconnected'.
        """
        for model in self._ws_repo.get_all():
            latest = self._history_repo.get_latest_for_workstation(model.id)
            if latest is None:
                continue
            try:
                status = WorkstationStatus(latest.status)
            except ValueError:
                continue
            ws = Workstation(
                id=model.id,
                status=status,
                power_state=latest.power_state,
                power_consumption=latest.power_consumption,
                last_updated=latest.recorded_at,
                is_maintenance=model.is_maintenance,
            )
            self._cache[model.id] = ws

    # ─── Queries ────────────────────────────────────────────────
    def get_all_workstations(self) -> List[Workstation]:
        """Return all workstations as domain models, enriched with cached status."""
        models = self._ws_repo.get_all()
        result: List[Workstation] = []
        for m in models:
            ws = self._model_to_domain(m)
            # Overlay cached live data if available
            if ws.id in self._cache:
                cached = self._cache[ws.id]
                ws.status            = cached.status
                ws.power_consumption = cached.power_consumption
                ws.power_state       = cached.power_state
                ws.voltage           = cached.voltage
                ws.last_updated      = cached.last_updated
            result.append(ws)
        return result

    def get_workstation(self, workstation_id: int) -> Optional[Workstation]:
        model = self._ws_repo.get_by_id(workstation_id)
        if model is None:
            return None
        ws = self._model_to_domain(model)
        if ws.id in self._cache:
            cached = self._cache[ws.id]
            ws.status            = cached.status
            ws.power_consumption = cached.power_consumption
            ws.power_state       = cached.power_state
            ws.last_updated      = cached.last_updated
        return ws

    def get_summary(self) -> dict:
        """Return summary counts for the dashboard header."""
        workstations = self.get_all_workstations()
        return {
            "total":       len(workstations),
            "available":   sum(1 for w in workstations if w.status == WorkstationStatus.AVAILABLE),
            "in_use":      sum(1 for w in workstations if w.status == WorkstationStatus.IN_USE),
            "idle":        sum(1 for w in workstations if w.status == WorkstationStatus.IDLE),
            "maintenance": sum(1 for w in workstations if w.status == WorkstationStatus.MAINTENANCE),
            "disconnected":sum(1 for w in workstations if w.status == WorkstationStatus.DISCONNECTED),
            "failure":     sum(1 for w in workstations if w.status == WorkstationStatus.FAILURE),
        }

    # ─── Mutations ──────────────────────────────────────────────
    def create_workstation(self, name: str, description: str = "",
                            area: str = "") -> Workstation:
        logger.info(f"Creating workstation: {name}")
        model = self._ws_repo.create(name=name, description=description, area=area)
        ws = self._model_to_domain(model)
        _audit().log(AuditAction.WS_CREATED, username=self._actor,
                     entity="Workstation", entity_id=ws.id, new_value=name)
        return ws

    def update_workstation(self, workstation_id: int, name: Optional[str] = None,
                            description: Optional[str] = None,
                            area: Optional[str] = None) -> Optional[Workstation]:
        logger.info(f"Updating workstation #{workstation_id}")
        old = self._ws_repo.get_by_id(workstation_id)
        old_val = old.name if old else None
        model = self._ws_repo.update(workstation_id, name=name,
                                      description=description, area=area)
        if model:
            _audit().log(AuditAction.WS_UPDATED, username=self._actor,
                         entity="Workstation", entity_id=workstation_id,
                         old_value=old_val, new_value=model.name)
        return self._model_to_domain(model) if model else None

    def delete_workstation(self, workstation_id: int) -> bool:
        logger.info(f"Deleting workstation #{workstation_id}")
        old = self._ws_repo.get_by_id(workstation_id)
        name = old.name if old else str(workstation_id)
        self._cache.pop(workstation_id, None)
        ok = self._ws_repo.delete(workstation_id)
        if ok:
            _audit().log(AuditAction.WS_DELETED, username=self._actor,
                         entity="Workstation", entity_id=workstation_id,
                         old_value=name)
        return ok

    def set_maintenance(self, workstation_id: int, is_maintenance: bool) -> bool:
        logger.info(f"Setting maintenance={is_maintenance} on ws #{workstation_id}")
        success = self._ws_repo.set_maintenance(workstation_id, is_maintenance)
        if success:
            if workstation_id in self._cache:
                if is_maintenance:
                    self._cache[workstation_id].status = WorkstationStatus.MAINTENANCE
                self._cache[workstation_id].is_maintenance = is_maintenance
            action = (AuditAction.MAINTENANCE_ENABLED if is_maintenance
                      else AuditAction.MAINTENANCE_DISABLED)
            _audit().log(action, username=self._actor,
                         entity="Workstation", entity_id=workstation_id)
        return success

    def assign_device(self, workstation_id: int, device_id: str,
                       device_name: str = "") -> bool:
        logger.info(f"Assigning device {device_id} to ws #{workstation_id}")
        try:
            self._dm_repo.upsert(workstation_id, device_id, device_name)
            _audit().log(AuditAction.WS_DEVICE_ASSIGNED, username=self._actor,
                         entity="Workstation", entity_id=workstation_id,
                         new_value=f"{device_name or device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to assign device: {e}")
            return False

    def remove_device(self, workstation_id: int) -> bool:
        ok = self._dm_repo.delete_by_workstation(workstation_id)
        if ok:
            _audit().log(AuditAction.WS_DEVICE_REMOVED, username=self._actor,
                         entity="Workstation", entity_id=workstation_id)
        return ok

    # ─── Live status update (called by polling service) ─────────
    def update_live_status(self, workstation_id: int, power_state: bool,
                            power_watts: float, voltage: float = 0.0) -> None:
        ws = self._cache.get(workstation_id) or Workstation(id=workstation_id)
        model = self._ws_repo.get_by_id(workstation_id)

        is_maintenance = model.is_maintenance if model else False
        status = WorkstationStatus.from_power(
            power_watts, is_maintenance=is_maintenance, is_offline=False
        )
        ws.status            = status
        ws.power_state       = power_state
        ws.power_consumption = power_watts
        ws.voltage           = voltage
        ws.is_maintenance    = is_maintenance
        ws.last_updated      = datetime.now()
        self._cache[workstation_id] = ws

        try:
            self._history_repo.record(
                workstation_id=workstation_id,
                status=status.value,
                power_consumption=power_watts,
                power_state=power_state,
            )
        except Exception as e:
            logger.warning(f"Failed to persist status history for ws #{workstation_id}: {e}")

    def mark_offline(self, workstation_id: int) -> None:
        ws = self._cache.get(workstation_id) or Workstation(id=workstation_id)
        ws.status      = WorkstationStatus.DISCONNECTED
        ws.last_updated = datetime.now()
        self._cache[workstation_id] = ws

        try:
            self._history_repo.record(
                workstation_id=workstation_id,
                status=WorkstationStatus.DISCONNECTED.value,
                power_consumption=0.0,
                power_state=False,
            )
        except Exception as e:
            logger.warning(f"Failed to persist offline status for ws #{workstation_id}: {e}")

    def set_power_state_optimistic(self, workstation_id: int, power_state: bool) -> None:
        """
        Immediately reflect a command result in the cache (before the next
        poll confirms it), so the UI feels responsive after Turn ON/OFF.
        """
        ws = self._cache.get(workstation_id) or Workstation(id=workstation_id)
        ws.power_state  = power_state
        ws.last_updated = datetime.now()
        if not power_state and ws.status == WorkstationStatus.IN_USE:
            ws.status = WorkstationStatus.AVAILABLE
        self._cache[workstation_id] = ws

    # ─── History queries ──────────────────────────────────────────
    def get_status_history(self, workstation_id: int, limit: int = 50):
        return self._history_repo.get_recent(workstation_id, limit)

    # ─── Helpers ────────────────────────────────────────────────
    def _model_to_domain(self, model: WorkstationModel) -> Workstation:
        mapping = self._dm_repo.get_by_workstation(model.id)
        return Workstation(
            id             = model.id,
            name           = model.name,
            description    = model.description or "",
            area           = model.area or "",
            device_id      = mapping.device_id if mapping else None,
            is_maintenance = model.is_maintenance,
            status         = WorkstationStatus.MAINTENANCE if model.is_maintenance
                             else WorkstationStatus.DISCONNECTED,
            created_at     = model.created_at,
        )
