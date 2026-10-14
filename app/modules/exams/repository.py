"""Database access for student exam operations."""

from datetime import date

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.modules.exams.models import (
    ExamAttendance,
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
    def list_student_report_cards(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list, int]:
        query = (
            db.query(ExamReportCard, ExamSeries)
            .join(ExamSeries, ExamSeries.id == ExamReportCard.exam_id)
            .filter(
                ExamReportCard.student_id == student_id,
                ExamReportCard.is_active.is_(True),
                ExamReportCard.status == ExamReportCard.Status.PUBLISHED,
                ExamSeries.organization_id == organization_id,
                ExamSeries.is_active.is_(True),
                ExamSeries.status != ExamSeries.STATUS_CANCELLED,
            )
        )
        total_items = query.count()
        rows = (
            query.order_by(
                ExamReportCard.published_at.desc(),
                ExamReportCard.created_at.desc(),
                ExamReportCard.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total_items

    @staticmethod
    def get_student_exam_detail(
        db: Session,
        exam_id: int,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        header = (
            db.query(ExamSeries, ExamSection, ExamStudentRegistration)
            .join(ExamSection, ExamSection.exam_id == ExamSeries.id)
            .join(
                ExamStudentRegistration,
                ExamStudentRegistration.exam_section_id == ExamSection.id,
            )
            .filter(
                ExamSeries.id == exam_id,
                ExamSeries.organization_id == organization_id,
                ExamSeries.is_active.is_(True),
                ExamSeries.status != ExamSeries.STATUS_CANCELLED,
                ExamSection.status != ExamSection.STATUS_CANCELLED,
                ExamStudentRegistration.student_id == student_id,
                ExamStudentRegistration.registration_status
                != ExamStudentRegistration.STATUS_CANCELLED,
            )
            .first()
        )
        if not header:
            return None

        exam, exam_section, registration = header
        papers = (
            db.query(ExamPaper)
            .filter(
                ExamPaper.section_id == exam_section.id,
                ExamPaper.status != ExamPaper.STATUS_CANCELLED,
            )
            .order_by(ExamPaper.id.asc())
            .all()
        )
        paper_ids = [paper.id for paper in papers]
        schedules = []
        attendance = []
        results = []
        if paper_ids:
            schedules = (
                db.query(ExamSchedule)
                .filter(
                    ExamSchedule.exam_paper_id.in_(paper_ids),
                    ExamSchedule.section_id == exam_section.section_id,
                    ExamSchedule.status != ExamSchedule.STATUS_CANCELLED,
                )
                .order_by(ExamSchedule.exam_date.asc(), ExamSchedule.start_time.asc())
                .all()
            )
            attendance = (
                db.query(ExamAttendance)
                .filter(
                    ExamAttendance.exam_paper_id.in_(paper_ids),
                    ExamAttendance.student_id == student_id,
                )
                .all()
            )
            results = (
                db.query(ExamResult)
                .filter(
                    ExamResult.exam_paper_id.in_(paper_ids),
                    ExamResult.student_id == student_id,
                    ExamResult.result_status == ExamResult.STATUS_PUBLISHED,
                )
                .all()
            )
        report_card = (
            db.query(ExamReportCard)
            .filter(
                ExamReportCard.exam_id == exam_id,
                ExamReportCard.student_id == student_id,
                ExamReportCard.is_active.is_(True),
                ExamReportCard.status == ExamReportCard.Status.PUBLISHED,
            )
            .order_by(ExamReportCard.version.desc())
            .first()
        )
        return {
            "header": header,
            "papers": papers,
            "schedules": schedules,
            "attendance": attendance,
            "results": results,
            "report_card": report_card,
        }

    @staticmethod
    def list_student_exam_series(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list, int]:
        query = (
            db.query(ExamSeries, ExamSection, ExamStudentRegistration)
            .join(ExamSection, ExamSection.exam_id == ExamSeries.id)
            .join(
                ExamStudentRegistration,
                ExamStudentRegistration.exam_section_id == ExamSection.id,
            )
            .filter(
                ExamSeries.organization_id == organization_id,
                ExamSeries.is_active.is_(True),
                ExamSeries.status != ExamSeries.STATUS_CANCELLED,
                ExamSection.status != ExamSection.STATUS_CANCELLED,
                ExamStudentRegistration.student_id == student_id,
                ExamStudentRegistration.registration_status
                != ExamStudentRegistration.STATUS_CANCELLED,
            )
        )
        total_items = query.count()
        rows = (
            query.order_by(ExamSeries.created_at.desc(), ExamSeries.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total_items

    @staticmethod
    def list_upcoming_exam_series(
        db: Session,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
        today: date,
    ) -> list:
        query = (
            db.query(ExamSeries, ExamSection, ExamStudentRegistration)
            .join(ExamSection, ExamSection.exam_id == ExamSeries.id)
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
                or_(ExamSeries.end_date.is_(None), ExamSeries.end_date >= today),
                ExamSection.section_id == section_id,
                ExamSection.status.in_(
                    (ExamSection.STATUS_SCHEDULED, ExamSection.STATUS_PUBLISHED)
                ),
                ExamStudentRegistration.student_id == student_id,
                ExamStudentRegistration.registration_status
                != ExamStudentRegistration.STATUS_CANCELLED,
            )
        )
        if academic_year:
            query = query.filter(ExamSeries.academic_year == academic_year)
        return (
            query.order_by(
                ExamSeries.start_date.asc(),
                ExamSeries.id.asc(),
            )
            .all()
        )

    @staticmethod
    def get_exam_series_schedule_summary(
        db: Session,
        exam_section_id: int,
        section_id: int,
        today: date,
    ) -> dict:
        paper_count = (
            db.query(func.count(ExamPaper.id))
            .filter(
                ExamPaper.section_id == exam_section_id,
                ExamPaper.status != ExamPaper.STATUS_CANCELLED,
            )
            .scalar()
            or 0
        )
        schedule = (
            db.query(
                func.count(ExamSchedule.id).label("scheduled_count"),
                func.min(
                    case(
                        (ExamSchedule.exam_date >= today, ExamSchedule.exam_date),
                        else_=None,
                    )
                ).label("next_date"),
                func.max(ExamSchedule.exam_date).label("last_date"),
            )
            .join(ExamPaper, ExamPaper.id == ExamSchedule.exam_paper_id)
            .filter(
                ExamPaper.section_id == exam_section_id,
                ExamPaper.status != ExamPaper.STATUS_CANCELLED,
                ExamSchedule.section_id == section_id,
                ExamSchedule.status.in_(
                    (ExamSchedule.STATUS_SCHEDULED, ExamSchedule.STATUS_PUBLISHED)
                ),
            )
            .first()
        )
        return {
            "paper_count": int(paper_count),
            "scheduled_paper_count": int(schedule.scheduled_count or 0),
            "next_exam_date": schedule.next_date,
            "last_exam_date": schedule.last_date,
        }

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
