from typing import Optional, List
from pydantic import BaseModel, SecretStr
from sqlmodel import Field
from datetime import datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class User(BaseModel):
    userId: int
    userName: str
    fullName: str
    email: Optional[str] = None
    token: Optional[Token] = None


class UserLogin(BaseModel):
    username: str = Field(..., description="User Name", min_length=4, max_length=50)
    password: SecretStr = Field(
        min_length=8,
        max_length=128,
        description="Your password",
    )


class ProductBase(BaseModel):
    product_code: str
    product_name: str
    product_description: str
    quantity_in_stock: int
    price: float


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    pass


class UserBase(BaseModel):
    user_id: int
    user_name: str
    email: str
    full_name: str


class UserCreate(UserBase):
    hashed_password: str


class UserRead(UserBase):
    pass


class PaymentBase(BaseModel):
    payment_id: int
    order_number: int
    payment_date: datetime
    amount: float
    payment_method: str


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    pass


class OrderBase(BaseModel):
    order_number: int
    order_date: datetime
    required_date: datetime
    shipped_date: Optional[datetime] = None
    status: str
    comments: Optional[str] = None
    user_id: int
    product_code: str


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    pass


# Relationships for Pydantic models
class UserWithOrders(UserRead):
    orders: List[OrderRead] = []


class ProductWithOrders(ProductRead):
    orders: List[OrderRead] = []


class OrderWithDetails(OrderRead):
    user: UserRead
    product: ProductRead
    payment: Optional[PaymentRead] = None


class PaymentWithOrder(PaymentRead):
    order: OrderRead
