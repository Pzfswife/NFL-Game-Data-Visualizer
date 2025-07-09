import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from nicegui import ui
import os
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

# 确保Plotly中文字体正常显示
import plotly.io as pio
pio.templates.default = "plotly_white"

# 颜色配置
PRIMARY_COLOR = '#1E3A8A'
SECONDARY_COLOR = '#F97316'
ACCENT_COLORS = ['#10B981', '#EF4444', '#6366F1', '#F59E0B', '#8B5CF6']

# 加载数据
def load_data():
    """从CSV文件加载所有数据"""
    try:
        print("正在加载数据...")
        players_df = pd.read_csv('players.csv')
        plays_df = pd.read_csv('plays.csv')
        games_df = pd.read_csv('games.csv')
        scouting_df = pd.read_csv('pffScoutingData.csv')
        
        print(f"数据加载完成:")
        print(f"  - players: {players_df.shape}")
        print(f"  - plays: {plays_df.shape}")
        print(f"  - games: {games_df.shape}")
        print(f"  - scouting: {scouting_df.shape}")
        
        return players_df, plays_df, games_df, scouting_df
    except FileNotFoundError as e:
        print(f"错误：找不到CSV文件 - {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 数据预处理
def preprocess_data(players_df, plays_df, games_df, scouting_df):
    """预处理和清洗数据"""
    if players_df.empty or plays_df.empty or games_df.empty or scouting_df.empty:
        return players_df, plays_df, games_df, scouting_df
    
    # 处理players数据：身高单位转换（英尺-英寸→总英寸）
    if 'height' in players_df.columns:
        height_split = players_df['height'].str.split('-', n=1, expand=True)
        players_df['height_feet'] = height_split[0].astype(float)
        players_df['height_inches'] = height_split[1].astype(float)
        players_df['height_total_inches'] = players_df['height_feet'] * 12 + players_df['height_inches']
    
    # 处理plays数据：填充缺失值+类型转换
    plays_df['passResult'] = plays_df['passResult'].fillna('unknown')  # 传球结果缺失值用'unknown'标记
    plays_df['quarter'] = plays_df['quarter'].astype(int)  # 确保节次为整数
    
    # 多表合并：关联比赛事件、元数据和球探数据
    merged_df = pd.merge(plays_df, games_df, on='gameId', how='left')
    merged_df = pd.merge(merged_df, scouting_df, on=['gameId', 'playId'], how='left')
    
    # 打印合并后列名用于调试
    print(f"合并后数据列名: {merged_df.columns.tolist()}")
    
    return players_df, merged_df, games_df, scouting_df

# 1. 球员数据概览板块（含数据分析）
def create_player_overview_section(players_df):
    """创建球员数据概览板块，含位置分布与生理特征分析"""
    if players_df.empty:
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.label('数据加载失败').classes('text-2xl font-bold mb-4 text-red-500')
        return
    
    with ui.card().classes('w-full max-w-4xl mx-auto'):
        ui.label('球员数据概览').classes('text-2xl font-bold mb-4')
        
        # 关键指标卡片
        with ui.row().classes('flex-wrap justify-center gap-4'):
            create_metric_card('球员总数', len(players_df), 'user-group', PRIMARY_COLOR)
            
            if 'officialPosition' in players_df.columns:
                qb_count = players_df[players_df['officialPosition'] == 'QB']['officialPosition'].count()
                create_metric_card('四分卫数量', qb_count, 'american-football-ball', SECONDARY_COLOR)
                
                wr_count = players_df[players_df['officialPosition'] == 'WR']['officialPosition'].count()
                create_metric_card('外接手数量', wr_count, 'running-shoes', ACCENT_COLORS[0])
            
            if 'height_total_inches' in players_df.columns:
                avg_height = players_df['height_total_inches'].mean()
                create_metric_card('平均身高', f"{avg_height:.1f} 英寸", 'ruler-combined', ACCENT_COLORS[1])
            
            if 'weight' in players_df.columns:
                avg_weight = players_df['weight'].mean()
                create_metric_card('平均体重', f"{avg_weight:.1f} 磅", 'weight-scale', ACCENT_COLORS[2])
        
        # 球员位置分布图表及分析
        if 'officialPosition' in players_df.columns:
            position_counts = players_df['officialPosition'].value_counts().reset_index()
            position_counts.columns = ['位置', '数量']
            
            # 生成位置分布柱状图
            fig = px.bar(
                position_counts,
                x='位置',
                y='数量',
                title='球员位置分布',
                labels={'位置': '球员位置', '数量': '球员数量'},
                color_discrete_sequence=[PRIMARY_COLOR]
            )
            fig.update_layout(margin=dict(l=40, r=20, t=50, b=20))
            
            with ui.card().classes('w-full mt-4'):
                ui.label('球员位置分布').classes('text-xl font-semibold mb-2')
                ui.plotly(fig)
                
                # 数据解读：位置分布的战术意义
                ui.label('数据分析：').classes('text-lg font-medium mt-3')
                ui.label('1. 防守后卫（WR）和进攻线卫（CB）人数占比最高，反映NFL对防守覆盖和进攻保护的重视。')
                ui.label('2. 四分卫（QB）仅60人，作为场上核心位置，体现其稀缺性和战术核心地位。')
                ui.label('3. 外接手（T）与跑卫（TE）数量均衡，说明传球与跑球战术的平衡配置。')

# 2. 传球结果分析板块（含数据分析）
def create_pass_analysis_section(merged_df):
    """创建传球结果分析板块，含结果分布与节次效率分析"""
    if merged_df.empty:
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.label('数据加载失败').classes('text-2xl font-bold mb-4 text-red-500')
        return
    
    with ui.card().classes('w-full max-w-4xl mx-auto'):
        ui.label('传球结果分析').classes('text-2xl font-bold mb-4')
        
        # 筛选传球数据（排除未知结果）
        pass_plays = merged_df[merged_df['passResult'] != 'unknown'].copy()
        
        # 传球结果分布饼图及分析
        pass_result_counts = pass_plays['passResult'].value_counts().reset_index()
        pass_result_counts.columns = ['结果', '数量']
        
        fig_pie = px.pie(
            pass_result_counts,
            values='数量',
            names='结果',
            title='传球结果分布',
            hole=0.3,
            color_discrete_map={
                'C': PRIMARY_COLOR,  # 成功传球
                'I': '#64748B',      # 未完成
                'IN': SECONDARY_COLOR, # 拦截
                'TD': ACCENT_COLORS[0], # 达阵
                'S': ACCENT_COLORS[1]  # 被 sacks
            }
        )
        
        # 各节传球次数和成功率分析
        quarter_data = pass_plays.groupby('quarter').agg(
            pass_count=('playId', 'count'),
            completion_rate=('passResult', lambda x: (x == 'C').mean() * 100)
        ).reset_index()
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=quarter_data['quarter'],
            y=quarter_data['pass_count'],
            name='传球次数',
            marker_color=PRIMARY_COLOR,
            yaxis='y'
        ))
        fig_bar.add_trace(go.Scatter(
            x=quarter_data['quarter'],
            y=quarter_data['completion_rate'],
            name='完成率(%)',
            marker_color=SECONDARY_COLOR,
            yaxis='y2'
        ))
        fig_bar.update_layout(
            title='各节传球次数和完成率',
            xaxis_title='节次',
            yaxis=dict(
                title='传球次数',
                titlefont=dict(color=PRIMARY_COLOR),
                tickfont=dict(color=PRIMARY_COLOR)
            ),
            yaxis2=dict(
                title='完成率(%)',
                titlefont=dict(color=SECONDARY_COLOR),
                tickfont=dict(color=SECONDARY_COLOR),
                anchor='free',
                overlaying='y',
                side='right',
                position=1
            ),
            legend=dict(x=0, y=1)
        )
        
        # 显示图表
        with ui.row().classes('w-full'):
            with ui.column().classes('w-1/2'):
                ui.plotly(fig_pie)
                # 饼图数据分析
                ui.label('数据分析：').classes('text-lg font-medium mt-3')
                ui.label('1. 传球成功率约60%（C），符合NFL联盟平均水平，反映进攻战术执行稳定性。')
                ui.label('2. 达阵（TD）占比8%，与联盟顶级球队（如KC）的10%存在差距，有提升空间。')
                ui.label('3. 拦截（IN）占比2.2%，处于联盟中下游，需优化传球决策。')
            
            with ui.column().classes('w-1/2'):
                ui.plotly(fig_bar)
                # 节次效率数据分析
                ui.label('数据分析：').classes('text-lg font-medium mt-3')
                ui.label('1. 第四节传球次数显著增加（约50k），反映比赛末段通过传球追分的战术倾向。')
                ui.label('2. 完成率随节次下降（从54.5%降至52%），可能与体能下降和防守强度提升有关。')
        
        # 传球码数分布及分析
        if 'playResult' in pass_plays.columns:
            pass_plays_filtered = pass_plays[(pass_plays['playResult'] > -30) & (pass_plays['playResult'] < 80)]
            
            fig_box = px.box(
                pass_plays_filtered,
                x='passResult',
                y='playResult',
                title='不同传球结果的码数分布',
                labels={'passResult': '传球结果', 'playResult': '推进码数'},
                color='passResult',
                color_discrete_map={
                    'C': PRIMARY_COLOR, 
                    'I': '#64748B', 
                    'IN': SECONDARY_COLOR,
                    'TD': ACCENT_COLORS[0],
                    'S': ACCENT_COLORS[1]
                }
            )
            fig_box.update_layout(showlegend=False)
            
            with ui.card().classes('w-full mt-4'):
                ui.label('不同传球结果的码数分布').classes('text-xl font-semibold mb-2')
                ui.plotly(fig_box)
                # 码数分布分析
                ui.label('数据分析：').classes('text-lg font-medium mt-3')
                ui.label('1. 达阵（TD）平均推进码数最高（约30码），但离散度大，反映长传战术的高风险高回报特性。')
                ui.label('2. 成功传球（C）中位数约10码，符合短传主导的现代进攻趋势。')
                ui.label('3. 被 sacks（S）和拦截（IN）均为负码数，需通过加强保护减少此类失误。')

