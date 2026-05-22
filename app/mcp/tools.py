from ..query import service as query_service
from ..orders import service as order_service

# Tool Metadata Registry
# This is returned by the /mcp/tools endpoint
TOOL_METADATA = [
    {
        "name": "query_tests",
        "description": "Search and recommend diagnostic tests using patient case query",
        "input_schema": {
            "query": "string"
        }
    },
    {
        "name": "place_order",
        "description": "Place diagnostic test order using test_id",
        "input_schema": {
            "test_id": "integer",
            "patient_name": "string",
            "lab_name": "string",
            "contact": "string"
        }
    },
    {
        "name": "get_my_orders",
        "description": "Get logged-in user's placed orders",
        "input_schema": {}
    }
]

def execute_query_tests(arguments: dict, user_id: int):
    query = arguments.get("query")
    if not query:
        return {"error": "Missing 'query' argument"}
    return query_service.process_diagnostic_query(query)

def execute_place_order(arguments: dict, user_id: int):
    test_id = arguments.get("test_id")
    patient_name = arguments.get("patient_name")
    lab_name = arguments.get("lab_name")
    contact = arguments.get("contact")
    
    if not test_id or not patient_name or not contact:
        return {"error": "Missing required arguments for place_order"}
    
    # 1. Verify test exists
    test = order_service.get_test_by_id(test_id)
    if not test:
        return {"error": "Diagnostic test not found"}
    
    # 2. Place order
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
        "status": "Placed",
        "ordered_test": test
    }

def execute_get_my_orders(arguments: dict, user_id: int):
    orders = order_service.get_user_orders(user_id)
    if not orders:
        return {"orders": [], "message": "No orders found"}
    return {"orders": orders}

# Mapping of tool names to their internal handler functions
TOOL_HANDLERS = {
    "query_tests": execute_query_tests,
    "place_order": execute_place_order,
    "get_my_orders": execute_get_my_orders
}
