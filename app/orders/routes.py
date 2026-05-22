from fastapi import APIRouter # , Depends, HTTPException, status
# from pydantic import BaseModel
# from . import service
# from ..auth.service import get_current_user
# from ..database import User

router = APIRouter()

# class OrderRequest(BaseModel):
#     test_id: int
#     patient_name: str
#     contact: str

# @router.post("/order_test", response_model=dict, status_code=status.HTTP_201_CREATED)
# async def create_order(
#     request: OrderRequest,
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Protected API to place a diagnostic test order.
#     """
#     # 1. Verify test exists
#     test = service.get_test_by_id(request.test_id)
#     if not test:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Diagnostic test not found"
#         )
#     
#     # 2. Place order
#     order_id = service.place_order(
#         user_id=current_user.id,
#         test_id=request.test_id,
#         patient_name=request.patient_name,
#         contact=request.contact
#     )
#     
#     return {
#         "message": "Order placed successfully",
#         "order_id": order_id,
#         "status": "Placed",
#         "patient_name": request.patient_name,
#         "contact": request.contact,
#         "ordered_test": {
#             "test_id": test["id"],
#             "name": test["name"],
#             "lab_name": test["lab"],
#             "price": test["price"]
#         }
#     }

# @router.get("/my-orders", response_model=dict)
# async def get_my_orders(current_user: User = Depends(get_current_user)):
#     """
#     Protected API to fetch all orders placed by the current logged-in user.
#     """
#     orders = service.get_user_orders(current_user.id)
#     
#     if not orders:
#         return {
#             "orders": [],
#             "message": "No orders found"
#         }
#     
#     return {"orders": orders}