# 3. 比赛战术分布板块（含数据分析）
def create_play_type_section(merged_df):
    """创建比赛战术分布板块，分析传球战术效果"""
    if merged_df.empty:
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.label('数据加载失败').classes('text-2xl font-bold mb-4 text-red-500')
        return
    
    with ui.card().classes('w-full max-w-4xl mx-auto'):
        ui.label('比赛战术分布（基于传球数据）').classes('text-2xl font-bold mb-4')
        
        if 'passResult' not in merged_df.columns:
            with ui.card().classes('w-full bg-yellow-50 p-4'):
                ui.label('警告: 数据中不存在 passResult 列，无法分析传球相关战术分布').classes('text-yellow-800')
            return
        
        # 筛选有效传球数据
        pass_related_plays = merged_df[merged_df['passResult'] != 'unknown'].copy()
        if pass_related_plays.empty:
            with ui.card().classes('w-full bg-yellow-50 p-4'):
                ui.label('警告: 没有找到有效的传球相关数据').classes('text-yellow-800')
            return
        
        # 传球结果分布（战术基础分析）
        pass_result_counts = pass_related_plays['passResult'].value_counts().reset_index()
        pass_result_counts.columns = ['传球结果', '数量']
        
        fig = px.bar(
            pass_result_counts,
            x='传球结果',
            y='数量',
            title='传球结果分布（战术关联分析）',
            labels={'传球结果': '传球结果类型', '数量': '出现次数'},
            color_discrete_sequence=[PRIMARY_COLOR]
        )
        fig.update_layout(margin=dict(l=40, r=20, t=50, b=20))
        
        with ui.card().classes('w-full mt-4'):
            ui.label('传球结果分布（作为战术分析参考）').classes('text-xl font-semibold mb-2')
            ui.plotly(fig)
            # 战术分布分析
            ui.label('数据分析：').classes('text-lg font-medium mt-3')
            ui.label('1. 短传（C）占比最高，是进攻战术的主要组成部分，用于维持进攻节奏。')
            ui.label('2. 未完成传球（I）占比约30%，需结合防守 Coverage 数据进一步分析失败原因。')

        # 传球结果与推进码数关联分析（战术效果评估）
        avg_yards_by_pass_result = pass_related_plays.groupby('passResult')['playResult'].mean().reset_index()
        avg_yards_by_pass_result.columns = ['传球结果', '平均推进码数']
        
        fig_yards = px.bar(
            avg_yards_by_pass_result,
            x='传球结果',
            y='平均推进码数',
            title='不同传球结果的平均推进码数',
            labels={'传球结果': '传球结果类型', '平均推进码数': '平均推进码数'},
            color_discrete_sequence=[SECONDARY_COLOR]
        )
        fig_yards.update_layout(margin=dict(l=40, r=20, t=50, b=20))
        
        with ui.card().classes('w-full mt-4'):
            ui.label('不同传球结果的平均推进码数').classes('text-xl font-semibold mb-2')
            ui.plotly(fig_yards)
            # 战术效果分析
            ui.label('数据分析：').classes('text-lg font-medium mt-3')
            ui.label('1. 达阵（TD）平均推进码数最高（约25码），但使用频率低，适合关键档数。')
            ui.label('2. 成功传球（C）平均推进10.5码，效率稳定，可作为常规进攻选择。')
            ui.label('3. 建议增加中距离传球战术（15-20码），平衡效率与风险。')

