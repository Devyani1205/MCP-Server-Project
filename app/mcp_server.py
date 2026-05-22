import os
import sys

# Ensure the project root is in sys.path for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ["FASTMCP_NO_BANNER"] = "1"

from fastmcp import FastMCP
from jose import JWTError, jwt
from app.query import service as query_service
from app.orders import service as order_service
from app.auth import service as auth_service
from app.auth.schema import UserCreate, UserRole
from app.database import init_db, get_db, Order, DiagnosticTest
from app.config import settings
from app.session import SESSION

# Initialize database before starting MCP server
try:
    init_db()
    try:
        import init_db as seeder_module
        seeder_module.seed_diagnostic_tests()
    except (ImportError, Exception):
        pass
except Exception:
    pass

mcp = FastMCP("Diagnostic-MCP")


def validate_token(token: str):
    """Internal helper to validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("user_id")
        if not user_id:
            return None
            
        return {
            "user_id": user_id,
            "role": payload.get("role")
        }
    except JWTError:
        return None


def is_doctor(role: str) -> bool:
    """Check if the user has the doctor role."""
    return role == "doctor"


@mcp.tool()
def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user and start a session.
    
    Args:
        email: User's registered email address.
        password: User's password.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        user = auth_service.get_user_by_email(db, email)
        if not user or not auth_service.verify_password(password, user.password_hash):
            return {"error": "Invalid email or password"}

        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role or "doctor"  # ADDED
        }
        token = auth_service.create_access_token(data=token_data)
        
        # Store in session
        SESSION.set_session(user_id=user.id, token=token)
        
        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }
    finally:
        db_gen.close()


@mcp.tool()
def register_user(
    name: str,
    email: str,
    password: str,
    role: str = "doctor",
    lab_name: str = None
) -> dict:
    """
    Initiate user registration. Sends an OTP to the user's email.
    
    Args:
        name: Full name of the user.
        email: Email address for registration.
        password: Secure password (min 8 chars, uppercase, lowercase, number, special char).
        role: User role ("doctor", "coordinator", "lab", "admin").
        lab_name: (Required ONLY for "lab" role) Name of the lab. Ignored for other roles.

    SECURITY NOTE: Never display the password in the final summary message.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
            role=UserRole(role),
            lab_name=lab_name
        )
        auth_service.initiate_registration(db, user_data)
        return {
            "message": "Registration initiated. Please check your email for the OTP.",
            "name": name,
            "email": email,
            "role": role
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_gen.close()


@mcp.tool()
def verify_registration_otp(email: str, otp: str) -> dict:
    """
    Verify the registration OTP and finalize user account creation.
    
    Args:
        email: Registered email address.
        otp: 6-digit OTP code received via email.

    SECURITY NOTE: Never display the password in the final summary message.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        user = auth_service.finalize_registration(db, email, otp)
        if not user:
            return {"error": "Invalid or expired OTP code"}
        return {
            "message": "Account verified and created successfully. You can now login.",
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_gen.close()


@mcp.tool()
def forgot_password(email: str) -> dict:
    """
    Initiate password reset flow for an existing account.
    
    Args:
        email: Registered email address.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        auth_service.initiate_forgot_password(db, email)
        return {"message": "If the email is registered, a reset OTP has been sent."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_gen.close()


@mcp.tool()
def reset_password(email: str, otp: str, new_password: str) -> dict:
    """
    Reset password using the OTP code.
    
    Args:
        email: Registered email address.
        otp: 6-digit OTP code received via email.
        new_password: New secure password.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        success = auth_service.finalize_password_reset(db, email, otp, new_password)
        if not success:
            return {"error": "Invalid or expired OTP code"}
        return {"message": "Password reset successful. You can now login with your new password."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_gen.close()


@mcp.tool()
def logout() -> dict:
    """
    Log out the current user and clear the session.
    """
    SESSION.clear_session()
    return {"message": "Logged out successfully"}


@mcp.tool()
def query_tests(query: str) -> dict:
    """
    Search and recommend diagnostic tests based on a patient case or medical query.
    
    Args:
        query: The medical query or patient case description (e.g., 'Lung cancer with EGFR mutation')
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role == "lab":
        return {"error": "Lab users are not authorized to access this tool"}

    return query_service.process_diagnostic_query(query)




@mcp.tool()
def place_order(
    test_id: int,
    patient_name: str,
    lab_name: str,
    contact: str
) -> dict:
    """
    Place a new diagnostic test order. Uses current user session.
    
    Args:
        test_id: The unique ID of the diagnostic test to order.
        patient_name: Full name of the patient.
        lab_name: Name of the lab or clinic.
        contact: Contact number for the order.
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    user_id = data["user_id"]
    role = data["role"]

    if role == "lab":
        return {"error": "Lab users are not authorized to access this tool"}



    # Validation for contact number
    if not contact.isdigit(): # ADDED
        return {"error": "Contact number must contain only digits"} # ADDED

    if len(contact) != 10: # ADDED
        return {"error": "Contact number must be exactly 10 digits"} # ADDED

    try:
        order_id = order_service.place_order(
            user_id=user_id,
            test_id=test_id,
            patient_name=patient_name,
            lab_name=lab_name,
            contact=contact
        )

        return {
            "message": "Order placed successfully",
            "order_id": order_id,
            "user_id": user_id
        }
    except Exception as e:
        return {"error": f"Failed to place order: {str(e)}"}


@mcp.tool()
def get_my_orders() -> dict:
    """
    Retrieve the list of orders placed by the authenticated user.
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    user_id = data["user_id"]
    role = data["role"]
    if role == "lab":
        return {"error": "Lab users are not authorized to access this tool"}
    
    print(f"[DEBUG] Role: {role}")


    orders = order_service.get_user_orders(user_id)
    
    return {
        "orders": orders,
        "count": len(orders),
        "user_id": user_id
    }


@mcp.tool()
def get_profile() -> dict:
    """
    Retrieve the profile information for the authenticated user.
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    user_id = data["user_id"]
    role = data["role"]

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = auth_service.get_user_by_id(db, user_id)
        if not user:
            return {"error": "User not found"}
        
        response = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
        
        # Strictly include lab_name ONLY for lab accounts
        if user.role == "lab":
            response["lab_name"] = user.lab_name
            
        return response

    finally:
        db_gen.close()



@mcp.tool()
def get_all_orders() -> dict:
    """
    Retrieve all orders from the database. (Coordinator only)
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role in ["doctor", "lab"]:
        return {"error": "Lab users are not authorized to access this tool" if role == "lab" else "Unauthorized: doctor cannot access this action"}




    db_gen = get_db()
    db = next(db_gen)
    try:
        # Only coordinators and admins can access all orders
        query = db.query(Order)


        orders = query.all()
        orders_list = []
        for o in orders:
            orders_list.append({
                "id": o.id,
                "order_id": o.order_id,
                "user_id": o.user_id,
                "test_id": o.test_id,
                "patient_name": o.patient_name,
                "lab_name": o.lab_name,
                "contact": o.contact,
                "status": o.status,
                "created_at": str(o.created_at)
            })
        return {
            "orders": orders_list,
            "count": len(orders_list)
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] tool failed: {e}")
        return {"error": "Internal server error"}
    finally:
        db_gen.close()


@mcp.tool()
def get_order_by_id(order_id: int) -> dict:
    """
    Retrieve a specific order by its ID. (Coordinator only)
    
    Args:
        order_id: The unique integer ID of the order.
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role in ["doctor", "lab"]:
        return {"error": "Lab users are not authorized to access this tool" if role == "lab" else "Unauthorized: doctor cannot access this action"}




    db_gen = get_db()
    db = next(db_gen)
    try:
        # Only coordinators and admins can access order by ID directly
        query = db.query(Order)


        order = query.filter(Order.id == order_id).first()
        if not order:
            return {"error": f"Order with ID {order_id} not found"}
            
        return {
            "id": order.id,
            "order_id": order.order_id,
            "user_id": order.user_id,
            "test_id": order.test_id,
            "patient_name": order.patient_name,
            "lab_name": order.lab_name,
            "contact": order.contact,
            "status": order.status,
            "created_at": str(order.created_at)
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] tool failed: {e}")
        return {"error": "Internal server error"}
    finally:
        db_gen.close()


@mcp.tool()
def update_order_status(order_id: int, status: str) -> dict:
    """
    Update the status of an existing order. (Coordinator only)
    
    Args:
        order_id: The unique integer ID of the order.
        status: New status ("Placed", "Sample Collected", "Processing", "Completed").
    """
    VALID_STATUSES = ["Placed", "Sample Collected", "Processing", "Completed"]
    
    if status not in VALID_STATUSES:
        return {"error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}

    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role not in ["coordinator", "admin", "lab"]:
        return {"error": f"Unauthorized: {role} cannot access this action"}

    db_gen = get_db()
    db = next(db_gen)
    try:
        # Fetch order first to check ownership
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": f"Order with ID {order_id} not found"}

        # Strict Lab Validation
        if role == "lab":
            user = auth_service.get_user_by_id(db, data["user_id"])
            if not user or order.lab_name != user.lab_name:
                return {"error": "Unauthorized access to another lab order"}

            
        order.status = status
        db.commit()
        
        return {
            "message": "Status updated successfully",
            "order_id": order.id,
            "new_status": order.status
        }

    except Exception as e:
        db.rollback()
        print(f"[ERROR] tool failed: {e}")
        return {"error": "Internal server error"}
    finally:
        db_gen.close()


@mcp.tool()
def get_all_users() -> dict:
    """
    Retrieve all users from the database. (Admin only)
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role != "admin":
        return {"error": "Unauthorized: admin access required"}

    db_gen = get_db()
    db = next(db_gen)
    try:
        users = auth_service.get_all_users(db)
        users_list = []
        for u in users:
            users_list.append({
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "active_status": u.is_verified
            })
        return {
            "users": users_list,
            "count": len(users_list)
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] get_all_users failed: {e}")
        return {"error": "Internal server error"}
    finally:
        db_gen.close()



@mcp.tool()
def get_my_lab_orders() -> dict:
    """
    Retrieve orders belonging to the logged-in lab user. (Lab only)
    """
    session = SESSION.get_session()
    if not session:
        return {"error": "User not logged in. Please use login_user tool first."}

    data = validate_token(session["token"])
    if not data:
        SESSION.clear_session()
        return {"error": "Session expired or invalid. Please login again."}

    role = data.get("role")
    if role != "lab":
        return {"error": "Unauthorized: this tool is for lab users only"}

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = auth_service.get_user_by_id(db, data["user_id"])
        if not user:
             return {"error": "User not found"}
        
        lab_name = user.lab_name
        orders = db.query(Order).filter(Order.lab_name == lab_name).all()

        
        orders_list = []
        for o in orders:
            orders_list.append({
                "id": o.id,
                "order_id": o.order_id,
                "user_id": o.user_id,
                "test_id": o.test_id,
                "patient_name": o.patient_name,
                "lab_name": o.lab_name,
                "contact": o.contact,
                "status": o.status,
                "created_at": str(o.created_at)
            })
        return {
            "orders": orders_list,
            "count": len(orders_list),
            "lab_name": lab_name
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR] get_my_lab_orders failed: {e}")
        return {"error": "Internal server error"}
    finally:
        db_gen.close()


if __name__ == "__main__":

    mcp.run(transport="stdio", show_banner=False, log_level="ERROR")