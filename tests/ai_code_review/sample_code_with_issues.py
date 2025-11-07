"""
Sample code with intentional issues for testing AI Code Review.

This file contains various code quality, security, and performance issues
to validate that the AI reviewer can identify and provide recommendations.
"""

import os


# SECURITY ISSUE: SQL Injection Vulnerability (Critical)
def authenticate_user(username, password):
    """Authenticate user with database lookup."""
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result


# SECURITY ISSUE: Hardcoded Credentials (Critical)
DATABASE_PASSWORD = "admin123"  # Never hardcode passwords!
API_KEY = "sk-1234567890abcdef"  # API keys should be in environment variables


# PERFORMANCE ISSUE: N+1 Query Problem (Major)
def get_user_orders(user_ids):
    """Retrieve orders for multiple users."""
    orders = []
    for user_id in user_ids:
        # This creates N database queries (N+1 problem)
        user = db.query(User).filter_by(id=user_id).first()
        user_orders = db.query(Order).filter_by(user_id=user.id).all()
        orders.extend(user_orders)
    return orders


# CODE QUALITY ISSUE: Magic Numbers (Minor)
def calculate_discount(price):
    """Calculate discount based on price."""
    if price > 100:
        return price * 0.15  # Magic number: what does 0.15 represent?
    elif price > 50:
        return price * 0.10  # Magic number: should be a named constant
    return 0


# CODE QUALITY ISSUE: No Error Handling (Major)
def read_config_file(file_path):
    """Read configuration from file."""
    # No try-except, will crash if file doesn't exist
    with open(file_path) as f:
        return f.read()


# BEST PRACTICE ISSUE: Using print() instead of logging (Minor)
def process_data(data):
    """Process incoming data."""
    print("Processing data...")  # Should use logging module
    result = data * 2
    print(f"Result: {result}")  # Debugging print statements left in
    return result


# PERFORMANCE ISSUE: Inefficient Algorithm (Major)
def find_duplicates(items):
    """Find duplicate items in list."""
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):  # O(n²) algorithm
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates


# CODE QUALITY ISSUE: Poor Variable Naming (Minor)
def calc(x, y, z):
    """Calculate something."""  # Vague docstring
    a = x + y  # What is 'a'?
    b = a * z  # What is 'b'?
    return b  # What does this represent?


# SECURITY ISSUE: Path Traversal Vulnerability (Critical)
def read_user_file(filename):
    """Read file from user uploads directory."""
    # Vulnerable to path traversal: ../../../etc/passwd
    file_path = f"/uploads/{filename}"
    with open(file_path) as f:
        return f.read()


# BEST PRACTICE ISSUE: Mutable Default Argument (Major)
def add_to_list(item, target_list=[]):
    """Add item to list."""
    # Mutable default arguments are shared across calls!
    target_list.append(item)
    return target_list


# CODE QUALITY ISSUE: God Function (Major)
def handle_user_request(request):
    """Handle incoming user request."""
    # Function does too much - violates Single Responsibility Principle
    if not validate_request(request):
        return {"error": "Invalid request"}

    user = authenticate_user(request.username, request.password)
    if not user:
        return {"error": "Auth failed"}

    data = fetch_user_data(user.id)
    processed = process_data(data)
    result = calculate_result(processed)
    save_to_database(result)
    send_notification(user.email, result)
    log_activity(user.id, "request_handled")
    update_metrics("requests_handled")

    return {"status": "success", "result": result}


# PERFORMANCE ISSUE: Memory Inefficiency (Minor)
def load_large_dataset():
    """Load entire dataset into memory."""
    # Loads entire file into memory at once - should use streaming/chunking
    with open("large_data.csv") as f:
        data = f.read()  # Could be gigabytes!
    return data.split("\n")


# SECURITY ISSUE: Weak Password Hashing (Critical)
def hash_password(password):
    """Hash user password for storage."""
    import hashlib
    # MD5 is cryptographically broken, use bcrypt or Argon2
    return hashlib.md5(password.encode()).hexdigest()


# CODE QUALITY ISSUE: Inconsistent Return Types (Major)
def get_user_age(user_id):
    """Get user age."""
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        return user.age  # Returns integer
    return "Not found"  # Returns string - inconsistent!


# BEST PRACTICE ISSUE: No Type Hints (Minor)
def calculate_total(items, tax_rate, discount):
    """Calculate total price with tax and discount."""
    # No type hints make code harder to understand and maintain
    subtotal = sum(item['price'] for item in items)
    after_discount = subtotal * (1 - discount)
    total = after_discount * (1 + tax_rate)
    return total


# GOOD PRACTICE: Example of well-written function
def calculate_total_with_tax(
    items: list[dict],
    tax_rate: float,
    discount_percentage: float = 0.0
) -> float:
    """
    Calculate total price with tax and optional discount.

    Args:
        items: List of items with 'price' keys
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%)
        discount_percentage: Discount as decimal (default: 0.0)

    Returns:
        Total price including tax and discount

    Raises:
        ValueError: If tax_rate or discount_percentage is negative
    """
    if tax_rate < 0 or discount_percentage < 0:
        raise ValueError("Tax rate and discount must be non-negative")

    subtotal = sum(item['price'] for item in items)
    after_discount = subtotal * (1 - discount_percentage)
    total = after_discount * (1 + tax_rate)

    return round(total, 2)


# Summary of Issues:
# - Critical: 4 (SQL injection, hardcoded credentials, path traversal, weak password hashing)
# - Major: 5 (N+1 query, no error handling, inefficient algorithm, mutable default, god function, inconsistent returns)
# - Minor: 4 (magic numbers, print statements, poor naming, no type hints, memory inefficiency)
# Total: 13 issues
