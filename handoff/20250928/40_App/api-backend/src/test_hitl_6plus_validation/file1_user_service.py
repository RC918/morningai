# Corrected code for file1_user_service.py
def validate_user(user_id):
    if not user_id:
        raise ValueError("user_id cannot be empty")
    return f"User {user_id} is valid"

# Corrected code for file2_order_service.py
def process_order(order_id):
    if not order_id:
        raise ValueError("order_id cannot be empty")
    return f"Order {order_id} processed successfully"

# Corrected code for file3_payment_service.py
def handle_payment(payment_id):
    if not payment_id:
        raise ValueError("payment_id cannot be empty")
    return f"Payment {payment_id} completed"

# Corrected code for file4_inventory_service.py
def check_inventory(product_id):
    if not product_id:
        raise ValueError("product_id cannot be empty")
    return f"Inventory checked for product {product_id}"

# Corrected code for file5_shipping_service.py
def ship_order(order_id):
    if not order_id:
        raise ValueError("order_id cannot be empty")
    return f"Order {order_id} shipped"

# Corrected code for file6_notification_service.py
def send_notification(user_id, message):
    if not user_id or not message:
        raise ValueError("user_id and message cannot be empty")
    return f"Notification sent to user {user_id}: {message}"

# Corrected code for file7_analytics_service.py
def log_event(event_name, event_data):
    if not event_name or not event_data:
        raise ValueError("event_name and event_data cannot be empty")
    return f"Event {event_name} logged with data: {event_data}"