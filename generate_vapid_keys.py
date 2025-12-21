from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Generate EC private key (P-256)
private_key = ec.generate_private_key(ec.SECP256R1())

# Extract private key number
private_numbers = private_key.private_numbers()
private_bytes = private_numbers.private_value.to_bytes(32, "big")

# Extract public key
public_numbers = private_key.public_key().public_numbers()
public_bytes = (
    b"\x04"
    + public_numbers.x.to_bytes(32, "big")
    + public_numbers.y.to_bytes(32, "big")
)

# Base64 URL-safe encode (VAPID format)
private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode().rstrip("=")
public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip("=")

print("\n✅ VAPID KEYS GENERATED SUCCESSFULLY\n")
print("PUBLIC KEY:\n", public_key_b64)
print("\nPRIVATE KEY:\n", private_key_b64)
