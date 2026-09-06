### Step 3: Pillar 3 - Security (Least Privilege)

Before writing RBAC or secret-store code, run the three-question triage in [[agent-execution-isolation]]: does this agent spawn a process that needs OS-level isolation, hold credentials that must stay out of its environment, or make tool-driven network calls that need an out-of-process egress boundary? That skill owns the sandbox, credential-broker, and proxy checklists; this pillar records that they were asked.

```python
from functools import wraps
from typing import Callable
import hashlib
import secrets

class AgentRole(Enum):
    READ_ONLY = "read_only"
    STANDARD = "standard"
    ELEVATED = "elevated"
    ADMIN = "admin"

@dataclass
class AgentCredential:
    """Secure credential for AI agent."""
    credential_id: str
    agent_id: str
    role: AgentRole
    api_key_hash: str
    created_at: datetime
    expires_at: datetime
    scopes: List[str]

class AgentSecurityManager:
    """
    AI Agent Security Controls.

    Pillar 3: Least Privilege
    - Service principals for agents
    - Role-based access control (RBAC)
    - Secrets management
    - API key rotation
    """

    def create_agent_credential(
        self,
        agent_id: str,
        role: AgentRole,
        scopes: List[str],
        expires_days: int = 90
    ) -> Dict:
        """
        Create secure credential for agent.

        Least Privilege:
        - Define specific scopes
        - Time-limited credentials
        - Role-based permissions
        """
        # Generate secure API key
        api_key = f"agent_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        credential = AgentCredential(
            credential_id=f"cred_{secrets.token_hex(8)}",
            agent_id=agent_id,
            role=role,
            api_key_hash=api_key_hash,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            scopes=scopes
        )

        # Store credential (hash only, never plain key)
        self.credential_store.save(credential)

        audit_log.info(
            "agent_credential_created",
            agent_id=agent_id,
            credential_id=credential.credential_id,
            role=role.value,
            scopes=scopes,
            expires_at=credential.expires_at.isoformat()
        )

        # Return API key only once (store securely)
        return {
            "credential_id": credential.credential_id,
            "api_key": api_key,  # Only returned at creation
            "expires_at": credential.expires_at.isoformat(),
            "warning": "Store API key securely. It cannot be retrieved again."
        }

    def define_agent_permissions(
        self,
        agent_id: str,
        role: AgentRole
    ) -> Dict[str, List[str]]:
        """
        Define permissions based on agent role.

        RBAC Matrix:
        - READ_ONLY: Query data, no modifications
        - STANDARD: Normal operations
        - ELEVATED: Sensitive operations with approval
        - ADMIN: Full access (rare, audited)
        """
        permission_matrix = {
            AgentRole.READ_ONLY: {
                "data": ["read"],
                "tools": ["query", "search", "retrieve"],
                "actions": []
            },
            AgentRole.STANDARD: {
                "data": ["read", "create"],
                "tools": ["query", "search", "retrieve", "create"],
                "actions": ["respond", "summarize", "analyze"]
            },
            AgentRole.ELEVATED: {
                "data": ["read", "create", "update"],
                "tools": ["query", "search", "retrieve", "create", "update"],
                "actions": ["respond", "summarize", "analyze", "execute"]
            },
            AgentRole.ADMIN: {
                "data": ["read", "create", "update", "delete"],
                "tools": ["*"],
                "actions": ["*"]
            }
        }

        permissions = permission_matrix.get(role, permission_matrix[AgentRole.READ_ONLY])

        # Store permissions
        self._store_agent_permissions(agent_id, permissions)

        return permissions

    def require_permission(self, required_scope: str):
        """
        Decorator to enforce permission checks on agent operations.

        Usage:
        @agent_security.require_permission("data:update")
        def update_customer_record(agent_id, record_id, data):
            ...
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(agent_id: str, *args, **kwargs):
                # Get agent's permissions
                permissions = self._get_agent_permissions(agent_id)

                # Parse scope
                resource, action = required_scope.split(":")

                # Check permission
                if action not in permissions.get(resource, []):
                    audit_log.warning(
                        "agent_permission_denied",
                        agent_id=agent_id,
                        required_scope=required_scope,
                        available_permissions=permissions
                    )
                    raise PermissionError(
                        f"Agent {agent_id} lacks permission: {required_scope}"
                    )

                # Log access
                audit_log.info(
                    "agent_permission_granted",
                    agent_id=agent_id,
                    scope=required_scope
                )

                return func(agent_id, *args, **kwargs)
            return wrapper
        return decorator

    def rotate_credentials(
        self,
        agent_id: str,
        initiated_by: str
    ) -> Dict:
        """
        Rotate agent credentials.

        Best practice:
        - Regular rotation (90 days)
        - Immediate rotation on compromise
        - Zero-downtime rotation
        """
        # Get current credential
        current_cred = self.credential_store.get_active(agent_id)

        if not current_cred:
            raise ValueError(f"No active credential for agent {agent_id}")

        # Create new credential with same permissions
        new_cred = self.create_agent_credential(
            agent_id=agent_id,
            role=current_cred.role,
            scopes=current_cred.scopes
        )

        # Mark old credential for deprecation (grace period)
        current_cred.expires_at = datetime.utcnow() + timedelta(hours=24)
        self.credential_store.update(current_cred)

        audit_log.info(
            "agent_credential_rotated",
            agent_id=agent_id,
            old_credential_id=current_cred.credential_id,
            new_credential_id=new_cred["credential_id"],
            initiated_by=initiated_by
        )

        return new_cred
```
