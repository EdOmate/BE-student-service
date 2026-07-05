from app.modules.auth.repository import AuthRepository
from core.jwt_config import create_access_token, create_refresh_token, get_token_subject
from app.modules.auth.model import StudentParent


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
            "access_token": create_access_token(parent.id),
            "refresh_token": create_refresh_token(parent.id),
        }

    @staticmethod
    def get_parent_profile_by_token(db, token):
        parent_id = get_token_subject(token)
        if not parent_id:
            return None
        parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
        if not parent:
            return None

        student = parent.student
        return {
            "parent_id": parent.id,
            "username": parent.username,
            "student_id": parent.student_id,
            "parent_info": {
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
                "profile_picture": student.profile_picture if student else None,
                "enrollment_status": student.enrollment_status if student else None,
            },
        }
