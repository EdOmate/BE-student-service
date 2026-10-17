from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import AuthenticatedStudent, get_authenticated_parent, get_authenticated_student
from app.modules.canteen.service import StudentCanteenService
from app.modules.canteen.schema import BookTodayMealRequest, CreatePreOrderRequest, PurchaseFoodItemsRequest
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


canteen_router = APIRouter(prefix='/api/v1/canteen', tags=['Canteen'])


@canteen_router.get('/monthly-spend')
async def get_monthly_spend(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentCanteenService.get_monthly_spend(
        db, auth.student_id, auth.student.organization_id
    )
    return SuccessResponse(message='Monthly canteen spend fetched successfully', data=data)


@canteen_router.get('/today-menu')
async def get_todays_menu(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentCanteenService.get_todays_menu(
        db, auth.student_id, auth.student.organization_id
    )
    return SuccessResponse(message="Today's canteen menu fetched successfully", data=data)


@canteen_router.get('/orders/snapshot')
async def get_recent_orders(auth: AuthenticatedStudent = Depends(get_authenticated_student), db: Session = Depends(get_db)):
    return SuccessResponse(message='Recent canteen orders fetched successfully', data=StudentCanteenService.get_recent_orders(db, auth.student_id, auth.student.organization_id))


@canteen_router.get('/orders')
async def list_orders(order_filter: str = Query(default='all', alias='filter'), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), auth: AuthenticatedStudent = Depends(get_authenticated_student), db: Session = Depends(get_db)):
    try:
        data = StudentCanteenService.list_orders(db, auth.student_id, auth.student.organization_id, order_filter, page, page_size)
        return SuccessResponse(message='Canteen orders fetched successfully', data=data)
    except ValueError as error:
        return ErrorResponse(message=str(error), status_code=400)


@canteen_router.post('/meal-bookings')
async def book_today_meal(
    payload: BookTodayMealRequest,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        data = StudentCanteenService.book_today_meal(
            db, auth.student_id, auth.student.organization_id, payload.meal_option_id
        )
        return SuccessResponse(message='Meal booked successfully', data=data, status_code=201)
    except ValueError as error:
        db.rollback()
        return ErrorResponse(message=str(error), status_code=400)


@canteen_router.get('/options')
async def get_order_options(
    search: str | None = Query(default=None, max_length=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    return SuccessResponse(
        message='Canteen options fetched successfully',
        data=StudentCanteenService.get_order_options(db, auth.student.organization_id, search),
    )


@canteen_router.post('/preorder-requests')
async def create_preorder_request(payload: CreatePreOrderRequest, auth: AuthenticatedStudent = Depends(get_authenticated_parent), db: Session = Depends(get_db)):
    try:
        return SuccessResponse(message='Food meal request created successfully', data=StudentCanteenService.create_preorder_request(db, auth.student_id, auth.student.organization_id, payload), status_code=201)
    except ValueError as error:
        db.rollback(); return ErrorResponse(message=str(error), status_code=400)


@canteen_router.post('/food-purchases')
async def purchase_food_items(payload: PurchaseFoodItemsRequest, auth: AuthenticatedStudent = Depends(get_authenticated_student), db: Session = Depends(get_db)):
    try:
        return SuccessResponse(message='Food items purchased successfully', data=StudentCanteenService.purchase_food_items(db, auth.student_id, auth.student.organization_id, payload.food_item_ids), status_code=201)
    except ValueError as error:
        db.rollback(); return ErrorResponse(message=str(error), status_code=400)
