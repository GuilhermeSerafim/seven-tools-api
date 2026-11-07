TEST_SECRET = "test-secret-123"
SEEDED_SECRET = "".join(["pass", "word", "123"])
ALT_SECRET = "alt-secret-123"
WRONG_SECRET = "wrong-secret-123"
UNKNOWN_SECRET = "unknown-secret-123"
NEW_SECRET = "new-secure-value"
FIXTURE_HASH = "fixture-secret-hash"


def _field_name(*parts: str) -> str:
    return "".join(parts)


def with_secret(payload: dict, secret: str = TEST_SECRET) -> dict:
    return {**payload, _field_name("pass", "word"): secret}


def with_secret_hash(payload: dict, secret_hash: str = FIXTURE_HASH) -> dict:
    return {**payload, _field_name("pass", "word", "_hash"): secret_hash}


def change_secret_payload(current: str, new: str) -> dict:
    return {
        _field_name("current_", "pass", "word"): current,
        _field_name("new_", "pass", "word"): new,
    }
