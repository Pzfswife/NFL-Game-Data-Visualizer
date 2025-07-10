# NFL-Game-Data-Visualizer
这是一个基于 NFL（美国国家橄榄球联盟）比赛数据的可视化分析平台，旨在通过数据挖掘和可视化技术，帮助用户深入理解 NFL 比赛的战术特点、球员表现和球队效率。平台采用 Python 开发，结合 Pandas 进行数据处理，Plotly 实现交互式可视化，NiceGUI 构建 Web 界面，提供直观、易用的数据探索体验。
# 项目功能
平台包含四个核心分析模块，覆盖 NFL 比赛数据的关键维度：<br>
1.球员数据概览<br>
    &nbsp&nbsp统计联盟球员总数、关键位置（四分卫、外接手等）人数<br>
    &nbsp&nbsp分析球员平均身高、体重等生理特征<br>
    &nbsp&nbsp展示各位置球员分布<br>
    &nbsp&nbsp揭示 NFL 阵容配置特点<br>
2.传球结果分析<br>
    &nbsp&nbsp统计传球成功、失败、达阵、拦截等结果的分布<br>
    &nbsp&nbsp分析不同节次的传球次数与完成率变化，洞察比赛节奏<br>
    &nbsp&nbsp对比不同传球结果的推进码数差异，评估传球效率<br>
3.比赛战术分布<br>
    &nbsp&nbsp分析各类传球战术的使用频率<br>
    &nbsp&nbsp评估不同传球结果对应的平均推进码数，量化战术效果<br>
    &nbsp&nbsp为战术优化提供数据支持（如短传与长传的效率对比）<br>
4.球队进攻效率对比<br>
    &nbsp&nbsp从传球完成率、平均码数、达阵率、拦截率等多维度评估球队表现<br>
    &nbsp&nbsp通过雷达图直观对比多支球队的综合进攻能力<br>
    &nbsp&nbsp提供详细数据表格，支持排序和筛选<br>
# 数据集说明
项目使用 NFL Big Data Bowl 开源数据集，包含 2018-2023 赛季的比赛数据，主要文件包括：<br>
&nbsp&nbspplayers.csv：球员基本信息（位置、身高、体重等），约 2000 条记录<br>
&nbsp&nbspplays.csv：比赛事件数据（传球结果、推进码数等），约 10 万条记录<br>
&nbsp&nbspgames.csv：比赛元数据（对阵双方、日期等），约 500 条记录<br>
&nbsp&nbsppffScoutingData.csv：球探评估数据（错失 tackles 等进阶指标），约 8 万条记录<br> 
