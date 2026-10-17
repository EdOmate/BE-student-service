"""Read/write SQLAlchemy mappings for the shared canteen schema.

The main EduOps backend owns table creation.  These mappings let the student
service serve parent and student canteen flows without duplicating business
schema or migrations.
"""

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects import mysql

from core.database import Base
from core.model_defaults import utc_now


class CanteenTimestampMixin:
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now, onupdate=utc_now)


class OrgCanteenItem(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_items'
    __table_args__ = (UniqueConstraint('organization_id', 'name', name='uniq_canteen_item'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    image_url = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    food_type = Column(String(20), nullable=False, default='veg')
    allergens = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class OrgCanteenMealSlot(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_meal_slots'
    __table_args__ = (UniqueConstraint('organization_id', 'code', name='uniq_canteen_meal_slot'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    code = Column(String(30), nullable=False)
    serving_start_time = Column(mysql.TIME(fsp=6), nullable=False)
    serving_end_time = Column(mysql.TIME(fsp=6), nullable=False)
    order_cutoff_time = Column(mysql.TIME(fsp=6), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class OrgCanteenMealOption(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_meal_options'
    __table_args__ = (UniqueConstraint('organization_id', 'meal_slot_id', 'name', name='uniq_canteen_meal_option'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    meal_slot_id = Column(BigInteger, ForeignKey('org_canteen_meal_slots.id'), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class OrgCanteenMealOptionItem(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_meal_option_items'
    __table_args__ = (UniqueConstraint('meal_option_id', 'item_id', name='uniq_canteen_meal_option_item'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    meal_option_id = Column(BigInteger, ForeignKey('org_canteen_meal_options.id'), nullable=False, index=True)
    item_id = Column(BigInteger, ForeignKey('org_canteen_items.id'), nullable=False, index=True)
    quantity = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)


class OrgCanteenMenu(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_menus'
    __table_args__ = (UniqueConstraint('organization_id', 'menu_date', 'meal_slot_id', name='uniq_canteen_menu_date_slot'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    menu_date = Column(Date, nullable=False, index=True)
    meal_slot_id = Column(BigInteger, ForeignKey('org_canteen_meal_slots.id'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='published')
    notes = Column(mysql.LONGTEXT, nullable=True)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)


class OrgCanteenMenuItem(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_menu_items'
    __table_args__ = (UniqueConstraint('menu_id', 'meal_option_id', name='uniq_canteen_menu_item'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    menu_id = Column(BigInteger, ForeignKey('org_canteen_menus.id'), nullable=False, index=True)
    meal_option_id = Column(BigInteger, ForeignKey('org_canteen_meal_options.id'), nullable=False, index=True)
    available_quantity = Column(mysql.INTEGER(unsigned=True), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)


class OrgCanteenOrder(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_orders'
    __table_args__ = (
        UniqueConstraint('organization_id', 'student_id', 'order_date', 'meal_slot_id', name='uniq_canteen_order_student_date_slot'),
        Index('idx_canteen_order_org_date_status', 'organization_id', 'order_date', 'status'),
        CheckConstraint("(order_type = 'meal' AND menu_id IS NOT NULL AND meal_slot_id IS NOT NULL AND meal_option_id IS NOT NULL AND food_item_id IS NULL) OR (order_type = 'food_item' AND menu_id IS NULL AND meal_slot_id IS NULL AND meal_option_id IS NULL AND food_item_id IS NOT NULL)", name='canteen_order_product_matches_type'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    student_id = Column(BigInteger, ForeignKey('org_school_students.id'), nullable=False, index=True)
    menu_id = Column(BigInteger, ForeignKey('org_canteen_menus.id'), nullable=True, index=True)
    meal_option_id = Column(BigInteger, ForeignKey('org_canteen_meal_options.id'), nullable=True, index=True)
    food_item_id = Column(BigInteger, ForeignKey('org_canteen_items.id'), nullable=True, index=True)
    order_date = Column(Date, nullable=False)
    meal_slot_id = Column(BigInteger, ForeignKey('org_canteen_meal_slots.id'), nullable=True, index=True)
    order_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='ordered')
    purchased_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_status = Column(String(20), nullable=False, default='pending')
    notes = Column(mysql.LONGTEXT, nullable=True)


class OrgCanteenPreOrderRequest(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_preorder_requests'
    __table_args__ = (Index('idx_canteen_preorder_request_org_date_status', 'organization_id', 'requested_date', 'status'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    student_id = Column(BigInteger, ForeignKey('org_school_students.id'), nullable=False, index=True)
    requested_date = Column(Date, nullable=False)
    meal_slot_id = Column(BigInteger, ForeignKey('org_canteen_meal_slots.id'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='requested')
    parent_notes = Column(mysql.LONGTEXT, nullable=True)
    reviewed_by_id = Column(Integer, nullable=True, index=True)
    reviewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    review_remark = Column(mysql.LONGTEXT, nullable=True)
    served_price = Column(Numeric(10, 2), nullable=True)
    served_at = Column(mysql.DATETIME(fsp=6), nullable=True)


class OrgCanteenPreOrderRequestItem(CanteenTimestampMixin, Base):
    __tablename__ = 'org_canteen_preorder_request_items'
    __table_args__ = (UniqueConstraint('request_id', 'food_item_id', name='uniq_canteen_preorder_request_item'),)

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    request_id = Column(BigInteger, ForeignKey('org_canteen_preorder_requests.id'), nullable=False, index=True)
    food_item_id = Column(BigInteger, ForeignKey('org_canteen_items.id'), nullable=False, index=True)
    quantity = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    notes = Column(String(300), nullable=True)
