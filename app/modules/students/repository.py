"""Database access for student-domain records."""

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.modules.academics.models import (
    OrgSchoolClass,
    OrgSchoolSection,
    OrgSchoolTimetable,
    SchoolStudentSectionMapping,
)
from app.modules.auth.model import OrgSchoolStudent, StudentParent
from app.modules.students.models import (
    OrgClassStudentAttendance,
    OrgStudentLeaveRequest,
)


class StudentRepository:
    @staticmethod
    def get_student_by_id(
        db: Session,
        student_id: int,
    ) -> OrgSchoolStudent | None:
        return (
            db.query(OrgSchoolStudent)
            .filter(OrgSchoolStudent.id == student_id)
            .first()
        )

    @staticmethod
    def get_parent_by_student_id(
        db: Session,
        student_id: int,
    ) -> StudentParent | None:
        return (
            db.query(StudentParent)
            .filter(StudentParent.student_id == student_id)
            .first()
        )

    @staticmethod
    def get_parent_by_id(
        db: Session,
        parent_id: int,
    ) -> StudentParent | None:
        return (
            db.query(StudentParent)
            .filter(StudentParent.id == parent_id)
            .first()
        )

    @staticmethod
    def get_active_section_mapping(db: Session, student_id: int):
        return (
            db.query(SchoolStudentSectionMapping)
            .options(
                joinedload(SchoolStudentSectionMapping.section)
                .joinedload(OrgSchoolSection.org_class)
                .joinedload(OrgSchoolClass.master_class)
            )
            .filter(
                SchoolStudentSectionMapping.student_id == student_id,
                SchoolStudentSectionMapping.status == "Active",
            )
            .order_by(SchoolStudentSectionMapping.id.desc())
            .first()
        )

    @staticmethod
    def get_attendance_for_date(
        db: Session,
        student_id: int,
        attendance_date: date,
    ):
        return (
            db.query(OrgClassStudentAttendance)
            .filter(
                OrgClassStudentAttendance.student_id == student_id,
                OrgClassStudentAttendance.date == attendance_date,
            )
            .order_by(OrgClassStudentAttendance.id.desc())
            .first()
        )

    @staticmethod
    def get_approved_leave_for_date(
        db: Session,
        student_id: int,
        selected_date: date,
    ):
        return (
            db.query(OrgStudentLeaveRequest)
            .filter(
                OrgStudentLeaveRequest.student_id == student_id,
                OrgStudentLeaveRequest.status == 2,
                OrgStudentLeaveRequest.start_date <= selected_date,
                OrgStudentLeaveRequest.end_date >= selected_date,
            )
            .order_by(OrgStudentLeaveRequest.id.desc())
            .first()
        )

    @staticmethod
    def get_active_timetable(db: Session, section_id: int):
        return (
            db.query(OrgSchoolTimetable)
            .filter(
                OrgSchoolTimetable.section_id == section_id,
                OrgSchoolTimetable.status == 1,
            )
            .order_by(
                OrgSchoolTimetable.is_default.desc(),
                OrgSchoolTimetable.created_at.desc(),
            )
            .first()
        )
