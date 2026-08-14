from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
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


class OrgEventHoliday(Base):
    __tablename__ = "org_event_holiday"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer,
        ForeignKey("org_events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    holiday_type = Column(Integer, default=1, nullable=False)
    is_paid_leave = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrgEventPTM(Base):
    __tablename__ = "org_event_ptm"
    __table_args__ = (
        Index("ix_org_event_ptm_section_start", "section_id", "scheduled_start_at"),
        CheckConstraint(
            "scheduled_end_at > scheduled_start_at",
            name="org_event_ptm_end_after_start",
        ),
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer,
        ForeignKey("org_events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    coordinator_id = Column(Integer, nullable=True)
    scheduled_start_at = Column(DateTime, nullable=False)
    scheduled_end_at = Column(DateTime, nullable=False)
    meeting_mode = Column(String(20), default="in_person", nullable=False)
    venue = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    agenda = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    requires_appointment = Column(Boolean, default=False, nullable=False)
    appointment_duration_minutes = Column(SmallInteger, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Notice(Base):
    __tablename__ = 'org_notices'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('org_events.id', ondelete='CASCADE'), unique=True)
    organization_id = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    authorized_signee = Column(String(30))
    expiration_date = Column(Date)
    is_pinned = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BroadcastChannel(Base):
    __tablename__ = 'org_broadcast_channels'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('org_events.id', ondelete='CASCADE'), unique=True)
    organization_id = Column(Integer)
    channel_name_tag = Column(String(100), unique=True)
    description = Column(Text)
    moderator_staff_id = Column(Integer)
    is_active_flag = Column(Boolean, default=True)
    lifecycle_state = Column(String(20), default="active")
    auto_expire_at = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BroadcastChannelMember(Base):
    __tablename__ = "org_broadcast_channel_members"
    __table_args__ = (
        UniqueConstraint("channel_id", "student_id"),
        Index("ix_broadcast_member_channel_state", "channel_id", "member_state"),
    )

    id = Column(Integer, primary_key=True)
    channel_id = Column(
        Integer,
        ForeignKey("org_broadcast_channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(Integer, index=True, nullable=False)
    member_state = Column(String(20), default="active", nullable=False)
    joined_at = Column(DateTime, server_default=func.now())
    removed_at = Column(DateTime, nullable=True)


class BroadcastMessage(Base):
    __tablename__ = 'org_broadcast_messages'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('org_broadcast_channels.id', ondelete='CASCADE'))
    title = Column(String(255))
    body = Column(Text)
    message_state = Column(String(20), default="draft")
    is_pinned = Column(Boolean, default=True)
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


class OrgEventAttachment(Base):
    __tablename__ = "org_event_attachments"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer,
        ForeignKey("org_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=True)
    file_url = Column(Text, nullable=False)
    mime_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    status = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EventTarget(Base):
    __tablename__ = "org_event_targets"
    __table_args__ = (
        Index("ix_org_event_target_type_id", "target_type", "target_id"),
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer,
        ForeignKey("org_events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_type = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    status = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
