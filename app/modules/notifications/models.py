from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class Notification(Base):
    __tablename__ = "org_notifications"
    __table_args__ = (
        Index("ix_notification_org_source", "organization_id", "source_module"),
        Index("ix_notification_org_created", "organization_id", "created_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    source_module = Column(String(80), nullable=True)
    source_ref = Column(String(150), nullable=True)
    event_key = Column(String(150), nullable=True, index=True)
    template_key = Column(String(150), nullable=True)
    title = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    priority = Column(String(20), nullable=False, default="normal")
    payload_json = Column("payload", mysql.JSON, nullable=False, default=dict)
    attachments_json = Column("attachments", mysql.JSON, nullable=False, default=list)
    metadata_json = Column("metadata", mysql.JSON, nullable=False, default=dict)
    created_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipients = relationship("NotificationRecipient", back_populates="notification")


class NotificationRecipient(Base):
    __tablename__ = "org_notification_recipients"
    __table_args__ = (
        UniqueConstraint(
            "notification_id",
            "recipient_type",
            "recipient_id",
            name="uq_notification_recipient",
        ),
        Index(
            "ix_notification_recipient_identity_read",
            "recipient_type",
            "recipient_id",
            "is_read",
        ),
        Index(
            "ix_notification_recipient_created",
            "notification_id",
            "created_at",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    notification_id = Column(
        BigInteger,
        ForeignKey("org_notifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_type = Column(String(50), nullable=False)
    recipient_id = Column(String(100), nullable=False)
    recipient_name = Column(String(255), nullable=True)
    recipient_email = Column(String(254), nullable=True)
    recipient_mobile = Column(String(20), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    notification = relationship("Notification", back_populates="recipients")
    deliveries = relationship("NotificationDelivery", back_populates="recipient")


class NotificationDelivery(Base):
    __tablename__ = "org_notification_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "recipient_id",
            "channel",
            name="uq_notification_recipient_channel",
        ),
        Index("ix_notification_delivery_status", "status", "scheduled_at"),
        Index("ix_notification_delivery_channel", "recipient_id", "channel"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recipient_id = Column(
        BigInteger,
        ForeignKey("org_notification_recipients.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel = Column(String(20), nullable=False)
    recipient_address = Column(Text, nullable=True)
    channel_payload_json = Column(
        "channel_payload", mysql.JSON, nullable=False, default=dict
    )
    status = Column(String(20), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    scheduled_at = Column(DateTime, nullable=True)
    provider_name = Column(String(50), nullable=True)
    provider_message_id = Column(String(150), nullable=True)
    provider_response_json = Column(
        "provider_response", mysql.JSON, nullable=False, default=dict
    )
    last_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipient = relationship("NotificationRecipient", back_populates="deliveries")
