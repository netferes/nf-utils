import sys
from pathlib import Path

__all__ = ["load_config"]

def override_config(config:dict, new_config:dict) -> dict:
    """
    覆盖配置文件
    args:
        config: 配置文件
        new_config: 新配置文件
    """
    if not config:
        return new_config

    if not new_config:
        return config

    for key, value in new_config.items():
        if key in config:
            if isinstance(config[key], dict) and isinstance(value, dict):
                config[key] = override_config(config[key], value)
            else:
                config[key] = value
        else:
            config[key] = value

    return {**config}

def load_config(config_path:Path=None,global_config:Path=None) -> dict:
    """
    加载配置文件
    args:
        ...
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("yaml is not installed, please install it with `pip install PyYAML`")

    is_dev = '--dev' in sys.argv
    
    config_paths: list[Path] = []
    if global_config:
        if isinstance(global_config,str):
            global_config = Path(global_config)
        if not global_config.exists():
            raise FileNotFoundError(f"global config file {global_config} not found")
        config_paths.append(global_config)

    if not config_path:
        config_path = Path(sys.argv[0]).parent / "config.yaml"
    elif isinstance(config_path,str):
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"config file {config_path} not found")
        
    config_paths.append(config_path)

    if is_dev:
        dev_config_path = config_path.parent / "config.dev.yaml"
        if dev_config_path.exists():
            config_paths.append(dev_config_path)
    
    result = {}
    for item in config_paths:
        with open(item,"r") as config_file:
            value = yaml.load(config_file, Loader=yaml.FullLoader)
            result = override_config(result, value)
    
    result["is_dev"] = is_dev
    return result
    