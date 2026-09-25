"""
Integration tests for the F-010 SQL repositories.

These cover the two behaviours that only a real database can demonstrate: the atomic
credit charge and the atomic validation-budget charge. Both are read-modify-write hazards
that unit tests with mocked repositories cannot see.

Run with: pytest -m e2e
"""

import asyncio
import base64
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.features.ai_config.domain.entities.user_api_key_entity import UserApiKeyEntity
from src.app.features.ai_config.domain.services.key_validation_throttle import KeyValidationThrottle
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.features.ai_config.infrastructure.crypto.key_decryption import decrypt_user_key
from src.app.features.ai_config.infrastructure.repositories.sql_key_validation_attempt_repository import (
    SqlKeyValidationAttemptRepository,
)
from src.app.features.ai_config.infrastructure.repositories.user_api_key_repository_impl import UserApiKeyRepositoryImpl
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.infrastructure.security.api_key_cipher import ApiKeyCipher


RAW_KEY = "sk-proj-abcdefghijklmnopqrstuv1234"
REPLACEMENT_KEY = "sk-proj-zyxwvutsrqponmlkjihgf9876"


def build_cipher() -> ApiKeyCipher:
    return ApiKeyCipher(base64.b64encode(os.urandom(32)).decode())


async def create_user(session: AsyncSession, email: str) -> UserEntity:
    user = UserEntity.create(
        email=email,
        display_name="Credit Test User",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )
    saved = await UserRepositoryImpl(session).save(user)
    assert saved is not None
    return saved


@pytest.fixture
async def session(test_engine) -> AsyncSession:
    """
    A session these repositories can commit through.

    The shared `db_session` fixture wraps each test in an outer transaction it rolls back,
    which the credit and budget repositories close the moment they commit — and committing
    is the whole point here, since the atomicity being tested lives in the commit. Rows are
    therefore left behind; each test uses a distinct email, and the session-scoped
    `test_engine` downgrades the schema when the suite ends.
    """
    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as active_session:
        yield active_session


