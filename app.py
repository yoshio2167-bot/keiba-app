import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="競馬予想AIシミュレーター", layout="wide")

st.title("競馬予想AIシミュレーター ＆ スクショ解析ツール")

# --- タブによる機能の切り替え ---
tab1, tab2 = st.tabs(["レースシミュレーション", "スクショからデータ化"])

with tab1:
  st.header("レースシミュレーション実行")
  st.write("下の入力欄にCSVデータを貼り付けるか、右側のタブでスクショから変換してください。")

  # 従来のテキスト入力・ペースト欄
  pasted_data = st.text_area(
      "ペースト #1 (CSVデータを貼り付け)",
      placeholder="馬番,馬名,単勝オッズ...\n1,サンプルホースA,4.5",
  )

  if pasted_data:
    try:
      # 簡易的なCSV読み込みテスト
      from io import StringIO

      df_input = pd.read_csv(StringIO(pasted_data))
      st.success("データを正常に読み込みました！")
      st.dataframe(df_input)
    except Exception as e:
      st.info(
          "データを貼り付けるとここにプレビューが表示されます。（CSV形式で入力してください）"
      )

  # シミュレーション実行ボタン（仮）
  if st.button("シミュレーション実行"):
    st.write("シミュレーションを実行中...")

with tab2:
  st.header("出馬表スクショからのデータ自動変換")
  st.write(
      "スマホで撮影した出馬表のスクリーンショットをアップロードすると、AIが数値を読み取ってCSV形式に変換します。"
  )

  # スマホのスクショ画像をアップロード
  uploaded_file = st.file_uploader(
      "出馬表のスクリーンショットを選択", type=["jpg", "jpeg", "png"]
  )

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた出馬表", use_column_width=True)

    if st.button("この画像を解析してCSV化する"):
      with st.spinner("画像を解析中...少々お待ちください"):
        # --- 画像解析処理（実際のOCR・Vision AI連携部分） ---
        # ※ここにAPI連携を入れることで、画像から実データを抽出できます。
        # ここではサンプルとして自動生成されたCSVを表示します。

        sample_parsed_data = {
            "馬番": [1, 2, 3, 4, 5],
            "馬名": [
                "ロードサラマンダー",
                "エコロデュエル",
                "ショウナンライシン",
                "マイネルクリソーラ",
                "シルキーヴォイス",
            ],
            "単勝オッズ": [4.2, 11.5, 8.0, 3.4, 25.1],
        }
        df_result = pd.DataFrame(sample_parsed_data)

        st.success("解析が完了しました！")
        st.dataframe(df_result)

        # CSVテキストを出力
        csv_output = df_result.to_csv(index=False)
        st.write(
            "👇 以下のテキストをコピーして「レースシミュレーション」タブの入力欄に貼り付けてください"
        )
        st.text_area(
            "変換されたCSVデータ", csv_output, key="converted_csv_area"
        )
