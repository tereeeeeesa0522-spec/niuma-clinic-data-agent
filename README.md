# niuma-clinic-data-agent

牛马诊所限时义诊活动｜数据分析 Agent Demo

## 功能
- 上传 CSV/XLSX
- 自动生成活动总览
- 症状标签表现
- 互动推荐歌曲 10% / 50% / 80% / 100% 播放深度分析
- BGM → 单曲详情页主动访问分析
- 收藏与音乐人转化
- 自动输出运营诊断

## Demo 数据
直接上传 `sample_data.csv` 即可体验。

## 必须字段
date,user_id,employment_status,emotion_tag,song_name,distribution_type,song_exposed,song_clicked,detail_clicked,play_started,play_progress,favorite,share,comment,artist_page_visit,follow_artist

`play_progress` 使用 0~1，例如 0.8 = 播放到 80%。


## v2 优化
- 新增「使用 Demo 示例数据」一键体验按钮
- 调整模拟播放数据，使完播率落在更合理区间


## V3 更新
- 恢复完整播放进度口径：10% / 50% / 80% / 100%（完播率）
- 症状标签表现、互动页歌曲表现、BGM 详情页主动播放表现统一展示上述节点


## V4 修复
- 修复「症状标签表现」新增 10% 到达率后出现的 KeyError。
- 10% / 50% / 80% / 100% 播放进度现在可在标签表现与歌曲表现中正常展示。

## V5 音乐人维度更新
- 原始数据新增 `artist_name`（音乐人）字段；若缺失，Demo 会按活动曲目自动补全。
- 「就诊症状 / 标签表现」增加对应音乐人。
- 「推广歌曲表现」增加音乐人字段。
- 「音乐人转化表现」按音乐人聚合，不再只显示歌曲。
- 音乐人核心指标：关联歌曲曝光UV、推广歌曲播放UV、关联歌曲收藏率、音乐人主页访问UV/率、新增关注UV、音乐人转粉率。
