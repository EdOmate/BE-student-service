from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.model import OrgSchoolStudent, StudentParent
from app.modules.students.models import OrgSchoolStudentSibling
from core.database import get_db
from core.jwt_config import get_token_payload


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedStudent:
    role: str
    parent_id: int | None
    main_student_id: int
    student_id: int
    student: OrgSchoolStudent


def get_authenticated_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    requested_student_id: str | None = Header(None, alias="X-Student-ID"),
) -> AuthenticatedStudent:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = get_token_payload(credentials.credentials)
    if (
        not payload
        or payload.get("token_type") != "access"
        or payload.get("role") not in ("parent", "student")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        subject_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload["role"]
    parent_id = None
    main_student_id = None
    if role == "parent":
        parent = (
            db.query(StudentParent)
            .filter(StudentParent.id == subject_id)
            .first()
        )
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Parent account not found",
            )
        parent_id = parent.id
        main_student_id = parent.student_id
        student_id = main_student_id
        if requested_student_id is not None:
            try:
                selected_student_id = int(requested_student_id)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="X-Student-ID header must be a valid student ID",
                )

            if selected_student_id != main_student_id:
                is_sibling = (
                    db.query(OrgSchoolStudentSibling.id)
                    .filter(
                        OrgSchoolStudentSibling.student_id == main_student_id,
                        OrgSchoolStudentSibling.sibling_id == selected_student_id,
                    )
                    .first()
                    is not None
                )
                if not is_sibling:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="The selected student is not linked to this parent",
                    )
                student_id = selected_student_id
    else:
        student_id = subject_id
        main_student_id = student_id

    student = (
        db.query(OrgSchoolStudent)
        .filter(OrgSchoolStudent.id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student account not found",
        )

    return AuthenticatedStudent(
        role=role,
        parent_id=parent_id,
        main_student_id=main_student_id,
        student_id=student.id,
        student=student,
    )


def get_authenticated_parent(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
) -> AuthenticatedStudent:
    if auth.role != "parent" or auth.parent_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a parent can perform this action",
        )
    return auth
