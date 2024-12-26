"""Tests for configuration models."""
import pytest
from pydantic import BaseModel
from models.config_models import ConfigModel

@pytest.fixture
def test_config_class():
    """Fixture to provide test config class."""
    class TestConfig(BaseModel):
        """Test configuration class."""
        name: str
        value: int
    return TestConfig

def test_config_model_creation(test_config_class):
    """Test basic creation of config model."""
    config = ConfigModel[test_config_class]()
    
    assert not config.debug
    assert config.cache_enabled
    assert isinstance(config.options, dict)
    assert len(config.options) == 0
    assert config.config is None

def test_config_model_with_debug(test_config_class):
    """Test config model with debug enabled."""
    config = ConfigModel[test_config_class](debug=True)
    assert config.debug

def test_config_model_with_cache_disabled(test_config_class):
    """Test config model with cache disabled."""
    config = ConfigModel[test_config_class](cache_enabled=False)
    assert not config.cache_enabled

def test_config_model_with_options(test_config_class):
    """Test config model with custom options."""
    options = {
        "timeout": 30,
        "retry_count": 3
    }
    config = ConfigModel[test_config_class](options=options)
    
    assert config.options == options
    assert config.options["timeout"] == 30
    assert config.options["retry_count"] == 3

def test_config_model_with_specific_config(test_config_class):
    """Test config model with component specific configuration."""
    specific_config = test_config_class(name="test", value=42)
    config = ConfigModel[test_config_class](config=specific_config)
    
    assert config.config == specific_config
    assert config.config.name == "test"
    assert config.config.value == 42

def test_config_model_with_all_fields(test_config_class):
    """Test config model with all fields populated."""
    specific_config = test_config_class(name="test", value=42)
    options = {"timeout": 30}
    
    config = ConfigModel[test_config_class](
        debug=True,
        cache_enabled=False,
        options=options,
        config=specific_config
    )
    
    assert config.debug
    assert not config.cache_enabled
    assert config.options == options
    assert config.config == specific_config

def test_config_model_options_mutation(test_config_class):
    """Test mutating options in config model."""
    config = ConfigModel[test_config_class]()
    
    # Add new option
    config.options["new_option"] = "value"
    assert "new_option" in config.options
    assert config.options["new_option"] == "value"
    
    # Update existing option
    config.options["new_option"] = "updated"
    assert config.options["new_option"] == "updated"

def test_config_model_type_checking(test_config_class):
    """Test type checking for specific config."""
    # Valid config
    specific_config = test_config_class(name="test", value=42)
    config = ConfigModel[test_config_class](config=specific_config)
    assert isinstance(config.config, test_config_class)
    
    # Invalid config structure
    with pytest.raises(ValueError):
        ConfigModel[test_config_class](config={"invalid": "structure"})  # type: ignore

def test_config_model_json_serialization(test_config_class):
    """Test JSON serialization of config model."""
    specific_config = test_config_class(name="test", value=42)
    config = ConfigModel[test_config_class](
        debug=True,
        config=specific_config
    )
    
    json_data = config.model_dump_json()
    assert isinstance(json_data, str)
    assert "test" in json_data
    assert "42" in json_data
