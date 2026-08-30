
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="牛马诊所限时义诊活动｜数据分析 Agent",
    page_icon="💊",
    layout="wide"
)

REQUIRED = [
    "date","user_id","employment_status","emotion_tag","song_name",
    "distribution_type","song_exposed","song_clicked","detail_clicked",
    "play_started","play_progress","favorite","share","comment",
    "artist_page_visit","follow_artist"
]

def safe_div(a,b):
    return a/b if b else 0

def pct(x):
    return f"{x*100:.1f}%"

def uv(df, condition):
    return df.loc[condition, "user_id"].nunique()

def analyse(df):
    df = df.copy()
    df["play_progress"] = pd.to_numeric(df["play_progress"], errors="coerce").fillna(0).clip(0,1)
    binary_cols = ["song_exposed","song_clicked","detail_clicked","play_started","favorite","share","comment","artist_page_visit","follow_artist"]
    for c in binary_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    activity_uv = df["user_id"].nunique()
    status_uv = df.loc[df["employment_status"].fillna("").astype(str).str.strip()!="","user_id"].nunique()
    tag_uv = df.loc[df["emotion_tag"].fillna("").astype(str).str.strip()!="","user_id"].nunique()
    song_dist_uv = uv(df, df["song_exposed"]==1)
    active_play_uv = uv(df, df["play_started"]==1)
    detail_uv = uv(df, df["detail_clicked"]==1)

    funnel = pd.DataFrame({
        "阶段":["活动访问UV","职场状态选择UV","症状标签选择UV","歌曲分发UV","主动播放UV"],
        "UV":[activity_uv,status_uv,tag_uv,song_dist_uv,active_play_uv]
    })

    inter = df[df["distribution_type"].astype(str).str.contains("互动", na=False)].copy()
    tag_rows=[]
    for tag,g in inter.groupby("emotion_tag"):
        if not str(tag).strip():
            continue
        exp_uv = uv(g, g["song_exposed"]==1)
        click_uv = uv(g, g["song_clicked"]==1)
        play_uv = uv(g, g["play_started"]==1)
        p50 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.5))
        p80 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.8))
        p100 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.999))
        fav = uv(g, g["favorite"]==1)
        tag_rows.append({
            "症状标签":tag,
            "对应歌曲":g["song_name"].mode().iloc[0],
            "选择UV":g["user_id"].nunique(),
            "歌曲卡CTR":safe_div(click_uv,exp_uv),
            "50%到达率":safe_div(p50,play_uv),
            "80%到达率":safe_div(p80,play_uv),
            "完播率":safe_div(p100,play_uv),
            "收藏率":safe_div(fav,play_uv)
        })
    tag_perf = pd.DataFrame(tag_rows)

    song_rows=[]
    for (dist,song),g in df.groupby(["distribution_type","song_name"]):
        exp_uv = uv(g, g["song_exposed"]==1)
        click_uv = uv(g, g["song_clicked"]==1)
        detail_song_uv = uv(g, g["detail_clicked"]==1)
        play_uv = uv(g, g["play_started"]==1)
        p10 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.1))
        p50 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.5))
        p80 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.8))
        p100 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.999))
        fav = uv(g, g["favorite"]==1)
        artist = uv(g, g["artist_page_visit"]==1)
        follow = uv(g, g["follow_artist"]==1)
        song_rows.append({
            "分发类型":dist,
            "歌曲":song,
            "曝光UV":exp_uv,
            "点击UV":click_uv,
            "详情页导流UV":detail_song_uv,
            "播放UV":play_uv,
            "歌曲卡CTR":safe_div(click_uv,exp_uv) if "互动" in str(dist) else None,
            "BGM→详情页转化率":safe_div(detail_song_uv,exp_uv) if "BGM" in str(dist) else None,
            "10%到达率":safe_div(p10,play_uv),
            "50%到达率":safe_div(p50,play_uv),
            "80%到达率":safe_div(p80,play_uv),
            "完播率":safe_div(p100,play_uv),
            "收藏率":safe_div(fav,play_uv),
            "音乐人主页访问率":safe_div(artist,play_uv),
            "音乐人转粉率":safe_div(follow,artist)
        })
    song_perf = pd.DataFrame(song_rows)

    return {
        "activity_uv":activity_uv,
        "tag_uv":tag_uv,
        "active_play_uv":active_play_uv,
        "detail_uv":detail_uv,
        "interaction_completion":safe_div(tag_uv,activity_uv),
        "funnel":funnel,
        "tag_perf":tag_perf,
        "song_perf":song_perf
    }

