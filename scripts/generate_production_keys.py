#!/usr/bin/env python3
"""Generate secure keys for production deployment."""

from cryptography.fernet import Fernet
import secrets

print("=" * 60)
print("PRODUCTION KEYS GENERATOR")
print("=" * 60)
print("\nCopy these values to your Vercel environment variables:\n")

# Generate encryption key
encryption_key = Fernet.generate_key().decode()
print(f"ENCRYPTION_MASTER_KEY={encryption_key}")

# Generate JWT secret
jwt_secret = secrets.token_urlsafe(64)
print(f"JWT_SECRET={jwt_secret}")

# Generate Flask secret
flask_secret = secrets.token_urlsafe(64)
print(f"FLASK_SECRET_KEY={flask_secret}")

print("\n" + "=" * 60)
print("IMPORTANT: Save these keys securely!")
print("Never commit these to version control.")
print("=" * 60)
