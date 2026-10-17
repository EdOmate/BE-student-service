"""Student and parent canteen queries."""

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.canteen.models import (
    OrgCanteenItem,
    OrgCanteenMealOption,
    OrgCanteenMealOptionItem,
    OrgCanteenMealSlot,
    OrgCanteenMenu,
    OrgCanteenMenuItem,
    OrgCanteenOrder,
    OrgCanteenPreOrderRequest,
    OrgCanteenPreOrderRequestItem,
)


IST = ZoneInfo('Asia/Kolkata')


class StudentCanteenService:
    @staticmethod
    def _serialize_order(db: Session, order: OrgCanteenOrder) -> dict:
        if order.order_type == 'meal':
            item = db.query(OrgCanteenMealOption).filter(OrgCanteenMealOption.id == order.meal_option_id).first()
            title = item.name if item else 'Meal option'
        else:
            item = db.query(OrgCanteenItem).filter(OrgCanteenItem.id == order.food_item_id).first()
            title = item.name if item else 'Food item'
        return {'id': order.id, 'record_type': order.order_type, 'title': title, 'status': order.status, 'amount': float(order.total_amount or 0), 'order_date': order.order_date.isoformat(), 'created_at': order.created_at.isoformat() if order.created_at else None}

    @staticmethod
    def get_recent_orders(db: Session, student_id: int, organization_id: int) -> dict:
        orders = db.query(OrgCanteenOrder).filter(
            OrgCanteenOrder.organization_id == organization_id,
            OrgCanteenOrder.student_id == student_id,
        ).order_by(OrgCanteenOrder.created_at.desc(), OrgCanteenOrder.id.desc()).limit(5).all()
        return {'orders': [StudentCanteenService._serialize_order(db, order) for order in orders]}

    @staticmethod
    def list_orders(db: Session, student_id: int, organization_id: int, order_filter: str, page: int, page_size: int) -> dict:
        if order_filter not in {'all', 'meal', 'food_item', 'request'}:
            raise ValueError('filter must be all, meal, food_item, or request')
        records = []
        if order_filter in {'all', 'meal', 'food_item'}:
            query = db.query(OrgCanteenOrder).filter(OrgCanteenOrder.organization_id == organization_id, OrgCanteenOrder.student_id == student_id)
            if order_filter == 'meal': query = query.filter(OrgCanteenOrder.order_type == 'meal')
            if order_filter == 'food_item': query = query.filter(OrgCanteenOrder.order_type == 'food_item')
            records.extend(StudentCanteenService._serialize_order(db, order) for order in query.all())
        if order_filter in {'all', 'request'}:
            requests = db.query(OrgCanteenPreOrderRequest).filter(OrgCanteenPreOrderRequest.organization_id == organization_id, OrgCanteenPreOrderRequest.student_id == student_id).all()
            for request in requests:
                item_rows = db.query(OrgCanteenPreOrderRequestItem, OrgCanteenItem).join(OrgCanteenItem, OrgCanteenItem.id == OrgCanteenPreOrderRequestItem.food_item_id).filter(OrgCanteenPreOrderRequestItem.request_id == request.id).all()
                records.append({'id': request.id, 'record_type': 'request', 'title': ', '.join(f'{item.name} ×{row.quantity}' for row, item in item_rows) or 'Custom meal request', 'status': request.status, 'amount': float(request.served_price or 0), 'order_date': request.requested_date.isoformat(), 'created_at': request.created_at.isoformat() if request.created_at else None})
        records.sort(key=lambda record: record['created_at'] or '', reverse=True)
        total_items = len(records)
        start = (page - 1) * page_size
        return {'results': records[start:start + page_size], 'pagination': {'page': page, 'page_size': page_size, 'total_items': total_items, 'total_pages': (total_items + page_size - 1) // page_size, 'has_next': start + page_size < total_items}}

    @staticmethod
    def get_monthly_spend(
        db: Session,
        student_id: int,
        organization_id: int,
        reference_date: date | None = None,
    ) -> dict:
        current_date = reference_date or datetime.now(IST).date()
        month_start = current_date.replace(day=1)
        month_end = current_date.replace(day=monthrange(current_date.year, current_date.month)[1])

        # Cancelled and refunded orders do not count towards a student's spend.
        total, order_count = (
            db.query(
                func.coalesce(func.sum(OrgCanteenOrder.total_amount), Decimal('0.00')),
                func.count(OrgCanteenOrder.id),
            )
            .filter(
                OrgCanteenOrder.organization_id == organization_id,
                OrgCanteenOrder.student_id == student_id,
                OrgCanteenOrder.order_date.between(month_start, month_end),
                OrgCanteenOrder.status.in_(['ordered', 'purchased']),
            )
            .one()
        )

        return {
            'currency': 'INR',
            'month': month_start.strftime('%Y-%m'),
            'month_label': month_start.strftime('%B %Y'),
            'total_spend': float(total or Decimal('0.00')),
            'order_count': int(order_count or 0),
        }

    @staticmethod
    def get_todays_menu(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict:
        today = datetime.now(IST).date()
        menu_rows = (
            db.query(OrgCanteenMenu, OrgCanteenMealSlot)
            .join(OrgCanteenMealSlot, OrgCanteenMealSlot.id == OrgCanteenMenu.meal_slot_id)
            .filter(
                OrgCanteenMenu.organization_id == organization_id,
                OrgCanteenMenu.menu_date == today,
                OrgCanteenMenu.status == 'published',
                OrgCanteenMealSlot.is_active.is_(True),
            )
            .order_by(OrgCanteenMealSlot.serving_start_time)
            .all()
        )
        booked_slot_ids = {
            meal_slot_id
            for (meal_slot_id,) in db.query(OrgCanteenOrder.meal_slot_id).filter(
                OrgCanteenOrder.organization_id == organization_id,
                OrgCanteenOrder.student_id == student_id,
                OrgCanteenOrder.order_date == today,
                OrgCanteenOrder.meal_slot_id.is_not(None),
            )
        }
        slots = []
        for menu, meal_slot in menu_rows:
            option_rows = (
                db.query(OrgCanteenMenuItem, OrgCanteenMealOption)
                .join(OrgCanteenMealOption, OrgCanteenMealOption.id == OrgCanteenMenuItem.meal_option_id)
                .filter(
                    OrgCanteenMenuItem.menu_id == menu.id,
                    OrgCanteenMenuItem.is_available.is_(True),
                    OrgCanteenMealOption.is_active.is_(True),
                )
                .order_by(OrgCanteenMealOption.name)
                .all()
            )
            options = []
            for menu_item, meal_option in option_rows:
                item_rows = (
                    db.query(OrgCanteenMealOptionItem, OrgCanteenItem)
                    .join(OrgCanteenItem, OrgCanteenItem.id == OrgCanteenMealOptionItem.item_id)
                    .filter(OrgCanteenMealOptionItem.meal_option_id == meal_option.id)
                    .order_by(OrgCanteenItem.name)
                    .all()
                )
                options.append({
                    'id': meal_option.id,
                    'name': meal_option.name,
                    'description': meal_option.description,
                    'price': float(meal_option.price),
                    'items': [
                        {'id': item.id, 'name': item.name, 'quantity': option_item.quantity}
                        for option_item, item in item_rows
                    ],
                })
            slots.append({
                'id': meal_slot.id,
                'name': meal_slot.name,
                'serving_start_time': meal_slot.serving_start_time.isoformat(),
                'serving_end_time': meal_slot.serving_end_time.isoformat(),
                'is_booked': meal_slot.id in booked_slot_ids,
                'meal_options': options,
            })
        return {'date': today.isoformat(), 'slots': slots}

    @staticmethod
    def book_today_meal(
        db: Session,
        student_id: int,
        organization_id: int,
        meal_option_id: int,
    ) -> dict:
        today = datetime.now(IST).date()
        row = (
            db.query(OrgCanteenMenu, OrgCanteenMenuItem, OrgCanteenMealOption)
            .join(OrgCanteenMenuItem, OrgCanteenMenuItem.menu_id == OrgCanteenMenu.id)
            .join(OrgCanteenMealOption, OrgCanteenMealOption.id == OrgCanteenMenuItem.meal_option_id)
            .filter(
                OrgCanteenMenu.organization_id == organization_id,
                OrgCanteenMenu.menu_date == today,
                OrgCanteenMenu.status == 'published',
                OrgCanteenMenuItem.is_available.is_(True),
                OrgCanteenMealOption.is_active.is_(True),
                OrgCanteenMealOption.id == meal_option_id,
            )
            .one_or_none()
        )
        if not row:
            raise ValueError('This meal option is not available today')
        menu, _, meal_option = row
        existing = db.query(OrgCanteenOrder.id).filter(
            OrgCanteenOrder.organization_id == organization_id,
            OrgCanteenOrder.student_id == student_id,
            OrgCanteenOrder.order_date == today,
            OrgCanteenOrder.meal_slot_id == menu.meal_slot_id,
        ).first()
        if existing:
            raise ValueError('A meal is already booked for this slot today')
        order = OrgCanteenOrder(
            organization_id=organization_id,
            student_id=student_id,
            menu_id=menu.id,
            meal_option_id=meal_option.id,
            meal_slot_id=menu.meal_slot_id,
            order_date=today,
            order_type='meal',
            status='ordered',
            payment_status='pending',
            subtotal=meal_option.price,
            total_amount=meal_option.price,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return {
            'id': order.id,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'meal_option_id': meal_option.id,
        }

    @staticmethod
    def get_order_options(
        db: Session,
        organization_id: int,
        search: str | None = None,
    ) -> dict:
        slots = (
            db.query(OrgCanteenMealSlot)
            .filter(
                OrgCanteenMealSlot.organization_id == organization_id,
                OrgCanteenMealSlot.is_active.is_(True),
            )
            .order_by(OrgCanteenMealSlot.serving_start_time)
            .all()
        )
        item_query = db.query(OrgCanteenItem).filter(
            OrgCanteenItem.organization_id == organization_id,
            OrgCanteenItem.is_active.is_(True),
        )
        normalized_search = search.strip() if search else ''
        if normalized_search:
            item_query = item_query.filter(OrgCanteenItem.name.ilike(f'%{normalized_search}%'))
        items = item_query.order_by(OrgCanteenItem.name).all()
        return {
            'meal_slots': [
                {
                    'id': slot.id,
                    'name': slot.name,
                    'serving_start_time': slot.serving_start_time.isoformat(),
                    'serving_end_time': slot.serving_end_time.isoformat(),
                }
                for slot in slots
            ],
            'food_items': [
                {
                    'id': item.id,
                    'name': item.name,
                    'price': float(item.price),
                    'food_type': item.food_type,
                }
                for item in items
            ],
        }

    @staticmethod
    def create_preorder_request(db: Session, student_id: int, organization_id: int, data) -> dict:
        if data.requested_date <= datetime.now(IST).date():
            raise ValueError('Food requests must be created for a future date')
        slot = db.query(OrgCanteenMealSlot).filter(OrgCanteenMealSlot.id == data.meal_slot_id, OrgCanteenMealSlot.organization_id == organization_id, OrgCanteenMealSlot.is_active.is_(True)).first()
        if not slot: raise ValueError('Invalid meal slot')
        item_ids = [item.food_item_id for item in data.items]
        if len(set(item_ids)) != len(item_ids): raise ValueError('Each food item can be requested only once')
        items = {item.id: item for item in db.query(OrgCanteenItem).filter(OrgCanteenItem.organization_id == organization_id, OrgCanteenItem.id.in_(item_ids), OrgCanteenItem.is_active.is_(True)).all()}
        if len(items) != len(item_ids): raise ValueError('One or more food items are unavailable')
        request = OrgCanteenPreOrderRequest(organization_id=organization_id, student_id=student_id, requested_date=data.requested_date, meal_slot_id=slot.id, status='requested', parent_notes=data.parent_notes.strip() if data.parent_notes else None)
        db.add(request); db.flush()
        for row in data.items: db.add(OrgCanteenPreOrderRequestItem(request_id=request.id, food_item_id=row.food_item_id, quantity=row.quantity))
        db.commit(); db.refresh(request)
        return {'id': request.id, 'status': request.status}

    @staticmethod
    def purchase_food_items(db: Session, student_id: int, organization_id: int, food_item_ids: list[int]) -> dict:
        if len(set(food_item_ids)) != len(food_item_ids): raise ValueError('Each food item can be selected only once')
        items = db.query(OrgCanteenItem).filter(OrgCanteenItem.organization_id == organization_id, OrgCanteenItem.id.in_(food_item_ids), OrgCanteenItem.is_active.is_(True)).all()
        if len(items) != len(food_item_ids): raise ValueError('One or more food items are unavailable')
        today = datetime.now(IST).date(); orders = []
        for item in items:
            order = OrgCanteenOrder(organization_id=organization_id, student_id=student_id, food_item_id=item.id, order_date=today, order_type='food_item', status='ordered', payment_status='pending', subtotal=item.price, total_amount=item.price)
            db.add(order); orders.append(order)
        db.commit()
        return {'order_ids': [order.id for order in orders], 'total_amount': float(sum((item.price for item in items), Decimal('0.00'))), 'status': 'ordered'}
