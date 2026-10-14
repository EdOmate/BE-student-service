from datetime import datetime
from math import ceil

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.modules.auth.dependencies import AuthenticatedStudent
from app.modules.events.models import StudentNotificationDeviceToken
from app.modules.notifications.schema import DeviceTokenUpsertRequest
from app.modules.notifications.models import Notification, NotificationRecipient


class StudentNotificationService:
    @staticmethod
    def _recipient_identity(auth: AuthenticatedStudent) -> tuple[str, str]:
        identity_id = auth.parent_id if auth.role == "parent" else auth.student_id
        return auth.role, str(identity_id)

    @staticmethod
    def _recipient_query(db: Session, auth: AuthenticatedStudent):
        recipient_type, recipient_id = StudentNotificationService._recipient_identity(
            auth
        )
        recipient_filters = [
            (
                NotificationRecipient.recipient_type == recipient_type
            )
            & (NotificationRecipient.recipient_id == recipient_id)
        ]
        if auth.role == "parent":
            # A parent session represents the linked student in the student app.
            # Include notifications addressed directly to that student as well as
            # any notification addressed specifically to the parent account.
            recipient_filters.append(
                (NotificationRecipient.recipient_type == "student")
                & (NotificationRecipient.recipient_id == str(auth.student_id))
            )
        return (
            db.query(NotificationRecipient)
            .join(Notification, Notification.id == NotificationRecipient.notification_id)
            .filter(
                Notification.organization_id == auth.student.organization_id,
                or_(*recipient_filters),
            )
        )

    @staticmethod
    def _serialize_notification(recipient: NotificationRecipient) -> dict:
        notification = recipient.notification
        deliveries = recipient.deliveries
        channels = [delivery.channel for delivery in deliveries]
        statuses = [delivery.status for delivery in deliveries]
        if "failed" in statuses:
            delivery_status = "failed"
        elif "processing" in statuses:
            delivery_status = "processing"
        elif "pending" in statuses:
            delivery_status = "pending"
        elif statuses and all(status == "sent" for status in statuses):
            delivery_status = "sent"
        elif statuses:
            delivery_status = "cancelled"
        else:
            delivery_status = None

        return {
            "id": notification.id,
            "recipient_id": recipient.id,
            "title": notification.title or "Notification",
            "message": notification.message,
            "source_module": notification.source_module,
            "source_ref": notification.source_ref,
            "event_key": notification.event_key,
            "channel": channels[0] if len(channels) == 1 else "multi",
            "channels": channels,
            "priority": notification.priority,
            "status": delivery_status,
            "action_url": notification.action_url,
            "payload": notification.payload_json or {},
            "attachments": notification.attachments_json or [],
            "metadata": notification.metadata_json or {},
            "is_read": recipient.is_read,
            "read_at": recipient.read_at.isoformat() if recipient.read_at else None,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            ),
        }

    @staticmethod
    def list_notifications(
        db: Session,
        auth: AuthenticatedStudent,
        page: int,
        page_size: int,
        is_read: bool | None = None,
        query_text: str | None = None,
    ) -> dict:
        base_query = StudentNotificationService._recipient_query(db, auth)
        unread_count = base_query.filter(NotificationRecipient.is_read.is_(False)).count()

        if is_read is not None:
            base_query = base_query.filter(NotificationRecipient.is_read.is_(is_read))
        if query_text:
            search = f"%{query_text.strip()}%"
            base_query = base_query.filter(
                or_(
                    Notification.title.ilike(search),
                    Notification.message.ilike(search),
                    Notification.source_module.ilike(search),
                )
            )

        total_items = base_query.count()
        recipients = (
            base_query.options(
                selectinload(NotificationRecipient.notification),
                selectinload(NotificationRecipient.deliveries),
            )
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "results": [
                StudentNotificationService._serialize_notification(recipient)
                for recipient in recipients
            ],
            "unread_count": unread_count,
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
    def update_read_status(
        db: Session,
        auth: AuthenticatedStudent,
        notification_id: int,
        is_read: bool,
    ) -> NotificationRecipient | None:
        recipient = (
            StudentNotificationService._recipient_query(db, auth)
            .filter(NotificationRecipient.notification_id == notification_id)
            .options(
                selectinload(NotificationRecipient.notification),
                selectinload(NotificationRecipient.deliveries),
            )
            .first()
        )
        if not recipient:
            return None

        recipient.is_read = is_read
        recipient.read_at = datetime.utcnow() if is_read else None
        recipient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(recipient)
        return recipient

    @staticmethod
    def upsert_device_token(
        db: Session,
        auth: AuthenticatedStudent,
        data: DeviceTokenUpsertRequest,
    ) -> tuple[StudentNotificationDeviceToken, bool]:
        now = datetime.utcnow()
        token = data.fcm_token.strip()
        device_id = data.device_id.strip() if data.device_id else None
        device_name = data.device_name.strip() if data.device_name else None

        existing = (
            db.query(StudentNotificationDeviceToken)
            .filter(StudentNotificationDeviceToken.fcm_token == token)
            .first()
        )
        created = existing is None

        if device_id:
            owner_filters = [
                StudentNotificationDeviceToken.organization_id
                == auth.student.organization_id,
                StudentNotificationDeviceToken.student_id == auth.student_id,
                StudentNotificationDeviceToken.user_role == auth.role,
                StudentNotificationDeviceToken.device_id == device_id,
                StudentNotificationDeviceToken.token_status == "active",
            ]
            if auth.role == "parent":
                owner_filters.append(
                    StudentNotificationDeviceToken.parent_id == auth.parent_id
                )
            else:
                owner_filters.append(
                    StudentNotificationDeviceToken.parent_id.is_(None)
                )
            query = db.query(StudentNotificationDeviceToken).filter(*owner_filters)
            if existing:
                query = query.filter(StudentNotificationDeviceToken.id != existing.id)
            query.update(
                {
                    StudentNotificationDeviceToken.token_status: "inactive",
                    StudentNotificationDeviceToken.push_enabled: False,
                    StudentNotificationDeviceToken.updated_at: now,
                },
                synchronize_session=False,
            )

        if existing is None:
            existing = StudentNotificationDeviceToken(
                fcm_token=token,
                created_at=now,
            )
            db.add(existing)

        existing.organization_id = auth.student.organization_id
        existing.student_id = auth.student_id
        existing.parent_id = auth.parent_id if auth.role == "parent" else None
        existing.user_role = auth.role
        existing.platform = data.platform
        existing.device_id = device_id
        existing.device_name = device_name
        existing.push_enabled = data.push_enabled
        existing.token_status = "active" if data.push_enabled else "inactive"
        existing.last_seen_at = now
        if created:
            existing.last_registered_at = now
        existing.metadata_json = data.metadata
        existing.updated_at = now

        db.commit()
        db.refresh(existing)
        return existing, created

    @staticmethod
    def serialize_device_token(token: StudentNotificationDeviceToken) -> dict:
        return {
            "id": token.id,
            "organization_id": token.organization_id,
            "student_id": token.student_id,
            "parent_id": token.parent_id,
            "user_role": token.user_role,
            "platform": token.platform,
            "device_id": token.device_id,
            "device_name": token.device_name,
            "push_enabled": token.push_enabled,
            "token_status": token.token_status,
            "last_seen_at": (
                token.last_seen_at.isoformat() if token.last_seen_at else None
            ),
            "last_registered_at": (
                token.last_registered_at.isoformat()
                if token.last_registered_at
                else None
            ),
        }
