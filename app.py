import streamlit as st
import pandas as pd
import random
import zipfile
import io
import os

st.title("🏇 中央競馬・土日開催 全3場全12R 予想＆実績検証シミュレーター")

# サイドバーで曜日、競馬場、レース選択
st.sidebar.header("📍 開催選択")
selected_day = st.sidebar.radio("開催日", ["土曜日", "日曜日"])
day_prefix = "sat" if selected_day == "土曜日" else "sun"

selected_course = st.sidebar.selectbox("競馬場", ["阪神", "中山", "東京"])
course_prefix_map = {"阪神": "hanshin", "中山": "nakayama", "東京": "tokyo"}
course_prefix = course_prefix_map[selected_course]

race_options = [f"第{i}レース (R{i})" for i in range(1, 13)]
selected_race = st.sidebar.selectbox(f"{selected_course} 全12R 選択", race_options)
race_num = int(selected_race.replace("第", "").replace("レース", "").split(" ")[0])

surface = st.sidebar.radio("コース種別", ["芝", "ダート"])
distance = st.sidebar.selectbox("距離", ["1200m (短距離)", "1400m", "1600m (マイル)", "1800m", "2000m (中距離)", "2400m以上 (長距離)"])
weather = st.sidebar.selectbox("天候", ["晴", "曇", "雨", "雪"])
track_condition = st.sidebar.selectbox("馬場状態", ["良", "稍重", "重", "不良"])

st.markdown(f"**現在表示中:** **{selected_day}** / {selected_course} **{selected_race}** ({surface}・{distance}) / 天候: **{weather}** / 馬場: **{track_condition}**")

# 1. ZIPファイル または 複数CSVのドラッグ＆ドロップ対応
st.subheader("1. 出馬表データ（ZIPファイル または CSV一括ドロップ対応）")
uploaded_file = st.file_uploader(
    "ZIPファイル（例: keiba_data_72races.zip など）またはCSVファイルをここにドラッグ＆ドロップしてください", 
    type=["zip", "csv"], 
    accept_multiple_files=False
)

matched_df = None
extracted_files = {}

if uploaded_file is not None:
    if uploaded_file.name.endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
                for filename in z.namelist():
                    if filename.endswith('.csv'):
                        with z.open(filename) as f:
                            base_name = os.path.basename(filename)
                            extracted_files[base_name.lower()] = f.read()
            st.success(f"📦 ZIPファイル「{uploaded_file.name}」からCSVデータを読み込みました！")
        except Exception as e:
            st.error(f"ZIPファイルの読み込みに失敗しました: {e}")
    else:
        base_name = os.path.basename(uploaded_file.name)
        extracted_files[base_name.lower()] = uploaded_file.read()

target_filename = f"{day_prefix}_{course_prefix}_r{race_num}.csv"

if extracted_files:
    if target_filename.lower() in extracted_files:
        content = extracted_files[target_filename.lower()]
        try:
            matched_df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
        except UnicodeDecodeError:
            matched_df = pd.read_csv(io.BytesIO(content), encoding='shift-jis')
        st.success(f"📁 「{target_filename}」を自動マッチして読み込みました！")
    else:
        st.warning(f"⚠️ アップロードされたデータの中に「{target_filename}」が見つかりませんでした。標準の自動生成データを使用します。")

if matched_df is not None:
    df = matched_df
