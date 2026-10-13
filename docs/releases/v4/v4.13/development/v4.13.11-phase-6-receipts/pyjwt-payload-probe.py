"""Exercise GHSA-42vr-xj54-vc7v against the installed PyJWT and print one JSON line.

A deeply nested but valid JSON payload is decoded without signature
verification (the advisory's pre-verification path). An affected PyJWT lets a
RecursionError escape; a fixed one raises a documented PyJWT error. An ordinary
HS256 token must still decode normally.
"""

from __future__ import annotations

import base64
import json
import sys

import jwt


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def nested_token(depth: int) -> str:
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64(("[" * depth + "]" * depth).encode())
    return f"{header}.{payload}.{b64(b'x')}"


result: dict[str, object] = {"pyjwt": jwt.__version__, "python": sys.version.split()[0]}
try:
    jwt.decode(nested_token(20000), options={"verify_signature": False})
    result["nested"] = "decoded"
except RecursionError:
    result["nested"] = "RecursionError (unhandled class leaks)"
except jwt.PyJWTError as exc:
    result["nested"] = f"handled {type(exc).__name__}"

token = jwt.encode({"sub": "probe", "n": 1}, "k" * 32, algorithm="HS256")
claims = jwt.decode(token, "k" * 32, algorithms=["HS256"])
result["ordinary"] = "decoded" if claims == {"sub": "probe", "n": 1} else f"unexpected {claims!r}"
print(json.dumps(result))
