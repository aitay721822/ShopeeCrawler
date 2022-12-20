# 蝦皮爬蟲 [selenium ver.]

做個存檔紀錄寫了什麼專案，以後有用到但失效了會再更新

整個更新的邏輯十分簡單，就是先暫存首幾頁，然後再一直爬取第一頁，看 id 有無相同，若沒有就寄送email提醒。

## Requirement

- Python 3.5 up
- pyyaml
- selenium
- requests

## Usage

1. 安裝依賴套件

   `pip install -r requirements.txt`

2. 使用終端機打入下列指令:

   `python main.py` or `python3 main.py`

3. 依步驟執行

## Tested environment

- Ubuntu 22.04 LTS
- Windows 10 22H2
