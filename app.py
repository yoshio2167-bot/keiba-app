from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st
from itertools import combinations
st.set_page_config(page_title="競馬予想AIシミュレーター ＆ 予想家比較ボード", layout="wide", initial_sidebar_state="collapsed")
st.title("競馬予想AIシミュレーター ＆ 予想家比較ボード")
tab1, tab2, tab3 = st.tabs(["🚀 シミュレーション", "📊 結果照合・判定", "📝 プロ予想・ハイブリッド比較"])
セッション状態の初期化
if "pasted_csv" not in st.session_state:
st.session_state.pasted_csv = ""
with tab1:
st.header("モンテカルロ・シミュレーション ＆ 5頭ボックス")
st.write("出馬表CSVを貼り付けてボタンを押すだけで、高速に展開予測と5頭ボックス買い目、即PAT用リストを算出します。")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
threshold_roi = st.slider("🎯 勝負見送りライン（期待回収率 % 未満をパス）", 100, 200, 120, 10)
with col_s2:
sim_count = st.selectbox("🔄 シミュレーション回数", options=[1, 100, 300, 500], index=1)
with col_s3:
total_budget = st.number_input("💰 投資予算 (円)", 500, 50000, 2000, 500)
col_btn1, col_btn2 = st.columns([0.8, 0.2])
with col_btn2:
if st.button("🗑️ 一括削除", type="secondary"):
st.session_state.pasted_csv = ""
st.rerun()
pasted_data = st.text_area(
"CSVデータ貼り付け欄",
value=st.session_state.pasted_csv,
placeholder="日付,開催地,レース番号,距離・馬場,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量",
height=150,
)
st.session_state.pasted_csv = pasted_data
df_input = None
if pasted_data.strip():
try:
lines = [l.strip() for l in pasted_data.strip().split("\n") if l.strip()]
if lines:
has_header = "馬番" in lines[0] or "馬名" in lines[0] or "日付" in lines[0]
data_lines = lines[1:] if has_header else lines
parsed_rows = []
for l in data_lines:
parts = [p.strip() for p in l.split(",")]
if len(parts) >= 15:
parsed_rows.append({
"日付": parts[0], "開催地": parts[1], "レース番号": parts[2],
"距離・馬場": parts[3], "レース条件": parts[4], "馬番": parts[5],
"馬名": parts[6], "人気": parts[7], "単勝オッズ": parts[8],
"脚質": parts[9], "上がり3F": parts[10], "スピード指数": parts[11],
"近走5走成績": parts[12], "騎手": parts[13], "斤量": parts[14]
})
if parsed_rows:
df_input = pd.DataFrame(parsed_rows)
df_input["人気_num"] = pd.to_numeric(df_input["人気"].str.extract(r'(\d+)')[0], errors="coerce").fillna(5.0)
df_input["オッズ_num"] = pd.to_numeric(df_input["単勝オッズ"].str.extract(r'([\d.]+)')[0], errors="coerce").fillna(15.0)
df_input["speed_val"] = pd.to_numeric(df_input["スピード指数"].str.extract(r'([\d.]+)')[0], errors="coerce").fillna(0.0)
df_input["上がり3F_val"] = pd.to_numeric(df_input["上がり3F"].str.extract(r'([\d.]+)')[0], errors="coerce").fillna(35.0)
st.success(f"データを正常に読み込みました（全 {len(df_input)} 頭）")
except Exception as e:
st.error(f"データ解析エラー: {e}")
if st.button("🚀 高精度AI解析・予想を実行", type="primary"):
if df_input is not None and not df_input.empty:
with st.spinner("高速解析中..."):
df_res = df_input.copy()
def calc_score(row):
odds = row["オッズ_num"]
score = 150.0 / (np.log(odds + 1.0) + 0.6) + row["speed_val"] * 0.5
if "逃" in str(row["脚質"]) or "先行" in str(row["脚質"]):
score += 10.0
return max(10.0, score)
df_res["ベース評価"] = df_res.apply(calc_score, axis=1)
np.random.seed(42)
scores = df_res["ベース評価"].values
win_counts = np.zeros(len(df_res))
place_counts = np.zeros(len(df_res))
for _ in range(sim_count):
noise = np.random.normal(0, np.mean(scores) * 0.2, size=len(df_res)) if sim_count > 1 else np.zeros(len(df_res))
sim_scores = scores + noise
top_idx = np.argsort(sim_scores)[::-1]
win_counts[top_idx[0]] += 1
for p in top_idx[:3]:
place_counts[p] += 1
df_res["シミュ勝率_str"] = ((win_counts / sim_count) * 100).round(1).astype(str) + "%"
df_res["シミュ複勝率_str"] = ((place_counts / sim_count) * 100).round(1).astype(str) + "%"
raw_win = (win_counts / sim_count) * 100
df_res["AI期待回収率_str"] = ((raw_win / 100) * df_res["オッズ_num"] * 100).round(1).astype(str) + "%"
df_res["_win_num"] = raw_win
df_ranked = df_res.sort_values(by="_win_num", ascending=False).reset_index(drop=True)
st.session_state.df_ranked = df_ranked
st.session_state.total_budget = total_budget
st.subheader("📊 高精度予想・ランキング結果（上位5頭）")
display_cols = [c for c in ["開催地", "レース番号", "馬番", "馬名", "人気", "単勝オッズ", "シミュ勝率_str", "シミュ複勝率_str", "AI期待回収率_str", "脚質", "騎手"] if c in df_ranked.columns]
st.dataframe(df_ranked[display_cols], use_container_width=True, height=220)
top5_rows = df_ranked.head(5)
top5_nums = []
for _, r in top5_rows.iterrows():
try:
top5_nums.append(int(r["馬番"]))
except:
pass
bet_amt = max(100, int((total_budget / 100 / 10) * 100))
ipat_text = "\n".join([f"{c[0]}-{c[1]}-{c[2]}  ({bet_amt}円)" for c in combinations(sorted(top5_nums), 3)]) if len(top5_nums) >= 3 else ""
st.markdown("### 📋 即PAT入力用買い目リスト")
st.code(ipat_text, language="text")
export_df = df_ranked.copy()
csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 シミュレーション結果をCSVで保存", csv_data, "sim_result.csv", "text/csv")
st.markdown("### 📋 スプレッドシート用コピー欄")
st.code(StringIO(export_df.to_csv(sep="\t", index=False)).getvalue(), language="text")
else:
st.warning("CSVデータが入力されていません。")
with tab2:
st.header("実際のレース結果との照合・自動判定")
uploaded_file = st.file_uploader("シミュレーション結果CSVをアップロード", type=["csv"])
if uploaded_file is not None:
df_saved = pd.read_csv(uploaded_file)
st.success("ファイル読み込み完了！")
horse_opts = [f"{r.get('馬番')}番 {r.get('馬名')}" for _, r in df_saved.iterrows()]
act_1 = st.selectbox("🥇 1着馬", ["選択してください"] + horse_opts, key="r_1")
act_2 = st.selectbox("🥈 2着馬", ["選択してください"] + horse_opts, key="r_2")
act_3 = st.selectbox("🥉 3着馬", ["選択してください"] + horse_opts, key="r_3")
if st.button("🔍 的中判定を実行"):
if "選択してください" in [act_1, act_2, act_3]:
st.warning("1〜3着すべてを選択してください。")
else:
def parse_num(s):
m = re.match(r"^(\d+)番", str(s))
return m.group(1) if m else ""
act_nums = {parse_num(act_1), parse_num(act_2), parse_num(act_3)}
top5_nums = {str(df_saved.iloc[i].get('馬番')) for i in range(min(5, len(df_saved)))}
match_cnt = len(act_nums.intersection(top5_nums))
if match_cnt == 3:
st.success("🎉 3連複的中！上位5頭に1〜3着が網羅されています。")
elif match_cnt == 2:
st.warning("⚠️ 惜しい外れ（上位5頭に2頭が該当）")
else:
st.warning("❌ 外れ")
with tab3:
st.header("プロ予想 ＆ 合算ハイブリッド比較ボード")
if "df_ranked" in st.session_state and not st.session_state.df_ranked.empty:
df_r = st.session_state.df_ranked
candidates = [f"{row.get('馬番')}番 {row.get('馬名')}" for _, row in df_r.iterrows()]
st.subheader("プロ予想家 上位6頭セレクト")
p_picks = []
cols = st.columns(3)
for i, label in enumerate(["◎ 本命", "○ 対抗", "▲ 単穴", "△ 連下1", "× 連下2", "☆ 注目"]):
with cols[i % 3]:
p_picks.append(st.selectbox(label, ["選択してください"] + candidates, key=f"p_pick_{i}"))
compare_mode = st.selectbox("モード", ["🔥 合算ハイブリッド", "📝 プロ予想単体", "🤖 AIシミュレーション単体"])
st.subheader("実際のレース結果")
h_1 = st.selectbox("🥇 1着", ["選択してください"] + candidates, key="h_1")
h_2 = st.selectbox("🥈 2着", ["選択してください"] + candidates, key="h_2")
h_3 = st.selectbox("🥉 3着", ["選択してください"] + candidates, key="h_3")
if st.button("🔄 的中判定を実行", type="primary"):
valid_p = [int(re.match(r"^(\d+)番", p).group(1)) for p in p_picks if p != "選択してください" and re.match(r"^(\d+)番", p)]
ai_nums = [int(df_r.iloc[i]["馬番"]) for i in range(min(5, len(df_r)))]
if "合算" in compare_mode:
target = []
for n in ai_nums + valid_p:
if n not in target: target.append(n)
target = target[:6]
elif "プロ" in compare_mode:
target = valid_p[:6]
else:
target = ai_nums[:5]
combos = list(combinations(sorted(target[:6]), 3)) if len(target) >= 3 else []
def p_num(s):
m = re.match(r"^(\d+)番", str(s))
return int(m.group(1)) if m else None
act_set = {p_num(h_1), p_num(h_2), p_num(h_3)}
hit = any(set(c) == act_set for c in combos)
st.markdown("---")
if hit:
st.success("🎉 的中しました！")
else:
st.warning("❌ 外れました。")
else:
st.info("まずはTab1でシミュレーションを実行してください。")