def diagnosis(m):
    lines=[]
    lines.append(
        f"本期活动访问 UV 为 {m['activity_uv']:,}，完成症状标签选择的用户为 {m['tag_uv']:,}，"
        f"核心互动完成率为 {pct(m['interaction_completion'])}。"
    )
    tag=m["tag_perf"]
    if not tag.empty:
        top=tag.sort_values("选择UV",ascending=False).iloc[0]
        lines.append(f"用户选择最多的症状是「{top['症状标签']}」，选择 UV 为 {int(top['选择UV']):,}。")
        med_ctr=tag["歌曲卡CTR"].median()
        med_50=tag["50%到达率"].median()
        bad=tag[(tag["歌曲卡CTR"]>=med_ctr)&(tag["50%到达率"]<med_50)]
        if not bad.empty:
            b=bad.sort_values("歌曲卡CTR",ascending=False).iloc[0]
            lines.append(
                f"优先检查「{b['症状标签']} → {b['对应歌曲']}」：歌曲卡 CTR 为 {pct(b['歌曲卡CTR'])}，"
                f"但 50% 播放到达率仅 {pct(b['50%到达率'])}。这更像是“标签/包装能吸引点击，但歌曲没有很好承接情绪预期”，"
                f"建议优先调整对应歌曲，而不是降低该症状标签曝光。"
            )
        strong=tag[(tag["选择UV"]>=tag["选择UV"].median())&(tag["80%到达率"]>=tag["80%到达率"].median())]
        if not strong.empty:
            s=strong.sort_values(["选择UV","80%到达率"],ascending=False).iloc[0]
            lines.append(
                f"当前匹配表现较好的组合是「{s['症状标签']} → {s['对应歌曲']}」，"
                f"80% 播放到达率为 {pct(s['80%到达率'])}，兼具较高需求和较深消费。"
            )
    song=m["song_perf"]
    if not song.empty:
        bgm=song[song["分发类型"].astype(str).str.contains("BGM",na=False)]
        if not bgm.empty:
            b=bgm.sort_values("BGM→详情页转化率",ascending=False).iloc[0]
            lines.append(
                f"BGM 中「{b['歌曲']}」从被动曝光到单曲详情页主动访问的转化最好，"
                f"BGM→详情页转化率为 {pct(b['BGM→详情页转化率'])}。"
            )
        fav=song.sort_values("收藏率",ascending=False).iloc[0]
        lines.append(f"深层消费方面，「{fav['歌曲']}」收藏率最高（{pct(fav['收藏率'])}），可作为后续持续加曝光的候选。")
    return "\n\n".join(lines)

st.title("💊 牛马诊所限时义诊活动｜数据分析 Agent")
st.caption("专治：投简历疼、面试疼、上班疼、没人疼")

with st.sidebar:
    st.header("使用说明")
    st.write("点击 Demo 示例数据即可直接体验；也支持上传活动 CSV / XLSX，系统会自动计算看板并输出运营诊断。")
    st.markdown("**核心口径**")
    st.write("播放深度主看 UV；播放进度按歌曲时长百分比计算，统一观察 10% / 50% / 80% / 100% 四个节点。")
    st.write("BGM 为自动播放，因此不使用活动内 BGM 播放深度判断歌曲质量，而看 BGM 曝光 → 单曲详情页主动访问。")

st.markdown("### 开始体验")
col_demo, col_upload = st.columns([1, 2])
with col_demo:
    use_demo = st.button("🚀 使用 Demo 示例数据", type="primary", use_container_width=True)
