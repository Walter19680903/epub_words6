@echo off

chcp 65001
cd /d D:\cbeta_cloud\epub_words6


if exist venv (
    echo 已偵測到虛擬環境 venv，直接啟用中...
) else (
    echo 尚未偵測到虛擬環境，現在建立...
    python -m venv venv
)

call venv\Scripts\activate
echo 已啟動虛擬環境。

python.exe -m pip install --upgrade pip
REM pip install xlwings
REM pip install pywin32
REM pip install openpyxl
REM pip install xlrd
REM pip install python-docx pywin32
REM pip install bs4
REM pip install ebooklib
pip install beautifulsoup4
pip install flask


cmd /K

