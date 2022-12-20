import os
import re
from sys import platform

import zipfile
import xml.etree.ElementTree as ET
import requests

# code from `https://gist.github.com/primaryobjects/d5346bf7a173dbded1a70375ff7461b4`
def extract_version_registry(output):
    try:
        google_version = ''
        for letter in output[output.rindex('DisplayVersion    REG_SZ') + 24:]:
            if letter != '\n':
                google_version += letter
            else:
                break
        return(google_version.strip())
    except TypeError:
        return

def extract_version_folder():
    # Check if the Chrome folder exists in the x32 or x64 Program Files folders.
    for i in range(2):
        path = 'C:\\Program Files' + (' (x86)' if i else '') +'\\Google\\Chrome\\Application'
        if os.path.isdir(path):
            paths = [f.path for f in os.scandir(path) if f.is_dir()]
            for path in paths:
                filename = os.path.basename(path)
                pattern = '\d+\.\d+\.\d+\.\d+'
                match = re.search(pattern, filename)
                if match and match.group():
                    # Found a Chrome version.
                    return match.group(0)

    return None

def detect_chrome_version():
    version = None
    install_path = None

    try:
        if platform == "linux" or platform == "linux2":
            # linux
            install_path = "/usr/bin/google-chrome"
        elif platform == "darwin":
            # OS X
            install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        elif platform == "win32":
            # Windows...
            try:
                # Try registry key.
                stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
                output = stream.read()
                version = extract_version_registry(output)
            except Exception as ex:
                # Try folder path.
                version = extract_version_folder()
    except Exception as ex:
        print(ex)

    version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip() if install_path else version

    return version
# ---

chromedriver_base_url = 'https://chromedriver.storage.googleapis.com/'
def download_chrome_driver(dst_dir, filename):
    def get_all_version():
        index_url = f'{chromedriver_base_url}?delimiter=/&prefix='
        response = requests.get(index_url)
        if response.status_code == 200:
            xml = ET.fromstring(response.text)
            return [child[0].text.strip('/') for child in xml if 'CommonPrefixes' in child.tag and child[0].text != 'icons/']
        else:
            return None

    def extract_major_version(version):
        return version.split('.')[0]

    def list_all_files(version):
        index_url = f'{chromedriver_base_url}?delimiter=/&prefix={version}/'
        response = requests.get(index_url)
        if response.status_code == 200:
            xml = ET.fromstring(response.text)
            res = []
            for child in xml:
                if 'Contents' in child.tag and '.zip' in child[0].text:
                    res.append({
                        'filename': child[0].text[child[0].text.rindex('/') + 1:],
                        'uri': child[0].text,
                    })
            return res
        else:
            return None

    current_version = detect_chrome_version()
    versions = get_all_version()

    choose_version = None
    for version in versions:
        if version == current_version:
            choose_version = version
            break

    if not choose_version:
        compatible_versions = []
        current_major_version = extract_major_version(current_version)
        for version in versions:
            if extract_major_version(version) == current_major_version:
                compatible_versions.append(version)
        
        while not choose_version:
            print('已為您找到合適的 Chrome Driver 版本')
            print(f'目前版本為: {current_version}')
            print('--------------------------------')
            print('請選擇下列版本之一:')
            for i, version in enumerate(compatible_versions):
                print(f'{i}. {version}')
            print('--------------------------------')
            choose_index = int(input(f'請輸入編號[0 ~ {len(compatible_versions) - 1}]: ').strip())

            if 0 <= choose_index < len(compatible_versions):
                choose_version = compatible_versions[choose_index]
            else:
                print('輸入錯誤，請重新輸入')

    files = list_all_files(choose_version)
    choose_file = None
    while not choose_file:
        print('請依照作業系統選擇下列檔案之一:')
        print('--------------------------------')
        for i, file in enumerate(files):
            print(f'{i}. {file["filename"]}')
        print('--------------------------------')
        choose_index = int(input(f'請輸入編號[0 ~ {len(files) - 1}]: ').strip())
        if 0 <= choose_index < len(files):
            choose_file = files[choose_index]['uri']
        else:
            print('輸入錯誤，請重新輸入')


    download_url = f"{chromedriver_base_url}{choose_file}"
    print(f'downloading chrome driver version {choose_version} from {download_url}')
    response = requests.get(download_url, timeout=600)
    if response.status_code == 200:
        # Save the zip file.
        with open('chromedriver.zip', 'wb') as f:
            f.write(response.content)
        # extract the zip file.
        with zipfile.ZipFile('chromedriver.zip', 'r') as zip_ref:
            zip_ref.extractall(dst_dir)
        # rename the file 
        if platform == 'win32': 
            # add extension if not exists
            if not filename.endswith('.exe'): 
                filename += '.exe'
            os.rename(os.path.join(dst_dir, 'chromedriver.exe'), os.path.join(dst_dir, filename))
        else: 
            os.rename(os.path.join(dst_dir, 'chromedriver'), os.path.join(dst_dir, filename))
        # delete the zip file.
        os.remove('chromedriver.zip')
        print('download success')
        return True
    else:
        print('download failed')
        return False