@pytest.mark.e2e
@pytest.mark.asyncio
class TestUserApiKeyRepositoryIntegration:
    """Storage of encrypted provider keys against a real database."""

    async def test_upsert_then_read_back_round_trips_the_key(self, session: AsyncSession):
        user = await create_user(session, "keys-roundtrip@test.com")
        cipher = build_cipher()
        repository = UserApiKeyRepositoryImpl(session)

        encrypted = await cipher.encrypt(RAW_KEY, str(user.id.value))
        await repository.upsert(
            UserApiKeyEntity.create(
                user_id=user.id,
                provider=AIProvider.OPENAI,
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=RAW_KEY,
            )
        )

        stored = await repository.find_by_user_and_provider(user.id, AIProvider.OPENAI)

        assert stored is not None
        assert stored.masked_key == "sk-proj***...1234"
        assert await decrypt_user_key(cipher, stored, str(user.id.value)) == RAW_KEY

    async def test_no_plaintext_key_is_stored_in_the_row(self, session: AsyncSession):
        """NFR-010-01: a database dump must not yield the key."""
        user = await create_user(session, "keys-ciphertext@test.com")
        cipher = build_cipher()
        repository = UserApiKeyRepositoryImpl(session)

        encrypted = await cipher.encrypt(RAW_KEY, str(user.id.value))
        await repository.upsert(
            UserApiKeyEntity.create(
                user_id=user.id,
                provider=AIProvider.GEMINI,
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=RAW_KEY,
            )
        )

        row = (
            await session.execute(
                text("SELECT encrypted_key, masked_key FROM user_api_keys WHERE user_id = :uid"),
                {"uid": user.id.value},
            )
        ).one()

        assert RAW_KEY.encode() not in bytes(row.encrypted_key)
        assert RAW_KEY not in row.masked_key

    async def test_rotating_replaces_the_row_rather_than_adding_one(self, session: AsyncSession):
        """US-EP6-BE-003: no second row may hold the superseded secret."""
        user = await create_user(session, "keys-rotate@test.com")
        cipher = build_cipher()
        repository = UserApiKeyRepositoryImpl(session)
        user_id = str(user.id.value)

        first = await cipher.encrypt(RAW_KEY, user_id)
        await repository.upsert(
            UserApiKeyEntity.create(
                user_id=user.id,
                provider=AIProvider.OPENAI,
                ciphertext=first.ciphertext,
                nonce=first.nonce,
                key_version=first.key_version,
                raw_key=RAW_KEY,
            )
        )

        stored = await repository.find_by_user_and_provider(user.id, AIProvider.OPENAI)
        assert stored is not None
        second = await cipher.encrypt(REPLACEMENT_KEY, user_id)
        stored.replace_secret(
            ciphertext=second.ciphertext,
            nonce=second.nonce,
            key_version=second.key_version,
            raw_key=REPLACEMENT_KEY,
        )
        await repository.upsert(stored)

        count = (
            await session.execute(
                text("SELECT count(*) FROM user_api_keys WHERE user_id = :uid"),
                {"uid": user.id.value},
            )
        ).scalar_one()
        rotated = await repository.find_by_user_and_provider(user.id, AIProvider.OPENAI)

        assert count == 1
        assert rotated is not None
        assert await decrypt_user_key(cipher, rotated, user_id) == REPLACEMENT_KEY

    async def test_delete_removes_the_row_entirely(self, session: AsyncSession):
        """NFR-010-04 requires a hard delete, so the row must be gone, not flagged."""
        user = await create_user(session, "keys-delete@test.com")
        cipher = build_cipher()
        repository = UserApiKeyRepositoryImpl(session)

        encrypted = await cipher.encrypt(RAW_KEY, str(user.id.value))
        await repository.upsert(
            UserApiKeyEntity.create(
                user_id=user.id,
                provider=AIProvider.DEEPSEEK,
                ciphertext=encrypted.ciphertext,
                nonce=encrypted.nonce,
                key_version=encrypted.key_version,
                raw_key=RAW_KEY,
            )
        )

        assert await repository.delete(user.id, AIProvider.DEEPSEEK) is True

        count = (
            await session.execute(
                text("SELECT count(*) FROM user_api_keys WHERE user_id = :uid"),
                {"uid": user.id.value},
            )
        ).scalar_one()
        assert count == 0
        assert await repository.delete(user.id, AIProvider.DEEPSEEK) is False


@pytest.mark.e2e
@pytest.mark.asyncio
class TestAtomicCreditCharge:
    """The credit charge must hold under concurrency (the point of the conditional UPDATE)."""

    async def test_charging_returns_the_new_balance(self, session: AsyncSession):
        user = await create_user(session, "credits-basic@test.com")
        repository = UserRepositoryImpl(session)

        assert await repository.consume_ai_credit(user.id) == 4
        assert await repository.consume_ai_credit(user.id) == 3

    async def test_charging_refuses_once_the_balance_is_spent(self, session: AsyncSession):
        user = await create_user(session, "credits-exhausted@test.com")
        repository = UserRepositoryImpl(session)

        for _ in range(5):
            await repository.consume_ai_credit(user.id)

        # None, not a negative balance: the guard is in the WHERE clause.
        assert await repository.consume_ai_credit(user.id) is None
        refreshed = await repository.find_by_id(user.id)
        assert refreshed is not None
        assert refreshed.ai_credits_remaining == 0

    async def test_concurrent_charges_each_spend_their_own_credit(self, test_engine):
        """
        Five simultaneous refinements must cost five credits, not one.

        Each task needs its own session, since a single session serializes statements and
        would hide exactly the interleaving this guards against.
        """
        session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as setup_session:
            user = await create_user(setup_session, "credits-concurrent@test.com")
            await setup_session.commit()

        async def charge_once() -> int | None:
            async with session_maker() as session:
                return await UserRepositoryImpl(session).consume_ai_credit(user.id)

        results = await asyncio.gather(*(charge_once() for _ in range(5)))

        assert sorted(r for r in results if r is not None) == [0, 1, 2, 3, 4]

        async with session_maker() as session:
            refreshed = await UserRepositoryImpl(session).find_by_id(user.id)
            assert refreshed is not None
            assert refreshed.ai_credits_remaining == 0

    async def test_concurrent_charges_cannot_overdraw(self, test_engine):
        """With one credit left, only one of many simultaneous runs may be charged."""
        session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as setup_session:
            user = await create_user(setup_session, "credits-overdraw@test.com")
            repository = UserRepositoryImpl(setup_session)
            for _ in range(4):
                await repository.consume_ai_credit(user.id)
            await setup_session.commit()

        async def charge_once() -> int | None:
            async with session_maker() as session:
                return await UserRepositoryImpl(session).consume_ai_credit(user.id)

        results = await asyncio.gather(*(charge_once() for _ in range(5)))

        assert [r for r in results if r is not None] == [0]

    async def test_charging_does_not_touch_other_columns(self, session: AsyncSession):
        """
        A credit charge must not roll back a concurrent password change or forced logout.

        The refinement's user snapshot can be tens of seconds stale, so writing the whole
        row would resurrect the old password hash and revalidate revoked refresh tokens.
        """
        user = await create_user(session, "credits-isolation@test.com")
        repository = UserRepositoryImpl(session)

        # Simulate the concurrent password reset that lands mid-refinement.
        user.update_details(password_hash="rotated-hash")
        user.revoke_sessions()
        await repository.update(user)

        await repository.consume_ai_credit(user.id)

        refreshed = await repository.find_by_id(user.id)
        assert refreshed is not None
        assert refreshed.password_hash == "rotated-hash"
        assert refreshed.token_version == user.token_version
        assert refreshed.ai_credits_remaining == 4


