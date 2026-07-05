from sqlalchemy.orm import Session
from django.contrib.auth.hashers import check_password

from core.django_setup import setup_django
from app.modules.auth.model import StudentParent


class AuthRepository:
    @staticmethod
    def parent_login_username_password(db, username, password):
        setup_django()

        parent = (
            db.query(StudentParent)
            .filter(StudentParent.username == username)
            .first()
        )
        if not parent:
            return None
        if not check_password(password, parent.password):
            return None
        return parent
