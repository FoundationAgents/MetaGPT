# CCS Security Integration for MetaGPT

[CCS (Cross-framework Command Security)](https://github.com/Correctover/ccs-verifier) provides sub-millisecond runtime verification for AI Agent command execution, protecting against RCE, SSRF, and credential leakage attacks.

## Integration

`ccs_guard.py` wraps MetaGPT's `shell_execute()` with CCS verification:

```python
from examples.ccs_security.ccs_guard import safe_shell_execute

# CCS verifies the command before execution
stdout, stderr, rc = await safe_shell_execute("curl https://api.example.com/data")

# Dangerous commands are blocked:
# safe_shell_execute("curl http://169.254.169.254/latest/meta-data/")
# → ("", "[CCS] Command denied: SSRF: cloud metadata access", -1)
```

## Install

```bash
pip install ccs-verifier
```

## How It Works

1. Command is passed to CCS `Verifier` with built-in rules (RCE, SSRF, CredentialLeak)
2. CCS performs in-process semantic verification (~7.5μs P50 latency)
3. Safe commands proceed to MetaGPT's `shell_execute()`
4. Dangerous commands are blocked with detailed reason

## Reference

- [CCS IETF Draft](https://datatracker.ietf.org/doc/draft-correctover-ccs/)
- [CCS Zenodo DOI](https://doi.org/10.5281/zenodo.21783723)
