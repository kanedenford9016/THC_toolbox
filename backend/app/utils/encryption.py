"""Encryption utilities for sensitive data."""
from cryptography.fernet import Fernet
import base64
from config.settings import config

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize the encryption service with the master key."""
        key = config.ENCRYPTION_MASTER_KEY
        if not key:
            raise ValueError("ENCRYPTION_MASTER_KEY not set in environment variables")
        
        # Ensure the key is properly formatted
        if isinstance(key, str):
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """
        Encrypt sensitive data.
        
        Args:
            data: String or bytes to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if data is None:
            return None
        
        if isinstance(data, (int, float)):
            data = str(data)
        
        if isinstance(data, str):
            data = data.encode()
        
        encrypted = self.cipher.encrypt(data)
        return encrypted.decode()
    
    def decrypt(self, encrypted_data):
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted string
        """
        if encrypted_data is None:
            return None
        
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode()
    
    def encrypt_dict_fields(self, data_dict, fields):
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data_dict: Dictionary containing data
            fields: List of field names to encrypt
            
        Returns:
            New dictionary with encrypted fields
        """
        result = data_dict.copy()
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.encrypt(result[field])
        return result
    
    def decrypt_dict_fields(self, data_dict, fields):
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data_dict: Dictionary containing encrypted data
            fields: List of field names to decrypt
            
        Returns:
            New dictionary with decrypted fields
        """
        result = data_dict.copy()
        for field in fields:
            if field in result and result[field] is not None:
                try:
                    result[field] = self.decrypt(result[field])
                except Exception:
                    # If decryption fails, keep the original value
                    pass
        return result
    
    @staticmethod
    def generate_key():
        """Generate a new Fernet key for encryption."""
        return Fernet.generate_key().decode()

encryption_service = EncryptionService()
