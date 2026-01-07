---
template_id: compliance_governance_pci_dss_python
template_name: PCI-DSS v4.0 Compliance - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - compliance_frameworks/python_iso27001_implementation.md
related_templates:
  - privacy_protection/python_gdpr_compliance.md
tools:
  - cryptography (encryption)
  - stripe (payment processing)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - python
---

# PCI-DSS v4.0 Compliance - Python

**Payment Card Industry Data Security Standard for Python applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Structure

**12 Requirements** across 6 control objectives:

1. **Build and Maintain a Secure Network**
   - Req 1: Install and maintain network security controls
   - Req 2: Apply secure configurations to all system components

2. **Protect Account Data**
   - Req 3: Protect stored account data
   - Req 4: Protect cardholder data with strong cryptography during transmission

3. **Maintain a Vulnerability Management Program**
   - Req 5: Protect all systems and networks from malicious software
   - Req 6: Develop and maintain secure systems and software

4. **Implement Strong Access Control Measures**
   - Req 7: Restrict access to system components and cardholder data by business need to know
   - Req 8: Identify users and authenticate access to system components
   - Req 9: Restrict physical access to cardholder data

5. **Regularly Monitor and Test Networks**
   - Req 10: Log and monitor all access to system components and cardholder data
   - Req 11: Test security of systems and networks regularly

6. **Maintain an Information Security Policy**
   - Req 12: Support information security with organizational policies and programs

### Key Concepts

- **Cardholder Data (CHD)**: PAN, cardholder name, expiration date, service code
- **Sensitive Authentication Data (SAD)**: Full track data, CAV2/CVC2/CVV2/CID, PINs
- **Cardholder Data Environment (CDE)**: Systems, processes, people that store/process/transmit CHD

---

## Requirement 3: Protect Stored Account Data

