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

def load_config(config_path:Path=None, dev_config_path:Path=None) -> dict:
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
    root = Path(sys.argv[0]).parent
    config_paths: list[Path] = [] 
    if config_path:
        config_paths.append(config_path)
    else:
        config_paths.append(root / "config.yaml")

    if is_dev:
        if dev_config_path:
            config_paths.append(dev_config_path)
        elif (root / "config.dev.yaml").exists():
            config_paths.append(root / "config.dev.yaml")
    
    result = {}
    for item in config_paths:
        if not item.exists():
            raise FileNotFoundError(f"config file {item} not found")
        with open(item,"r") as config_file:
            value = yaml.load(config_file, Loader=yaml.FullLoader)
            result = override_config(result, value)
    
    result["is_dev"] = is_dev
    return result
    