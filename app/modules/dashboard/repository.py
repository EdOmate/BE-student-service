import json
from datetime import date

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.academics.models import SchoolStudentSectionMapping
from app.modules.exams.models import (
    ExamGradeRule,
    ExamPaper,
    ExamResult,
    ExamSection,
    ExamSeries,
)
from app.modules.fees.models import OrgStudentFeeInstallment
from app.modules.lms.models import LMSAssignment, LMSAssignmentSubmission
from app.modules.students.models import OrgClassStudentAttendance


class DashboardRepository:
    @staticmethod
    def get_active_section_id(db: Session, student_id: int):
        mapping = (
            db.query(SchoolStudentSectionMapping)
            .filter(
                SchoolStudentSectionMapping.student_id == student_id,
                SchoolStudentSectionMapping.status == "Active",
            )
            .order_by(SchoolStudentSectionMapping.id.desc())
            .first()
        )
        return mapping.section_id if mapping else None

    @staticmethod
    def get_today_attendance(db: Session, student_id: int, today: date):
        return (
            db.query(OrgClassStudentAttendance)
            .filter(
                OrgClassStudentAttendance.student_id == student_id,
                OrgClassStudentAttendance.date == today,
            )
            .order_by(OrgClassStudentAttendance.id.desc())
            .first()
        )

    @staticmethod
    def get_pending_homework(db: Session, student_id: int, section_id: int | None):
        if section_id is None:
            return 0, None

        pending_filter = or_(
            LMSAssignmentSubmission.id.is_(None),
        )
        query = (
            db.query(LMSAssignment)
            .outerjoin(
                LMSAssignmentSubmission,
                and_(
                    LMSAssignmentSubmission.assignment_id == LMSAssignment.id,
                    LMSAssignmentSubmission.student_id == student_id,
                ),
            )
            .filter(
                LMSAssignment.status == 2,
                func.json_contains(
                    LMSAssignment.section_ids,
                    json.dumps(section_id),
                )
                == 1,
                pending_filter,
            )
        )
        count = query.count()
        earliest = query.order_by(
            LMSAssignment.due_at.is_(None),
            LMSAssignment.due_at.asc(),
            LMSAssignment.id.asc(),
        ).first()
        return count, earliest

    @staticmethod
    def get_latest_result(db: Session, student_id: int, organization_id: int):
        latest = (
            db.query(ExamSeries.id, ExamSeries.title, ExamResult.published_at)
            .join(ExamSection, ExamSection.exam_id == ExamSeries.id)
            .join(ExamPaper, ExamPaper.section_id == ExamSection.id)
            .join(ExamResult, ExamResult.exam_paper_id == ExamPaper.id)
            .filter(
                ExamResult.student_id == student_id,
                ExamResult.result_status == 2,
            )
            .order_by(ExamResult.published_at.desc(), ExamResult.id.desc())
            .first()
        )
        if not latest:
            return None

        totals = (
            db.query(
                ExamResult.student_id,
                func.sum(ExamResult.obtained_marks).label("obtained"),
                func.sum(ExamPaper.max_marks).label("maximum"),
            )
            .join(ExamPaper, ExamPaper.id == ExamResult.exam_paper_id)
            .join(ExamSection, ExamSection.id == ExamPaper.section_id)
            .filter(
                ExamSection.exam_id == latest.id,
                ExamResult.result_status == 2,
            )
            .group_by(ExamResult.student_id)
            .all()
        )
        ranked = []
        for row in totals:
            maximum = float(row.maximum or 0)
            percentage = float(row.obtained or 0) * 100 / maximum if maximum else 0
            ranked.append((row.student_id, percentage))
        ranked.sort(key=lambda item: item[1], reverse=True)
        own_percentage = next(
            (percentage for sid, percentage in ranked if sid == student_id),
            0,
        )
        rank = next(
            (index for index, item in enumerate(ranked, 1) if item[0] == student_id),
            None,
        )
        grade_rule = (
            db.query(ExamGradeRule)
            .filter(
                ExamGradeRule.organization_id == organization_id,
                ExamGradeRule.is_active.is_(True),
                ExamGradeRule.min_percentage <= own_percentage,
                ExamGradeRule.max_percentage >= own_percentage,
            )
            .order_by(ExamGradeRule.min_percentage.desc())
            .first()
        )
        return {
            "exam_id": latest.id,
            "exam_title": latest.title,
            "published_at": latest.published_at,
            "percentage": round(own_percentage, 2),
            "rank": rank,
            "participants": len(ranked),
            "grade": grade_rule.grade_name if grade_rule else None,
        }

    @staticmethod
    def get_fee_status(db: Session, student_id: int):
        try:
            installments = (
                db.query(OrgStudentFeeInstallment)
                .filter(
                    OrgStudentFeeInstallment.student_id == student_id,
                    OrgStudentFeeInstallment.balance_amount > 0,
                    OrgStudentFeeInstallment.status.in_((1, 2)),
                )
                .order_by(
                    OrgStudentFeeInstallment.due_date.asc(),
                    OrgStudentFeeInstallment.id.asc(),
                )
                .all()
            )
        except SQLAlchemyError:
            db.rollback()
            return None

        return {
            "due_amount": sum(float(item.balance_amount or 0) for item in installments),
            "due_date": installments[0].due_date if installments else None,
            "installment_count": len(installments),
        }
