import json
import os

def generate_html(test_json_path, html_output_path):
    """
    讀取指定的 JSON 檔案，並產生 HTML 表格，然後寫入 html_output_path。
    """
    # 讀取 JSON 檔案
    with open(test_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 定義各分類對應的 JSON 鍵與輸出欄位標題（順序決定輸出順序）
    categories = [
        ("異體字", "異體字"),
        ("同義詞/近義詞(意譯)", "同義詞"),
        ("複合詞", "複合詞"),
        ("相關詞", "相關詞"),
        ("音譯詞", "音譯詞")
    ]
    
    # 用來存放所有群首詞的表格資料，每筆資料是一個 tuple (row, is_summary)
    # is_summary 為 True 表示該列為統計行
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
        
        # 針對每個分類，取得一個 list，每個元素為 (字詞, 筆數)，但 total 為 0 的項目跳過
        cat_lists = {}
        max_rows = 0
        for json_key, title in categories:
            lst = []
            for word, entry in info.get(json_key, {}).items():
                try:
                    cnt = int(entry.get("total", 0))
                except:
                    cnt = 0
                if cnt != 0:  # 只加入 total 不為 0 的項目
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
                count_nonzero += 1
                sum_total += cnt
        
        # 如果名相總個數為0，則跳過整個群組（不加入任何列）
        if count_nonzero == 0:
            continue
        
        # 產生該群首詞的詳細資料列
        # 每一行欄位順序：
        # [名相總個數, 名相總筆數, 群首詞, 群首詞筆數,
        #  異體字, 異體字筆數, 同義詞, 同義詞筆數,
        #  複合詞, 複合詞筆數, 相關詞, 相關詞筆數,
        #  音譯詞, 音譯詞筆數]
        # 第一行顯示前四欄，其餘行前四欄置空
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
            for json_key, title in categories:
                lst = cat_lists[json_key]
                if i < len(lst):
                    word, cnt = lst[i]
                    row.extend([word, str(cnt)])
                else:
                    row.extend(["", ""])
            group_detail_rows.append((row, False))
        # 將詳細列加入 group_rows
        group_rows.extend(group_detail_rows)
    
        # 新增統計行 (summary row)：
        # 第1欄：名相總個數；第2欄：名相總筆數；
        # 第3欄固定為 1；第4欄固定為群首詞筆數（即 main_total）；
        # 接下來每個分類依序統計非零項目數與筆數總和
        summary_row = []
        summary_row.append(str(count_nonzero))
        summary_row.append(str(sum_total))
        summary_row.append("1")
        summary_row.append(str(main_total))
        for json_key, title in categories:
            items = cat_lists[json_key]
            cat_count = len(items)
            cat_sum = sum(cnt for word, cnt in items)
            summary_row.append(str(cat_count))
            summary_row.append(str(cat_sum))
        # 將 summary row 加入，標記為 True 以便後續加上樣式
        group_rows.append((summary_row, True))
    
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
    
    header_html = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    
    # 組合每一行的 HTML，統計行用粗體與淺藍色背景 (AliceBlue: #F0F8FF)
    # 非統計行的第三欄（群首詞）若有值，則以粗體藍字呈現
    row_html_list = []
    for row, is_summary in group_rows:
        if not is_summary and row[2].strip():
            row[2] = f'<span style="font-weight: bold; color: blue;">{row[2]}</span>'
        if is_summary:
            row_html = '<tr style="font-weight: bold; background-color: #F0F8FF;">' + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        else:
            row_html = "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        row_html_list.append(row_html)
    
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
    html_dir = os.path.dirname(html_output_path)
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"已產生 {html_output_path}")
    return html_content

# 測試範例：
if __name__ == "__main__":
    test_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words6_json", "T0848.json")
    output_html = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html", "T0848.html")
    generate_html(test_json, output_html)