```python
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict
import uuid

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class CardDataProtectionManager:
    """
    Protect stored cardholder data.

    PCI-DSS Requirement 3: Protect stored account data
    PCI-DSS Requirement 3.3: Mask PAN when displayed
    PCI-DSS Requirement 3.4: Render PAN unreadable
    """

    def __init__(self, master_key: bytes):
        """
        Initialize card data protection.

        Args:
            master_key: 256-bit master encryption key (must be stored in HSM)
        """
        self.master_key = master_key

    def tokenize_pan(self, pan: str) -> str:
        """
        Tokenize Primary Account Number (PAN) instead of storing.

        PCI-DSS Requirement 3.2.1: Do not store sensitive authentication data

        Args:
            pan: Primary Account Number

        Returns:
            Token that replaces PAN
        """
        # Validate PAN format
        if not self._validate_pan(pan):
            raise ValueError("Invalid PAN format")

        # Generate cryptographically secure token
        token = f"TKN{uuid.uuid4().hex[:16].upper()}"

        # Store token-to-PAN mapping in secure vault (HSM/external tokenization service)
        self._store_token_mapping(token, pan)

        logger.info("PAN tokenized", extra={
            "event": "pan_tokenized",
            "token_prefix": token[:6],
            "timestamp": datetime.utcnow().isoformat()
        })

        return token

    def mask_pan(self, pan: str) -> str:
        """
        Mask PAN for display.

        PCI-DSS Requirement 3.3: Mask PAN when displayed
        Only first 6 and last 4 digits shown

        Args:
            pan: Primary Account Number

        Returns:
            Masked PAN (e.g., "411111******1111")
        """
        if len(pan) < 13:
            raise ValueError("PAN too short to mask")

        # Show first 6 (BIN) and last 4 digits
        masked = pan[:6] + "*" * (len(pan) - 10) + pan[-4:]

        logger.info("PAN masked for display", extra={
            "event": "pan_masked",
            "masked_pan": masked,
            "timestamp": datetime.utcnow().isoformat()
        })

        return masked

    def encrypt_pan(self, pan: str) -> Dict[str, str]:
        """
        Encrypt PAN with AES-256-GCM.

        PCI-DSS Requirement 3.4.1: Use strong cryptography
        PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit

        Args:
            pan: Primary Account Number to encrypt

        Returns:
            Dictionary with ciphertext, nonce, tag
        """
        if not self._validate_pan(pan):
            raise ValueError("Invalid PAN format")

        # Use AES-256-GCM with random nonce
        aesgcm = AESGCM(self.master_key)
        nonce = os.urandom(12)  # 96-bit nonce

        # Encrypt PAN
        ciphertext = aesgcm.encrypt(
            nonce,
            pan.encode('utf-8'),
            None  # No associated data
        )

        logger.info("PAN encrypted", extra={
            "event": "pan_encrypted",
            "algorithm": "AES-256-GCM",
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "ciphertext": ciphertext.hex(),
            "nonce": nonce.hex(),
            "algorithm": "AES-256-GCM"
        }

    def decrypt_pan(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt PAN.

        Args:
            encrypted_data: Dictionary with ciphertext and nonce

        Returns:
            Decrypted PAN
        """
        aesgcm = AESGCM(self.master_key)

        ciphertext = bytes.fromhex(encrypted_data["ciphertext"])
        nonce = bytes.fromhex(encrypted_data["nonce"])

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            logger.info("PAN decrypted", extra={
                "event": "pan_decrypted",
                "timestamp": datetime.utcnow().isoformat()
            })

            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error("PAN decryption failed", extra={
                "event": "decryption_failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise

    def hash_pan_for_search(self, pan: str) -> str:
        """
        Create one-way hash of PAN for searching.

        PCI-DSS Requirement 3.4.1: Render PAN unreadable

        Args:
            pan: Primary Account Number

        Returns:
            SHA-256 hash of PAN
        """
        pan_hash = hashlib.sha256(pan.encode('utf-8')).hexdigest()

        logger.info("PAN hashed", extra={
            "event": "pan_hashed",
            "algorithm": "SHA-256",
            "timestamp": datetime.utcnow().isoformat()
        })

        return pan_hash

    def _validate_pan(self, pan: str) -> bool:
        """
        Validate PAN using Luhn algorithm.

        Args:
            pan: Primary Account Number

        Returns:
            True if valid, False otherwise
        """
        # Remove spaces and hyphens
        pan = re.sub(r'[\s-]', '', pan)

        # Check length (13-19 digits)
        if not (13 <= len(pan) <= 19):
            return False

        # Check all numeric
        if not pan.isdigit():
            return False

        # Luhn algorithm
        def luhn_check(number):
            digits = [int(d) for d in str(number)]
            checksum = 0
            for i, digit in enumerate(reversed(digits)):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit
            return checksum % 10 == 0

        return luhn_check(pan)

    def _store_token_mapping(self, token: str, pan: str):
        """
        Store token-to-PAN mapping in secure vault.

        Note: In production, use HSM or external tokenization service
        """
        # This would typically interface with a secure token vault
        # For demonstration purposes only
        pass
```

---

## Requirement 4: Protect Cardholder Data in Transit

