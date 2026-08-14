"""Database access for student-domain records."""

from datetime import date

from sqlalchemy import func
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
    OrgStudentBehaviorPointLog,
    OrgStudentGroup,
    OrgStudentGroupAssignment,
    OrgStudentHouse,
    OrgStudentHouseAssignment,
)


class StudentRepository:
    @staticmethod
    def get_active_house_assignment(
        db: Session,
        student_id: int,
        organization_id: int,
    ):
        return (
            db.query(OrgStudentHouseAssignment, OrgStudentHouse)
            .join(
                OrgStudentHouse,
                OrgStudentHouse.id == OrgStudentHouseAssignment.house_id,
            )
            .filter(
                OrgStudentHouseAssignment.student_id == student_id,
                OrgStudentHouseAssignment.organization_id == organization_id,
                OrgStudentHouseAssignment.status
                == OrgStudentHouseAssignment.STATUS_ACTIVE,
                OrgStudentHouse.organization_id == organization_id,
                OrgStudentHouse.is_active.is_(True),
            )
            .order_by(
                OrgStudentHouseAssignment.academic_year.desc(),
                OrgStudentHouseAssignment.id.desc(),
            )
            .first()
        )

    @staticmethod
    def get_house_points(
        db: Session,
        organization_id: int,
        academic_year: str,
    ) -> dict[int, int]:
        active_house_ids = (
            db.query(OrgStudentHouse.id)
            .filter(
                OrgStudentHouse.organization_id == organization_id,
                OrgStudentHouse.academic_year == academic_year,
                OrgStudentHouse.is_active.is_(True),
            )
            .all()
        )
        points_by_house = {int(row.id): 0 for row in active_house_ids}
        rows = (
            db.query(
                OrgStudentHouseAssignment.house_id,
                func.coalesce(func.sum(OrgStudentBehaviorPointLog.points), 0),
            )
            .outerjoin(
                OrgStudentBehaviorPointLog,
                OrgStudentBehaviorPointLog.student_id
                == OrgStudentHouseAssignment.student_id,
            )
            .filter(
                OrgStudentHouseAssignment.organization_id == organization_id,
                OrgStudentHouseAssignment.academic_year == academic_year,
                OrgStudentHouseAssignment.status
                == OrgStudentHouseAssignment.STATUS_ACTIVE,
            )
            .group_by(OrgStudentHouseAssignment.house_id)
            .all()
        )
        points_by_house.update(
            {int(house_id): int(points or 0) for house_id, points in rows}
        )
        return points_by_house

    @staticmethod
    def get_student_points(db: Session, student_id: int) -> int:
        value = (
            db.query(
                func.coalesce(func.sum(OrgStudentBehaviorPointLog.points), 0)
            )
            .filter(OrgStudentBehaviorPointLog.student_id == student_id)
            .scalar()
        )
        return int(value or 0)

    @staticmethod
    def count_active_houses(
        db: Session,
        organization_id: int,
        academic_year: str,
    ) -> int:
        return (
            db.query(OrgStudentHouse)
            .filter(
                OrgStudentHouse.organization_id == organization_id,
                OrgStudentHouse.academic_year == academic_year,
                OrgStudentHouse.is_active.is_(True),
            )
            .count()
        )

    @staticmethod
    def list_active_groups(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> list[tuple]:
        member_counts = (
            db.query(
                OrgStudentGroupAssignment.group_id.label("group_id"),
                func.count(OrgStudentGroupAssignment.id).label("member_count"),
            )
            .filter(
                OrgStudentGroupAssignment.organization_id == organization_id,
                OrgStudentGroupAssignment.status
                == OrgStudentGroupAssignment.STATUS_ACTIVE,
            )
            .group_by(OrgStudentGroupAssignment.group_id)
            .subquery()
        )
        return (
            db.query(
                OrgStudentGroupAssignment,
                OrgStudentGroup,
                func.coalesce(member_counts.c.member_count, 0),
            )
            .join(
                OrgStudentGroup,
                OrgStudentGroup.id == OrgStudentGroupAssignment.group_id,
            )
            .outerjoin(
                member_counts,
                member_counts.c.group_id == OrgStudentGroup.id,
            )
            .filter(
                OrgStudentGroupAssignment.student_id == student_id,
                OrgStudentGroupAssignment.organization_id == organization_id,
                OrgStudentGroupAssignment.status
                == OrgStudentGroupAssignment.STATUS_ACTIVE,
                OrgStudentGroup.organization_id == organization_id,
                OrgStudentGroup.is_active.is_(True),
            )
            .order_by(OrgStudentGroup.name.asc())
            .all()
        )

    @staticmethod
    def list_leave_requests(
        db: Session,
        student_id: int,
        organization_id: int,
        status: int | None,
        page: int,
        page_size: int,
    ) -> dict:
        query = db.query(OrgStudentLeaveRequest).filter(
            OrgStudentLeaveRequest.student_id == student_id,
            OrgStudentLeaveRequest.organization_id == organization_id,
        )
        if status is not None:
            query = query.filter(OrgStudentLeaveRequest.status == status)

        total_items = query.count()
        leaves = (
            query.order_by(
                OrgStudentLeaveRequest.requested_at.desc(),
                OrgStudentLeaveRequest.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"leaves": leaves, "total_items": total_items}

    @staticmethod
    def has_overlapping_leave_request(
        db: Session,
        student_id: int,
        organization_id: int,
        start_date: date,
        end_date: date,
    ) -> bool:
        return (
            db.query(OrgStudentLeaveRequest.id)
            .filter(
                OrgStudentLeaveRequest.student_id == student_id,
                OrgStudentLeaveRequest.organization_id == organization_id,
                OrgStudentLeaveRequest.status.in_((1, 2)),
                OrgStudentLeaveRequest.start_date <= end_date,
                OrgStudentLeaveRequest.end_date >= start_date,
            )
            .first()
            is not None
        )

    @staticmethod
    def create_leave_request(
        db: Session,
        organization_id: int,
        student_id: int,
        start_date: date,
        end_date: date,
        leave_type: int,
        reason: str,
        attachments: list,
        duration: int,
        requested_by_id: int,
    ) -> OrgStudentLeaveRequest:
        leave = OrgStudentLeaveRequest(
            organization_id=organization_id,
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            reason=reason,
            attachments=attachments,
            status=OrgStudentLeaveRequest.STATUS_PENDING,
            duration=duration,
            requested_by_id=requested_by_id,
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return leave

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
