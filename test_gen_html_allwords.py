import json
import os

MY_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 設定 JSON 輸入檔案與 HTML 輸出檔案的路徑
test_json_path = os.path.join(MY_SCRIPT_DIR, "words6_json", "T0848.json")
html_output_path = os.path.join(MY_SCRIPT_DIR, "html", "T0848.html")

# -------------------------------
# 讀取 JSON 檔案
with open(test_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 定義各分類對應的 JSON 鍵與輸出欄位標題（此處順序決定輸出順序）
categories = [
    ("異體字", "異體字"),
    ("同義詞/近義詞(意譯)", "同義詞"),
    ("複合詞", "複合詞"),
    ("相關詞", "相關詞"),
    ("音譯詞", "音譯詞")
]

# 用來存放所有群首詞的表格資料，每個群首詞可能展開多行，最後再加上統計行
group_rows = []

# 依據 JSON 中每個主詞依 id 排序（假設 id 為數字型字串）
sorted_terms = sorted(data.items(), key=lambda kv: int(kv[1].get("id", "0")))

# 處理每一個群首詞
for main_term, info in sorted_terms:
    # 取得群首詞的筆數（來自 found.total）
    try:
        main_total = int(info.get("found", {}).get("total", 0))
    except:
        main_total = 0

    # 針對每個分類，取得一個 list，每個元素為 (字詞, 筆數)
    cat_lists = {}
    max_rows = 0
    for json_key, title in categories:
        lst = []
        for word, entry in info.get(json_key, {}).items():
            try:
                cnt = int(entry.get("total", 0))
            except:
                cnt = 0
            lst.append((word, cnt))
        cat_lists[json_key] = lst
        if len(lst) > max_rows:
            max_rows = len(lst)
    # 如果所有分類皆無資料，至少顯示一行
    if max_rows == 0:
        max_rows = 1

    # 計算該群首詞整體統計：
    # 全群包括：群首詞本身（found.total）以及各分類中 total 不為 0 的字詞
    count_nonzero = 0
    sum_total = 0
    if main_total != 0:
        count_nonzero += 1
        sum_total += main_total
    for json_key, _ in categories:
        for word, cnt in cat_lists[json_key]:
            if cnt != 0:
                count_nonzero += 1
                sum_total += cnt

    # 產生該群首詞的詳細資料列
    # 每一行欄位順序：
    # [名相總個數, 名相總筆數, 群首詞, 群首詞筆數,
    #  異體字, 異體字筆數, 同義詞, 同義詞筆數,
    #  複合詞, 複合詞筆數, 相關詞, 相關詞筆數,
    #  音譯詞, 音譯詞筆數]
    # 只有第一行顯示前4欄，其他行置空
    group_detail_rows = []
    for i in range(max_rows):
        if i == 0:
            row = [
                str(count_nonzero),
                str(sum_total),
                main_term,
                str(main_total)
            ]
        else:
            row = ["", "", "", ""]
        # 對每個分類依序處理
        for json_key, title in categories:
            lst = cat_lists[json_key]
            if i < len(lst):
                word, cnt = lst[i]
                row.extend([word, str(cnt)])
            else:
                row.extend(["", ""])
        group_detail_rows.append(row)
    # 將詳細列加入 group_rows
    group_rows.extend(group_detail_rows)

    # 接著新增統計行 (summary row)：
    # 第1欄：名相總個數；第2欄：名相總筆數；第3欄固定為 1；
    # 第4欄：群首詞筆數（取 main_total）；接下來每個分類的統計 (非零項目數, 筆數總和)
    summary_row = []
    summary_row.append(str(count_nonzero))
    summary_row.append(str(sum_total))
    summary_row.append("1")
    summary_row.append(str(main_total))
    # 對每個分類計算統計值
    for json_key, title in categories:
        items = cat_lists[json_key]
        cat_count = sum(1 for word, cnt in items if cnt != 0)
        cat_sum = sum(cnt for word, cnt in items if cnt != 0)
        summary_row.append(str(cat_count))
        summary_row.append(str(cat_sum))
    group_rows.append(summary_row)

# -------------------------------
# 建立 HTML 表格

# 定義表頭
headers = [
    "名相總個數", "名相總筆數",
    "群首詞", "群首詞筆數",
    "異體字", "異體字筆數",
    "同義詞", "同義詞筆數",
    "複合詞", "複合詞筆數",
    "相關詞", "相關詞筆數",
    "音譯詞", "音譯詞筆數"
]

# 組合表頭的 HTML
header_html = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"

# 組合每一行的 HTML
row_html_list = []
for row in group_rows:
    row_html = "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    row_html_list.append(row_html)

# 組合整個 HTML 頁面
html_content = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>佛經詞表彙整</title>
<style>
  table {{
    border-collapse: collapse;
    width: 100%;
  }}
  th, td {{
    border: 1px solid #000;
    padding: 4px;
    text-align: center;
  }}
  th {{
    background-color: #f0f0f0;
  }}
</style>
</head>
<body>
<table>
{header_html}
{''.join(row_html_list)}
</table>
</body>
</html>
"""

# 寫入 HTML 檔案
# 確保輸出目錄存在
html_dir = os.path.dirname(html_output_path)
if not os.path.exists(html_dir):
    os.makedirs(html_dir)

with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"已產生 {html_output_path}")
