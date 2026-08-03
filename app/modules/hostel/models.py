from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.sql import func
from core.database import Base

class OrgHostel(Base):
    __tablename__ = 'org_hostels'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    name = Column(String(255))
    code = Column(String(50))
    hostel_type = Column(Integer)
    description = Column(Text)
    address = Column(Text)
    contact_number = Column(String(30))
    total_capacity = Column(Integer)
    status = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelRoom(Base):
    __tablename__ = 'org_hostel_rooms'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    floor_id = Column(BigInteger)
    room_no = Column(String(50))
    room_name = Column(String(100))
    room_type = Column(Integer)
    gender_allowed = Column(Integer)
    sharing_capacity = Column(Integer)
    monthly_fee = Column(Numeric(10, 2))
    status = Column(Integer)
    is_active = Column(Boolean, default=True)
    remarks = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelBed(Base):
    __tablename__ = 'org_hostel_beds'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    room_id = Column(BigInteger, ForeignKey('org_hostel_rooms.id', ondelete='CASCADE'))
    bed_no = Column(String(50))
    bed_label = Column(String(100))
    status = Column(Integer)
    is_active = Column(Boolean, default=True)
    remarks = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelStudentAllocation(Base):
    __tablename__ = 'org_hostel_student_allocations'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    allocation_no = Column(String(100))
    student_id = Column(BigInteger, index=True)
    academic_year = Column(String(20))
    bed_id = Column(BigInteger, ForeignKey('org_hostel_beds.id'))
    allocation_type = Column(Integer)
    allocation_date = Column(Date)
    expected_checkout_date = Column(Date)
    actual_checkout_date = Column(Date)
    status = Column(Integer)
    is_current = Column(Boolean, default=True)
    previous_allocation_id = Column(BigInteger)
    allocated_by_id = Column(Integer)
    checkout_by_id = Column(Integer)
    checkout_reason = Column(Text)
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelMessMenu(Base):
    __tablename__ = 'org_hostel_mess_menus'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    plan_id = Column(BigInteger)
    menu_date = Column(Date, index=True)
    day_of_week = Column(Integer)
    meal_type = Column(Integer)
    title = Column(String(255))
    items = Column(JSON, default=list)
    notes = Column(Text)
    calories = Column(Integer)
    status = Column(Integer)
    published_by_id = Column(Integer)
    published_at = Column(DateTime)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelAttendance(Base):
    __tablename__ = 'org_hostel_attendance'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    allocation_id = Column(BigInteger, ForeignKey('org_hostel_student_allocations.id'))
    student_id = Column(BigInteger, index=True)
    academic_year = Column(String(20))
    attendance_date = Column(Date)
    session = Column(Integer)
    status = Column(Integer)
    marked_at = Column(DateTime)
    marked_by_id = Column(Integer)
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelLeaveRequest(Base):
    __tablename__ = 'org_hostel_leave_requests'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    student_id = Column(BigInteger, index=True)
    academic_year = Column(String(20))
    allocation_id = Column(BigInteger, ForeignKey('org_hostel_student_allocations.id'))
    leave_type = Column(Integer)
    day_type = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    destination = Column(String(255))
    guardian_contact = Column(String(30))
    reason = Column(Text)
    status = Column(Integer)
    approved_by_id = Column(Integer)
    approved_at = Column(DateTime)
    rejected_by_id = Column(Integer)
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgHostelComplaint(Base):
    __tablename__ = 'org_hostel_complaints'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    complaint_no = Column(String(100))
    student_id = Column(BigInteger, index=True)
    academic_year = Column(String(20))
    allocation_id = Column(BigInteger)
    target_type = Column(Integer)
    hostel_id = Column(BigInteger)
    room_id = Column(BigInteger)
    bed_id = Column(BigInteger)
    category = Column(Integer)
    priority = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    status = Column(Integer)
    assigned_to_id = Column(Integer)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
