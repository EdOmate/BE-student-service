from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from core.database import Base

class OrgPublicHoliday(Base):
    __tablename__ = 'org_public_holidays'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer)
    academic_year = Column(String(20))
    name = Column(String(255))
    description = Column(Text)
    holiday_date = Column(Date, index=True)
    half_day = Column(Boolean, default=False)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgEvent(Base):
    __tablename__ = 'org_events'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, index=True)
    title = Column(String(255))
    description = Column(Text)
    event_type = Column(Integer)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    is_all_day = Column(Boolean, default=False)
    location = Column(String(255))
    status = Column(Integer)
    created_by_id = Column(Integer)
    approved_by_id = Column(Integer)
    published_by_id = Column(Integer)
    rejection_reason = Column(Text)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Notice(Base):
    __tablename__ = 'org_notices'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('org_events.id', ondelete='CASCADE'), unique=True)
    organization_id = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    authorized_signee = Column(String(255))
    expiration_date = Column(Date)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BroadcastChannel(Base):
    __tablename__ = 'org_broadcast_channels'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('org_events.id', ondelete='CASCADE'), unique=True)
    organization_id = Column(Integer)
    channel_name_tag = Column(String(255))
    description = Column(Text)
    moderator_staff_id = Column(Integer)
    is_active_flag = Column(Boolean, default=True)
    lifecycle_state = Column(String(30))
    auto_expire_at = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BroadcastMessage(Base):
    __tablename__ = 'org_broadcast_messages'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('org_broadcast_channels.id', ondelete='CASCADE'))
    title = Column(String(255))
    body = Column(Text)
    message_state = Column(String(30))
    is_pinned = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BroadcastMessageAcknowledgement(Base):
    __tablename__ = 'org_broadcast_message_acknowledgements'
    __table_args__ = (UniqueConstraint('message_id', 'student_id'),)
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('org_broadcast_messages.id', ondelete='CASCADE'))
    student_id = Column(BigInteger, index=True)
    acknowledged_at = Column(DateTime, server_default=func.now())
