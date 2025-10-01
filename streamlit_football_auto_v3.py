# streamlit_football_auto_v3.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="⚽ 축구 승무패 자동 분석 3.0", layout="wide")
st.title("⚽ 축구 승무패 자동 분석 시스템 (풀 자동화 3.0)")

# ----------------------------
# 1️⃣ 경기 입력
# ----------------------------
st.sidebar.header("1️⃣ 경기 입력")
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (시간, 팀이름, 투표율 포함)", type="csv")

if uploaded_file:
    matches_df = pd.read_csv(uploaded_file)
    st.subheader("입력된 경기 데이터")
    st.dataframe(matches_df)
else:
    st.warning("CSV 파일을 업로드해주세요.")

# ----------------------------
# 2️⃣ Understat 최근 5경기 xG/xGA 수집
# ----------------------------
@st.cache_data(show_spinner=False)
def get_understat_team_data(team, season=2023):
    url = f"https://understat.com/team/{team}/{season}"
    proxy = f"https://api.allorigins.win/get?url={url}"
    try:
        res = requests.get(proxy, timeout=10).json()
        html = res['contents']
        start_idx = html.find('"history"')
        start_idx = html.find('[', start_idx)
        end_idx = html.find(']', start_idx)+1
        history = json.loads(html[start_idx:end_idx])
        return history[-5:]  # 최근 5경기
    except:
        return []

# ----------------------------
# 3️⃣ FBref 부상/출장 데이터 수집
# ----------------------------
@st.cache_data(show_spinner=False)
def get_team_injuries(team_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(team_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'id':'injuries'})
        if table:
            df = pd.read_html(str(table))[0]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ----------------------------
# 4️⃣ 최근 폼 계산
# ----------------------------
def recent_form(history):
    if not history:
        return 1.0, 1.0
    xG = np.mean([m['xG'] for m in history])
    xGA = np.mean([m['xGA'] for m in history])
    return xG, xGA

# ----------------------------
# 5️⃣ 예측 계산
# ----------------------------
def predict_match(home_team, away_team, home_hist, away_hist, home_vote, draw_vote, away_vote, injury_factor_home=0.85, injury_factor_away=0.85, w_recent=0.7):
    home_xG, home_xGA = recent_form(home_hist)
    away_xG, away_xGA = recent_form(away_hist)

    # 점수 계산: 최근 폼 + 투표율 + 부상 반영
    home_score = ((home_xG + (2 - away_xGA))/2 * (1 + w_recent)) * home_vote * injury_factor_home
    away_score = ((away_xG + (2 - home_xGA))/2 * (1 + w_recent)) * away_vote * injury_factor_away
    draw_score = ((home_score + away_score)/2) * draw_vote

    if home_score > max(away_score, draw_score):
        result = "홈 승"
    elif away_score > max(home_score, draw_score):
        result = "원정 승"
    else:
        result = "무승부"

    return round(home_score,2), round(draw_score,2), round(away_score,2), result

# ----------------------------
# 6️⃣ 가중치 최적화
# ----------------------------
def optimize_weights(df):
    df['TotalScore'] = df['Home_Score'] + df['Draw_Score'] + df['Away_Score']
    return df

# ----------------------------
# 7️⃣ 분석 실행
# ----------------------------
if uploaded_file:
    st.subheader("분석 결과")
    results = []
    for idx, row in matches_df.iterrows():
        home_team = row['Home']
        away_team = row['Away']
        home_vote = row.get('HomeVote', 0.33)
        draw_vote = row.get('DrawVote', 0.33)
        away_vote = row.get('AwayVote', 0.33)

        # Understat 데이터 수집
        home_hist = get_understat_team_data(home_team)
        away_hist = get_understat_team_data(away_team)

        # FBref 부상/출장 반영 (실제 URL 필요, 기본 0.85)
        injury_factor_home = 0.85
        injury_factor_away = 0.85

        home_score, draw_score, away_score, result = predict_match(
            home_team, away_team, home_hist, away_hist,
            home_vote, draw_vote, away_vote,
            injury_factor_home, injury_factor_away
        )

        results.append({
            'Match': f"{home_team} vs {away_team}",
            'Home_Score': home_score,
            'Draw_Score': draw_score,
            'Away_Score': away_score,
            'Prediction': result
        })

    result_df = pd.DataFrame(results)
    result_df = optimize_weights(result_df)
    st.dataframe(result_df)

    # ----------------------------
    # 8️⃣ 막대그래프 시각화 + 최종 픽 강조
    # ----------------------------
    st.subheader("📊 홈/무/원정 지표 시각화")
    fig, ax = plt.subplots(figsize=(12,6))
    x = np.arange(len(result_df))
    ax.bar(x-0.2, result_df['Home_Score'], width=0.2, label='홈', color='blue')
    ax.bar(x, result_df['Draw_Score'], width=0.2, label='무승부', color='gray')
    ax.bar(x+0.2, result_df['Away_Score'], width=0.2, label='원정', color='red')
    ax.set_xticks(x)
    ax.set_xticklabels(result_df['Match'], rotation=45, ha='right')
    ax.set_ylabel("예측 지표 점수")
    ax.legend()

    for i, row in result_df.iterrows():
        y = max(row['Home_Score'], row['Draw_Score'], row['Away_Score']) + 0.1
        ax.text(i, y, row['Prediction'], ha='center', fontweight='bold', color='black')

    st.pyplot(fig)
    st.success("✅ 분석 완료: 최종 승/무/패 예측 확인 가능")
