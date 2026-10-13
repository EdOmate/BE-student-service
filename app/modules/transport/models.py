"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql

from core.database import Base
from core.model_defaults import utc_now


class TransportLocationMaster(Base):
    __tablename__ = 'org_transport_location_master'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    location_name = Column(String(255), nullable=False)
    address_line = Column(String(500), nullable=False)
    landmark = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportVehicleMaster(Base):
    __tablename__ = 'org_transport_vehicle_master'
    __table_args__ = (
        UniqueConstraint('organization_id', 'vehicle_number'),
    )

    VEHICLE_TYPE_CHOICES = (('bus', 'Bus'), ('van', 'Van'), ('suv', 'SUV'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    vehicle_number = Column(String(50), nullable=False)
    vehicle_type = Column(String(20), nullable=False)
    max_capacity = Column(Integer, nullable=False)
    gps_device_id = Column(String(100), nullable=True)
    insurance_valid_until = Column(Date, nullable=True)
    permit_valid_until = Column(Date, nullable=True)
    fitness_valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportBillingSlab(Base):
    __tablename__ = 'org_transport_billing_slab'
    __table_args__ = (
        UniqueConstraint('organization_id', 'slab_name'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    slab_name = Column(String(255), nullable=False)
    min_distance_km = Column(Numeric(8, 2), nullable=True)
    max_distance_km = Column(Numeric(8, 2), nullable=True)
    monthly_fee = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Boolean, nullable=False, default=True)
    notes = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportRouteMaster(Base):
    __tablename__ = 'org_transport_route_master'

    TRIP_TYPE_CHOICES = (('inbound', 'Inbound'), ('outbound', 'Outbound'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    route_name = Column(String(255), nullable=False)
    trip_type = Column(String(20), nullable=False)
    assigned_vehicle_id = Column(
        BigInteger,
        ForeignKey('org_transport_vehicle_master.id'),
        nullable=True,
        index=True,
    )
    assigned_driver_id = Column(Integer, nullable=True, index=True)
    assigned_nanny_id = Column(Integer, nullable=True, index=True)
    start_location_id = Column(
        BigInteger,
        ForeignKey('org_transport_location_master.id'),
        nullable=True,
        index=True,
    )
    end_location_id = Column(
        BigInteger,
        ForeignKey('org_transport_location_master.id'),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportRouteStop(Base):
    __tablename__ = 'org_transport_route_stop'
    __table_args__ = (
        UniqueConstraint('route_id', 'sequence_number'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=False,
        index=True,
    )
    location_id = Column(
        BigInteger,
        ForeignKey('org_transport_location_master.id'),
        nullable=True,
        index=True,
    )
    sequence_number = Column(Integer, nullable=False)
    scheduled_eta = Column(mysql.TIME(fsp=6), nullable=True)
    radius_meters = Column(Integer, nullable=False, default=1000)
    billing_slab_id = Column(
        BigInteger,
        ForeignKey('org_transport_billing_slab.id'),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportStudentAssignment(Base):
    __tablename__ = 'org_transport_student_assignment'
    __table_args__ = (
        Index('org_transpo_organiz_321d2b_idx', 'organization_id'),
        Index('org_transpo_student_086b45_idx', 'student_id'),
        Index('org_transpo_route_i_42dfd0_idx', 'route_id'),
        Index('org_transpo_stop_id_9ab2f0_idx', 'stop_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=False,
        index=True,
    )
    stop_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_stop.id'),
        nullable=False,
        index=True,
    )
    change_request_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_change_request.id'),
        nullable=True,
        index=True,
    )
    is_temporary = Column(Boolean, nullable=False, default=False)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    status = Column(Boolean, nullable=False, default=True)
    notes = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportRouteChangeRequest(Base):
    __tablename__ = 'org_transport_route_change_request'
    __table_args__ = (
        Index('org_transpo_organiz_63c6e4_idx', 'organization_id'),
        Index('org_transpo_student_bc9fb2_idx', 'student_id'),
        Index('org_transpo_status_7fbb33_idx', 'status'),
    )

    REQUEST_TYPE_CHOICES = (('temporary', 'Temporary'), ('permanent', 'Permanent'))
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    request_type = Column(String(20), nullable=False)
    current_route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=True,
        index=True,
    )
    current_stop_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_stop.id'),
        nullable=True,
        index=True,
    )
    requested_route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=True,
        index=True,
    )
    requested_stop_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_stop.id'),
        nullable=True,
        index=True,
    )
    from_date = Column(Date, nullable=True)
    to_date = Column(Date, nullable=True)
    reason = Column(mysql.LONGTEXT, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    capacity_check_passed = Column(Boolean, nullable=False, default=False)
    approved_by_id = Column(Integer, nullable=True, index=True)
    rejected_by_id = Column(Integer, nullable=True, index=True)
    decision_reason = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportTripSession(Base):
    __tablename__ = 'org_transport_trip_session'
    __table_args__ = (
        UniqueConstraint('route_id', 'trip_date', 'trip_type'),
        Index('org_transpo_organiz_fcec4f_idx', 'organization_id'),
        Index('org_transpo_status_16c815_idx', 'status'),
        Index('org_transpo_trip_da_cf7115_idx', 'trip_date'),
    )

    TRIP_TYPE_CHOICES = (('inbound', 'Inbound'), ('outbound', 'Outbound'))
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('delayed', 'Delayed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=False,
        index=True,
    )
    vehicle_id = Column(
        BigInteger,
        ForeignKey('org_transport_vehicle_master.id'),
        nullable=True,
        index=True,
    )
    driver_id = Column(Integer, nullable=True, index=True)
    nanny_id = Column(Integer, nullable=True, index=True)
    trip_date = Column(Date, nullable=False)
    trip_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='planned')
    start_time = Column(mysql.DATETIME(fsp=6), nullable=True)
    end_time = Column(mysql.DATETIME(fsp=6), nullable=True)
    start_odometer = Column(Numeric(12, 2), nullable=True)
    end_odometer = Column(Numeric(12, 2), nullable=True)
    gps_start_latitude = Column(Numeric(10, 7), nullable=True)
    gps_start_longitude = Column(Numeric(10, 7), nullable=True)
    gps_end_latitude = Column(Numeric(10, 7), nullable=True)
    gps_end_longitude = Column(Numeric(10, 7), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportTripManifest(Base):
    __tablename__ = 'org_transport_trip_manifest'
    __table_args__ = (
        UniqueConstraint('trip_session_id', 'student_id'),
    )

    MANIFEST_STATUS_CHOICES = (
        ('expected', 'Expected'),
        ('on_leave', 'On Leave'),
        ('skipped', 'Skipped'),
        ('boarded', 'Boarded'),
        ('deboarded', 'De-boarded'),
        ('manual_override', 'Manual Override'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    trip_session_id = Column(
        BigInteger,
        ForeignKey('org_transport_trip_session.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    route_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_master.id'),
        nullable=False,
        index=True,
    )
    stop_id = Column(
        BigInteger,
        ForeignKey('org_transport_route_stop.id'),
        nullable=False,
        index=True,
    )
    manifest_status = Column(String(20), nullable=False, default='expected')
    sequence_number = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportScanLog(Base):
    __tablename__ = 'org_transport_scan_log'
    __table_args__ = (
        Index('org_transpo_organiz_67754b_idx', 'organization_id'),
        Index('org_transpo_student_5bf317_idx', 'student_id'),
        Index('org_transpo_trip_se_ea954a_idx', 'trip_session_id'),
        Index('org_transpo_scan_ti_191d96_idx', 'scan_time'),
    )

    SCAN_TYPE_CHOICES = (
        ('boarded', 'Boarded'),
        ('deboarded', 'De-boarded'),
        ('campus_entry', 'Campus Entry'),
        ('manual_board', 'Manual Board'),
        ('manual_deboard', 'Manual De-board'),
    )
    SCAN_SOURCE_CHOICES = (
        ('driver_app', 'Driver App'),
        ('nanny_app', 'Nanny App'),
        ('guard_app', 'Guard App'),
        ('admin_override', 'Admin Override'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    trip_session_id = Column(
        BigInteger,
        ForeignKey('org_transport_trip_session.id'),
        nullable=True,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    scan_type = Column(String(20), nullable=False)
    scan_source = Column(String(20), nullable=False)
    scan_time = Column(mysql.DATETIME(fsp=6), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    device_id = Column(String(100), nullable=True)
    offline_event_id = Column(String(100), nullable=True)
    is_offline_synced = Column(Boolean, nullable=False, default=False)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportTripAlert(Base):
    __tablename__ = 'org_transport_trip_alert'
    __table_args__ = (
        Index('org_transpo_organiz_1eb842_idx', 'organization_id'),
        Index('org_transpo_status_ba6a0e_idx', 'status'),
    )

    ALERT_TYPE_CHOICES = (
        ('sos', 'SOS'),
        ('delay', 'Delay'),
        ('breakdown', 'Breakdown'),
        ('route_deviation', 'Route Deviation'),
        ('capacity_issue', 'Capacity Issue'),
    )
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    trip_session_id = Column(
        BigInteger,
        ForeignKey('org_transport_trip_session.id'),
        nullable=True,
        index=True,
    )
    alert_type = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False, default='medium')
    message = Column(mysql.LONGTEXT, nullable=False)
    status = Column(String(20), nullable=False, default='open')
    raised_by_id = Column(Integer, nullable=True, index=True)
    resolved_by_id = Column(Integer, nullable=True, index=True)
    resolved_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportParentNotificationLog(Base):
    __tablename__ = 'org_transport_parent_notification_log'
    __table_args__ = (
        Index('org_transpo_organiz_c311e2_idx', 'organization_id'),
        Index('org_transpo_student_b4f7fe_idx', 'student_id'),
        Index('org_transpo_trip_se_49274f_idx', 'trip_session_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    trip_session_id = Column(
        BigInteger,
        ForeignKey('org_transport_trip_session.id'),
        nullable=True,
        index=True,
    )
    notification_type = Column(String(40), nullable=False)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=True)
    payload_json = Column(JSON(none_as_null=True), nullable=True)
    delivery_status = Column(String(20), nullable=False, default='pending')
    sent_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportGateScan(Base):
    __tablename__ = 'org_transport_gate_scan'
    __table_args__ = (
        Index('org_transpo_organiz_84b08a_idx', 'organization_id'),
        Index('org_transpo_student_20ef8d_idx', 'student_id'),
        Index('org_transpo_scan_ti_13a7b0_idx', 'scan_time'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    gate_name = Column(String(100), nullable=True)
    scan_type = Column(String(20), nullable=False)
    scan_time = Column(mysql.DATETIME(fsp=6), nullable=False)
    device_id = Column(String(100), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportFeeAssignment(Base):
    __tablename__ = 'org_transport_fee_assignment'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    billing_slab_id = Column(
        BigInteger,
        ForeignKey('org_transport_billing_slab.id'),
        nullable=False,
        index=True,
    )
    monthly_fee = Column(Numeric(12, 2), nullable=False, default=0)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TransportTripRouteGPSLog(Base):
    __tablename__ = 'org_transport_trip_route_gps_log'
    __table_args__ = (
        Index('org_transpo_trip_se_109566_idx', 'trip_session_id'),
        Index('org_transpo_vehicle_e34ff2_idx', 'vehicle_id'),
        Index('org_transpo_recorde_bcd48d_idx', 'recorded_at'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False)
    trip_session_id = Column(
        BigInteger,
        ForeignKey('org_transport_trip_session.id'),
        nullable=False,
        index=True,
    )
    vehicle_id = Column(
        BigInteger,
        ForeignKey('org_transport_vehicle_master.id'),
        nullable=True,
        index=True,
    )
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    speed = Column(Numeric(8, 2), nullable=True)
    heading = Column(Numeric(8, 2), nullable=True)
    accuracy = Column(Numeric(8, 2), nullable=True)
    recorded_at = Column(mysql.DATETIME(fsp=6), nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)

__all__ = [
    'TransportLocationMaster',
    'TransportVehicleMaster',
    'TransportBillingSlab',
    'TransportRouteMaster',
    'TransportRouteStop',
    'TransportStudentAssignment',
    'TransportRouteChangeRequest',
    'TransportTripSession',
    'TransportTripManifest',
    'TransportScanLog',
    'TransportTripAlert',
    'TransportParentNotificationLog',
    'TransportGateScan',
    'TransportFeeAssignment',
    'TransportTripRouteGPSLog',
]
