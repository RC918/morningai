# Corrected code for file1_user_service.py
def validate_user(user_id):
    if not user_id:
        raise ValueError("User ID cannot be empty")
    return True

# Corrected code for file2_order_service.py
def process_order(order_data):
    if not order_data:
        raise ValueError("Order data is missing")
    return {"status": "processed", "data": order_data}

# Corrected code for file3_payment_service.py
def handle_payment(payment_info):
    if not payment_info:
        raise ValueError("Payment information is required")
    return {"status": "payment_successful"}

# Corrected code for file4_inventory_service.py
def check_inventory(product_id):
    if not product_id:
        raise ValueError("Product ID is required")
    return {"available": True, "product_id": product_id}

# Corrected code for file5_shipping_service.py
def schedule_shipping(address):
    if not address:
        raise ValueError("Shipping address is missing")
    return {"status": "shipping_scheduled", "address": address}

# Corrected code for file6_notification_service.py
def send_notification(user_email, message):
    if not user_email or not message:
        raise ValueError("Email and message are required")
    return {"status": "notification_sent", "email": user_email}

# Corrected code for file7_analytics_service.py
def log_event(event_data):
    if not event_data:
        raise ValueError("Event data is missing")
    return {"status": "event_logged", "data": event_data}