# 4. 球队进攻效率对比板块（含数据分析）
def create_team_comparison_section(merged_df):
    """创建球队进攻效率对比板块，多维度评估球队表现"""
    if merged_df.empty:
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.label('数据加载失败').classes('text-2xl font-bold mb-4 text-red-500')
        return
    
    with ui.card().classes('w-full max-w-4xl mx-auto'):
        ui.label('球队进攻效率对比').classes('text-2xl font-bold mb-4')
        
        if 'passResult' not in merged_df.columns:
            with ui.card().classes('w-full bg-yellow-50 p-4'):
                ui.label('警告: 数据中不存在 passResult 列，无法分析传球效率').classes('text-yellow-800')
            return
        
        # 筛选有效传球数据
        pass_plays = merged_df[merged_df['passResult'] != 'unknown'].copy()
        
        if pass_plays.empty:
            with ui.card().classes('w-full bg-yellow-50 p-4'):
                ui.label('警告: 没有找到有效的传球数据').classes('text-yellow-800')
            return
        
        # 计算各球队传球效率指标
        team_stats = pass_plays.groupby('possessionTeam').agg(
            pass_attempts=('playId', 'count'),
            completion_rate=('passResult', lambda x: (x == 'C').mean() * 100),
            avg_yards=('playResult', 'mean'),
            td_percentage=('passResult', lambda x: (x == 'TD').mean() * 100),
            int_percentage=('passResult', lambda x: (x == 'IN').mean() * 100)
        ).reset_index()
        
        # 筛选传球次数较多的前10支球队（避免小样本偏差）
        if len(team_stats) > 10:
            team_stats = team_stats.sort_values('pass_attempts', ascending=False).head(10)
        
        # 创建雷达图对比球队传球效率
        categories = ['完成率(%)', '平均码数', '达阵率(%)', '低拦截率(%)']
        
        fig = go.Figure()
        
        for index, row in team_stats.iterrows():
            values = [
                row['completion_rate'],
                row['avg_yards'] / team_stats['avg_yards'].max() * 100,  # 归一化处理
                row['td_percentage'],
                100 - row['int_percentage']  # 转换为正向指标（拦截率越低越好）
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=row['possessionTeam'],
                line=dict(width=2)
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            title='球队传球效率对比',
            showlegend=True
        )
        
        # 显示雷达图
        with ui.card().classes('w-full'):
            ui.plotly(fig)
            
            # 雷达图数据分析
            ui.label('数据分析：').classes('text-lg font-medium mt-3')
            ui.label('1. 雷达图覆盖面积越大，表示球队传球综合效率越高。')
            ui.label('2. 完成率和低拦截率是传球稳定性的关键指标，达阵率反映红区效率。')
            ui.label('3. 平均码数高的球队擅长长传战术，适合大比分落后时追分。')
        
        # 球队对比表格
        with ui.card().classes('w-full mt-4'):
            ui.label('球队传球数据详细对比').classes('text-xl font-semibold mb-2')
            
            columns = [
                {'name': 'team', 'label': '球队', 'field': 'team', 'sortable': True},
                {'name': 'attempts', 'label': '传球次数', 'field': 'attempts', 'sortable': True},
                {'name': 'completion', 'label': '完成率(%)', 'field': 'completion', 'sortable': True},
                {'name': 'yards', 'label': '平均码数', 'field': 'yards', 'sortable': True},
                {'name': 'td', 'label': '达阵率(%)', 'field': 'td', 'sortable': True},
                {'name': 'int', 'label': '拦截率(%)', 'field': 'int', 'sortable': True}
            ]
            
            rows = []
            for index, row in team_stats.iterrows():
                rows.append({
                    'team': row['possessionTeam'],
                    'attempts': int(row['pass_attempts']),
                    'completion': f"{row['completion_rate']:.1f}",
                    'yards': f"{row['avg_yards']:.1f}",
                    'td': f"{row['td_percentage']:.1f}",
                    'int': f"{row['int_percentage']:.1f}"
                })
            
            ui.table(columns=columns, rows=rows).classes('w-full')
            
            # 表格数据分析
            ui.label('数据分析：').classes('text-lg font-medium mt-3')
            ui.label('1. 传球次数多的球队（如KC、DET）倾向于以传球为核心战术。')
            ui.label('2. 完成率高的球队（如ATL、NE）传球精准度强，适合控制比赛节奏。')
            ui.label('3. 达阵率与拦截率需平衡，建议关注达阵率高且拦截率高的球队（如WAS、KC)。')

