"""Standalone test for the password_auth_callback added in #2070.

Uses sys.modules stubs to avoid pulling in the chainlit package
(which requires PyYAML, literalai, syncer, watchfiles, ... and a running DB).

Run:
    python3 tests/examples/test_password_auth_callback.py
"""
import importlib.util
import os
import sys
import unittest
from unittest import mock


def _load_app_module():
    """Load examples/ui_with_chainlit/app.py with chainlit stubbed out."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    app_path = os.path.join(repo_root, "examples", "ui_with_chainlit", "app.py")

    captured = {"password_auth_callback": None, "set_chat_profiles": None}

    class _ClUser:
        def __init__(self, identifier):
            self.identifier = identifier

    class _ChainlitStub:
        User = _ClUser

        @staticmethod
        def password_auth_callback(fn):
            captured["password_auth_callback"] = fn
            return fn

        @staticmethod
        def set_chat_profiles(fn):
            captured["set_chat_profiles"] = fn
            return fn

        @staticmethod
        def on_message(fn):
            return fn

        # The remaining attributes are accessed as class namespaces at import
        # time (e.g. `cl.ChatProfile`, `cl.Starter`, `cl.Message`); they don't
        # need real implementations, just a usable class object.
        class ChatProfile: ...
        class Starter: ...
        class Message: ...

    sys.modules["chainlit"] = _ChainlitStub
    sys.modules["init_setup"] = mock.MagicMock()
    sys.modules.setdefault("metagpt", mock.MagicMock())
    sys.modules.setdefault("metagpt.roles", mock.MagicMock())
    sys.modules.setdefault("metagpt.team", mock.MagicMock())

    spec = importlib.util.spec_from_file_location("_app_under_test", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, captured


_callback = None


def setUpModule():
    global _callback
    _, captured = _load_app_module()
    _callback = captured["password_auth_callback"]
    assert _callback is not None, "password_auth_callback was not registered by app.py"


class TestPasswordAuthCallback(unittest.TestCase):
    def _call(self, *args):
        """Invoke the module-level callback directly (not through self)."""
        return _callback(*args)

    def test_correct_credentials_returns_user(self):
        """Matching username/password returns a cl.User with that identifier."""
        with mock.patch.dict(
            os.environ, {"CHAINLIT_USERNAME": "alice", "CHAINLIT_PASSWORD": "wonderland"}
        ):
            result = self._call("alice", "wonderland")
        self.assertIsNotNone(result)
        self.assertEqual(result.identifier, "alice")

    def test_wrong_password_returns_none(self):
        with mock.patch.dict(
            os.environ, {"CHAINLIT_USERNAME": "alice", "CHAINLIT_PASSWORD": "wonderland"}
        ):
            self.assertIsNone(self._call("alice", "wrong"))

    def test_wrong_username_returns_none(self):
        with mock.patch.dict(
            os.environ, {"CHAINLIT_USERNAME": "alice", "CHAINLIT_PASSWORD": "wonderland"}
        ):
            self.assertIsNone(self._call("mallory", "wonderland"))

    def test_empty_credentials_returns_none(self):
        with mock.patch.dict(
            os.environ, {"CHAINLIT_USERNAME": "alice", "CHAINLIT_PASSWORD": "wonderland"}
        ):
            self.assertIsNone(self._call("", ""))
            self.assertIsNone(self._call("alice", ""))
            self.assertIsNone(self._call("", "wonderland"))

    def test_falls_back_to_default_when_env_unset(self):
        """When env vars are unset, the default admin/admin must work."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("CHAINLIT_USERNAME", "CHAINLIT_PASSWORD")}
        with mock.patch.dict(os.environ, env, clear=True):
            result = self._call("admin", "admin")
        self.assertIsNotNone(result)
        self.assertEqual(result.identifier, "admin")

    def test_default_rejected_when_env_set(self):
        """If env is set to non-admin values, admin/admin must NOT succeed."""
        with mock.patch.dict(
            os.environ, {"CHAINLIT_USERNAME": "alice", "CHAINLIT_PASSWORD": "wonderland"}
        ):
            self.assertIsNone(self._call("admin", "admin"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
