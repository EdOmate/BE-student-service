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

class TransportVehicleMaster(Base):
    __tablename__ = 'org_transport_vehicle_master'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    vehicle_number = Column(String(50))
    license_plate = Column(String(50))
    vehicle_type = Column(String(50))
    max_capacity = Column(Integer)
    gps_device_id = Column(String(255))
    insurance_valid_until = Column(Date)
    permit_valid_until = Column(Date)
    fitness_valid_until = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TransportRouteMaster(Base):
    __tablename__ = 'org_transport_route_master'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    route_name = Column(String(255))
    trip_type = Column(String(30))
    assigned_vehicle_id = Column(Integer, ForeignKey('org_transport_vehicle_master.id'))
    assigned_driver_id = Column(Integer)
    assigned_nanny_id = Column(Integer)
    start_location_name = Column(String(255))
    end_location_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TransportRouteStop(Base):
    __tablename__ = 'org_transport_route_stop'
    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey('org_transport_route_master.id', ondelete='CASCADE'))
    stop_name = Column(String(255))
    sequence_number = Column(Integer)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    scheduled_eta = Column(Time)
    radius_meters = Column(Integer)
    billing_slab_id = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TransportStudentAssignment(Base):
    __tablename__ = 'org_transport_student_assignment'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    student_id = Column(BigInteger, index=True)
    route_id = Column(Integer, ForeignKey('org_transport_route_master.id'))
    stop_id = Column(Integer, ForeignKey('org_transport_route_stop.id'))
    change_request_id = Column(Integer)
    is_temporary = Column(Boolean, default=False)
    effective_from = Column(Date)
    effective_to = Column(Date)
    status = Column(Boolean, default=True)
    notes = Column(Text)
    created_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TransportTripSession(Base):
    __tablename__ = 'org_transport_trip_session'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    route_id = Column(Integer, ForeignKey('org_transport_route_master.id'))
    vehicle_id = Column(Integer, ForeignKey('org_transport_vehicle_master.id'))
    driver_id = Column(Integer)
    nanny_id = Column(Integer)
    trip_date = Column(Date)
    trip_type = Column(String(30))
    status = Column(String(30))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    gps_start_latitude = Column(Numeric(10, 7))
    gps_start_longitude = Column(Numeric(10, 7))
    gps_end_latitude = Column(Numeric(10, 7))
    gps_end_longitude = Column(Numeric(10, 7))
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TransportTripRouteGPSLog(Base):
    __tablename__ = 'org_transport_trip_route_gps_log'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    trip_session_id = Column(Integer, ForeignKey('org_transport_trip_session.id', ondelete='CASCADE'), index=True)
    vehicle_id = Column(Integer)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    speed = Column(Numeric(8, 2))
    heading = Column(Numeric(8, 2))
    accuracy = Column(Numeric(8, 2))
    recorded_at = Column(DateTime, index=True)
    created_at = Column(DateTime, server_default=func.now())

class TransportTripAlert(Base):
    __tablename__ = 'org_transport_trip_alert'
    id = Column(Integer, primary_key=True)
    organization_id = Column(BigInteger)
    trip_session_id = Column(Integer, ForeignKey('org_transport_trip_session.id'))
    alert_type = Column(String(50))
    severity = Column(String(30))
    message = Column(Text)
    status = Column(String(30))
    raised_by_id = Column(Integer)
    resolved_by_id = Column(Integer)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
