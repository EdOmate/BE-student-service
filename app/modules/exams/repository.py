"""Database access for student exam operations."""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.exams.models import (
    ExamGradeRule,
    ExamPaper,
    ExamReportCard,
    ExamResult,
    ExamResultPublishLog,
    ExamSchedule,
    ExamSection,
    ExamSeries,
    ExamStudentRegistration,
)


class ExamRepository:
    @staticmethod
    def get_latest_result(
        db: Session,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
    ) -> dict | None:
        latest_query = (
            db.query(
                ExamSeries.id,
                ExamSeries.title,
                ExamResult.published_at,
                ExamGradeRule.grading_scale_id,
            )
            .join(ExamSection, ExamSection.exam_id == ExamSeries.id)
            .join(ExamPaper, ExamPaper.section_id == ExamSection.id)
            .join(ExamResult, ExamResult.exam_paper_id == ExamPaper.id)
            .join(
                ExamResultPublishLog,
                (ExamResultPublishLog.exam_id == ExamSeries.id)
                & (ExamResultPublishLog.section_id == ExamSection.section_id),
            )
            .outerjoin(ExamGradeRule, ExamGradeRule.id == ExamResult.grade_rule_id)
            .filter(
                ExamSeries.organization_id == organization_id,
                ExamSeries.is_active.is_(True),
                ExamSeries.status == ExamSeries.STATUS_PUBLISHED,
                ExamSection.section_id == section_id,
                ExamSection.status.in_(
                    (ExamSection.STATUS_PUBLISHED, ExamSection.STATUS_COMPLETED)
                ),
                ExamPaper.status != ExamPaper.STATUS_CANCELLED,
                ExamResult.student_id == student_id,
                ExamResult.result_status == ExamResult.STATUS_PUBLISHED,
            )
        )
        if academic_year:
            latest_query = latest_query.filter(
                ExamSeries.academic_year == academic_year
            )
        latest = latest_query.order_by(
            ExamResult.published_at.desc(),
            ExamResultPublishLog.published_at.desc(),
            ExamResult.id.desc(),
        ).first()
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
            .join(
                ExamStudentRegistration,
                (ExamStudentRegistration.exam_section_id == ExamSection.id)
                & (ExamStudentRegistration.student_id == ExamResult.student_id),
            )
            .filter(
                ExamSection.exam_id == latest.id,
                ExamSection.section_id == section_id,
                ExamPaper.status != ExamPaper.STATUS_CANCELLED,
                ExamResult.result_status == ExamResult.STATUS_PUBLISHED,
                ExamStudentRegistration.registration_status
                != ExamStudentRegistration.STATUS_CANCELLED,
            )
            .group_by(ExamResult.student_id)
            .all()
        )
        ranked = []
        for row in totals:
            maximum = float(row.maximum or 0)
            percentage = (
                float(row.obtained or 0) * 100 / maximum if maximum else 0
            )
            ranked.append((row.student_id, percentage))
        ranked.sort(key=lambda item: item[1], reverse=True)
        percentage = next(
            (value for sid, value in ranked if sid == student_id),
            0,
        )
        rank = next(
            (index for index, item in enumerate(ranked, 1) if item[0] == student_id),
            None,
        )
        report_card = (
            db.query(ExamReportCard)
            .filter(
                ExamReportCard.exam_id == latest.id,
                ExamReportCard.student_id == student_id,
                ExamReportCard.is_active.is_(True),
                ExamReportCard.status.in_(
                    (
                        ExamReportCard.Status.GENERATED,
                        ExamReportCard.Status.PUBLISHED,
                    )
                ),
            )
            .order_by(ExamReportCard.version.desc(), ExamReportCard.id.desc())
            .first()
        )
        grade = report_card.grade if report_card else None
        if report_card and report_card.percentage is not None:
            percentage = float(report_card.percentage)
        if not grade and latest.grading_scale_id:
            grade_rule = (
                db.query(ExamGradeRule)
                .filter(
                    ExamGradeRule.organization_id == organization_id,
                    ExamGradeRule.grading_scale_id == latest.grading_scale_id,
                    ExamGradeRule.is_active.is_(True),
                    ExamGradeRule.min_percentage <= percentage,
                    ExamGradeRule.max_percentage >= percentage,
                )
                .order_by(ExamGradeRule.min_percentage.desc())
                .first()
            )
            grade = grade_rule.grade_name if grade_rule else None
        return {
            "exam_id": latest.id,
            "exam_title": latest.title,
            "published_at": latest.published_at,
            "percentage": round(percentage, 2),
            "rank": rank,
            "participants": len(ranked),
            "grade": grade,
        }

    @staticmethod
    def get_upcoming_exam(
        db: Session,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
        today: date,
    ):
        query = (
            db.query(ExamSchedule, ExamPaper, ExamSeries)
            .join(ExamPaper, ExamPaper.id == ExamSchedule.exam_paper_id)
            .join(ExamSection, ExamSection.id == ExamPaper.section_id)
            .join(ExamSeries, ExamSeries.id == ExamSection.exam_id)
            .join(
                ExamStudentRegistration,
                ExamStudentRegistration.exam_section_id == ExamSection.id,
            )
            .filter(
                ExamSeries.organization_id == organization_id,
                ExamSeries.is_active.is_(True),
                ExamSeries.status.in_(
                    (ExamSeries.STATUS_SCHEDULED, ExamSeries.STATUS_ONGOING)
                ),
                ExamSection.status.in_(
                    (ExamSection.STATUS_SCHEDULED, ExamSection.STATUS_PUBLISHED)
                ),
                ExamPaper.status == ExamPaper.STATUS_SCHEDULED,
                ExamSchedule.section_id == section_id,
                ExamSchedule.status == ExamSchedule.STATUS_PUBLISHED,
                ExamSchedule.exam_date >= today,
                ExamStudentRegistration.student_id == student_id,
                ExamStudentRegistration.registration_status
                != ExamStudentRegistration.STATUS_CANCELLED,
            )
        )
        if academic_year:
            query = query.filter(ExamSeries.academic_year == academic_year)
        return query.order_by(
            ExamSchedule.exam_date.asc(),
            ExamSchedule.start_time.asc(),
            ExamSchedule.id.asc(),
        ).first()