with col_upload:
    uploaded = st.file_uploader("或上传自己的活动数据", type=["csv","xlsx"], label_visibility="collapsed")

if use_demo:
    st.session_state["use_demo_data"] = True

if uploaded is not None:
    st.session_state["use_demo_data"] = False
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
    st.success(f"已加载：{uploaded.name}")
elif st.session_state.get("use_demo_data", False):
    demo_path = Path(__file__).with_name("sample_data.csv")
    df = pd.read_csv(demo_path)
    st.success("已加载内置 Demo 示例数据，可直接查看完整看板和 Agent 诊断。")
else:
    st.info("首次体验建议直接点击「使用 Demo 示例数据」；也可以上传 CSV / XLSX。")
    st.stop()

missing=[c for c in REQUIRED if c not in df.columns]
if missing:
    st.error("缺少必要字段："+"、".join(missing))
    st.stop()

m=analyse(df)

st.subheader("01｜活动总览")
c1,c2,c3,c4=st.columns(4)
c1.metric("活动访问 UV", f"{m['activity_uv']:,}")
c2.metric("核心互动完成率", pct(m["interaction_completion"]))
c3.metric("推广歌曲主动播放 UV", f"{m['active_play_uv']:,}")
c4.metric("活动直接导流详情页 UV", f"{m['detail_uv']:,}")

st.markdown("**活动核心漏斗**")
st.bar_chart(m["funnel"].set_index("阶段"))

st.subheader("02｜就诊症状 / 标签表现")
tag_show=m["tag_perf"].copy()
if not tag_show.empty:
    for c in ["歌曲卡CTR","10%到达率","50%到达率","80%到达率","完播率","收藏率"]:
        tag_show[c]=tag_show[c].map(pct)
    st.dataframe(tag_show.sort_values("选择UV",ascending=False),use_container_width=True,hide_index=True)
else:
    st.info("暂无互动推荐数据")

st.subheader("03｜推广歌曲表现")
left,right=st.columns(2)

with left:
    st.markdown("**互动页推荐歌曲**")
    inter=m["song_perf"][m["song_perf"]["分发类型"].astype(str).str.contains("互动",na=False)].copy()
    if not inter.empty:
        cols=["歌曲","曝光UV","点击UV","播放UV","歌曲卡CTR","10%到达率","50%到达率","80%到达率","完播率","收藏率"]
        x=inter[cols].copy()
        for c in ["歌曲卡CTR","10%到达率","50%到达率","80%到达率","完播率","收藏率"]:
            x[c]=x[c].map(pct)
        st.dataframe(x,use_container_width=True,hide_index=True)

with right:
    st.markdown("**BGM 歌曲**")
    bgm=m["song_perf"][m["song_perf"]["分发类型"].astype(str).str.contains("BGM",na=False)].copy()
    if not bgm.empty:
        cols=["歌曲","曝光UV","详情页导流UV","播放UV","BGM→详情页转化率","10%到达率","50%到达率","80%到达率","完播率","收藏率"]
        x=bgm[cols].copy()
        for c in ["BGM→详情页转化率","10%到达率","50%到达率","80%到达率","完播率","收藏率"]:
            x[c]=x[c].map(pct)
        st.dataframe(x,use_container_width=True,hide_index=True)

st.subheader("04｜音乐人转化")
artist=m["song_perf"][["歌曲","音乐人主页访问率","音乐人转粉率"]].copy()
artist["音乐人主页访问率"]=artist["音乐人主页访问率"].map(pct)
artist["音乐人转粉率"]=artist["音乐人转粉率"].map(pct)
st.dataframe(artist,use_container_width=True,hide_index=True)

st.subheader("🤖 Agent 运营诊断")
st.caption("规则型数据分析 Agent：根据标签需求、点击、播放深度、收藏与音乐人转化自动定位问题")
st.markdown(diagnosis(m))

with st.expander("查看原始数据"):
    st.dataframe(df,use_container_width=True,hide_index=True)
