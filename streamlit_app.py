import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


# 간단한 Streamlit 앱: CSV 업로드 후 4가지 그래프(히스토그램, 막대, 산점도, 상자그림)를 그립니다.
st.set_page_config(page_title="성적 시각화 앱", layout="wide")

st.title("📊 성적 데이터 시각화")
st.write("CSV 파일을 업로드하면 히스토그램, 막대그래프, 산점도, 상자그림을 그립니다.")


@st.cache_data
def load_csv(uploaded_file):
    return pd.read_csv(uploaded_file)


with st.sidebar:
    st.header("설정")
    uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])  # (1)
    sample_data = st.checkbox("샘플 데이터 사용")
    chart_type = st.selectbox("그래프 종류 선택", ["히스토그램", "막대그래프", "산점도", "상자그림"])  # (2)

# 데이터 로딩
if uploaded_file is not None:
    try:
        df = load_csv(uploaded_file)
        st.success("CSV 파일이 로드되었습니다.")
    except Exception as e:
        st.error(f"파일을 읽는 동안 오류가 발생했습니다: {e}")
        st.stop()
elif sample_data:
    # 샘플 성적 데이터
    df = pd.DataFrame({
        "학생": [f"학생{i}" for i in range(1, 21)],
        "수학": np.random.randint(40, 100, size=20),
        "영어": np.random.randint(35, 100, size=20),
        "과학": np.random.randint(30, 100, size=20),
        "반": np.random.choice(["A반", "B반"], size=20)
    })
    st.info("샘플 데이터를 사용합니다.")
else:
    st.info("왼쪽 사이드바에서 CSV를 업로드하거나 샘플 데이터를 선택하세요.")
    st.stop()


st.subheader("데이터 미리보기")
st.dataframe(df.head())
st.write("기본 통계")
st.write(df.describe(include='all'))

# 컬럼 분류
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=[object, "category"]).columns.tolist()

st.markdown("---")

st.header(f"선택된 그래프: {chart_type}")

def draw_histogram(df):
    if not numeric_cols:
        st.warning("숫자형 열이 없습니다.")
        return
    col = st.selectbox("히스토그램: 숫자형 열 선택", numeric_cols, key="hist_col")  # (3)
    bins = st.slider("빈 개수", 5, 100, 20, key="hist_bins")
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=bins)),
        y='count()'
    )
    st.altair_chart(chart, use_container_width=True)


def draw_bar(df):
    if not cat_cols and not numeric_cols:
        st.warning("사용 가능한 열이 없습니다.")
        return
    cat = st.selectbox("막대그래프: 범주형 열 선택", cat_cols or df.columns.tolist(), key="bar_cat")  # (3)
    agg_num = st.selectbox("집계할 숫자형 열 선택 (선택하지 않으면 개수)", ["(count)"] + numeric_cols, key="bar_num")
    if agg_num == "(count)":
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{cat}:N", sort='-y'),
            y='count()'
        )
    else:
        agg = st.selectbox("집계 방식 선택", ["sum", "mean"], key="bar_agg")
        if agg == "sum":
            y_enc = alt.Y(f"sum({agg_num}):Q")
        else:
            y_enc = alt.Y(f"mean({agg_num}):Q")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{cat}:N", sort='-y'),
            y=y_enc
        )
    st.altair_chart(chart, use_container_width=True)


def draw_scatter(df):
    if len(numeric_cols) < 2:
        st.warning("산점도를 그리려면 숫자형 열이 최소 2개 필요합니다.")
        return
    x_col = st.selectbox("X축 (숫자형)", numeric_cols, key="scatter_x")
    y_col = st.selectbox("Y축 (숫자형)", [c for c in numeric_cols if c != x_col], key="scatter_y")
    color = None
    if cat_cols:
        color = st.selectbox("색상 그룹 (선택)", ["(없음)"] + cat_cols, key="scatter_color")
        if color == "(없음)":
            color = None
    chart = alt.Chart(df).mark_circle(size=60).encode(
        x=alt.X(f"{x_col}:Q", title=x_col),
        y=alt.Y(f"{y_col}:Q", title=y_col),
    )
    if color:
        chart = chart.encode(color=alt.Color(f"{color}:N"))
    chart = chart.interactive()
    st.altair_chart(chart, use_container_width=True)


def draw_box(df):
    if not numeric_cols:
        st.warning("숫자형 열이 없습니다.")
        return
    val = st.selectbox("상자그림: 숫자형 열 선택", numeric_cols, key="box_val")
    group = None
    if cat_cols:
        group = st.selectbox("그룹 (선택)", ["(없음)"] + cat_cols, key="box_group")
        if group == "(없음)":
            group = None
    if group:
        chart = alt.Chart(df).mark_boxplot().encode(
            x=alt.X(f"{group}:N", title=group),
            y=alt.Y(f"{val}:Q", title=val)
        )
    else:
        # 단일 열의 분포를 상자그림으로 보여주기 위해 상수 x 사용
        df_tmp = df.copy()
        df_tmp["_const"] = "all"
        chart = alt.Chart(df_tmp).mark_boxplot().encode(
            x=alt.X("_const:N", title=""),
            y=alt.Y(f"{val}:Q", title=val)
        )
    st.altair_chart(chart, use_container_width=True)


if chart_type == "히스토그램":
    draw_histogram(df)
elif chart_type == "막대그래프":
    draw_bar(df)
elif chart_type == "산점도":
    draw_scatter(df)
elif chart_type == "상자그림":
    draw_box(df)

st.markdown("---")
st.write("앱 사용법: CSV 업로드 → 그래프 종류 선택 → 변수 선택 → 그래프 확인")

