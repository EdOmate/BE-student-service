from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.model import OrgSchoolStudent, StudentParent
from core.database import get_db
from core.jwt_config import get_token_payload


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedStudent:
    role: str
    parent_id: int | None
    student_id: int
    student: OrgSchoolStudent


def get_authenticated_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
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
        student_id = parent.student_id
    else:
        student_id = subject_id

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