else:
    seed_key = hash(day_prefix) + hash(course_prefix) + race_num * 37
    random.seed(seed_key)

    num_horses = 14 if race_num == 11 else 12
    base_names = ['テーオー', 'ロード', 'リバティ', 'コントレイル', 'イクイノックス', 'ダノン', 'ドウデュース', 'グランブリッジ', 'シャドウ', 'レッド', 'ファントム', 'ブルー', 'セイウン', 'ダイワ']

    horses = [f"{base_names[i % len(base_names)]}{i+1}号" for i in range(num_horses)]
    odds = [round(1.5 + (i * 2.8) + random.uniform(0.0, 1.5), 1) if i < 3 else round(10.0 + (i * 3.5), 1) for i in range(num_horses)]

    df = pd.DataFrame({
        '枠番': [(i % 8) + 1 for i in range(num_horses)],
        '馬番': [i + 1 for i in range(num_horses)],
        '馬名': horses,
        '単勝オッズ': odds,
        '脚質': [random.choice(['逃げ', '先行', '差し', '追込']) for _ in range(num_horses)],
        '上がり3F': [round(random.uniform(33.2, 35.5), 1) for _ in range(num_horses)],
        'スピード指数': [random.randint(78, 95) for _ in range(num_horses)],
        '騎手勝率': [round(random.uniform(0.08, 0.22), 2) for _ in range(num_horses)],
        '距離適性': [random.randint(80, 94) for _ in range(num_horses)],
        'スタミナ': [random.randint(80, 94) for _ in range(num_horses)],
        '間隔(週)': [random.randint(2, 10) for _ in range(num_horses)],
        '直近5走平均着順': [round(random.uniform(1.5, 6.5), 1) for _ in range(num_horses)]
    })
    if not uploaded_file:
        st.info(f"※ ZIP未選択のため、**{selected_day}・{selected_course} {selected_race}** の標準データを使用しています。")

# 安全セーフティカラム確認
default_columns = {
    '枠番': 1, '馬番': 1, '馬名': '不明馬', '単勝オッズ': 10.0,
    '脚質': '先行', '上がり3F': 35.0, 'スピード指数': 80,
    '騎手勝率': 0.10, '距離適性': 80, 'スタミナ': 80,
    '間隔(週)': 4, '直近5走平均着順': 5.0
}
for col, default_val in default_columns.items():
    if col not in df.columns:
        df[col] = default_val

st.subheader("2. 出馬表データの確認")
st.dataframe(df)

if 'result_df' not in st.session_state:
    st.session_state.result_df = None

if st.button("AI予想＆買い目を実行"):
    max_rank = 10.0
    df['直近成績スコア'] = (max_rank - df['直近5走平均着順'].clip(1, 10)) * 10
    df['上がり3Fスコア'] = (40.0 - df['上がり3F'].clip(32, 40)) * 10
    
    is_long_straight = selected_course in ["東京", "新潟", "阪神"]
    is_power_cond = (track_condition in ["重", "不良"]) or (weather in ["雨", "雪"])
    
    w_speed = 0.25
    w_jockey = 0.15
    w_dist = 0.15
    w_stamina = 0.10
    w_recent = 0.10
    w_3f = 0.15
    w_interval = 0.10

    if "1200m" in distance or "1400m" in distance:
        w_speed += 0.05
        w_3f += 0.05
        w_stamina -= 0.05
    elif "2400m" in distance:
        w_stamina += 0.15
        w_dist += 0.05
        w_speed -= 0.10

    if surface == "ダート" or is_power_cond:
        w_stamina += 0.10
        w_speed -= 0.05
        w_3f -= 0.05
    elif is_long_straight and surface == "芝":
        w_3f += 0.05

    total_w = w_speed + w_jockey + w_dist + w_stamina + w_recent + w_3f + w_interval
    w_speed /= total_w
    w_jockey /= total_w
    w_dist /= total_w
    w_stamina /= total_w
    w_recent /= total_w
    w_3f /= total_w
    w_interval /= total_w

    df['スコア'] = (
        df['スピード指数'] * w_speed +
        df['騎手勝率'] * 100 * w_jockey +
        df['距離適性'] * w_dist +
        df['スタミナ'] * w_stamina +
        df['直近成績スコア'] * w_recent +
        df['上がり3Fスコア'] * w_3f +
        (df['間隔(週)'] * 0.5) * w_interval
    )
    
    result_df = df.sort_values(by='スコア', ascending=False).reset_index(drop=True)
    
    印リスト = []
    for i in range(len(result_df)):
        if i == 0: 印リスト.append("◎ 本命")
        elif i == 1: 印リスト.append("○ 対抗")
        elif i == 2: 印リスト.append("▲ 単穴")
        elif 3 <= i <= 4: 印リスト.append("△ 連下")
        else: 印リスト.append("-")
    
    result_df['印'] = 印リスト
    st.session_state.result_df = result_df

