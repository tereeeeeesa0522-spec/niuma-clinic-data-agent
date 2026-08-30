
import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path

st.set_page_config(
    page_title="牛马诊所限时义诊活动｜数据分析 Agent",
    page_icon="💊",
    layout="wide"
)

ONLINE_DATA_URL = "https://raw.githubusercontent.com/tereeeeeesa0522-spec/niuma-clinic-data-agent/main/sample_data.csv"

SONG_ARTIST_MAP = {
    "你已经长大了，想去哪里都可以": "张三七_",
    "快乐着疲惫": "DEN",
    "恐高的长脖子小鹿": "就是哈比",
    "走走走": "Matt吕彦良",
    "垃圾飞行指南": "门门",
    "食等睡等": "陈以诺Sarah",
    "开心最重要": "才才",
    "我想和你东游西晃": "动物园钉子户",
    "mimimomo": "雷同二友",
    "吗喽狂想曲": "玫瑰岛RoseIsland乐队",
    "金都": "大都会乐团",
    "植物人的闹钟": "失眠白貉",
    "Sunday": "关浩德Walter",
    "没有羊的牧羊人": "裘德",
}

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

@st.cache_data(ttl=300)
def load_online_data():
    """
    从公开在线数据源读取最新 Demo 数据。
    真实业务落地时，这里可以替换为内部 API / SQL / 数仓查询。
    """
    return pd.read_csv(ONLINE_DATA_URL)

