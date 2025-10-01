import streamlit as st
import pandas as pd

st.title("⚽ 무대포 분석 - 축구 승무패 14경기")

# 입력 폼
st.subheader("경기 데이터 입력")
matches = []
for i in range(1, 15):
    team_input = st.text_input(f"{i}경기 (예: 팀A vs 팀B)", key=f"match_{i}")
    odds = st.text_input(f"{i}경기 배당률 (승,무,패) - 콤마로 구분", key=f"odds_{i}")
    votes = st.text_input(f"{i}경기 투표율 (승,무,패 %) - 콤마로 구분", key=f"votes_{i}")
    matches.append({"경기": team_input, "배당률": odds, "투표율": votes})

# 버튼 클릭 시 분석
if st.button("데이터 분석하기"):
    df = pd.DataFrame(matches)

    # 입력 값이 비어있으면 "데이터 없음" 메시지
    if df["경기"].str.strip().eq("").all():
        st.warning("⚠ 경기 데이터를 입력하세요!")
    else:
        st.success("✅ 데이터 불러오기 성공!")
        st.dataframe(df)

        # 간단한 분석 규칙
        st.subheader("자동 픽 분석")
        picks = []
        for idx, row in df.iterrows():
            try:
                votes = [float(x) for x in row["투표율"].split(",")]
                max_vote = max(votes)
                pick_type = votes.index(max_vote)  # 0=승, 1=무, 2=패

                # 규칙 적용
                if max_vote >= 70:  
                    result = ["승","무","패"][pick_type]
                    picks.append(f"{row['경기']} 👉 단통픽 ({result})")
                else:
                    picks.append(f"{row['경기']} 👉 복수 고려")
            except:
                picks.append(f"{row['경기']} 👉 데이터 오류")

        for p in picks:
            st.write(p)
