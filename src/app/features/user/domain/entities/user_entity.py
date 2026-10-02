from datetime import UTC, datetime

from src.app.features.user.domain.exceptions.user_exceptions import AICreditsExhaustedError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


# Free platform refinements granted to a new account (F-010 FR-010-01).
INITIAL_AI_CREDITS = 5


class UserEntity(BaseEntity):
    def __init__(
        self,
        id: EntityId,
        email: Email,
        display_name: str,
        password_hash: str,
        role: UserRole = UserRole.VIEWER,
        token_version: int = 0,
        ai_credits_remaining: int = INITIAL_AI_CREDITS,
        ai_credits_granted: int = INITIAL_AI_CREDITS,
        email_verified_at: datetime | None = None,
        workspace_id: EntityId | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        deactivated_at: datetime | None = None,
    ):
        self._email = email
        self._display_name = display_name
        self._password_hash = password_hash
        self._role = role
        self._token_version = token_version
        self._ai_credits_remaining = ai_credits_remaining
        self._ai_credits_granted = ai_credits_granted
        self._email_verified_at = email_verified_at
        self._workspace_id = workspace_id
        self._deactivated_at = deactivated_at
        super().__init__(id, created_at, updated_at)

    @property
    def email(self) -> Email:
        return self._email

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def token_version(self) -> int:
        return self._token_version

    @property
    def ai_credits_remaining(self) -> int:
        return self._ai_credits_remaining

    @property
    def ai_credits_granted(self) -> int:
        return self._ai_credits_granted

    @property
    def email_verified_at(self) -> datetime | None:
        return self._email_verified_at

    @property
    def workspace_id(self) -> EntityId | None:
        return self._workspace_id

    @property
    def deactivated_at(self) -> datetime | None:
        return self._deactivated_at

    @property
    def is_active(self) -> bool:
        return self._deactivated_at is None

    @property
    def is_email_verified(self) -> bool:
        return self._email_verified_at is not None

    @classmethod
    def create(
        cls,
        email: str,
        display_name: str,
        password_hash: str,
        role: UserRole | None = None,
        workspace_id: EntityId | None = None,
    ) -> "UserEntity":
        return cls(
            id=EntityId.generate(),
            email=Email(email),
            display_name=display_name,
            password_hash=password_hash,
            role=role or UserRole.default(),
            ai_credits_remaining=INITIAL_AI_CREDITS,
            ai_credits_granted=INITIAL_AI_CREDITS,
            email_verified_at=datetime.now(UTC),
            workspace_id=workspace_id,
        )

    @classmethod
    def create_workspace_member(
        cls,
        email: str,
        display_name: str,
        password_hash: str,
        role: UserRole,
        workspace_id: EntityId,
    ) -> "UserEntity":
        """
        A teammate or viewer added by a workspace Admin, pending email verification.

        Not verified on creation: with open sign-up any stranger can be an Admin, so an
        Admin's word does not prove the address is theirs to give. Until the person confirms
        it, a real sign-up for the same email replaces this pending account.
        """
        return cls(
            id=EntityId.generate(),
            email=Email(email),
            display_name=display_name,
            password_hash=password_hash,
            role=role,
            ai_credits_remaining=0,
            ai_credits_granted=0,
            email_verified_at=None,
            workspace_id=workspace_id,
        )

    @classmethod
    def create_pending_verification(
        cls,
        email: str,
        display_name: str,
        password_hash: str,
        role: UserRole | None = None,
        workspace_id: EntityId | None = None,
    ) -> "UserEntity":
        """
        A self-registered account that must confirm its email before it can sign in.

        Free credits are withheld until verification (F-010 FR-010-01).
        """
        return cls(
            id=EntityId.generate(),
            email=Email(email),
            display_name=display_name,
            password_hash=password_hash,
            role=role or UserRole.default(),
            ai_credits_remaining=0,
            ai_credits_granted=0,
            email_verified_at=None,
            workspace_id=workspace_id,
        )

    def receives_free_credits(self) -> bool:
        """Admins and members get free platform credits; viewers never do (F-010)."""
        return self._role in (UserRole.ADMIN, UserRole.MEMBER)

    def verify_email(self, granted_credits: int = 0, now: datetime | None = None) -> None:
        """
        Confirm the account's email and set its free platform credits.

        The amount is decided by the caller, which reserves it from the workspace's credit
        ceiling: granting here unconditionally would let one sign-up mint credits by adding
        and removing members.
        """
        self._email_verified_at = now or datetime.now(UTC)
        self._ai_credits_remaining = granted_credits
        self._ai_credits_granted = granted_credits
        self.mark_as_updated()

    def update_details(
        self,
        email: str | None = None,
        display_name: str | None = None,
        password_hash: str | None = None,
        role: UserRole | None = None,
    ) -> None:
        if email is not None:
            self._email = Email(email)
        if display_name is not None:
            self._display_name = display_name
        if password_hash is not None:
            self._password_hash = password_hash
        if role is not None:
            self._role = role
        self.mark_as_updated()

    def has_ai_credits(self) -> bool:
        """Whether a platform refinement can still be charged to this account."""
        return self._ai_credits_remaining > 0

    def consume_ai_credit(self) -> None:
        """
        Spend one free platform credit.

        Callers must invoke this only after the provider has returned successfully:
        FR-010-02 requires a failed refinement to leave the balance untouched.

        Raises:
            AICreditsExhaustedError: If no credits remain.
        """
        if not self.has_ai_credits():
            raise AICreditsExhaustedError

        self._ai_credits_remaining -= 1
        self.mark_as_updated()

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self._role == UserRole.ADMIN

    def belongs_to(self, workspace_id: EntityId) -> bool:
        return self._workspace_id is not None and self._workspace_id.value == workspace_id.value

    def deactivate(self) -> None:
        """Block sign-in and end every session (see revoke_sessions)."""
        self._deactivated_at = datetime.now(UTC)
        self.revoke_sessions()

    def activate(self) -> None:
        """
        Let a deactivated account sign in again.

        The token version is left alone: sessions revoked by deactivate() stay revoked.
        """
        self._deactivated_at = None
        self.mark_as_updated()

    def revoke_sessions(self) -> None:
        """
        Invalidate every refresh token issued before this call (forced logout
        across all devices). Refresh tokens embed the token_version they were
        issued under; bumping it makes older tokens fail validation.
        """
        self._token_version += 1
        self.mark_as_updated()
