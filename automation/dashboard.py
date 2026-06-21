import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from automation.analytics import get_youtube_stats, get_youtube_top_videos, get_tiktok_stats, get_tiktok_top_videos

st.set_page_config(page_title="MoneyPrinter Dashboard", layout="wide", page_icon="🎬")

st.title("🎬 MoneyPrinter Dashboard")
st.caption("YouTube Shorts + TikTok — Analytics Consolidado")

# ─── Filtro de período ───────────────────
days = st.sidebar.selectbox("Período", [7, 14, 28, 90], index=2, format_func=lambda d: f"Últimos {d} dias")

if st.sidebar.button("Atualizar dados"):
    st.cache_data.clear()


@st.cache_data(ttl=1800)
def load_yt_stats(d):
    return get_youtube_stats(d)


@st.cache_data(ttl=1800)
def load_yt_videos():
    return get_youtube_top_videos()


@st.cache_data(ttl=1800)
def load_tt_stats():
    return get_tiktok_stats()


@st.cache_data(ttl=1800)
def load_tt_videos():
    return get_tiktok_top_videos()


yt = load_yt_stats(days)
yt_videos = load_yt_videos()
tt = load_tt_stats()
tt_videos = load_tt_videos()

# ─── KPIs principais ────────────────────
st.subheader("Visão Geral")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Views YT", f"{yt.get('views', 0):,}", help=f"Últimos {days} dias")
col2.metric("Inscritos YT (net)", f"+{yt.get('net_subscribers', 0):,}")
col3.metric("Minutos assistidos", f"{yt.get('watch_minutes', 0):,}")
col4.metric("Seguidores TikTok", f"{tt.get('followers', 0):,}")
col5.metric("Likes TikTok total", f"{tt.get('total_likes', 0):,}")
col6.metric("Vídeos TikTok", f"{tt.get('video_count', 0):,}")

st.divider()

# ─── Gráfico de views diárias (YouTube) ─
st.subheader("YouTube — Views Diárias")
daily = yt.get("daily", [])
if daily:
    df_daily = pd.DataFrame(daily)
    fig = px.bar(df_daily, x="date", y="views", color_discrete_sequence=["#FF0000"],
                 labels={"date": "Data", "views": "Views"})
    fig.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem dados de views diárias disponíveis.")

st.divider()

# ─── Top vídeos ─────────────────────────
col_yt, col_tt = st.columns(2)

with col_yt:
    st.subheader("YouTube — Top Vídeos")
    if yt_videos:
        df_yt = pd.DataFrame(yt_videos)
        fig_yt = px.bar(df_yt.head(10), x="views", y="title", orientation="h",
                        color_discrete_sequence=["#FF0000"],
                        labels={"views": "Views", "title": ""})
        fig_yt.update_layout(height=400, margin=dict(t=10, b=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_yt, use_container_width=True)

        with st.expander("Ver tabela"):
            st.dataframe(df_yt[["title", "views", "likes", "comments"]], use_container_width=True, hide_index=True)
    else:
        st.info("Sem vídeos disponíveis.")

with col_tt:
    st.subheader("TikTok — Top Vídeos")
    if tt_videos:
        df_tt = pd.DataFrame(tt_videos)
        fig_tt = px.bar(df_tt.head(10), x="views", y="title", orientation="h",
                        color_discrete_sequence=["#00F2EA"],
                        labels={"views": "Views", "title": ""})
        fig_tt.update_layout(height=400, margin=dict(t=10, b=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_tt, use_container_width=True)

        with st.expander("Ver tabela"):
            st.dataframe(df_tt[["title", "views", "likes", "comments", "shares"]], use_container_width=True, hide_index=True)
    else:
        st.info("Sem vídeos disponíveis.")

st.divider()

# ─── Comparativo de engajamento ─────────
st.subheader("Engajamento Comparativo")
platforms = ["YouTube", "TikTok"]
likes = [yt.get("likes", 0), tt.get("total_likes", 0)]
fig_eng = go.Figure(data=[
    go.Bar(name="Likes", x=platforms, y=likes, marker_color=["#FF0000", "#00F2EA"]),
])
fig_eng.update_layout(height=300, margin=dict(t=10, b=10))
st.plotly_chart(fig_eng, use_container_width=True)

st.caption("Atualizado a cada 30 min | MoneyPrinter Automation")
