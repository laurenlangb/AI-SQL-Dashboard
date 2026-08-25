"""Unit tests for JWT session auth and credential checks."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
from fastapi import HTTPException

from app.auth import (
    COOKIE_NAME,
    JWT_ALGORITHM,
    USER_NAME,
    VALID_EMAIL,
    VALID_PASSWORD,
    check_credentials,
    create_token,
    get_current_user,
    require_user,
)
from app.config import JWT_SECRET


def _request_with_cookie(token=None):
    """Build a fake Request whose .cookies behaves like the real one."""
    cookies = {COOKIE_NAME: token} if token is not None else {}
    return Mock(cookies=cookies)


class CheckCredentialsTests(unittest.TestCase):
    # Login accepts the exact credentials
    def test_correct_credentials_pass(self):
        self.assertTrue(check_credentials(VALID_EMAIL, VALID_PASSWORD))

    # A wrong password is rejected even when the email is correct.
    def test_wrong_password_fails(self):
        self.assertFalse(check_credentials(VALID_EMAIL, "nope"))

    # A wrong email is rejected even when the password is correct.
    def test_wrong_email_fails(self):
        self.assertFalse(check_credentials("someone@else.com", VALID_PASSWORD))


class TokenRoundTripTests(unittest.TestCase):
    # A token issued at login decodes back into the same user identity (name + email).
    def test_create_then_decode_returns_user_payload(self):
        token = create_token()
        request = _request_with_cookie(token)

        user = get_current_user(request)

        self.assertIsNotNone(user)
        self.assertEqual(user["email"], VALID_EMAIL)
        self.assertEqual(user["name"], USER_NAME)


class GetCurrentUserFailureTests(unittest.TestCase):
    # Visitors with no session cookie are treated as unauthenticated.
    def test_no_cookie_returns_none(self):
        self.assertIsNone(get_current_user(_request_with_cookie(None)))

    # A non-JWT string in the cookie is treated as unauthenticated, not crashed on.
    def test_garbage_token_returns_none(self):
        self.assertIsNone(get_current_user(_request_with_cookie("not-a-real-token")))

    # Someone can't fake a login by making their own session cookie.
    def test_token_signed_with_wrong_secret_returns_none(self):
        bad_token = jwt.encode(
            {"email": VALID_EMAIL, "name": USER_NAME},
            "a-different-secret-that-is-32-plus-chars",
            algorithm=JWT_ALGORITHM,
        )
        self.assertIsNone(get_current_user(_request_with_cookie(bad_token)))

    # Tests when a token is expired - does not grant access
    def test_expired_token_returns_none(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_token = jwt.encode(
            {"email": VALID_EMAIL, "name": USER_NAME, "exp": past},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        self.assertIsNone(get_current_user(_request_with_cookie(expired_token)))


class RequireUserTests(unittest.TestCase):
    # Protected API routes return 401 for unauthenticated requests.
    def test_raises_401_when_no_session(self):
        with self.assertRaises(HTTPException) as ctx:
            require_user(_request_with_cookie(None))
        self.assertEqual(ctx.exception.status_code, 401)

    # A valid session lets the protected route through
    def test_returns_payload_when_session_valid(self):
        token = create_token()
        user = require_user(_request_with_cookie(token))
        self.assertEqual(user["email"], VALID_EMAIL)


if __name__ == "__main__":
    unittest.main()