```python
import ssl
import socket
from typing import Tuple

class SecureTransmissionManager:
    """
    Protect cardholder data during transmission.

    PCI-DSS Requirement 4: Protect cardholder data with strong cryptography
    PCI-DSS Requirement 4.2.1: Use strong cryptography (TLS 1.2+)
    """

    def __init__(self):
        self.min_tls_version = ssl.TLSVersion.TLSv1_2
        self.allowed_ciphers = [
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES256-SHA384'
        ]

    def create_secure_context(self) -> ssl.SSLContext:
        """
        Create SSL context with PCI-DSS compliant settings.

        PCI-DSS Requirement 4.2.1: Strong cryptography
        PCI-DSS Requirement 4.2.1.1: TLS 1.2 or higher

        Returns:
            Configured SSL context
        """
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Set minimum TLS version to 1.2
        context.minimum_version = self.min_tls_version

        # Disable weak ciphers
        context.set_ciphers(':'.join(self.allowed_ciphers))

        # Require certificate validation
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        # Load system certificates
        context.load_default_certs()

        logger.info("Secure SSL context created", extra={
            "event": "ssl_context_created",
            "min_tls_version": "TLS 1.2",
            "timestamp": datetime.utcnow().isoformat()
        })

        return context

    def validate_tls_connection(self, hostname: str, port: int = 443) -> Dict:
        """
        Validate TLS configuration of endpoint.

        PCI-DSS Requirement 4.2: Verify TLS implementation

        Args:
            hostname: Target hostname
            port: Target port

        Returns:
            Validation results
        """
        context = self.create_secure_context()

        try:
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cipher = ssock.cipher()
                    version = ssock.version()

                    # Check TLS version
                    tls_compliant = version in ["TLSv1.2", "TLSv1.3"]

                    # Check cipher strength
                    cipher_compliant = cipher[0] in self.allowed_ciphers

                    logger.info("TLS connection validated", extra={
                        "event": "tls_validated",
                        "hostname": hostname,
                        "tls_version": version,
                        "cipher": cipher[0],
                        "compliant": tls_compliant and cipher_compliant,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    return {
                        "tls_version": version,
                        "cipher": cipher[0],
                        "key_bits": cipher[2],
                        "compliant": tls_compliant and cipher_compliant
                    }
        except Exception as e:
            logger.error("TLS validation failed", extra={
                "event": "tls_validation_failed",
                "hostname": hostname,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
```

---

## Requirement 8: Identify Users and Authenticate Access

```python
import pyotp
import secrets
from datetime import datetime, timedelta

class PCIAuthenticationManager:
    """
    Implement strong authentication.

    PCI-DSS Requirement 8: Identify users and authenticate access
    PCI-DSS Requirement 8.3.6: Multi-factor authentication (MFA)
    """

    def __init__(self):
        self.password_min_length = 12
        self.password_max_age_days = 90
        self.lockout_threshold = 6  # PCI-DSS 8.3.4: Lock after 6 attempts
        self.lockout_duration_minutes = 30

    def generate_mfa_secret(self, user_id: str, user_email: str) -> Dict:
        """
        Generate MFA secret for user.

        PCI-DSS Requirement 8.3.6: MFA for admin access to CDE

        Args:
            user_id: User identifier
            user_email: User email

        Returns:
            MFA secret and QR code URI
        """
        # Generate secret
        secret = pyotp.random_base32()

        # Create TOTP URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="PCI-DSS Application"
        )

        logger.info("MFA secret generated", extra={
            "event": "mfa_secret_generated",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri
        }

    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """
        Verify MFA token.

        Args:
            secret: User's MFA secret
            token: Token from authenticator app

        Returns:
            True if valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        valid = totp.verify(token, valid_window=1)

        logger.info("MFA token verified", extra={
            "event": "mfa_token_verified",
            "valid": valid,
            "timestamp": datetime.utcnow().isoformat()
        })

        return valid

    def validate_password_complexity(self, password: str) -> Tuple[bool, list]:
        """
        Validate password complexity.

        PCI-DSS Requirement 8.3.6: Password complexity
        - Minimum 12 characters (or 8 if system doesn't support 12)
        - Numeric and alphabetic characters

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, violations)
        """
        violations = []

        # Minimum length
        if len(password) < self.password_min_length:
            violations.append(f"Password must be at least {self.password_min_length} characters")

        # Contains numeric
        if not any(c.isdigit() for c in password):
            violations.append("Password must contain at least one number")

        # Contains alphabetic
        if not any(c.isalpha() for c in password):
            violations.append("Password must contain at least one letter")

        # Contains uppercase
        if not any(c.isupper() for c in password):
            violations.append("Password must contain at least one uppercase letter")

        # Contains lowercase
        if not any(c.islower() for c in password):
            violations.append("Password must contain at least one lowercase letter")

        is_valid = len(violations) == 0

        if not is_valid:
            logger.warning("Password complexity validation failed", extra={
                "event": "password_validation_failed",
                "violations": violations,
                "timestamp": datetime.utcnow().isoformat()
            })

        return is_valid, violations

    def check_password_expiry(self, user_id: str, last_changed: datetime) -> bool:
        """
        Check if password has expired.

        PCI-DSS Requirement 8.3.9: Password change every 90 days

        Args:
            user_id: User identifier
            last_changed: When password was last changed

        Returns:
            True if expired, False otherwise
        """
        age_days = (datetime.utcnow() - last_changed).days
        expired = age_days >= self.password_max_age_days

        if expired:
            logger.warning("Password expired", extra={
                "event": "password_expired",
                "user_id": user_id,
                "age_days": age_days,
                "max_age_days": self.password_max_age_days,
                "timestamp": datetime.utcnow().isoformat()
            })

        return expired
```

