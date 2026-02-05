# Copyright (c) Agent-Mesh Contributors. All rights reserved.
# Licensed under the Apache License 2.0.
"""Agent-Mesh Trust Integration for MetaGPT.

Provides inter-agent trust verification for MetaGPT multi-agent teams.
"""

from .trust_layer import (
    TrustedRole,
    TrustPolicy,
    TrustVerifier,
    TrustedTeam,
    TrustViolationError,
)

__all__ = [
    "TrustedRole",
    "TrustPolicy",
    "TrustVerifier",
    "TrustedTeam",
    "TrustViolationError",
]

__version__ = "0.1.0"
