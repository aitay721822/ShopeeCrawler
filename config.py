from typing import Dict
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

default_config = {
    'email': {
        'enabled': False,                   # 是否啟用 email 通知
        'smtp_server': 'smtp.gmail.com',    # smtp server
        'smtp_port': 587,                   # smtp port
        'username': 'username',             # username
        'password': 'password',             # password
    },
    'user': {
        'init': True,                       # True: 需要初始化, False: 不需要初始化
        'url': 'https://shopee.tw/iPad-cat.11041546.11041612.11041613',
    },
    'system': {
        'state_file': 'state.txt',           # 紀錄已經通知過的商品 id
        'chrome_driver': 'chromedriver.exe', # chromedriver.exe 的路徑
        'init_pages': 5,                     # 初始要查詢的頁數
    }
}

_config_path = 'config.yaml'
def load_config(path: str = _config_path) -> Dict:
    try:
        with open(path, 'r') as f:
            config = load(f, Loader=Loader)
    except FileNotFoundError:
        config = default_config.copy()
        save_config(config)
    return config

def save_config(config: Dict, path: str = _config_path):
    with open(path, 'w+') as f:
        dump(config, f, Dumper=Dumper)

def get_default_config():
    return default_config.copy()
