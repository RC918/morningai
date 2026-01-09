# Corrected code for file1_user_service.py
def get_user(user_id):
    if not user_id:
        raise ValueError("user_id cannot be empty")
    return {"user_id": user_id, "name": "John Doe"}


# Corrected code for file2_order_service.py
def create_order(order_details):
    if not order_details:
        raise ValueError("order_details cannot be empty")
    return {"order_id": 12345, "details": order_details}


# Corrected code for file3_payment_service.py
def process_payment(payment_info):
    if not payment_info:
        raise ValueError("payment_info cannot be empty")
    return {"payment_id": 67890, "status": "success"}


# Corrected code for file4_inventory_service.py
def check_inventory(product_id):
    if not product_id:
        raise ValueError("product_id cannot be empty")
    return {"product_id": product_id, "available": True}


# Corrected code for file5_shipping_service.py
def schedule_shipping(address):
    if not address:
        raise ValueError("address cannot be empty")
    return {"shipping_id": 54321, "address": address}


# Corrected code for file6_notification_service.py
def send_notification(user_id, message):
    if not user_id or not message:
        raise ValueError("user_id and message cannot be empty")
    return {"user_id": user_id, "message": message, "status": "sent"}


# Corrected code for file7_analytics_service.py
def log_event(event_data):
    if not event_data:
        raise ValueError("event_data cannot be empty")
    return {"event_id": 98765, "data": event_data}