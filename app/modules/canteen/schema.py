from pydantic import BaseModel, Field
from datetime import date


class BookTodayMealRequest(BaseModel):
    meal_option_id: int = Field(gt=0)


class RequestedFoodItem(BaseModel):
    food_item_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=20)


class CreatePreOrderRequest(BaseModel):
    requested_date: date
    meal_slot_id: int = Field(gt=0)
    items: list[RequestedFoodItem] = Field(min_length=1, max_length=20)
    parent_notes: str | None = Field(default=None, max_length=5000)


class PurchaseFoodItemsRequest(BaseModel):
    food_item_ids: list[int] = Field(min_length=1, max_length=20)
