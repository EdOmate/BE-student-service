from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from core.database import Base

class LMSAssignment(Base):
    __tablename__ = 'org_lms_assignments'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(BigInteger)
    academic_year = Column(String(20))
    section_ids = Column(JSON, default=list)
    subject_id = Column(BigInteger)
    teacher_id = Column(BigInteger)
    title = Column(String(255))
    description = Column(Text)
    grading_mode = Column(Integer)
    max_marks = Column(Numeric(8, 2))
    deadline_type = Column(Integer)
    due_at = Column(DateTime)
    attachments = Column(JSON, default=list)
    status = Column(Integer)
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class LMSAssignmentSubmission(Base):
    __tablename__ = 'org_lms_assignment_submissions'
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id'),)
    id = Column(BigInteger, primary_key=True)
    assignment_id = Column(BigInteger, ForeignKey('org_lms_assignments.id', ondelete='CASCADE'))
    student_id = Column(BigInteger, index=True)
    submission_status = Column(Integer)
    submitted_at = Column(DateTime)
    remarks = Column(Text)
    files = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())

class LMSAssignmentEvaluation(Base):
    __tablename__ = 'org_lms_assignment_evaluations'
    id = Column(BigInteger, primary_key=True)
    submission_id = Column(BigInteger, ForeignKey('org_lms_assignment_submissions.id', ondelete='CASCADE'), unique=True)
    marks = Column(Numeric(8, 2))
    feedback = Column(Text)
    evaluated_by_id = Column(BigInteger)
    evaluated_at = Column(DateTime)

class StudyMaterial(Base):
    __tablename__ = 'org_lms_study_materials'
    id = Column(BigInteger, primary_key=True)
    section_id = Column(Integer, index=True)
    subject_id = Column(Integer)
    material_type = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    attachments = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    publish_at = Column(DateTime)
    expires_at = Column(DateTime)
    status = Column(Integer)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
