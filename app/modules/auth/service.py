from datetime import datetime
from datetime import timedelta
from secrets import token_urlsafe

from app.modules.auth.repository import AuthRepository
from app.modules.auth.model import OrgStudentLoginToken, StudentParent
from core.config import STORAGE_SERVICE
from core.jwt_config import (
    create_access_token,
    create_refresh_token,
    get_token_payload,
    get_token_subject,
)


class AuthService:
    @staticmethod
    def parent_login_username_password(db, username, password):
        parent = AuthRepository.parent_login_username_password(
            db,
            username,
            password,
        )
        if not parent:
            return None
        return AuthService.build_parent_login_response(parent)

    @staticmethod
    def build_parent_login_response(parent):
        return {
            "parent_id": parent.id,
            "username": parent.username,
            "student_id": parent.student_id,
            "access_token": create_access_token(parent.id, role="parent"),
            "refresh_token": create_refresh_token(parent.id, role="parent"),
        }

    @staticmethod
    def get_profile_by_token(db, token):
        payload = get_token_payload(token)
        if not payload or payload.get("token_type") != "access":
            return None

        role = payload.get("role")
        user_id = get_token_subject(token)
        if role not in ("parent", "student") or not user_id:
            return None

        if role == "parent":
            parent = db.query(StudentParent).filter(StudentParent.id == user_id).first()
        else:
            parent = db.query(StudentParent).filter(StudentParent.student_id == user_id).first()

        if not parent:
            return None

        student = parent.student
        if role == "student" and not student:
            return None

        return {
            "role": role,
            "parent_id": parent.id,
            "username": parent.username,
            "student_id": parent.student_id,
            "parent_info": {
                "id": parent.id,
                "username": parent.username,
                "father": {
                    "name": parent.father_name,
                    "phone": parent.father_phone,
                    "email": parent.father_email,
                    "occupation": parent.father_occupation,
                    "income": str(parent.father_income) if parent.father_income is not None else None,
                },
                "mother": {
                    "name": parent.mother_name,
                    "phone": parent.mother_phone,
                    "email": parent.mother_email,
                    "occupation": parent.mother_occupation,
                    "income": str(parent.mother_income) if parent.mother_income is not None else None,
                },
                "guardian": {
                    "name": parent.guardian_name,
                    "relation": parent.guardian_relation,
                    "phone": parent.guardian_phone,
                    "email": parent.guardian_email,
                    "address": parent.guardian_address,
                },
                "address": parent.address,
            },
            "student_info": {
                "id": student.id if student else None,
                "organization_id": student.organization_id if student else None,
                "admission_number": student.admission_number if student else None,
                "admission_type": student.admission_type if student else None,
                "full_name": student.full_name if student else None,
                "first_name": student.first_name if student else None,
                "middle_name": student.middle_name if student else None,
                "last_name": student.last_name if student else None,
                "date_of_birth": student.date_of_birth.isoformat() if student and student.date_of_birth else None,
                "gender": student.gender if student else None,
                "email": student.email if student else None,
                "isd_code": student.isd_code if student else None,
                "mobile": student.mobile if student else None,
                "nationality": student.nationality if student else None,
                "religion_id": student.religion_id if student else None,
                "caste_id": student.caste_id if student else None,
                "mother_tongue_id": student.mother_tongue_id if student else None,
                "blood_group_id": student.blood_group_id if student else None,
                "preferred_class_id": student.preferred_class_id if student else None,
                "profile_picture": f"{STORAGE_SERVICE}{student.profile_picture}" if student else None,
                "enrollment_status": student.enrollment_status if student else None,
            },
        }

    @staticmethod
    def create_student_session_from_parent_token(db, token, device_id=None, device_name=None):
        payload = get_token_payload(token)
        if not payload or payload.get("role") != "parent":
            return None

        parent_id = get_token_subject(token)
        if not parent_id:
            return None

        parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
        if not parent or not parent.student:
            return None

        student = parent.student
        access_token = create_access_token(student.id, role="student")
        refresh_token = create_refresh_token(student.id, role="student")

        login_token = OrgStudentLoginToken(
            organization_id=student.organization_id,
            parent_id=parent.id,
            student_id=student.id,
            token=refresh_token,
            device_id=device_id,
            device_name=device_name,
            qr_code_version=1,
            status="ACTIVE",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db.add(login_token)
        db.commit()
        db.refresh(login_token)

        return {
            "parent_id": parent.id,
            "student_id": student.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def create_student_login_token_from_parent_token(db, token, device_id=None, device_name=None):
        payload = get_token_payload(token)
        if not payload or payload.get("role") != "parent":
            return None

        parent_id = get_token_subject(token)
        if not parent_id:
            return None

        parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
        if not parent or not parent.student:
            return None

        student = parent.student
        login_token = token_urlsafe(32)
        record = OrgStudentLoginToken(
            organization_id=student.organization_id,
            parent_id=parent.id,
            student_id=student.id,
            token=login_token,
            device_id=device_id,
            device_name=device_name,
            qr_code_version=1,
            status="ACTIVE",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "parent_id": parent.id,
            "student_id": student.id,
            "login_token": login_token,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        }

    @staticmethod
    def login_student_with_token(db, token, device_id=None, device_name=None):
        record = (
            db.query(OrgStudentLoginToken)
            .filter(OrgStudentLoginToken.token == token)
            .first()
        )
        if not record or record.status != "ACTIVE":
            return None

        if record.expires_at and record.expires_at < datetime.utcnow():
            record.status = "EXPIRED"
            db.commit()
            return None

        parent = db.query(StudentParent).filter(StudentParent.id == record.parent_id).first()
        if not parent or not parent.student:
            return None
        student = parent.student

        record.status = "USED"
        record.used_at = datetime.utcnow()
        if device_id is not None:
            record.device_id = device_id
        if device_name is not None:
            record.device_name = device_name
        db.commit()

        access_token = create_access_token(student.id, role="student")
        refresh_token = create_refresh_token(student.id, role="student")

        return {
            "parent_id": record.parent_id,
            "student_id": student.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def refresh_session_tokens(db, refresh_token):
        payload = get_token_payload(refresh_token)
        if not payload or payload.get("token_type") != "refresh":
            return None

        role = payload.get("role")
        user_id = get_token_subject(refresh_token)
        if not user_id:
            return None

        if role == "parent":
            parent = db.query(StudentParent).filter(StudentParent.id == user_id).first()
            if not parent:
                return None
            return {
                "role": "parent",
                "parent_id": parent.id,
                "student_id": parent.student_id,
                "access_token": create_access_token(parent.id, role="parent"),
                "refresh_token": create_refresh_token(parent.id, role="parent"),
            }

        if role == "student":
            parent = db.query(StudentParent).filter(StudentParent.student_id == user_id).first()
            if not parent:
                return None

            active_login = (
                db.query(OrgStudentLoginToken)
                .filter(
                    OrgStudentLoginToken.student_id == user_id,
                    OrgStudentLoginToken.status.in_(["ACTIVE", "USED"]),
                )
                .order_by(OrgStudentLoginToken.id.desc())
                .first()
            )
            if not active_login:
                return None

            return {
                "role": "student",
                "parent_id": parent.id,
                "student_id": user_id,
                "access_token": create_access_token(user_id, role="student"),
                "refresh_token": create_refresh_token(user_id, role="student"),
            }

        return None
