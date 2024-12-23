"""Tests for configuration models."""
import pytest
from pydantic import BaseModel
from models.config_models import ConfigModel

class TestConfig(BaseModel):
    """Test configuration class."""
    name: str
    value: int

def test_config_model_creation():
    """Test basic creation of config model."""
    config = ConfigModel[TestConfig]()
    
    assert not config.debug
    assert config.cache_enabled
    assert isinstance(config.options, dict)
    assert len(config.options) == 0
    assert config.config is None

def test_config_model_with_debug():
    """Test config model with debug enabled."""
    config = ConfigModel[TestConfig](debug=True)
    assert config.debug

def test_config_model_with_cache_disabled():
    """Test config model with cache disabled."""
    config = ConfigModel[TestConfig](cache_enabled=False)
    assert not config.cache_enabled

def test_config_model_with_options():
    """Test config model with custom options."""
    options = {
        "timeout": 30,
        "retry_count": 3
    }
    config = ConfigModel[TestConfig](options=options)
    
    assert config.options == options
    assert config.options["timeout"] == 30
    assert config.options["retry_count"] == 3

def test_config_model_with_specific_config():
    """Test config model with component specific configuration."""
    specific_config = TestConfig(name="test", value=42)
    config = ConfigModel[TestConfig](config=specific_config)
    
    assert config.config == specific_config
    assert config.config.name == "test"
    assert config.config.value == 42

def test_config_model_with_all_fields():
    """Test config model with all fields populated."""
    specific_config = TestConfig(name="test", value=42)
    options = {"timeout": 30}
    
    config = ConfigModel[TestConfig](
        debug=True,
        cache_enabled=False,
        options=options,
        config=specific_config
    )
    
    assert config.debug
    assert not config.cache_enabled
    assert config.options == options
    assert config.config == specific_config

def test_config_model_options_mutation():
    """Test mutating options in config model."""
    config = ConfigModel[TestConfig]()
    
    # Add new option
    config.options["new_option"] = "value"
    assert "new_option" in config.options
    assert config.options["new_option"] == "value"
    
    # Update existing option
    config.options["new_option"] = "updated"
    assert config.options["new_option"] == "updated"

def test_config_model_type_checking():
    """Test type checking for specific config."""
    # Valid config
    specific_config = TestConfig(name="test", value=42)
    config = ConfigModel[TestConfig](config=specific_config)
    assert isinstance(config.config, TestConfig)
    
    # Invalid config structure
    with pytest.raises(ValueError):
        ConfigModel[TestConfig](config={"invalid": "structure"})  # type: ignore

def test_config_model_json_serialization():
    """Test JSON serialization of config model."""
    specific_config = TestConfig(name="test", value=42)
    config = ConfigModel[TestConfig](
        debug=True,
        config=specific_config
    )
    
    json_data = config.model_dump_json()
    assert isinstance(json_data, str)
    assert "test" in json_data
    assert "42" in json_data
