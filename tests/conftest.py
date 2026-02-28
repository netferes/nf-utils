"""
pytest 配置文件
"""

import sys
from pathlib import Path

# 将 utils 包添加到 Python 路径
utils_dir = Path(__file__).parent.parent
sys.path.insert(0, str(utils_dir))