@pytest.mark.e2e
@pytest.mark.asyncio
class TestAtomicValidationBudget:
    """The 5-per-hour budget must hold under concurrency (NFR-010-03)."""

    async def test_charges_increment_within_the_window(self, session: AsyncSession):
        user = await create_user(session, "budget-basic@test.com")
        repository = SqlKeyValidationAttemptRepository(session)
        user_id = str(user.id.value)

        assert (await repository.charge(user_id, 60)).attempt_count == 1
        assert (await repository.charge(user_id, 60)).attempt_count == 2

    async def test_the_window_rolls_once_it_has_expired(self, session: AsyncSession):
        user = await create_user(session, "budget-rollover@test.com")
        repository = SqlKeyValidationAttemptRepository(session)
        user_id = str(user.id.value)

        await repository.charge(user_id, 60)
        # Backdate the window rather than waiting an hour.
        await session.execute(
            text("UPDATE api_key_validation_attempts SET window_started_at = :opened WHERE id = :uid"),
            {"opened": datetime.now(tz=UTC) - timedelta(hours=2), "uid": user.id.value},
        )
        await session.commit()

        assert (await repository.charge(user_id, 60)).attempt_count == 1

    async def test_the_throttle_blocks_the_sixth_attempt(self, session: AsyncSession):
        user = await create_user(session, "budget-blocks@test.com")
        throttle = KeyValidationThrottle(SqlKeyValidationAttemptRepository(session))
        user_id = str(user.id.value)

        for _ in range(KeyValidationThrottle.MAX_ATTEMPTS):
            await throttle.consume(user_id)

        from src.app.features.ai_config.domain.exceptions.ai_config_exceptions import KeyValidationRateLimitedError

        with pytest.raises(KeyValidationRateLimitedError):
            await throttle.consume(user_id)

    async def test_concurrent_charges_each_count(self, test_engine):
        """
        Ten simultaneous validations must consume ten attempts, not one.

        A SELECT-then-UPDATE would let them all read the same count and collapse into a
        single charge, leaving provider probing effectively unmetered.
        """
        session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as setup_session:
            user = await create_user(setup_session, "budget-concurrent@test.com")
            await setup_session.commit()

        user_id = str(user.id.value)

        async def charge_once() -> int:
            async with session_maker() as session:
                charged = await SqlKeyValidationAttemptRepository(session).charge(user_id, 60)
                return charged.attempt_count

        counts = await asyncio.gather(*(charge_once() for _ in range(10)))

        assert sorted(counts) == list(range(1, 11))
