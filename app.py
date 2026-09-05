            # --- 3連複5点買い目の自動算出ロジック ---
            # シミュレーション結果の勝回/複回上位馬を取得
            top_horses = sim_df.reset_index().head(5)
            
            if len(top_horses) >= 4:
                b1 = top_horses.iloc[0]['馬番']
                b2 = top_horses.iloc[1]['馬番']
                b3 = top_horses.iloc[2]['馬番']
                b4 = top_horses.iloc[3]['馬番']
                b5 = top_horses.iloc[4]['馬番'] if len(top_horses) >= 5 else b4
                
                # 表示用エリア
                st.markdown(f"<span style='font-size:10px; color:#aaa;'>💡 おすすめ3連複5点買い目</span>", unsafe_allow_html=True)
                
                # 例: 軸1頭ながし (上位1頭軸から2〜5位へ流す4点) + 堅軸2頭軸フォーメーション1点
                trio_bets = [
                    f"① 軸: {b1} - 相手: {b2}, {b3}",
                    f"② 軸: {b1} - 相手: {b2}, {b4}",
                    f"③ 軸: {b1} - 相手: {b3}, {b4}",
                    f"④ 軸: {b1} - 相手: {b2}, {b5}",
                    f"⑤ 軸2頭: {b1}, {b2} - 相手: {b3}, {b4}, {b5}"
                ]
                
                for bet in trio_bets:
                    st.markdown(f"<span style='font-size:10px;'>・{bet}</span>", unsafe_allow_html=True)
