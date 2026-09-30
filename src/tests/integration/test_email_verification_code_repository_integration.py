"""
Integration tests for EmailVerificationCodeRepositoryImpl.

Run with: pytest -m e2e
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from src.app.features.auth.infrastructure.repositories.email_verification_code_repository_impl import (
    EmailVerificationCodeRepositoryImpl,
)
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


async def save_pending_user(db_session: AsyncSession, email: str) -> UserEntity:
    user = UserEntity.create_pending_verification(email=email, display_name="Pending User", password_hash="hashed")
    saved = await UserRepositoryImpl(db_session).save(user)
    assert saved is not None
    return saved


def build_code(user_id: EntityId, expires_in: timedelta = timedelta(minutes=5)) -> EmailVerificationCode:
    return EmailVerificationCode(
        id=EntityId.generate(),
        user_id=user_id,
        code_hash="hashed-code",
        expires_at=datetime.now(UTC) + expires_in,
    )


@pytest.mark.e2e
@pytest.mark.asyncio
class TestEmailVerificationCodeRepositoryIntegration:
    async def test_a_pending_user_round_trips_unverified(self, db_session: AsyncSession):
        user = await save_pending_user(db_session, "roundtrip@test.com")

        found = await UserRepositoryImpl(db_session).find_by_id(user.id.value)

        assert found is not None
        assert found.is_email_verified is False
        assert found.ai_credits_remaining == 0

    async def test_verification_is_persisted_by_update(self, db_session: AsyncSession):
        repository = UserRepositoryImpl(db_session)
        user = await save_pending_user(db_session, "verify@test.com")

        user.verify_email()
        updated = await repository.update(user)

        assert updated is not None
        assert updated.is_email_verified is True
        assert updated.ai_credits_remaining == 5

    async def test_latest_active_code_is_found_and_superseded(self, db_session: AsyncSession):
        repository = EmailVerificationCodeRepositoryImpl(db_session)
        user = await save_pending_user(db_session, "codes@test.com")
        issued = await repository.create(build_code(user.id))

        assert (await repository.find_latest_active_by_user_id(user.id)).id.value == issued.id.value

        await repository.invalidate_active_for_user(user.id)

        assert await repository.find_latest_active_by_user_id(user.id) is None

    async def test_expired_codes_are_not_active(self, db_session: AsyncSession):
        repository = EmailVerificationCodeRepositoryImpl(db_session)
        user = await save_pending_user(db_session, "expired@test.com")
        await repository.create(build_code(user.id, expires_in=timedelta(minutes=-1)))

        assert await repository.find_latest_active_by_user_id(user.id) is None

    async def test_failed_attempts_and_codes_issued_are_counted(self, db_session: AsyncSession):
        repository = EmailVerificationCodeRepositoryImpl(db_session)
        user = await save_pending_user(db_session, "attempts@test.com")
        code = await repository.create(build_code(user.id))
        await repository.create(build_code(user.id))

        code.record_failed_attempt()
        await repository.save(code)

        since = datetime.now(UTC) - timedelta(minutes=15)
        assert await repository.count_created_since(user.id, since) == 2