if st.session_state.result_df is not None:
    res_df = st.session_state.result_df
    
    st.subheader("📊 予想・印の結果")
    st.dataframe(res_df[['印', '枠番', '馬番', '馬名', '脚質', '上がり3F', '単勝オッズ', 'スコア']])
    
    st.subheader("🎫 焼き鳥防止！おすすめ買い目シミュレーション")
    if len(res_df) >= 3:
        本命行 = res_df.loc[res_df['印'] == "◎ 本命"].iloc[0]
        対抗行 = res_df.loc[res_df['印'] == "○ 対抗"].iloc[0]
        単穴行 = res_df.loc[res_df['印'] == "▲ 単穴"].iloc[0]
        
        st.markdown(f"""
        * **複勝:** **{本命行['馬番']}番 {本命行['馬名']}**
        * **ワイド流し:** **{本命行['馬番']}番 － {対抗行['馬番']}番, {単穴行['馬番']}番**
        """)
    
    st.subheader("📈 10回シミュレーション統計 (勝率・複勝率分析)")
    if st.button("📊 10回レースを自動シミュレートして統計を出す"):
        with st.spinner("シミュレーション実行中..."):
            wins = {name: 0 for name in res_df['馬名']}
            podiums = {name: 0 for name in res_df['馬名']}
            
            for _ in range(10):
                sim_df = res_df[['馬番', '馬名', 'スコア']].copy()
                sim_df['current_pos'] = sim_df['スコア'] + [random.uniform(-10, 10) for _ in range(len(sim_df))]
                sim_df = sim_df.sort_values(by='current_pos', ascending=False).reset_index(drop=True)
                
                winner = sim_df.loc[0, '馬名']
                wins[winner] += 1
                
                for i in range(min(3, len(sim_df))):
                    p_name = sim_df.loc[i, '馬名']
                    podiums[p_name] += 1
            
            stats_data = []
            for _, row in res_df.iterrows():
                m_name = row['馬名']
                w_count = wins[m_name]
                p_count = podiums[m_name]
                stats_data.append({
                    '枠番': row['枠番'],
                    '馬番': row['馬番'],
                    '馬名': m_name,
                    '1着回数': w_count,
                    '勝率(%)': f"{w_count / 10 * 100:.1f}%",
                    '3着内回数': p_count,
                    '複勝率(%)': f"{p_count / 10 * 100:.1f}%"
                })
            
            stats_df = pd.DataFrame(stats_data).sort_values(by='1着回数', ascending=False).reset_index(drop=True)
            st.success("統計データの集計が完了しました！")
            st.dataframe(stats_df)

    # 3. 実際の結果入力＆検証モード
    st.subheader("🎯 実際の結果（着順）入力 ＆ 的中・回収率検証")
    st.markdown("レース終了後、実際の1着〜3着の馬番を入力または選択して、AI予想が的中したか検証できます！")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        actual_1st_no = st.selectbox("実際の1着 馬番", res_df['馬番'].tolist(), index=0)
    with col2:
        actual_2nd_no = st.selectbox("実際の2着 馬番", res_df['馬番'].tolist(), index=min(1, len(res_df)-1))
    with col3:
        actual_3rd_no = st.selectbox("実際の3着 馬番", res_df['馬番'].tolist(), index=min(2, len(res_df)-1))
        
    if st.button("🏆 検証結果を集計する"):
        honmei_row = res_df.loc[res_df['印'] == "◎ 本命"].iloc[0]
        honmei_no = honmei_row['馬番']
        
        is_honmei_place = (honmei_no in [actual_1st_no, actual_2nd_no, actual_3rd_no])
        
        st.markdown("### 📊 検証レポート")
        st.write(f"- **AI本命 (◎):** {honmei_row['馬名']} (馬番: {honmei_no})")
        st.write(f"- **実際の入着:** 1着[{actual_1st_no}番] / 2着[{actual_2nd_no}番] / 3着[{actual_3rd_no}番]")
        
        if is_honmei_place:
            st.success("🎉 **本命馬が馬券圏内（3着以内）好走的中！**")
        else:
            st.warning("💦 本命馬は馬券圏外となりました。")
