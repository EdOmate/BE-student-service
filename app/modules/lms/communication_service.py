"""Assignment communication and activity operations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.lms.models import (
    LMSAssignmentActivityLog,
    LMSAssignmentComment,
    LMSSubmissionMessage,
    LMSSubmissionThread,
)
from app.modules.lms.repository import LMSRepository
from app.modules.students.repository import StudentRepository
from core.storage import S3StorageService


IST = ZoneInfo("Asia/Kolkata")


class AssignmentCommunicationService:
    @staticmethod
    def _assignment_data(db, assignment_id, student_id, organization_id):
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section:
            return None
        org_class = mapping.section.org_class
        return LMSRepository.get_student_assignment_detail(
            db=db,
            assignment_id=assignment_id,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )

    @staticmethod
    def get_thread(db, assignment_id, student_id, organization_id):
        data = AssignmentCommunicationService._assignment_data(
            db, assignment_id, student_id, organization_id
        )
        if not data:
            return "not_found", None
        if not data["submission_rows"]:
            return "submission_required", None
        submission = data["submission_rows"][0][0]
        thread = (
            db.query(LMSSubmissionThread)
            .filter(LMSSubmissionThread.submission_id == submission.id)
            .first()
        )
        messages = []
        if thread:
            messages = (
                db.query(LMSSubmissionMessage)
                .filter(LMSSubmissionMessage.thread_id == thread.id)
                .order_by(LMSSubmissionMessage.created_at, LMSSubmissionMessage.id)
                .all()
            )
        return "ok", {
            "assignment_id": assignment_id,
            "submission_id": submission.id,
            "thread_id": thread.id if thread else None,
            "messages": [
                AssignmentCommunicationService._serialize_message(message)
                for message in messages
            ],
        }

    @staticmethod
    def create_message(
        db,
        assignment_id,
        student_id,
        organization_id,
        role,
        parent_id,
        message_text,
        attachment_url,
    ):
        result, thread_data = AssignmentCommunicationService.get_thread(
            db, assignment_id, student_id, organization_id
        )
        if result != "ok":
            return result, None
        thread_id = thread_data["thread_id"]
        if thread_id is None:
            thread = LMSSubmissionThread(
                submission_id=thread_data["submission_id"]
            )
            db.add(thread)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                thread = (
                    db.query(LMSSubmissionThread)
                    .filter(
                        LMSSubmissionThread.submission_id
                        == thread_data["submission_id"]
                    )
                    .first()
                )
            thread_id = thread.id
        message = LMSSubmissionMessage(
            thread_id=thread_id,
            sender_id=parent_id if role == "parent" else student_id,
            sender_type=(
                LMSSubmissionMessage.SENDER_PARENT
                if role == "parent"
                else LMSSubmissionMessage.SENDER_STUDENT
            ),
            message=message_text,
            attachment_url=attachment_url,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return "created", AssignmentCommunicationService._serialize_message(
            message
        )

    @staticmethod
    def list_comments(db, assignment_id, student_id, organization_id):
        data = AssignmentCommunicationService._assignment_data(
            db, assignment_id, student_id, organization_id
        )
        if not data:
            return None
        comments = (
            db.query(LMSAssignmentComment)
            .filter(LMSAssignmentComment.assignment_id == assignment_id)
            .order_by(LMSAssignmentComment.created_at, LMSAssignmentComment.id)
            .all()
        )
        return [AssignmentCommunicationService._serialize_comment(item) for item in comments]

    @staticmethod
    def create_comment(
        db,
        assignment_id,
        student_id,
        organization_id,
        role,
        parent_id,
        message,
        parent_comment_id,
    ):
        data = AssignmentCommunicationService._assignment_data(
            db, assignment_id, student_id, organization_id
        )
        if not data:
            return "not_found", None
        if parent_comment_id:
            parent = (
                db.query(LMSAssignmentComment.id)
                .filter(
                    LMSAssignmentComment.id == parent_comment_id,
                    LMSAssignmentComment.assignment_id == assignment_id,
                )
                .first()
            )
            if not parent:
                return "invalid_parent", None
        comment = LMSAssignmentComment(
            assignment_id=assignment_id,
            parent_comment_id=parent_comment_id,
            user_id=parent_id if role == "parent" else student_id,
            message=message,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return "created", AssignmentCommunicationService._serialize_comment(
            comment
        )

    @staticmethod
    def log_activity(db, assignment_id, student_id, activity_type):
        db.add(
            LMSAssignmentActivityLog(
                assignment_id=assignment_id,
                student_id=student_id,
                activity_type=activity_type,
                created_at=datetime.now(IST).replace(tzinfo=None),
            )
        )
        db.commit()

    @staticmethod
    def _serialize_message(message):
        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_type": message.sender_type,
            "message": message.message,
            "attachment_url": (
                S3StorageService.file_url(message.attachment_url)
                if message.attachment_url
                else None
            ),
            "created_at": message.created_at,
        }

    @staticmethod
    def _serialize_comment(comment):
        return {
            "id": comment.id,
            "parent_comment_id": comment.parent_comment_id,
            "user_id": comment.user_id,
            "message": comment.message,
            "created_at": comment.created_at,
        }
