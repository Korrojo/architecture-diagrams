import json
from pathlib import Path

import pytest

from mongodb_local_cicd.cli import require_environment_confirmation
from mongodb_local_cicd.config import ConfigurationError, load_environment_config
from mongodb_local_cicd.local_config import LocalConfigProvider, LocalConfigurationError


def test_environment_config_is_explicit() -> None:
    config = load_environment_config("dev")
    assert config["environment"] == "dev"
    assert config["mongodb"]["database"] == "cicd_demo_dev"
    assert config["ops_manager"]["alert"]["event_type"] == "HOST_DOWN"


@pytest.mark.parametrize("environment", ["dev", "test", "perf", "prod"])
def test_standard_environment_set_is_supported(environment: str) -> None:
    config = load_environment_config(environment)
    assert config["environment"] == environment
    assert config["mongodb"]["database"] == f"cicd_demo_{environment}"


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        load_environment_config("qa")


def test_production_execution_requires_exact_confirmation() -> None:
    with pytest.raises(ValueError, match="--confirm PROD"):
        require_environment_confirmation("prod", True, None)
    require_environment_confirmation("prod", True, "PROD")
    require_environment_confirmation("dev", True, None)


def test_local_provider_separates_parameters_and_secrets(tmp_path: Path) -> None:
    local = tmp_path / ".local"
    local.mkdir()
    (local / "parameter-store.json").write_text(
        json.dumps({"/demo/uri": "mongodb://localhost:27017"}), encoding="utf-8"
    )
    (local / "secrets-manager.json").write_text(
        json.dumps({"demo/credentials": {"username": "demo", "password": "secret"}}),
        encoding="utf-8",
    )
    provider = LocalConfigProvider(tmp_path)
    assert provider.get_parameter("/demo/uri") == "mongodb://localhost:27017"
    assert provider.get_secret_json("demo/credentials")["username"] == "demo"
    with pytest.raises(LocalConfigurationError):
        provider.get_secret_json("/demo/uri")
