import streamlit as st

# サンプルデータ（ステータスと詳細を分離）
status_text = "馬券内絡み"
detail_text = "6番 アスタルファナ"
full_copy_text = "2026/09/06 中山 9R ダ1200m(湿不良) 浦安特別 ◎16番 ドントゥウザムーン / ◯6番 アスタルファナ / ▲2番 キョウエイカンフ 86.0% 100.0% 232.2% 1"

st.subheader("📋 検証結果 スプレッドシート用コピー欄")

# 1. 項目を分けたコピー用テキストの作成（タブ区切りにするとスプレッドシートの別列にペーストしやすい）
spreadsheet_row_data = f"{status_text}\t{detail_text}"

st.text_input("スプレッドシート用（列分け用タブ区切り）", value=spreadsheet_row_data, help="コピーしてスプレッドシートの連続する2つのセルに貼り付けると列が分かれます")

# 2. 検証結果コピー用ボックス
st.text_area("検証結果コピー用ボックス", value=full_copy_text, height=100)

# ※streamlit-extras や st_copy_to_clipboard などのカスタムコンポーネントを入れると完全な「ワンクリックコピー」が実現できます
