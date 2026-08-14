from datetime import datetime
from datetime import timedelta
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.modules.academics.models import SchoolStudentSectionMapping
from app.modules.auth.dependencies import AuthenticatedStudent
from app.modules.auth.model import OrgStudentLoginToken, StudentParent
from app.modules.auth.repository import AuthRepository
from app.modules.mainsite.models import OrgBloodGroupMaster
from app.modules.students.models import (
    OrgSchoolStudentAddress,
    OrgSchoolStudentMedical,
)
from core.config import STORAGE_SERVICE
from core.jwt_config import (
    create_access_token,
    create_refresh_token,
    get_token_payload,
    get_token_subject,
)


class AuthService:
    NATIONALITY_LABELS = {
        1: "Indian",
        2: "Foreigner",
    }
    EMERGENCY_CONTACT_RELATION_LABELS = {
        1: "Father",
        2: "Mother",
        3: "Brother",
        4: "Sister",
        5: "Grandfather",
        6: "Grandmother",
        7: "Uncle",
        8: "Aunt",
        9: "Other",
    }

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
    def get_user_profile(db: Session, auth: AuthenticatedStudent):
        student = auth.student
        mapping_info = (
            db.query(SchoolStudentSectionMapping)
            .filter(
                SchoolStudentSectionMapping.student_id == auth.student_id,
                SchoolStudentSectionMapping.status == "Active",
            )
            .order_by(SchoolStudentSectionMapping.id.desc())
            .first()
        )
        class_info = mapping_info.section.org_class if mapping_info else None

        return {
            "role": auth.role,
            "parent_id": auth.parent_id,
            "student_id": auth.student_id,
            "student_info": {
                "id": student.id,
                "organization_id": student.organization_id,
                "admission_number": student.admission_number,
                "admission_type": student.admission_type,
                "full_name": student.full_name,
                "first_name": student.first_name,
                "middle_name": student.middle_name,
                "last_name": student.last_name,
                "date_of_birth": (
                    student.date_of_birth.isoformat()
                    if student.date_of_birth
                    else None
                ),
                "gender": student.gender,
                "email": student.email,
                "isd_code": student.isd_code,
                "mobile": student.mobile,
                "nationality_id": student.nationality,
                "nationality": AuthService.NATIONALITY_LABELS.get(
                    student.nationality
                ),
                "religion_id": student.religion_id,
                "religion": (
                    student.religion.name
                    if student.religion
                    else None
                ),
                "caste_id": student.caste_id,
                "caste": (
                    student.caste.name
                    if student.caste
                    else None
                ),
                "mother_tongue_id": student.mother_tongue_id,
                "mother_tongue": (
                    student.mother_tongue.name
                    if student.mother_tongue
                    else None
                ),
                "blood_group_id": student.blood_group_id,
                "blood_group": (
                    student.blood_group.group_code
                    if student.blood_group
                    else None
                ),
                "class_id": class_info.id if class_info else None,
                "class_name": class_info.master_class.name if class_info else None,
                "preferred_class_id": student.preferred_class_id,
                "profile_picture": (
                    f"{STORAGE_SERVICE}{student.profile_picture}"
                    if student.profile_picture
                    else None
                ),
                "enrollment_status": student.enrollment_status,
            },
        }

    @staticmethod
    def get_parent_detail(
        db: Session,
        auth: AuthenticatedStudent,
    ) -> dict | None:
        query = db.query(StudentParent).filter(
            StudentParent.student_id == auth.student_id,
        )
        if auth.parent_id is not None:
            query = query.filter(StudentParent.id == auth.parent_id)

        parent = query.order_by(StudentParent.id.desc()).first()
        if not parent:
            return None

        return {
            "id": parent.id,
            "username": parent.username,
            "student_id": parent.student_id,
            "father": {
                "name": parent.father_name,
                "phone": parent.father_phone,
                "email": parent.father_email,
                "occupation": parent.father_occupation,
                "income": (
                    str(parent.father_income)
                    if parent.father_income is not None
                    else None
                ),
            },
            "mother": {
                "name": parent.mother_name,
                "phone": parent.mother_phone,
                "email": parent.mother_email,
                "occupation": parent.mother_occupation,
                "income": (
                    str(parent.mother_income)
                    if parent.mother_income is not None
                    else None
                ),
            },
            "guardian": {
                "name": parent.guardian_name,
                "relation": parent.guardian_relation,
                "phone": parent.guardian_phone,
                "email": parent.guardian_email,
            },
            "created_at": (
                parent.created_at.isoformat()
                if parent.created_at
                else None
            ),
            "updated_at": (
                parent.updated_at.isoformat()
                if parent.updated_at
                else None
            ),
        }

    @staticmethod
    def get_address_detail(
        db: Session,
        auth: AuthenticatedStudent,
    ) -> dict:
        rows = (
            db.query(OrgSchoolStudentAddress)
            .filter(OrgSchoolStudentAddress.student_id == auth.student_id)
            .order_by(OrgSchoolStudentAddress.id.asc())
            .all()
        )

        addresses = {
            "current": None,
            "permanent": None,
        }
        for row in rows:
            address_type = (row.address_type or "").strip().lower()
            if address_type not in addresses:
                continue
            addresses[address_type] = {
                "id": row.id,
                "address": row.address,
                "city": row.city,
                "state": row.state,
                "country": row.country,
                "postal_code": row.postal_code,
            }

        parent_query = db.query(StudentParent).filter(
            StudentParent.student_id == auth.student_id,
        )
        if auth.parent_id is not None:
            parent_query = parent_query.filter(
                StudentParent.id == auth.parent_id,
            )
        parent = parent_query.order_by(StudentParent.id.desc()).first()

        return {
            "student_id": auth.student_id,
            "current": addresses["current"],
            "permanent": addresses["permanent"],
            "parent_address": parent.address if parent else None,
            "guardian_address": parent.guardian_address if parent else None,
        }

    @staticmethod
    def get_health_detail(
        db: Session,
        auth: AuthenticatedStudent,
    ) -> dict | None:
        medical = (
            db.query(OrgSchoolStudentMedical)
            .filter(OrgSchoolStudentMedical.student_id == auth.student_id)
            .first()
        )
        if not medical:
            return None

        blood_group = None
        if medical.blood_group_id:
            blood_group = (
                db.query(OrgBloodGroupMaster)
                .filter(OrgBloodGroupMaster.id == medical.blood_group_id)
                .first()
            )

        return {
            "id": medical.id,
            "student_id": medical.student_id,
            "has_disability": medical.has_disability,
            "disability_details": medical.disability_details,
            "allergies": medical.allergies,
            "medical_conditions": medical.medical_conditions,
            "blood_group_id": medical.blood_group_id,
            "blood_group": blood_group.group_code if blood_group else None,
            "height": (
                str(medical.height)
                if medical.height is not None
                else None
            ),
            "weight": (
                str(medical.weight)
                if medical.weight is not None
                else None
            ),
            "emergency_contact": {
                "name": medical.emergency_contact_name,
                "phone": medical.emergency_contact_phone,
                "relation_id": medical.emergency_contact_relation,
                "relation": AuthService.EMERGENCY_CONTACT_RELATION_LABELS.get(
                    medical.emergency_contact_relation
                ),
            },
            "vaccination_records": medical.vaccination_records,
            "regular_medications": medical.regular_medications,
            "medical_insurance_number": medical.medical_insurance_number,
            "doctor": {
                "name": medical.doctor_name,
                "phone": medical.doctor_phone,
            },
            "created_at": (
                medical.created_at.isoformat()
                if medical.created_at
                else None
            ),
            "updated_at": (
                medical.updated_at.isoformat()
                if medical.updated_at
                else None
            ),
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
