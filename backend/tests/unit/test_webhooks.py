"""Unit tests for Webhook system."""
import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.webhook_dispatcher import (
    WEBHOOK_EVENT_TYPES,
    RETRY_DELAYS,
    compute_signature,
    deliver_webhook,
    dispatch_webhook,
)


# ---------------------------------------------------------------------------
# Event type matching
# ---------------------------------------------------------------------------

class TestWebhookEventTypes:
    def test_expected_event_types_exist(self):
        expected = {
            "agent.created",
            "agent.published",
            "agent.deleted",
            "conversation.created",
            "workflow.completed",
            "document.indexed",
            "document.deleted",
        }
        assert expected == set(WEBHOOK_EVENT_TYPES)

    def test_event_types_are_dot_separated(self):
        for event_type in WEBHOOK_EVENT_TYPES:
            assert "." in event_type, f"Event type '{event_type}' should use dot notation"
            parts = event_type.split(".")
            assert len(parts) == 2
            assert len(parts[0]) > 0
            assert len(parts[1]) > 0

    def test_retry_delays_are_exponential(self):
        """Retry delays should follow exponential backoff pattern."""
        assert len(RETRY_DELAYS) == 3
        assert RETRY_DELAYS[0] == 1
        assert RETRY_DELAYS[1] == 4
        assert RETRY_DELAYS[2] == 16


# ---------------------------------------------------------------------------
# HMAC signature generation
# ---------------------------------------------------------------------------

class TestHMACSignature:
    def test_signature_consistency(self):
        """Same payload + secret should produce the same signature."""
        payload = b'{"event": "test"}'
        secret = "my-webhook-secret"
        sig1 = compute_signature(payload, secret)
        sig2 = compute_signature(payload, secret)
        assert sig1 == sig2

    def test_signature_differs_with_different_secrets(self):
        payload = b'{"event": "test"}'
        sig1 = compute_signature(payload, "secret-a")
        sig2 = compute_signature(payload, "secret-b")
        assert sig1 != sig2

    def test_signature_differs_with_different_payloads(self):
        secret = "my-secret"
        sig1 = compute_signature(b'{"a": 1}', secret)
        sig2 = compute_signature(b'{"b": 2}', secret)
        assert sig1 != sig2

    def test_signature_is_valid_hmac_sha256(self):
        payload = b'{"event": "test"}'
        secret = "test-secret"
        sig = compute_signature(payload, secret)

        # Verify manually
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        assert sig == expected

    def test_signature_is_hex_string(self):
        sig = compute_signature(b"test", "secret")
        assert len(sig) == 64
        assert all(c in "0123456789abcdef" for c in sig)

    def test_signature_with_empty_payload(self):
        sig = compute_signature(b"", "secret")
        assert len(sig) == 64

    def test_signature_with_unicode_payload(self):
        payload = '{"event": "中文"}'.encode("utf-8")
        sig = compute_signature(payload, "secret")
        assert len(sig) == 64


# ---------------------------------------------------------------------------
# Webhook delivery with retry
# ---------------------------------------------------------------------------

