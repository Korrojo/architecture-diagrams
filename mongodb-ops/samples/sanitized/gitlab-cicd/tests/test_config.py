from pathlib import Path

import pytest

from mongodb_cicd.config import (
    ConfigurationError,
    load_environment_config,
    resolve_environment,
)


def test_resolve_environment_accepts_allow_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_ENV", "SAT")
    assert resolve_environment() == "sat"
    assert resolve_environment("dev") == "dev"


def test_resolve_environment_rejects_paths() -> None:
    with pytest.raises(ConfigurationError):
        resolve_environment("../../prod")


def test_load_sample_environment() -> None:
    config = load_environment_config("dev")
    assert config["mongodb"]["collection"] == "orders"
    assert config["ops_manager"]["role_name"] == "ordersCollectionReader"


def test_environment_file_must_match_requested_environment(tmp_path: Path) -> None:
    directory = tmp_path / "config" / "environments"
    directory.mkdir(parents=True)
    (directory / "dev.yml").write_text("environment: prod\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="must equal"):
        load_environment_config("dev", tmp_path)
