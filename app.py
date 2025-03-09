from flask import Flask, render_template_string, Response
import json
import os
import logging
import csv
from io import StringIO

app = Flask(__name__)

# 設定 logging
logging.basicConfig(level=logging.INFO)

# 設定 books.json 的路徑，請確保檔案存在且格式正確
BOOKS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'books.json')

# 讀取 books.json 並轉換成平面字典 book_list
try:
    with open(BOOKS_JSON_PATH, 'r', encoding='utf-8') as f:
        books_data = json.load(f)
    app.logger.info(f"成功讀取 books.json: {BOOKS_JSON_PATH}")
except Exception as e:
    app.logger.error(f"讀取 books.json 發生錯誤: {e}")
    books_data = {}

book_list = {}
for docx, inner in books_data.items():
    app.logger.info(f"處理檔案: {docx}")
    for code, values in inner.items():
        if isinstance(values, list) and len(values) >= 2:
            book_list[code] = values[1]
            # app.logger.info(f"加入 {code}: {values[1]}")

# 產生下拉選單用的字串列表，格式: "(T0848) 大毘盧遮那成佛神變加持經"
formatted_books = []
for code, title in sorted(book_list.items()):
    formatted_books.append(f"({code}) {title}")
app.logger.info(f"總共 {len(formatted_books)} 個選項")

# CSV 下載路由
@app.route("/download_csv")
def download_csv():
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Code", "Title"])
    for code, title in sorted(book_list.items()):
        writer.writerow([code, title])
    output = si.getvalue()
    si.close()
    app.logger.info("下載 CSV 檔案")
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=books.csv"}
    )

# 依照代碼讀取 html 子目錄中對應檔案內容
@app.route("/get_result/<code>")
def get_result(code):
    html_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")
    filename = os.path.join(html_dir, code.lower() + ".html")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        app.logger.info(f"成功讀取 {filename}")
        return content
    else:
        app.logger.error(f"找不到檔案 {filename}")
        return f"<p>找不到結果檔案: {code.lower()}.html</p>"

# HTML 模板，使用 flex 讓 "輸入經名" 與輸入框在同一行，
# 下拉選單下方並排兩個按鈕，再加上水平線與結果顯示區域。
template = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>經文名相查詢資料庫</title>
    <style>
        h1 {
            font-size: 36px;
            font-weight: bold;
            font-family: "黑體", sans-serif;
            color: black;
        }
        .input-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .input-group label {
            font-size: 27px; /* 原 18px * 1.5 */
            margin-right: 10px;
        }
        .dropdown-container {
            position: relative;
            flex: 1;
        }
        #searchInput {
            width: 100%;
            font-size: 24px; /* 原 16px * 1.5 */
            padding: 8px;
            box-sizing: border-box;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10'%3E%3Cpolygon points='0,0 10,0 5,5' fill='gray'/%3E%3C/svg%3E") no-repeat;
            background-position: right 10px center;
        }
        /* 下拉選單容器，初始隱藏 */
        #dropdown {
            position: absolute;
            top: 110%;
            left: 0;
            right: 0;
            background-color: white;
            border: 1px solid #ccc;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        #dropdown div {
            padding: 8px;
            cursor: pointer;
            font-size: 24px;
        }
        #dropdown div:hover {
            background-color: #f0f0f0;
        }
        /* 按鈕區，兩個按鈕並排 */
        .button-group {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .button-group button {
            font-size: 24px;
            padding: 8px 12px;
        }
        /* 結果區域 */
        #resultContainer {
            margin-top: 20px;
        }
    </style>
    <script>
        var options = {{ options|tojson }};
        
        function filterOptions() {
            var input = document.getElementById("searchInput");
            var filter = input.value.toLowerCase();
            var dropdown = document.getElementById("dropdown");
            dropdown.innerHTML = "";
            if (filter.trim() === "") {
                dropdown.style.display = "none";
                return;
            }
            var matched = options.filter(function(option) {
                return option.toLowerCase().indexOf(filter) > -1;
            });
            if (matched.length > 0) {
                matched.forEach(function(option) {
                    var div = document.createElement("div");
                    div.textContent = option;
                    div.onclick = function() {
                        document.getElementById("searchInput").value = option;
                        dropdown.style.display = "none";
                        // 提取括號中的代碼
                        var codeMatch = option.match(/\\((.*?)\\)/);
                        if(codeMatch && codeMatch[1]) {
                            fetchResult(codeMatch[1]);
                        }
                    };
                    dropdown.appendChild(div);
                });
                dropdown.style.display = "block";
            } else {
                dropdown.style.display = "none";
            }
        }
        
        function fetchResult(code) {
            fetch("/get_result/" + code.toLowerCase())
            .then(function(response) { return response.text(); })
            .then(function(data) {
                document.getElementById("resultContainer").innerHTML = data;
            })
            .catch(function(error) {
                document.getElementById("resultContainer").innerHTML = "取得結果失敗: " + error;
            });
        }
        
        function clearInput() {
            document.getElementById("searchInput").value = "";
            document.getElementById("dropdown").style.display = "none";
            document.getElementById("resultContainer").innerHTML = "";
        }
        
        function downloadCSV() {
            window.location.href = "/download_csv";
        }
        
        document.addEventListener("click", function(e) {
            var dropdown = document.getElementById("dropdown");
            var container = document.getElementById("dropdownContainer");
            if (!container.contains(e.target)) {
                dropdown.style.display = "none";
            }
        });
    </script>
</head>
<body>
    <h1>經文名相查詢資料庫</h1>
    <div class="input-group" id="dropdownContainer">
        <label for="searchInput">輸入經名</label>
        <div class="dropdown-container">
            <input type="text" id="searchInput" onkeyup="filterOptions()" placeholder="請輸入關鍵字...">
            <div id="dropdown"></div>
        </div>
    </div>
    <div class="button-group">
        <button id="clearButton" onclick="clearInput()">清除</button>
        <button id="downloadCSVButton" onclick="downloadCSV()">下載 CSV 檔</button>
    </div>
    <hr>
    <div id="resultContainer"></div>
</body>
</html>
'''

@app.route("/")
def index():
    app.logger.info("進入首頁")
    return render_template_string(template, options=formatted_books)

if __name__ == "__main__":
    app.run(debug=True)