---

## Requirement 10: Log and Monitor All Access

```python
import json
from enum import Enum

class PCIEventType(Enum):
    """PCI-DSS logging event types."""
    USER_ACCESS_CDE = "user_access_cde"
    PRIVILEGED_ACTION = "privileged_action"
    ACCESS_CARDHOLDER_DATA = "access_cardholder_data"
    SYSTEM_CHANGE = "system_change"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHENTICATION_SUCCESS = "authentication_success"

class PCIAuditLogger:
    """
    Comprehensive audit logging for PCI-DSS compliance.

    PCI-DSS Requirement 10: Log and monitor all access
    PCI-DSS Requirement 10.2: Implement audit trails
    """

    def log_cde_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        success: bool,
        ip_address: str
    ):
        """
        Log access to Cardholder Data Environment.

        PCI-DSS Requirement 10.2.1: User access to CHD
        PCI-DSS Requirement 10.3: Record audit trail entries

        Args:
            user_id: User identifier
            action: Action performed (read, write, delete)
            resource: Resource accessed
            success: Whether action succeeded
            ip_address: Source IP address
        """
        audit_entry = {
            "event_type": PCIEventType.USER_ACCESS_CDE.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "success": success,
            "ip_address": ip_address,
            "event_id": str(uuid.uuid4())
        }

        logger.warning("CDE access logged", extra=audit_entry)

        # Store in tamper-proof audit log
        self._store_audit_entry(audit_entry)

    def log_privileged_action(
        self,
        user_id: str,
        action: str,
        target_system: str,
        justification: str
    ):
        """
        Log actions by privileged users.

        PCI-DSS Requirement 10.2.2: Actions by privileged users

        Args:
            user_id: Administrator user ID
            action: Administrative action
            target_system: System affected
            justification: Business justification
        """
        audit_entry = {
            "event_type": PCIEventType.PRIVILEGED_ACTION.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "target_system": target_system,
            "justification": justification,
            "event_id": str(uuid.uuid4())
        }

        logger.warning("Privileged action logged", extra=audit_entry)
        self._store_audit_entry(audit_entry)

    def _store_audit_entry(self, entry: Dict):
        """
        Store audit entry in tamper-proof log.

        PCI-DSS Requirement 10.5.3: Protect audit trails
        Note: In production, use WORM storage or external SIEM
        """
        # Store in centralized logging system
        # Use write-once-read-many (WORM) storage
        # Sign entries with cryptographic hash
        pass
```

---

## Success Criteria

- [ ] PAN never stored in clear text
- [ ] PAN masked when displayed (show first 6, last 4 only)
- [ ] Strong cryptography used (AES-256-GCM, TLS 1.2+)
- [ ] MFA enforced for CDE access
- [ ] Password complexity enforced (12+ chars, numeric, alphabetic)
- [ ] Passwords expire after 90 days
- [ ] Account lockout after 6 failed attempts
- [ ] All CDE access logged with audit trail
- [ ] Logs protected from tampering
- [ ] Quarterly vulnerability scans passed

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
