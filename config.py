# FILE: config.py

# --- Database Configuration ---
# Use this file to store sensitive information securely.
DB_CONFIG = {
    'dbname': 'dbinventory',
    'user': 'postgres',
    'password': 'mbpi',         # <-- Make sure this is your correct database password
    'host': '192.168.1.13',
    'port': '5432'
}

# --- Admin Password for Creating New Users ---
# This should be a strong, unique password.
ADMIN_PASSWORD = "Itadmin"  # <-- Make sure this is the admin password you want to use