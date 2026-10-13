import pytest

from acheron import config
from acheron.config import (
    OPENROUTER_DECISIONS_URL,
    Config,
    decision_key,
    is_loopback,
    validate_decisions_url,
)

ACHERON_VARS = (
    "ACHERON_PROVIDER",
    "ACHERON_MODEL",
    "ACHERON_DECISIONS_URL",
    "ACHERON_DECISIONS_KEY",
    "ACHERON_RANKING",
    "OPENROUTER_API_KEY",
)


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """No Acheron variables and no stored OpenCode key, whatever the machine has."""
    for name in ACHERON_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config, "_AUTH_PATH", tmp_path / "missing-auth.json")
    return monkeypatch


def test_default_config_targets_openrouter_with_mercury(clean_env):
    cfg = Config.from_env()
    assert cfg.provider == "mercury"
    assert cfg.model == "inception/mercury-decide:free"
    assert cfg.decisions_url == OPENROUTER_DECISIONS_URL
    assert OPENROUTER_DECISIONS_URL == "https://openrouter.ai/api/alpha/decisions"


def test_perplexity_preset_resolves_its_model(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "perplexity")
    cfg = Config.from_env()
    assert cfg.model == "perplexity/pplx-decider-v1.1-27b"
    assert cfg.decisions_url == OPENROUTER_DECISIONS_URL


def test_unknown_provider_is_rejected(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "gpt")
    with pytest.raises(ValueError, match="ACHERON_PROVIDER"):
        Config.from_env()


def test_custom_provider_requires_a_url(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "custom")
    clean_env.setenv("ACHERON_MODEL", "openjev")
    with pytest.raises(ValueError, match="ACHERON_DECISIONS_URL"):
        Config.from_env()


def test_custom_provider_requires_a_model(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "custom")
    clean_env.setenv("ACHERON_DECISIONS_URL", "http://127.0.0.1:9931/v1/systemone")
    with pytest.raises(ValueError, match="ACHERON_MODEL"):
        Config.from_env()


def test_custom_provider_accepts_a_local_server_without_a_key(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "custom")
    clean_env.setenv("ACHERON_MODEL", "openjev")
    clean_env.setenv("ACHERON_DECISIONS_URL", "http://127.0.0.1:9931/v1/systemone")
    cfg = Config.from_env()
    assert cfg.provider == "custom"
    assert cfg.model == "openjev"
    assert cfg.decisions_url == "http://127.0.0.1:9931/v1/systemone"
    assert cfg.decisions_key is None


def test_decisions_key_is_read_from_its_own_variable(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "custom")
    clean_env.setenv("ACHERON_MODEL", "jev-latest")
    clean_env.setenv("ACHERON_DECISIONS_URL", "https://api.example.test/v1/systemone")
    clean_env.setenv("ACHERON_DECISIONS_KEY", "vendor-key")
    assert Config.from_env().decisions_key == "vendor-key"


def test_plain_http_to_a_remote_host_is_rejected(clean_env):
    clean_env.setenv("ACHERON_PROVIDER", "custom")
    clean_env.setenv("ACHERON_MODEL", "m")
    clean_env.setenv("ACHERON_DECISIONS_URL", "http://api.example.test/v1/systemone")
    with pytest.raises(ValueError, match="https"):
        Config.from_env()


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.test/v1/systemone",
        "http://127.0.0.1:9931/v1/systemone",
        "http://localhost:1234/v1/systemone",
        "http://[::1]:1234/v1/systemone",
    ],
)
def test_validate_accepts_https_and_loopback_http(url):
    assert validate_decisions_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://api.example.test/v1/systemone",
        "ftp://127.0.0.1/x",
        "api.example.test/v1/systemone",
        "https:///v1/systemone",
        "http://127.0.0.1.example.test/v1/systemone",
        "http://localhost.example.test/v1/systemone",
        "http://127.0.0.1:99999/v1/systemone",
        "http://127.0.0.1:port/v1/systemone",
        "https://api.example.test:0/v1/systemone",
        "https://user:secret@api.example.test/v1/systemone",
        "https://token@api.example.test/v1/systemone",
    ],
)
def test_validate_rejects_insecure_or_malformed_urls(url):
    with pytest.raises(ValueError):
        validate_decisions_url(url)


def test_loopback_detection_is_exact_host_match():
    assert is_loopback("http://127.0.0.1:9931/v1/systemone")
    assert is_loopback("http://localhost/v1/systemone")
    assert not is_loopback("http://localhost.example.test/v1/systemone")
    assert not is_loopback("https://api.example.test/?next=localhost")


def test_openrouter_key_goes_to_openrouter():
    assert (
        decision_key(OPENROUTER_DECISIONS_URL, openrouter_key="or-key", decisions_key=None)
        == "or-key"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.test/v1/systemone",
        "http://127.0.0.1:9931/v1/systemone",
        "https://openrouter.ai.example.test/api/alpha/decisions",
        "https://example.test/openrouter.ai/api/alpha/decisions",
        "https://openrouter.ai@example.test/api/alpha/decisions",
        "https://notopenrouter.ai/api/alpha/decisions",
    ],
)
def test_openrouter_key_never_goes_to_another_host(url):
    assert decision_key(url, openrouter_key="or-key", decisions_key=None) is None


def test_other_hosts_receive_only_the_dedicated_key():
    key = decision_key(
        "https://api.example.test/v1/systemone",
        openrouter_key="or-key",
        decisions_key="vendor-key",
    )
    assert key == "vendor-key"
