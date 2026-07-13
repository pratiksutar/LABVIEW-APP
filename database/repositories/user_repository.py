"""
User Repository
Handles all database operations for application users.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database.models.user_model import UserModel
from database.connection import DatabaseManager


class UserRepository:
    """Repository for User CRUD operations."""

    def __init__(self) -> None:
        self._db = DatabaseManager.instance()

    # ─── Read ────────────────────────────────────────────────────
    def count(self) -> int:
        session: Session = self._db.get_session()
        try:
            return session.query(UserModel).count()
        finally:
            session.close()

    def get_all(self) -> List[UserModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(UserModel).order_by(UserModel.username).all()
        finally:
            session.close()

    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        session: Session = self._db.get_session()
        try:
            return session.get(UserModel, user_id)
        finally:
            session.close()

    def get_by_username(self, username: str) -> Optional[UserModel]:
        session: Session = self._db.get_session()
        try:
            return session.query(UserModel).filter_by(username=username).first()
        finally:
            session.close()

    # ─── Create ──────────────────────────────────────────────────
    def create(self, username: str, password_hash: str, full_name: str,
               role: str, is_active: bool = True) -> UserModel:
        session: Session = self._db.get_session()
        try:
            model = UserModel(
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                is_active=is_active,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            session.expunge(model)
            return model
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ─── Update ──────────────────────────────────────────────────
    def update(self, user_id: int, full_name: Optional[str] = None,
               role: Optional[str] = None) -> Optional[UserModel]:
        session: Session = self._db.get_session()
        try:
            model = session.get(UserModel, user_id)
            if model is None:
                return None
            if full_name is not None:
                model.full_name = full_name
            if role is not None:
                model.role = role
            session.commit()
            session.refresh(model)
            session.expunge(model)
            return model
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_active(self, user_id: int, is_active: bool) -> bool:
        session: Session = self._db.get_session()
        try:
            model = session.get(UserModel, user_id)
            if model is None:
                return False
            model.is_active = is_active
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_password(self, user_id: int, password_hash: str) -> bool:
        session: Session = self._db.get_session()
        try:
            model = session.get(UserModel, user_id)
            if model is None:
                return False
            model.password_hash = password_hash
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_login(self, user_id: int) -> None:
        session: Session = self._db.get_session()
        try:
            model = session.get(UserModel, user_id)
            if model is None:
                return
            model.last_login = datetime.now()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
