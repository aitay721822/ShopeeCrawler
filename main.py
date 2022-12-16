import logging
import time
import os
import signal
import sys
import time
from typing import List
from client import Client, ProductItem
from notification import GoogleEmail, DummyEmail
from config import save_config, load_config, get_default_config


# logger ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s [%(filename)s:%(lineno)d]')
logger = logging.getLogger('main')

# program ---
def validate(config):
    # 檢查欄位是否丟失 - email
    email_config = config.get('email')
    if not email_config:
        return False
    if  'enabled' not in email_config or \
        'smtp_server' not in email_config or \
        'smtp_port' not in email_config or \
        'username' not in email_config or \
        'password' not in email_config:
        return False
    # 檢查欄位是否丟失 - user
    user_config = config.get('user')
    if not user_config:
        return False
    if 'init' not in user_config or 'url' not in user_config or 'receiver' not in user_config:
        return False
    # 檢查欄位是否丟失 - system
    system_config = config.get('system')
    if not system_config:
        return False
    if 'state_file' not in system_config or 'chrome_driver' not in system_config:
        return False
    # 檢查是否需要初始化
    need_init = user_config.get('init')
    if need_init:
        return False
    return True

def init(config):
    def update_config(cfg, entry, msg, conv_method=str):
        r = input(f'[目前值為: {cfg[entry]}] {msg}').strip()
        if len(r) == 0:
            return
        cfg[entry] = conv_method(r)

    config = get_default_config()
    email_config = config.get('email')
    email_config['enabled'] = input('是否啟用 email 通知 (y/n): ').lower() == 'y'
    if email_config['enabled']:
        update_config(email_config, 'smtp_server', '請輸入 smtp 伺服器位址: ')
        update_config(email_config, 'smtp_port', '請輸入 smtp 伺服器埠號: ', int)
        update_config(email_config, 'username', '請輸入 smtp 使用者名稱: ')
        update_config(email_config, 'password', '請輸入 smtp 使用者密碼: ')

    user_config = config.get('user')
    user_config['init'] = False
    update_config(user_config, 'url', '請輸入欲查詢之url: ')
    update_config(user_config, 'receiver', '請輸入欲寄送通知之email: ')

    system_config = config.get('system')
    update_config(system_config, 'chrome_driver', '請輸入 chrome driver 位置: ')
    update_config(system_config, 'init_pages', '請輸入一開始需要查找的頁數: ', int)

    save_config(config)
    return config

def save_id_to_file(s, filename):
    with open(filename, 'w+') as f:
        f.write(','.join(s))

def load_id_from_file(filename):
    with open(filename, 'r') as f:
        return set(f.read().split(','))

def main():
    config = load_config()
    if not validate(config):
        config = init(config)

    # 初始化寄信程序
    email_config = config.get('email')
    username, password = email_config.get('username'), email_config.get('password')
    if email_config.get('enabled'):
        email = GoogleEmail(username, password)
    else:
        email = DummyEmail()

    # 取得系統設定
    system_config = config.get('system')
    state_file = system_config.get('state_file')
    chrome_driver = system_config.get('chrome_driver')
    init_pages = system_config.get('init_pages')

    logger.info('Session start')
    client = Client(chrome_driver)

    logger.info('Prepare data')
    mem = load_id_from_file(state_file) if os.path.exists(state_file) else set()
    logger.info(f'Load {len(mem)} from {state_file}')

    # 註冊信號處理函式
    def signal_handler(sig, frame):
        logger.info(f'You pressed Ctrl+C! sigint: {sig}')
        save_id_to_file(mem, state_file)
        logger.info(f'Save {len(mem)} to {state_file}')
        client.close_driver()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    # 抓取第一輪資料
    user_config = config.get('user')
    url = user_config.get('url')
    receiver = user_config.get('receiver')
    for page in range(init_pages):
        logger.info(f'Fetch page {page}')
        for item in client.fetch(url, page = page):
            if item.id in mem:
                continue
            mem.add(item.id)
            logger.info(f'Fetch New Item {item.title}, {item.price} in **initialize step**')

    # 開始監控
    send_status = True
    logger.info('Start to monitor')
    while True:
        try:
            newItems: List[ProductItem] = []
            for item in client.fetch(url, page = 0):
                if item.id in mem:
                    continue
                mem.add(item.id)
                newItems.append(item)
                logger.info(f'Fetch New Item {item.title}, {item.price} in **monitor step**')
            if len(newItems) > 0:
                s = '<br>'.join([f"{i + 1}. {item.title}, {item.price}, {item.url}" for i, item in enumerate(newItems)])
                send_status = False
                while not send_status:
                    send_status = email.send(receiver, [receiver], '蝦皮提醒助手', s)
        except KeyboardInterrupt:
            client.close_driver()
            break
        except Exception as e:
            logger.exception(e)
            logger.error('driver restart')
            client.restart_driver()
        time.sleep(60)

if __name__ == '__main__':
    main()