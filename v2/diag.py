"""Credential resolver diagnostic.

Prints exactly what DotEnvProvider sees, in the order it checks. Run from
the same shell and cwd you use to run t3_smoke_test.py. If the 'winner'
key tail does not match the new key, the source line above it tells you
where the wrong key is coming from.

No secrets are printed in full. Only length and last 6 chars.
"""
import os
import sys
from pathlib import Path
from dotenv import dotenv_values

# Match what t3_smoke_test.py does: import the actual provider so we test
# the real resolver, not a reimplementation.
from usai_harness.key_manager import DotEnvProvider, user_config_env_path

ENV_VAR = "USAI_API_KEY"

print(f"=== cwd: {Path.cwd()} ===")
print(f"=== sys.executable: {sys.executable} ===")
print()

# Source 1: project-local .env at cwd
project_env = Path.cwd() / ".env"
print(f"[1] Project .env: {project_env}")
print(f"    exists: {project_env.exists()}")
if project_env.exists():
    vals = dotenv_values(project_env)
    k = (vals.get(ENV_VAR) or "").strip()
    print(f"    {ENV_VAR}: length={len(k)}, last6={k[-6:]!r}" if k else f"    {ENV_VAR}: empty or missing")

# Source 2: user-level .env
user_env = user_config_env_path()
print(f"[2] User-level .env: {user_env}")
print(f"    exists: {user_env.exists()}")
if user_env.exists():
    vals = dotenv_values(user_env)
    k = (vals.get(ENV_VAR) or "").strip()
    print(f"    {ENV_VAR}: length={len(k)}, last6={k[-6:]!r}" if k else f"    {ENV_VAR}: empty or missing")

# Source 3: os.environ
os_val = os.environ.get(ENV_VAR, "").strip()
print(f"[3] os.environ['{ENV_VAR}']: ", end="")
print(f"length={len(os_val)}, last6={os_val[-6:]!r}" if os_val else "unset or empty")

print()

# Now run the actual resolver and report what it returns.
provider = DotEnvProvider({"usai": ENV_VAR})
try:
    winner = provider.get_key("usai")
    print(f"=== Resolver returned: length={len(winner)}, last6={winner[-6:]!r} ===")
except Exception as e:
    print(f"=== Resolver raised: {e} ===")