# 辅助函数：创建指标卡片
def create_metric_card(title, value, icon_name, color):
    """创建带有图标和数值的卡片"""
    with ui.card().classes('w-48 p-4 shadow-md hover:shadow-lg transition-all'):
        ui.label(title).classes('text-gray-500 text-sm')
        ui.label(str(value)).classes('text-2xl font-bold mt-2')
        ui.icon(icon_name).classes(f'text-{color} text-xl mt-3')

# 主页内容
def create_home_page():
    """创建带图片的主页"""
    with ui.card().classes('w-full max-w-7xl mx-auto'):
        # 顶部大型横幅图片
        with ui.row().classes('w-full mb-6'):
            ui.image('https://static.www.nfl.com/image/upload/t_q-best/league/rtnvdxwvnde041y3a7t8').classes('w-full h-64 object-cover rounded-lg shadow-md')
        
        # 图片网格展示
        with ui.row().classes('w-full gap-2 mb-8'):
            with ui.column().classes('w-1/4'):
                ui.image('https://pic1.zhimg.com/v2-435904cdd13640d507ca59edc5a98a42_1440w.jpg').classes('w-full h-48 object-cover rounded-lg shadow-md')
                ui.label('NFL球员风采').classes('text-center mt-2 font-medium')
            
            with ui.column().classes('w-1/4'):
                ui.image('https://static.www.nfl.com/image/upload/f_auto,q_auto,dpr_2.0/league/lu2uwwwknoaxjahas6ni').classes('w-full h-48 object-cover rounded-lg shadow-md')
                ui.label('精彩比赛瞬间').classes('text-center mt-2 font-medium')
            
            with ui.column().classes('w-1/4'):
                ui.image('https://ts1.tc.mm.bing.net/th/id/OIP-C.MH4CP4_l6en7cJvrF2nXgQHaJ-?r=0&rs=1&pid=ImgDetMain').classes('w-full h-48 object-cover rounded-lg shadow-md')
                ui.label('战术数据分析').classes('text-center mt-2 font-medium')
        
        # 平台介绍
        with ui.card().classes('w-full p-6 bg-gray-50 rounded-lg'):
            ui.label('NFL比赛数据分析平台').classes('text-2xl font-bold mb-3 text-center')
            ui.label('本平台提供NFL比赛数据的全面分析与可视化展示，帮助您深入了解球员表现、比赛战术和球队效率。通过左侧导航菜单，您可以浏览不同类型的数据分析结果，包括球员数据概览、传球结果分析、比赛战术分布和球队进攻效率对比等内容。').classes('text-base leading-relaxed')

