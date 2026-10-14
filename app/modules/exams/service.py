"""Business logic for student exam APIs and summaries."""

from datetime import datetime
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.academics.models import OrgSchoolClass, OrgSchoolSection
from app.modules.exams.models import (
    ExamAttendance,
    ExamPaper,
    ExamResult,
    ExamSchedule,
    ExamSection,
    ExamSeries,
    ExamStudentRegistration,
)
from app.modules.exams.repository import ExamRepository
from app.modules.students.repository import StudentRepository


IST = ZoneInfo("Asia/Kolkata")


class ExamService:
    @staticmethod
    def list_report_cards(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        rows, total_items = ExamRepository.list_student_report_cards(
            db, student_id, organization_id, page, page_size
        )
        type_labels = dict(ExamSeries.EXAM_TYPE_CHOICES)
        results = []
        for report_card, exam in rows:
            results.append(
                {
                    "id": report_card.id,
                    "exam": {
                        "id": exam.id,
                        "title": exam.title,
                        "exam_type": exam.exam_type,
                        "exam_type_label": type_labels.get(exam.exam_type),
                        "academic_year": exam.academic_year,
                    },
                    "total_marks": float(report_card.total_marks)
                    if report_card.total_marks is not None
                    else None,
                    "obtained_marks": float(report_card.obtained_marks)
                    if report_card.obtained_marks is not None
                    else None,
                    "percentage": float(report_card.percentage)
                    if report_card.percentage is not None
                    else None,
                    "grade": report_card.grade,
                    "result_status": report_card.result_status,
                    "file_url": report_card.pdf_file,
                    "file_size": report_card.file_size,
                    "checksum": report_card.checksum,
                    "version": report_card.version,
                    "generated_at": report_card.generated_at.isoformat()
                    if report_card.generated_at
                    else None,
                    "published_at": report_card.published_at.isoformat()
                    if report_card.published_at
                    else None,
                }
            )
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1 and total_pages > 0,
            },
        }

    @staticmethod
    def get_exam_results(
        db: Session,
        exam_id: int,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        detail = ExamRepository.get_student_exam_detail(
            db, exam_id, student_id, organization_id
        )
        if not detail:
            return None

        exam, _, _ = detail["header"]
        results_by_paper = {
            result.exam_paper_id: result for result in detail["results"]
        }
        papers = []
        for paper in detail["papers"]:
            result = results_by_paper.get(paper.id)
            papers.append(
                {
                    "id": paper.id,
                    "subject_name": paper.subject_name,
                    "paper_code": paper.paper_code,
                    "max_marks": float(paper.max_marks),
                    "passing_marks": float(paper.passing_marks),
                    "result": (
                        {
                            "obtained_marks": float(result.obtained_marks),
                            "grade": result.grade,
                            "remarks": result.remarks,
                            "published_at": result.published_at.isoformat()
                            if result.published_at
                            else None,
                        }
                        if result
                        else None
                    ),
                }
            )

        report_card = detail["report_card"]
        published_results = [paper for paper in papers if paper["result"]]
        obtained_marks = sum(
            paper["result"]["obtained_marks"] for paper in published_results
        )
        total_marks = sum(paper["max_marks"] for paper in published_results)
        percentage = obtained_marks * 100 / total_marks if total_marks else None
        return {
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "exam_type": exam.exam_type,
                "exam_type_label": dict(ExamSeries.EXAM_TYPE_CHOICES).get(
                    exam.exam_type
                ),
                "academic_year": exam.academic_year,
            },
            "has_results": bool(published_results or report_card),
            "summary": {
                "total_marks": (
                    float(report_card.total_marks)
                    if report_card and report_card.total_marks is not None
                    else total_marks
                ),
                "obtained_marks": (
                    float(report_card.obtained_marks)
                    if report_card and report_card.obtained_marks is not None
                    else obtained_marks
                ),
                "percentage": (
                    float(report_card.percentage)
                    if report_card and report_card.percentage is not None
                    else round(percentage, 2) if percentage is not None else None
                ),
                "grade": report_card.grade if report_card else None,
                "result_status": report_card.result_status if report_card else None,
                "published_at": (
                    report_card.published_at.isoformat()
                    if report_card and report_card.published_at
                    else None
                ),
                "pdf_url": report_card.pdf_file if report_card else None,
            },
            "papers": papers,
        }

    @staticmethod
    def get_exam_detail(
        db: Session,
        exam_id: int,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        detail = ExamRepository.get_student_exam_detail(
            db, exam_id, student_id, organization_id
        )
        if not detail:
            return None

        exam, exam_section, registration = detail["header"]
        type_labels = dict(ExamSeries.EXAM_TYPE_CHOICES)
        status_labels = dict(ExamSeries.STATUS_CHOICES)
        section_status_labels = dict(ExamSection.SECTION_STATUS_CHOICES)
        registration_labels = dict(ExamStudentRegistration.REGISTRATION_STATUS_CHOICES)
        paper_status_labels = dict(ExamPaper.PAPER_STATUS_CHOICES)
        schedule_status_labels = dict(ExamSchedule.SCHEDULE_STATUS_CHOICES)
        attendance_labels = dict(ExamAttendance.ATTENDANCE_STATUS_CHOICES)
        result_status_labels = dict(ExamResult.RESULT_STATUS_CHOICES)
        schedules_by_paper = {}
        for schedule in detail["schedules"]:
            schedules_by_paper.setdefault(schedule.exam_paper_id, []).append(schedule)
        attendance_by_paper = {
            item.exam_paper_id: item for item in detail["attendance"]
        }
        results_by_paper = {item.exam_paper_id: item for item in detail["results"]}

        papers = []
        for paper in detail["papers"]:
            attendance = attendance_by_paper.get(paper.id)
            result = results_by_paper.get(paper.id)
            papers.append(
                {
                    "id": paper.id,
                    "subject_mapping_id": paper.subject_mapping_id,
                    "subject_name": paper.subject_name,
                    "paper_code": paper.paper_code,
                    "description": paper.description,
                    "max_marks": float(paper.max_marks),
                    "passing_marks": float(paper.passing_marks),
                    "status": paper.status,
                    "status_label": paper_status_labels.get(paper.status),
                    "schedules": [
                        {
                            "id": schedule.id,
                            "exam_date": schedule.exam_date.isoformat(),
                            "start_time": schedule.start_time.isoformat() if schedule.start_time else None,
                            "end_time": schedule.end_time.isoformat() if schedule.end_time else None,
                            "room_number": schedule.room_number,
                            "status": schedule.status,
                            "status_label": schedule_status_labels.get(schedule.status),
                            "remarks": schedule.remarks,
                        }
                        for schedule in schedules_by_paper.get(paper.id, [])
                    ],
                    "attendance": (
                        {
                            "status": attendance.status,
                            "status_label": attendance_labels.get(attendance.status),
                            "checked_in_at": attendance.checked_in_at.isoformat() if attendance.checked_in_at else None,
                            "remarks": attendance.remarks,
                        }
                        if attendance
                        else None
                    ),
                    "result": (
                        {
                            "obtained_marks": float(result.obtained_marks),
                            "grade": result.grade,
                            "remarks": result.remarks,
                            "status": result.result_status,
                            "status_label": result_status_labels.get(result.result_status),
                            "published_at": result.published_at.isoformat() if result.published_at else None,
                        }
                        if result
                        else None
                    ),
                }
            )

        report_card = detail["report_card"]
        return {
            "id": exam.id,
            "title": exam.title,
            "exam_type": exam.exam_type,
            "exam_type_label": type_labels.get(exam.exam_type),
            "description": exam.description,
            "academic_year": exam.academic_year,
            "start_date": exam.start_date.isoformat() if exam.start_date else None,
            "end_date": exam.end_date.isoformat() if exam.end_date else None,
            "status": exam.status,
            "status_label": status_labels.get(exam.status),
            "created_at": exam.created_at.isoformat(),
            "section": {
                "id": exam_section.id,
                "school_section_id": exam_section.section_id,
                "title": exam_section.title,
                "instructions": exam_section.instructions,
                "remarks": exam_section.remarks,
                "status": exam_section.status,
                "status_label": section_status_labels.get(exam_section.status),
            },
            "registration": {
                "id": registration.id,
                "status": registration.registration_status,
                "status_label": registration_labels.get(registration.registration_status),
                "roll_number": registration.roll_number,
                "seat_number": registration.seat_number,
                "admit_card_url": registration.admit_card_url,
                "remarks": registration.remarks,
            },
            "paper_count": len(papers),
            "scheduled_paper_count": sum(
                1 for paper in papers if paper["schedules"]
            ),
            "next_exam_date": min(
                (
                    schedule["exam_date"]
                    for paper in papers
                    for schedule in paper["schedules"]
                    if schedule["exam_date"] >= datetime.now(IST).date().isoformat()
                ),
                default=None,
            ),
            "last_exam_date": max(
                (
                    schedule["exam_date"]
                    for paper in papers
                    for schedule in paper["schedules"]
                ),
                default=None,
            ),
            "papers": papers,
            "has_results": bool(detail["results"] or report_card),
            "report_card": (
                {
                    "id": report_card.id,
                    "total_marks": float(report_card.total_marks) if report_card.total_marks is not None else None,
                    "obtained_marks": float(report_card.obtained_marks) if report_card.obtained_marks is not None else None,
                    "percentage": float(report_card.percentage) if report_card.percentage is not None else None,
                    "grade": report_card.grade,
                    "result_status": report_card.result_status,
                    "result_snapshot": report_card.result_snapshot,
                    "pdf_url": report_card.pdf_file,
                    "published_at": report_card.published_at.isoformat() if report_card.published_at else None,
                }
                if report_card
                else None
            ),
        }

    @staticmethod
    def list_exam_series(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        today = datetime.now(IST).date()
        rows, total_items = ExamRepository.list_student_exam_series(
            db,
            student_id,
            organization_id,
            page,
            page_size,
        )
        results = ExamService._serialize_exam_series(db, rows, today)
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1 and total_pages > 0,
            },
        }

    @staticmethod
    def list_upcoming_exam_series(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> list[dict]:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not ExamService._valid_mapping(mapping, organization_id):
            return []

        org_class = mapping.section.org_class
        today = datetime.now(IST).date()
        rows = ExamRepository.list_upcoming_exam_series(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
            today=today,
        )
        return ExamService._serialize_exam_series(db, rows, today)

    @staticmethod
    def _serialize_exam_series(db: Session, rows: list, today) -> list[dict]:
        type_labels = dict(ExamSeries.EXAM_TYPE_CHOICES)
        status_labels = dict(ExamSeries.STATUS_CHOICES)
        registration_labels = dict(ExamStudentRegistration.REGISTRATION_STATUS_CHOICES)
        results = []
        for exam, exam_section, registration in rows:
            schedule = ExamRepository.get_exam_series_schedule_summary(
                db,
                exam_section.id,
                exam_section.section_id,
                today,
            )
            results.append(
                {
                    "id": exam.id,
                    "title": exam.title,
                    "exam_type": exam.exam_type,
                    "exam_type_label": type_labels.get(exam.exam_type, "Other"),
                    "description": exam.description,
                    "academic_year": exam.academic_year,
                    "created_at": exam.created_at.isoformat(),
                    "start_date": exam.start_date.isoformat() if exam.start_date else None,
                    "end_date": exam.end_date.isoformat() if exam.end_date else None,
                    "status": exam.status,
                    "status_label": status_labels.get(exam.status, "Scheduled"),
                    "section": {
                        "id": exam_section.id,
                        "title": exam_section.title,
                        "instructions": exam_section.instructions,
                    },
                    "registration": {
                        "status": registration.registration_status,
                        "status_label": registration_labels.get(
                            registration.registration_status, "Registered"
                        ),
                        "roll_number": registration.roll_number,
                        "seat_number": registration.seat_number,
                        "admit_card_url": registration.admit_card_url,
                    },
                    "paper_count": schedule["paper_count"],
                    "scheduled_paper_count": schedule["scheduled_paper_count"],
                    "next_exam_date": (
                        schedule["next_exam_date"].isoformat()
                        if schedule["next_exam_date"]
                        else None
                    ),
                    "last_exam_date": (
                        schedule["last_exam_date"].isoformat()
                        if schedule["last_exam_date"]
                        else None
                    ),
                }
            )
        return results

    @staticmethod
    def get_latest_result_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not ExamService._valid_mapping(mapping, organization_id):
            return None
        org_class = mapping.section.org_class
        return ExamRepository.get_latest_result(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )

    @staticmethod
    def get_upcoming_exam_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not ExamService._valid_mapping(mapping, organization_id):
            return None
        org_class = mapping.section.org_class
        row = ExamRepository.get_upcoming_exam(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
            today=datetime.now(IST).date(),
        )
        if not row:
            return None
        schedule, paper, exam = row
        return {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_paper_id": paper.id,
            "subject_name": paper.subject_name,
            "exam_date": schedule.exam_date,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "room_number": schedule.room_number,
        }

    @staticmethod
    def _valid_mapping(mapping, organization_id: int) -> bool:
        if not mapping or not mapping.section:
            return False
        section: OrgSchoolSection = mapping.section
        org_class: OrgSchoolClass | None = section.org_class
        return bool(
            section.is_active
            and org_class
            and org_class.is_active
            and org_class.organization_id == organization_id
        )
