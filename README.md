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