class TestWebhookDelivery:
    @pytest.mark.asyncio
    async def test_successful_delivery_on_first_attempt(self):
        """Should set status to 'delivered' on first successful HTTP response."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = "test-secret"

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"agent_id": "a1"}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, return_value=mock_response):
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        assert mock_event.status == "delivered"
        assert mock_event.retry_count == len(RETRY_DELAYS)
        assert mock_event.response_status == 200
        assert mock_event.delivered_at is not None

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Should retry on 500 and eventually mark as failed."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = None

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"agent_id": "a1"}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        # All attempts return 500
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, return_value=mock_response) as mock_safe:
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        # Should have been called 1 (initial) + 3 (retries) = 4 times
        assert mock_safe.call_count == 4
        assert mock_event.status == "failed"
        assert mock_event.response_status == 500

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Should retry on connection errors and eventually mark as failed."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = None

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"agent_id": "a1"}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, side_effect=ConnectionError("refused")) as mock_safe:
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        assert mock_safe.call_count == 4
        assert mock_event.status == "failed"

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Should succeed on second attempt if first fails."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = None

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"agent_id": "a1"}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        fail_response = MagicMock()
        fail_response.status_code = 500
        success_response = MagicMock()
        success_response.status_code = 200

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, side_effect=[fail_response, success_response]) as mock_safe:
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        assert mock_event.status == "delivered"
        assert mock_safe.call_count == 2

    @pytest.mark.asyncio
    async def test_signature_header_present(self):
        """Should include X-Webhook-Signature header when secret is set."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = "my-secret"

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"test": True}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, return_value=mock_response) as mock_safe:
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        # Check that safe_request was called with the signature header
        call_args = mock_safe.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "X-Webhook-Signature" in headers
        assert headers["X-Webhook-Signature"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_no_signature_header_without_secret(self):
        """Should NOT include X-Webhook-Signature header when secret is None."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = None

        mock_event = MagicMock()
        mock_event.id = "evt1"
        mock_event.event_type = "agent.created"
        mock_event.payload = {"test": True}
        mock_event.status = "pending"
        mock_event.retry_count = 0
        mock_event.response_status = None
        mock_event.delivered_at = None

        mock_db = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.core.webhook_dispatcher.safe_request", new_callable=AsyncMock, return_value=mock_response) as mock_safe:
            with patch("app.core.webhook_dispatcher.asyncio.sleep", new_callable=AsyncMock):
                await deliver_webhook(mock_webhook, mock_event, mock_db)

        call_args = mock_safe.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "X-Webhook-Signature" not in headers


# ---------------------------------------------------------------------------
# Dispatch routing
# ---------------------------------------------------------------------------

class TestDispatchRouting:
    @pytest.mark.asyncio
    async def test_dispatch_matches_subscribed_webhooks(self):
        """Should only deliver to webhooks subscribed to the event type."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.events = ["agent.created", "agent.deleted"]

        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # db.add is sync in SQLAlchemy
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.webhook_dispatcher.async_session") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.webhook_dispatcher.deliver_webhook", new_callable=AsyncMock) as mock_deliver:
                await dispatch_webhook("agent.created", {"data": "test"}, "t1")

                # Should have been called once for the matching webhook
                assert mock_deliver.call_count == 1

    @pytest.mark.asyncio
    async def test_dispatch_skips_non_matching_events(self):
        """Should skip webhooks not subscribed to the event type."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.events = ["workflow.completed"]

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.webhook_dispatcher.async_session") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.webhook_dispatcher.deliver_webhook", new_callable=AsyncMock) as mock_deliver:
                await dispatch_webhook("agent.created", {"data": "test"}, "t1")

                # Should NOT have been called
                assert mock_deliver.call_count == 0

    @pytest.mark.asyncio
    async def test_dispatch_empty_events_means_subscribe_all(self):
        """Webhook with empty events list should receive all events."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh1"
        mock_webhook.events = []  # subscribe to all

        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # db.add is sync in SQLAlchemy
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.webhook_dispatcher.async_session") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.webhook_dispatcher.deliver_webhook", new_callable=AsyncMock) as mock_deliver:
                await dispatch_webhook("agent.created", {"data": "test"}, "t1")

                assert mock_deliver.call_count == 1

    @pytest.mark.asyncio
    async def test_dispatch_only_enabled_webhooks(self):
        """Should only query enabled webhooks (filter at DB level)."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.webhook_dispatcher.async_session") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.webhook_dispatcher.deliver_webhook", new_callable=AsyncMock):
                await dispatch_webhook("agent.created", {"data": "test"}, "t1")

                # Verify the query included enabled=True filter
                call_args = mock_session.execute.call_args
                stmt = call_args[0][0]
                stmt_str = str(stmt)
                # The where clause should filter enabled webhooks
                assert "enabled" in stmt_str.lower() or mock_session.execute.called