def analyse(df):
    df = df.copy()
    if "artist_name" not in df.columns:
        df["artist_name"] = df["song_name"].map(SONG_ARTIST_MAP).fillna("未知音乐人")
    else:
        df["artist_name"] = df["artist_name"].fillna("")
        missing_artist = df["artist_name"].astype(str).str.strip() == ""
        df.loc[missing_artist, "artist_name"] = df.loc[missing_artist, "song_name"].map(SONG_ARTIST_MAP).fillna("未知音乐人")
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
        p10 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.1))
        p50 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.5))
        p80 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.8))
        p100 = uv(g, (g["play_started"]==1)&(g["play_progress"]>=0.999))
        fav = uv(g, g["favorite"]==1)
        tag_rows.append({
            "症状标签":tag,
            "对应歌曲":g["song_name"].mode().iloc[0],
            "对应音乐人":g["artist_name"].mode().iloc[0],
            "选择UV":g["user_id"].nunique(),
            "歌曲卡CTR":safe_div(click_uv,exp_uv),
            "10%到达率":safe_div(p10,play_uv),
            "50%到达率":safe_div(p50,play_uv),
            "80%到达率":safe_div(p80,play_uv),
            "完播率":safe_div(p100,play_uv),
            "收藏率":safe_div(fav,play_uv)
        })
    tag_perf = pd.DataFrame(tag_rows)

    song_rows=[]
    for (dist,song,artist_name),g in df.groupby(["distribution_type","song_name","artist_name"]):
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
            "音乐人":artist_name,
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

    artist_rows=[]
    for artist_name,g in df.groupby("artist_name"):
        songs = " / ".join(sorted(g["song_name"].dropna().astype(str).unique()))
        exp_uv = uv(g, g["song_exposed"]==1)
        play_uv = uv(g, g["play_started"]==1)
        fav_uv = uv(g, g["favorite"]==1)
        artist_visit_uv = uv(g, g["artist_page_visit"]==1)
        follow_uv = uv(g, g["follow_artist"]==1)
        artist_rows.append({
            "音乐人":artist_name,
            "关联推广歌曲":songs,
            "关联歌曲曝光UV":exp_uv,
            "推广歌曲播放UV":play_uv,
            "关联歌曲收藏率":safe_div(fav_uv,play_uv),
            "音乐人主页访问UV":artist_visit_uv,
            "音乐人主页访问率":safe_div(artist_visit_uv,play_uv),
            "新增关注UV":follow_uv,
            "音乐人转粉率":safe_div(follow_uv,artist_visit_uv)
        })
    artist_perf = pd.DataFrame(artist_rows)

    return {
        "activity_uv":activity_uv,
        "tag_uv":tag_uv,
        "active_play_uv":active_play_uv,
        "detail_uv":detail_uv,
        "interaction_completion":safe_div(tag_uv,activity_uv),
        "funnel":funnel,
        "tag_perf":tag_perf,
        "song_perf":song_perf,
        "artist_perf":artist_perf
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

    artist_perf=m["artist_perf"]
    if not artist_perf.empty:
        valid_artist=artist_perf[artist_perf["音乐人主页访问UV"]>0]
        if not valid_artist.empty:
            top_artist=valid_artist.sort_values(["音乐人主页访问率","音乐人转粉率"],ascending=False).iloc[0]
            lines.append(
                f"音乐人转化方面，「{top_artist['音乐人']}」的主页访问率为 {pct(top_artist['音乐人主页访问率'])}，"
                f"转粉率为 {pct(top_artist['音乐人转粉率'])}，是当前从歌曲消费进一步转向音乐人关注表现较好的对象。"
            )
    return "\n\n".join(lines)


def has_gemini_key():
    try:
        return bool(st.secrets.get("GEMINI_API_KEY", ""))
    except Exception:
        return False

def metrics_for_llm(m):
    """只把已经由 Pandas 算好的汇总指标交给大模型，避免让模型自己算原始数据。"""
    tag = m["tag_perf"].copy()
    song = m["song_perf"].copy()
    artist = m["artist_perf"].copy()

    # 限制精度与数据量，降低 token 消耗
    for frame in [tag, song, artist]:
        for c in frame.columns:
            if pd.api.types.is_numeric_dtype(frame[c]):
                frame[c] = frame[c].round(4)

    def clean_records(frame):
        records = frame.to_dict(orient="records")
        clean = []
        for row in records:
            out = {}
            for k, v in row.items():
                if pd.isna(v):
                    out[k] = None
                elif hasattr(v, "item"):
                    out[k] = v.item()
                else:
                    out[k] = v
            clean.append(out)
        return clean

    return {
        "活动总览": {
            "活动访问UV": int(m["activity_uv"]),
            "症状标签选择UV": int(m["tag_uv"]),
            "核心互动完成率": round(float(m["interaction_completion"]), 4),
            "推广歌曲主动播放UV": int(m["active_play_uv"]),
            "活动直接导流详情页UV": int(m["detail_uv"]),
        },
        "症状标签表现": clean_records(tag),
        "推广歌曲表现": clean_records(song),
        "音乐人转化表现": clean_records(artist),
    }

def ask_gemini(m, question):
    from google import genai

    api_key = st.secrets.get("GEMINI_API_KEY", "")
    client = genai.Client(api_key=api_key)
    metrics = metrics_for_llm(m)

    system_context = """
你是一个音乐内容运营数据分析 Agent，负责分析“牛马诊所限时义诊活动”。

活动目标：
通过“职场疼痛/情绪标签 → 对应小众歌曲”的场景化包装，降低用户试听门槛，为推广歌曲及音乐人带来曝光、主动播放和深层消费。

必须遵守的数据口径：
1. 所有数值均来自 Pandas 已计算好的结构化指标，你不要自行重新计算或虚构不存在的数据。
2. 播放深度主看 UV；播放进度按歌曲总时长百分比计算，观察 10% / 50% / 80% / 100%（完播）节点。
3. 互动推荐歌曲重点看：标签选择需求、歌曲卡 CTR、10%/50%/80%/完播率、收藏率。
4. BGM 是自动播放，因此不能使用“活动内 BGM 播放深度”直接评价歌曲质量；重点看 BGM 曝光 → 单曲详情页主动访问，再观察详情页主动播放后的播放深度。
5. CTR 高但 50% 到达率明显低，通常表示标签/包装吸引点击，但歌曲对用户情绪预期的承接偏弱。
6. 标签选择 UV 高且 80% 到达率高，通常代表用户需求强且标签—歌曲匹配较好。
7. 音乐人维度重点看：音乐人主页访问 UV/率、新增关注 UV、音乐人转粉率；同时参考关联推广歌曲的播放与收藏。
8. 只能把能够追踪到的活动直接链路称为“活动直接导流”；不要把活动期间的所有全站增长都归因给活动。
9. 回答要像内容运营分析，不要只复述数字。优先给“现象 → 判断 → 建议动作”。
10. 如果数据不足以支持用户的问题，明确说“当前数据不足以判断”，并指出还需要什么字段。

当前看板指标：
""" + json.dumps(metrics, ensure_ascii=False)

    prompt = system_context + "\n\n用户问题：" + question

    # 为了提高公开 Demo 的稳定性，优先使用与 generate_content 接口成熟兼容的
    # Gemini 2.5 Flash；若遇到临时服务错误，再自动回退到 Flash-Lite。
    model_candidates = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    last_error = None

    for model_name in model_candidates:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                text = getattr(response, "text", None)
                if text:
                    return text
                raise RuntimeError(f"{model_name} 未返回文本内容")
            except Exception as e:
                last_error = e
                if attempt == 0:
                    time.sleep(2.0)

    raise RuntimeError(f"Gemini 调用连续失败：{type(last_error).__name__}: {last_error}")

def gemini_deep_diagnosis(m):
    return ask_gemini(
        m,
        """请基于当前数据做一次深度运营诊断。输出四部分：
1. 活动整体表现；
2. 最值得继续加曝光的标签—歌曲组合，并说明依据；
3. 最需要调整的标签—歌曲组合，并定位主要流失阶段；
4. 音乐人转化中最值得关注的对象和下一步动作。
尽量引用关键指标，但不要堆数字。"""
    )


st.title("💊 牛马诊所限时义诊活动｜数据分析 Agent")
st.caption("专治：投简历疼、面试疼、上班疼、没人疼")

with st.sidebar:
    st.header("使用说明")
    st.write("点击 Demo 示例数据即可直接体验；也支持上传活动 CSV / XLSX，系统会自动计算看板并输出运营诊断。")
    st.markdown("**核心口径**")
    st.write("播放深度主看 UV；播放进度按歌曲时长百分比计算，统一观察 10% / 50% / 80% / 100% 四个节点。")
    st.write("BGM 为自动播放，因此不使用活动内 BGM 播放深度判断歌曲质量，而看 BGM 曝光 → 单曲详情页主动访问。")
    st.write("音乐人维度按 artist_name 聚合，重点观察主页访问 UV / 率、新增关注 UV 与转粉率。")
    st.write("Gemini 接入后：Pandas 负责准确计算，LLM 只负责综合解释、诊断和自由问答。")
    st.write("当前 LLM：Gemini 3.5 Flash；失败时自动切换 Flash-Lite。")
    st.write("数据接入支持：在线同步 / 内置 Demo / CSV/XLSX 上传。在线同步用于模拟真实业务中的 API / SQL / 数仓自动取数。")

st.markdown("### 数据接入")
col_sync, col_demo = st.columns(2)

with col_sync:
    sync_online = st.button("🔄 同步最新在线数据", type="primary", use_container_width=True)

with col_demo:
    use_demo = st.button("🚀 使用 Demo 示例数据", use_container_width=True)

uploaded = st.file_uploader("或上传自己的活动数据（CSV / XLSX）", type=["csv","xlsx"])

if sync_online:
    try:
        with st.spinner("正在从在线数据源同步最新数据..."):
            df = load_online_data()
        st.session_state["data_mode"] = "online"
        st.session_state["online_df"] = df
        st.success("在线数据同步成功。看板已根据最新数据自动刷新。")
    except Exception as e:
        st.error("在线数据同步失败。你仍可使用 Demo 示例数据或手动上传文件。")
        st.caption(f"错误类型：{type(e).__name__}")
        st.session_state.pop("data_mode", None)

if use_demo:
    st.session_state["data_mode"] = "demo"

if uploaded is not None:
    st.session_state["data_mode"] = "upload"
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
    st.session_state["uploaded_df"] = df
    st.session_state["uploaded_name"] = uploaded.name
    st.success(f"已加载：{uploaded.name}")

mode = st.session_state.get("data_mode")

if mode == "online":
    if "online_df" in st.session_state:
        df = st.session_state["online_df"]
        st.caption("当前数据源：在线同步数据（GitHub Raw CSV）")
    else:
        try:
            df = load_online_data()
            st.session_state["online_df"] = df
            st.caption("当前数据源：在线同步数据（GitHub Raw CSV）")
        except Exception as e:
            st.error("在线数据读取失败，请重新点击「同步最新在线数据」。")
            st.stop()

elif mode == "demo":
    demo_path = Path(__file__).with_name("sample_data.csv")
    df = pd.read_csv(demo_path)
    st.success("已加载内置 Demo 示例数据，可直接查看完整看板和 Agent 诊断。")
    st.caption("当前数据源：仓库内置 Demo 数据")

elif mode == "upload":
    if "uploaded_df" not in st.session_state:
        st.info("请重新上传 CSV / XLSX。")
        st.stop()
    df = st.session_state["uploaded_df"]
    st.caption(f"当前数据源：手动上传 · {st.session_state.get('uploaded_name','文件')}")

else:
    st.info("推荐直接点击「🔄 同步最新在线数据」体验自动数据接入；也可以使用 Demo 示例数据或上传 CSV / XLSX。")
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
        cols=["歌曲","音乐人","曝光UV","点击UV","播放UV","歌曲卡CTR","10%到达率","50%到达率","80%到达率","完播率","收藏率"]
        x=inter[cols].copy()
        for c in ["歌曲卡CTR","10%到达率","50%到达率","80%到达率","完播率","收藏率"]:
            x[c]=x[c].map(pct)
        st.dataframe(x,use_container_width=True,hide_index=True)

with right:
    st.markdown("**BGM 歌曲**")
    bgm=m["song_perf"][m["song_perf"]["分发类型"].astype(str).str.contains("BGM",na=False)].copy()
    if not bgm.empty:
        cols=["歌曲","音乐人","曝光UV","详情页导流UV","播放UV","BGM→详情页转化率","10%到达率","50%到达率","80%到达率","完播率","收藏率"]
        x=bgm[cols].copy()
        for c in ["BGM→详情页转化率","10%到达率","50%到达率","80%到达率","完播率","收藏率"]:
            x[c]=x[c].map(pct)
        st.dataframe(x,use_container_width=True,hide_index=True)

st.subheader("04｜音乐人转化表现")
artist=m["artist_perf"].copy()
artist["关联歌曲收藏率"]=artist["关联歌曲收藏率"].map(pct)
artist["音乐人主页访问率"]=artist["音乐人主页访问率"].map(pct)
artist["音乐人转粉率"]=artist["音乐人转粉率"].map(pct)
artist=artist.sort_values(["音乐人主页访问UV","新增关注UV"],ascending=False)
st.dataframe(
    artist[[
        "音乐人","关联推广歌曲","关联歌曲曝光UV","推广歌曲播放UV",
        "关联歌曲收藏率","音乐人主页访问UV","音乐人主页访问率",
        "新增关注UV","音乐人转粉率"
    ]],
    use_container_width=True,
    hide_index=True
)

st.subheader("🤖 Agent 运营诊断")
st.caption("规则层负责稳定定位问题；接入 Gemini 后，可进一步进行开放式分析与问答。")
st.markdown(diagnosis(m))

st.divider()
st.subheader("✨ AI 深度分析 / 问问数据 Agent")

if has_gemini_key():
    st.success("Gemini API Key 已配置")

    if st.button("生成 AI 深度诊断", type="primary", use_container_width=True):
        with st.spinner("Agent 正在综合标签、歌曲与音乐人指标..."):
            try:
                st.session_state["deep_ai_answer"] = gemini_deep_diagnosis(m)
            except Exception as e:
                st.error("AI 调用失败。系统已自动重试并切换备用模型。")
                st.caption(f"错误类型：{type(e).__name__}")
                st.code(str(e)[:1200], language=None)

    if st.session_state.get("deep_ai_answer"):
        st.markdown(st.session_state["deep_ai_answer"])

    st.markdown("**你也可以直接问当前数据：**")
    question = st.text_input(
        "例如：如果只能换掉两首互动歌曲，应该换哪两首？为什么？",
        placeholder="输入你想问的数据问题"
    )
    if st.button("询问数据 Agent", use_container_width=True):
        if not question.strip():
            st.warning("请先输入问题。")
        else:
            with st.spinner("Agent 正在分析当前看板数据..."):
                try:
                    answer = ask_gemini(m, question.strip())
                    st.session_state["qa_answer"] = answer
                except Exception as e:
                    st.error("AI 调用失败。请稍后重试，或检查 Gemini API Key / API 额度。")
                    st.caption(f"错误类型：{type(e).__name__}")

    if st.session_state.get("qa_answer"):
        st.markdown(st.session_state["qa_answer"])
else:
    st.info("当前为规则型 Agent。配置 Gemini API Key 后，这里会自动解锁「AI 深度诊断」和自由问答。")
    st.caption("API Key 只需配置在 Streamlit Secrets 中，不要写入 GitHub 代码或公开仓库。")

with st.expander("查看原始数据"):
    st.dataframe(df,use_container_width=True,hide_index=True)