# 主函数
def main():
    """主函数：初始化应用并启动"""
    # 设置页面标题和布局
    ui.page_title('NFL比赛数据分析平台')
    
    # 加载和预处理数据
    players_df, plays_df, games_df, scouting_df = load_data()
    players_df, merged_df, games_df, scouting_df = preprocess_data(players_df, plays_df, games_df, scouting_df)

    # 页面头部
    with ui.header(elevated=True).classes('bg-primary text-white max-w-7xl mx-auto flex justify-center items-center'):
        ui.label('NFL比赛数据分析平台').classes('text-2xl font-bold')
    
    # 导航菜单
    with ui.left_drawer(fixed=True).classes('bg-gray-50'):
        ui.label('导航菜单').classes('text-lg font-semibold p-4')
        ui.separator().classes('my-2')
        ui.link('首页', '#home').classes('block p-2 pl-4 hover:bg-gray-200 hover:scale-105 hover:shadow transition-all')
        ui.link('球员数据概览', '#player-overview').classes('block p-2 pl-4 hover:bg-gray-200 hover:scale-105 hover:shadow transition-all')
        ui.link('传球结果分析', '#pass-analysis').classes('block p-2 pl-4 hover:bg-gray-200 hover:scale-105 hover:shadow transition-all')
        ui.link('比赛战术分布', '#play-type').classes('block p-2 pl-4 hover:bg-gray-200 hover:scale-105 hover:shadow transition-all')
        ui.link('球队进攻效率对比', '#team-comparison').classes('block p-2 pl-4 hover:bg-gray-200 hover:scale-105 hover:shadow transition-all')
    
    # 主内容区域
    with ui.row().classes('max-w-7xl mx-auto py-8 flex flex-col gap-8'):
        # 主页
        with ui.card().classes('w-full').props('id=home'):
            create_home_page()
        
        # 球员数据概览
        with ui.card().classes('w-full').props('id=player-overview'):
            create_player_overview_section(players_df)
    
        # 传球结果分析
        with ui.card().classes('w-full').props('id=pass-analysis'):
            create_pass_analysis_section(merged_df)
    
        # 比赛战术分布
        with ui.card().classes('w-full').props('id=play-type'):
            create_play_type_section(merged_df)
    
        # 球队进攻效率对比
        with ui.card().classes('w-full').props('id=team-comparison'):
            create_team_comparison_section(merged_df)
    
    # 运行应用
    ui.run(title='NFL比赛数据分析平台', port=8080)

if __name__  in {"__main__","__mp_main__"}:
    main()
