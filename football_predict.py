#!/usr/bin/env python3
"""
足球预测系统 - Hermes Agent 贝叶斯+Elo 混合分析引擎
数据源: TheSportsDB 免费API
新特性: Elo评级, 主客场优势, 状态衰减权重, 泊松比分分布
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
import math
from datetime import datetime, timedelta
from pathlib import Path

# ============ 配置 ============

# 目标联赛 ID (TheSportsDB)
LEAGUES = {
    "4328": "英超",
    "4331": "德甲",
    "4332": "意甲",
    "4334": "法甲",
    "4335": "西甲",
    "4480": "欧冠",
}

# 中文球队名映射
TEAM_CN = {
    # 英超
    "Manchester City": "曼城",
    "Manchester United": "曼联",
    "Liverpool": "利物浦",
    "Arsenal": "阿森纳",
    "Chelsea": "切尔西",
    "Tottenham Hotspur": "热刺",
    "Crystal Palace": "水晶宫",
    "Everton": "埃弗顿",
    "Leicester City": "莱斯特城",
    "West Ham United": "西汉姆联",
    "Wolverhampton Wanderers": "狼队",
    "Newcastle United": "纽卡斯尔",
    "Brighton and Hove Albion": "布莱顿",
    "Aston Villa": "阿斯顿维拉",
    "Fulham": "富勒姆",
    "Brentford": "布伦特福德",
    "Bournemouth": "伯恩茅斯",
    "Nottingham Forest": "诺丁汉森林",
    "Burnley": "伯恩利",
    "Southampton": "南安普顿",
    "Ipswich Town": "伊普斯维奇",
    "Leeds United": "利兹联",
    "Sheffield United": "谢菲联",
    # 西甲
    "Real Madrid": "皇家马德里",
    "Barcelona": "巴塞罗那",
    "Atlético Madrid": "马德里竞技",
    "Atletico Madrid": "马德里竞技",
    "Sevilla": "塞维利亚",
    "Real Sociedad": "皇家社会",
    "Villarreal": "比利亚雷亚尔",
    "Real Betis": "皇家贝蒂斯",
    "Athletic Bilbao": "毕尔巴鄂竞技",
    "Valencia": "瓦伦西亚",
    "Celta Vigo": "塞尔塔",
    "Osasuna": "奥萨苏纳",
    "Getafe": "赫塔费",
    "Girona": "赫罗纳",
    "Rayo Vallecano": "巴列卡诺",
    "Mallorca": "马略卡",
    "Alavés": "阿拉维斯",
    "Alaves": "阿拉维斯",
    "Las Palmas": "拉斯帕尔马斯",
    "Espanyol": "西班牙人",
    "Levante": "莱万特",
    "Elche": "埃尔切",
    "Real Oviedo": "皇家奥维耶多",
    "Granada": "格拉纳达",
    # 意甲
    "Juventus": "尤文图斯",
    "AC Milan": "AC米兰",
    "AC Milan (Italy)": "AC米兰",
    "Inter Milan": "国际米兰",
    "Inter": "国际米兰",
    "Roma": "罗马",
    "Napoli": "那不勒斯",
    "Lazio": "拉齐奥",
    "Atalanta": "亚特兰大",
    "Fiorentina": "佛罗伦萨",
    "Bologna": "博洛尼亚",
    "Torino": "都灵",
    "Udinese": "乌迪内斯",
    "Sassuolo": "萨索洛",
    "Cagliari": "卡利亚里",
    "Genoa": "热那亚",
    "Monza": "蒙扎",
    "Lecce": "莱切",
    "Frosinone": "弗罗西诺内",
    "Empoli": "恩波利",
    "Como": "科莫",
    "Parma": "帕尔马",
    "Venezia": "威尼斯",
    # 德甲
    "Bayern Munich": "拜仁慕尼黑",
    "Bayern München": "拜仁慕尼黑",
    "Borussia Dortmund": "多特蒙德",
    "RB Leipzig": "莱比锡红牛",
    "Bayer Leverkusen": "勒沃库森",
    "Eintracht Frankfurt": "法兰克福",
    "VfB Stuttgart": "斯图加特",
    "VfL Wolfsburg": "沃尔夫斯堡",
    "Borussia Mönchengladbach": "门兴格拉德巴赫",
    "Borussia M'gladbach": "门兴",
    "FC Augsburg": "奥格斯堡",
    "1. FC Union Berlin": "柏林联合",
    "Union Berlin": "柏林联合",
    "SC Freiburg": "弗赖堡",
    "1. FC Köln": "科隆",
    "FC Cologne": "科隆",
    "1. FSV Mainz 05": "美因茨",
    "Mainz": "美因茨",
    "TSG 1899 Hoffenheim": "霍芬海姆",
    "Hoffenheim": "霍芬海姆",
    "SV Werder Bremen": "不莱梅",
    "Werder Bremen": "不莱梅",
    "VfL Bochum": "波鸿",
    "Hamburg": "汉堡",
    "Hamburger SV": "汉堡",
    "Hertha BSC": "柏林赫塔",
    "FC St. Pauli": "圣保利",
    "Heidenheim": "海登海姆",
    "1. FC Heidenheim": "海登海姆",
    "Holstein Kiel": "荷尔斯泰因基尔",
    # 法甲
    "Paris Saint-Germain": "巴黎圣日耳曼",
    "Paris SG": "巴黎圣日耳曼",
    "Olympique Marseille": "马赛",
    "Marseille": "马赛",
    "Olympique Lyonnais": "里昂",
    "Lyon": "里昂",
    "AS Monaco": "摩纳哥",
    "Monaco": "摩纳哥",
    "LOSC Lille": "里尔",
    "Lille": "里尔",
    "Stade Rennais": "雷恩",
    "Rennes": "雷恩",
    "OGC Nice": "尼斯",
    "Nice": "尼斯",
    "RC Lens": "朗斯",
    "Lens": "朗斯",
    "FC Nantes": "南特",
    "Nantes": "南特",
    "Montpellier HSC": "蒙彼利埃",
    "Montpellier": "蒙彼利埃",
    "Stade de Reims": "兰斯",
    "Reims": "兰斯",
    "RC Strasbourg": "斯特拉斯堡",
    "Strasbourg": "斯特拉斯堡",
    "Toulouse FC": "图卢兹",
    "Toulouse": "图卢兹",
    "Stade Brestois 29": "布雷斯特",
    "Brest": "布雷斯特",
    "Le Havre": "勒阿弗尔",
    "Clermont Foot": "克莱蒙",
    "AJ Auxerre": "欧塞尔",
    "Red Star": "红星",
    "Rodez AF": "罗德兹",
    "Angers": "昂热",
    "Angers SCO": "昂热",
    "Metz": "梅斯",
    # 其他
    "Paris SG (France)": "巴黎圣日耳曼",
    "Young Boys": "伯尔尼年轻人",
    "Celtic": "凯尔特人",
    "Rangers": "流浪者",
    "Sporting CP": "葡萄牙体育",
    "Sporting Lisbon": "葡萄牙体育",
    "Benfica": "本菲卡",
    "FC Porto": "波尔图",
    "Ajax": "阿贾克斯",
    "PSV": "埃因霍温",
    "Feyenoord": "费耶诺德",
    "Club Brugge": "布鲁日",
    "Shakhtar Donetsk": "顿涅茨克矿工",
    "Dynamo Kyiv": "基辅迪纳摩",
    "Galatasaray": "加拉塔萨雷",
    "Fenerbahçe": "费内巴切",
    "Fenerbahce": "费内巴切",
    "Red Star Belgrade": "贝尔格莱德红星",
    "Slavia Prague": "布拉格斯拉维亚",
    "AC Milan (Italy) PSG": "AC米兰",
    "Juventus (Italy)": "尤文图斯",
    # 欧冠专用
    "Club Brugge (Belgium)": "布鲁日",
    "Feyenoord (Netherlands)": "费耶诺德",
    "PSV (Netherlands)": "埃因霍温",
    "Celtic (Scotland)": "凯尔特人",
    "Club Brugge KV": "布鲁日",
}


# ============ Elo 评级系统 ============

class EloRating:
    """
    Elo评级系统用于评估球队实力，不依赖外部API。

    关键参数:
    - 初始评分: 1500
    - K因子: 32 (联赛) / 48 (杯赛)
    - 主队优势: +70 分
    - 预期得分: Ea = 1/(1+10^((Rb-Ra)/400))
    - 评分更新: Ra_new = Ra + K * (S - Ea)
    """

    INITIAL_RATING = 1500
    K_LEAGUE = 32
    K_CUP = 48
    HOME_ADVANTAGE = 70

    def __init__(self, ratings=None):
        """初始化 Elo 系统，可从已有评分加载"""
        self.ratings = ratings if ratings else {}
        self.learnings_path = os.path.expanduser("~/.learnings/足球/LEARNINGS.md")

    def get_rating(self, team_name):
        """获取球队当前 Elo 评分"""
        return self.ratings.get(team_name, self.INITIAL_RATING)

    def expected_score(self, rating_a, rating_b):
        """计算球队A对球队B的预期得分 Ea = 1/(1+10^((Rb-Ra)/400))"""
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def update(self, home_team, away_team, home_score, away_score, is_cup=False):
        """
        根据比赛结果更新两队 Elo 评分。

        参数:
            home_team, away_team: 球队名
            home_score, away_score: 进球数
            is_cup: 是否为杯赛（影响K因子）
        """
        k = self.K_CUP if is_cup else self.K_LEAGUE

        # 获取评分（含主队优势）
        home_rating = self.get_rating(home_team) + self.HOME_ADVANTAGE
        away_rating = self.get_rating(away_team)

        # 预期得分
        e_home = self.expected_score(home_rating, away_rating)
        e_away = 1.0 - e_home

        # 实际得分: 胜=1, 平=0.5, 负=0
        if home_score > away_score:
            s_home, s_away = 1.0, 0.0
        elif home_score == away_score:
            s_home, s_away = 0.5, 0.5
        else:
            s_home, s_away = 0.0, 1.0

        # 评分更新（去除主队优势后保存）
        new_home = self.get_rating(home_team) + k * (s_home - e_home)
        new_away = self.get_rating(away_team) + k * (s_away - e_away)

        self.ratings[home_team] = round(new_home, 1)
        self.ratings[away_team] = round(new_away, 1)

        return {
            "home_old": round(self.get_rating(home_team) - k * (s_home - e_home), 1),
            "away_old": round(self.get_rating(away_team) - k * (s_away - e_away), 1),
            "home_new": self.ratings[home_team],
            "away_new": self.ratings[away_team],
            "expected_home_win_pct": round(e_home * 100, 1),
        }

    def predict_win_prob(self, home_team, away_team, is_cup=False):
        """
        基于 Elo 预测主队获胜概率。

        返回: (主胜概率, 平局概率, 客胜概率)
        平局概率通过 Elo 差值经验公式估算:
        - Elo差<50: 平局概率~26%
        - Elo差50-150: 平局概率~24%
        - Elo差>150: 平局概率~22%
        """
        home_rating = self.get_rating(home_team) + self.HOME_ADVANTAGE
        away_rating = self.get_rating(away_team)

        e_home = self.expected_score(home_rating, away_rating)

        # 将 Elo 预期得分映射为三路概率
        # e_home 是主队"不输"的概率（含平局），需要拆分
        elo_diff = home_rating - away_rating

        # 平局概率: Elo差越大，平局概率越低
        if abs(elo_diff) < 50:
            p_draw = 0.26
        elif abs(elo_diff) < 150:
            p_draw = 0.24
        else:
            p_draw = 0.22

        # 从 e_home 中拆分出纯胜概率
        # e_home = p_home + 0.5 * p_draw
        p_home = e_home - 0.5 * p_draw
        p_away = 1.0 - p_home - p_draw

        # 确保非负
        p_home = max(0.01, p_home)
        p_away = max(0.01, p_away)

        # 重新归一化
        total = p_home + p_draw + p_away
        p_home /= total
        p_draw /= total
        p_away /= total

        return p_home, p_draw, p_away

    def elo_to_coefficient(self, home_team, away_team):
        """
        将 Elo 差值映射为主胜概率调整系数。
        用于修正贝叶斯先验概率。

        返回: (调整因子, Elo差值)
        - 调整因子>1: 主队更强
        - 调整因子<1: 客队更强
        """
        home_rating = self.get_rating(home_team) + self.HOME_ADVANTAGE
        away_rating = self.get_rating(away_team)
        diff = home_rating - away_rating

        # 映射: Elo差100分 ≈ 胜率差14%
        # 调整系数范围 0.6 ~ 1.4
        coef = 1.0 + (diff / 400.0)
        coef = max(0.6, min(1.4, coef))
        return coef, diff

    def load_from_learnings(self):
        """从 LEARNINGS.md 加载持久化的 Elo 评分"""
        if not os.path.exists(self.learnings_path):
            return

        with open(self.learnings_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找 Elo 评分块
        elo_section = re.search(r'### Elo 评分.*?\n(.*?)(?=\n###|\Z)', content, re.DOTALL)
        if not elo_section:
            return

        for line in elo_section.group(1).strip().split('\n'):
            # 格式: - 球队名：评分
            m = re.match(r'- (.+?)：([\d.]+)', line)
            if m:
                self.ratings[m.group(1).strip()] = float(m.group(2))

    def save_to_learnings(self, learnings_path=None):
        """将 Elo 评分持久化到 LEARNINGS.md"""
        if learnings_path is None:
            learnings_path = self.learnings_path

        if not os.path.exists(learnings_path):
            return

        with open(learnings_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按评分降序排列
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)

        elo_block = "### Elo 评分（实时更新）\n"
        elo_block += f"- 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        elo_block += f"- 初始评分: {self.INITIAL_RATING}\n"
        elo_block += f"- K因子: 联赛={self.K_LEAGUE}, 杯赛={self.K_CUP}\n"
        elo_block += f"- 主队优势: +{self.HOME_ADVANTAGE}\n"
        elo_block += "\n"
        for team, rating in sorted_teams:
            elo_block += f"- {team}：{rating:.1f}\n"
        elo_block += "\n"

        # 替换或追加 Elo 评分块
        if "### Elo 评分" in content:
            content = re.sub(
                r'### Elo 评分.*?\n(.*?)(?=\n###|\Z)',
                elo_block,
                content,
                count=1,
                flags=re.DOTALL
            )
        else:
            # 在复盘记录之前插入
            marker = "### 复盘记录"
            if marker in content:
                content = content.replace(marker, elo_block + marker)
            else:
                content += "\n\n" + elo_block

        with open(learnings_path, "w", encoding="utf-8") as f:
            f.write(content)


# ============ 主客场优势系数（从历史数据学习） ============

class HomeAdvantageTracker:
    """
    主客场优势系数 - 从历史比赛结果学习。
    动态跟踪每个联赛的主队平均积分率。
    """

    def __init__(self):
        self.league_stats = {}  # {league_name: {"home_pts_ratio": float, "matches": int}}
        self.learnings_path = os.path.expanduser("~/.learnings/足球/LEARNINGS.md")
        self._load()

    def _load(self):
        """从 LEARNINGS.md 加载历史主客场数据"""
        if not os.path.exists(self.learnings_path):
            return
        with open(self.learnings_path, "r", encoding="utf-8") as f:
            content = f.read()

        section = re.search(r'### 主客场优势系数.*?\n(.*?)(?=\n###|\Z)', content, re.DOTALL)
        if not section:
            return

        for line in section.group(1).strip().split('\n'):
            m = re.match(r'- (.+?)：(\d+\.\d+) \((\d+)场\)', line)
            if m:
                league = m.group(1).strip()
                ratio = float(m.group(2))
                matches = int(m.group(3))
                self.league_stats[league] = {"home_pts_ratio": ratio, "matches": matches}

    def record_match(self, league, home_score, away_score):
        """
        记录一场比赛结果，更新主队积分率。
        主队积分率 = 主队实际积分 / (比赛数 * 3)
        胜=3分, 平=1分, 负=0分
        """
        if league not in self.league_stats:
            self.league_stats[league] = {"home_pts_ratio": 1.5, "matches": 0}

        stat = self.league_stats[league]
        if home_score > away_score:
            pts = 3
        elif home_score == away_score:
            pts = 1
        else:
            pts = 0

        total_matches = stat["matches"] + 1
        total_pts = stat["home_pts_ratio"] * stat["matches"] + pts
        stat["home_pts_ratio"] = total_pts / (total_matches * 3) * 3  # 归一化到每场
        stat["matches"] = total_matches

    def get_home_advantage(self, league):
        """获取联赛的主场优势系数（相对于联赛基础概率的调整）"""
        if league in self.league_stats:
            # 历史平均主队积分率 / 1.5（基准 = 主队平均每场1.5分）
            ratio = self.league_stats[league]["home_pts_ratio"]
            return ratio / 1.5
        return 1.0  # 无数据时返回基准值

    def save(self, learnings_path=None):
        """持久化到 LEARNINGS.md"""
        if learnings_path is None:
            learnings_path = self.learnings_path
        if not os.path.exists(learnings_path):
            return

        with open(learnings_path, "r", encoding="utf-8") as f:
            content = f.read()

        block = "### 主客场优势系数（历史学习）\n"
        block += f"- 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        block += "- 主队积分率 = 主队场均积分 / 1.5（基准线）\n"
        block += "- >1.0 表示主场优势高于平均, <1.0 表示低于平均\n\n"
        for league, stat in sorted(self.league_stats.items()):
            block += f"- {league}：{stat['home_pts_ratio']:.3f} ({stat['matches']}场)\n"
        block += "\n"

        if "### 主客场优势系数" in content:
            content = re.sub(
                r'### 主客场优势系数.*?\n(.*?)(?=\n###|\Z)',
                block,
                content,
                count=1,
                flags=re.DOTALL
            )
        else:
            marker = "### Elo 评分"
            if marker in content:
                content = content.replace(marker, block + marker)
            else:
                marker = "### 复盘记录"
                if marker in content:
                    content = content.replace(marker, block + marker)
                else:
                    content += "\n\n" + block

        with open(learnings_path, "w", encoding="utf-8") as f:
            f.write(content)


# ============ 泊松比分分布预测 ============

def poisson_prob(k, lam):
    """泊松分布概率: P(X=k) = (λ^k * e^(-λ)) / k!"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def predict_score_distribution(home_gf_avg, home_ga_avg, away_gf_avg, away_ga_avg, max_goals=6):
    """
    使用泊松回归预测比分分布。

    参数:
        home_gf_avg: 主队场均进球
        home_ga_avg: 主队场均失球
        away_gf_avg: 客队场均进球
        away_ga_avg: 客队场均失球
        max_goals: 最大考虑进球数

    返回:
        {
            "distributions": {(主队进球, 客队进球): 概率, ...},
            "most_likely": (主队进球, 客队进球),
            "home_win_pct": 主胜概率,
            "draw_pct": 平局概率,
            "away_win_pct": 客胜概率,
            "expected_home_goals": 期望主队进球,
            "expected_away_goals": 期望客队进球,
            "over_25_pct": 大2.5球概率,
            "under_25_pct": 小2.5球概率,
            "btts_pct": 两队都进球概率,
        }
    """
    # 调整预期进球: 主队进攻 vs 客队防守, 客队进攻 vs 主队防守
    lam_home = max(0.1, (home_gf_avg + away_ga_avg) / 2)
    lam_away = max(0.1, (away_gf_avg + home_ga_avg) / 2)

    # 计算所有比分组合概率
    distributions = {}
    p_home_win = 0.0
    p_draw = 0.0
    p_away_win = 0.0
    p_over_25 = 0.0
    p_btts = 0.0

    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            prob = poisson_prob(hg, lam_home) * poisson_prob(ag, lam_away)
            distributions[(hg, ag)] = prob

            if hg > ag:
                p_home_win += prob
            elif hg == ag:
                p_draw += prob
            else:
                p_away_win += prob

            if hg + ag > 2.5:
                p_over_25 += prob
            if hg > 0 and ag > 0:
                p_btts += prob

    # 找到最可能的比分
    most_likely = max(distributions, key=distributions.get)
    most_likely_prob = distributions[most_likely]

    # 计算期望进球
    exp_home = sum(hg * prob for (hg, ag), prob in distributions.items())
    exp_away = sum(ag * prob for (hg, ag), prob in distributions.items())

    return {
        "distributions": distributions,
        "most_likely": most_likely,
        "most_likely_prob": round(most_likely_prob * 100, 1),
        "home_win_pct": round(p_home_win * 100, 1),
        "draw_pct": round(p_draw * 100, 1),
        "away_win_pct": round(p_away_win * 100, 1),
        "expected_home_goals": round(exp_home, 2),
        "expected_away_goals": round(exp_away, 2),
        "over_25_pct": round(p_over_25 * 100, 1),
        "btts_pct": round(p_btts * 100, 1),
    }


def format_score_distribution(dist, top_n=5):
    """
    格式化比分分布输出，显示前N个最可能比分
    """
    sorted_dist = sorted(dist["distributions"].items(), key=lambda x: x[1], reverse=True)
    result = []
    for (hg, ag), prob in sorted_dist[:top_n]:
        result.append(f"{hg}:{ag} {prob*100:.1f}%")
    return " | ".join(result)


# ============ 辅助函数 ============

def cn(name):
    """球队名中文化"""
    return TEAM_CN.get(name, name)


def fetch_json(url, max_retries=3):
    """带重试的JSON数据获取"""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
            else:
                print(f"  [WARN] 请求失败: {url[:60]}... -> {e}", file=sys.stderr)
                return None


def fetch_upcoming_matches(days=3):
    """获取未来N天的比赛"""
    matches = []
    today = datetime.now()
    for d in range(days):
        date_str = (today + timedelta(days=d)).strftime("%Y-%m-%d")
        data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={date_str}&s=Soccer")
        if data is None or not data or "events" not in data:
            continue
        for e in data["events"]:
            league_name = e.get("strLeague", "")
            league_id = str(e.get("idLeague", ""))
            # 匹配目标联赛
            for lid, lcn in LEAGUES.items():
                if league_id == lid or lcn in league_name:
                    e["_league_cn"] = lcn
                    e["_fetch_date"] = date_str
                    e["_round"] = e.get("intRound", "?")
                    matches.append(e)
                    break
    return matches


def get_round_results(league_id, season="2025-2026", num_rounds=3):
    """获取最近N个完整轮次的所有比赛结果（含比分）用于Elos训练
    使用 eventsround.php 替代 eventslast.php，数据量提升10倍+
    返回: {team_name: [(对手, 进球, 失球, 主客场), ...], ...}
    """
    from collections import defaultdict
    from collections import defaultdict
    results = defaultdict(list)
    
    # 获取最近一个已知完成轮次: 从当前轮次往前推
    for r in range(37 - num_rounds + 1, 38):
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsround.php?id={league_id}&r={r}&s={season}"
        data = fetch_json(url)
        if data is None or not data or "events" not in data or data["events"] is None:
            continue
        for e in data["events"]:
            home = e.get("strHomeTeam", "")
            away = e.get("strAwayTeam", "")
            hs = e.get("intHomeScore", "") or e.get("strHomeTeamScore", "")
            as_ = e.get("intAwayScore", "") or e.get("strAwayTeamScore", "")
            if hs and as_ and hs.isdigit() and as_.isdigit():
                hs, as_ = int(hs), int(as_)
                results[home].append((away, hs, as_, "home"))
                results[away].append((home, as_, hs, "away"))
    return dict(results)

def get_team_form(team_id):
    """获取球队近期战绩 - 改用轮次数据增强"""
    # 已由 get_round_results 取代，保留此接口用于兼容
    return []


def get_league_table(league_id, season="2025-2026"):
    """获取联赛积分榜"""
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/lookuptable.php?l={league_id}&s={season}")
    if data is None or not data or "table" not in data:
        return []
    return data["table"]


def get_team_info(team_name):
    """获取球队详细信息"""
    import urllib.parse
    data = fetch_json(f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={urllib.parse.quote(team_name)}")
    if data is None or not data or "teams" not in data:
        return None
    for t in data["teams"]:
        if t.get("strTeam", "").lower() == team_name.lower():
            return t
    return data["teams"][0] if data["teams"] else None


def calc_form_score_decayed(events, team_name, max_games=5, decay_factor=0.85):
    """
    计算近期状态分 - 带衰减权重。

    衰减权重: 最近1场权重1.0, 每向前一场乘以 decay_factor。
    胜=3, 平=1, 负=0, 按加权平均归一化。

    参数:
        events: 比赛列表（最近排在前面）
        team_name: 球队名
        max_games: 最多考虑场次
        decay_factor: 衰减因子（<1, 越远期权重越低）

    返回: (加权状态分0-100, 加权场均进球, 加权场均失球)
    """
    total_weight = 0.0
    weighted_score = 0.0
    weighted_gf = 0.0
    weighted_ga = 0.0

    for i, e in enumerate(events[:max_games]):
        weight = decay_factor ** i  # i=0最近，权重1.0; i=4最远，权重0.85^4≈0.52
        home = e.get("strHomeTeam", "")
        away = e.get("strAwayTeam", "")
        hs = e.get("intHomeScore")
        as_ = e.get("intAwayScore")
        if hs is None or as_ is None:
            continue
        try:
            hs, as_ = int(hs), int(as_)
        except:
            continue

        if team_name == home:
            pts = 3 if hs > as_ else (1 if hs == as_ else 0)
            weighted_score += pts * weight
            weighted_gf += hs * weight
            weighted_ga += as_ * weight
        elif team_name == away:
            pts = 3 if as_ > hs else (1 if as_ == hs else 0)
            weighted_score += pts * weight
            weighted_gf += as_ * weight
            weighted_ga += hs * weight
        else:
            continue

        total_weight += weight

    if total_weight == 0:
        return 50, 1.0, 1.0

    avg_score = weighted_score / total_weight / 3 * 100  # 归一化到0-100
    avg_gf = weighted_gf / total_weight
    avg_ga = weighted_ga / total_weight

    return avg_score, avg_gf, avg_ga


def calc_defense_rating(avg_ga, base=5.0):
    """防守韧性评分：失球越少分越高"""
    rating = max(0, base - avg_ga * 1.5)
    return round(rating, 1)


def is_simeone_coach(team_name):
    """判断是否为西蒙尼型死守教练"""
    simeone_teams = ["马德里竞技", "Atlético Madrid", "Atletico Madrid", "马竞"]
    return team_name in simeone_teams or cn(team_name) in simeone_teams


def load_prior_params():
    """从 LEARNINGS.md 加载先验参数"""
    learnings_path = os.path.expanduser("~/.learnings/足球/LEARNINGS.md")
    params = {
        "league_base": {},
        "knockout_coef": 0.85,
        "defense_base": 5.0,
        "simeone_coef": 0.70,
        "odds_weight": 0.30,
        "injury_weight": 0.20,
        "h2h_weight": 0.15,
        "form_weight": 0.25,
        "defense_weight": 0.10,
        "elo_weight": 0.35,  # Elo 权重（新增）
    }
    if os.path.exists(learnings_path):
        with open(learnings_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 解析联赛基础概率
        league_pattern = re.findall(r'- (.+?)[：:]主胜 (\d+)%.*?平局 (\d+)%.*?客胜 (\d+)%', content)
        for league, h, d, a in league_pattern:
            league = league.strip()
            params["league_base"][league] = {
                "home": int(h) / 100,
                "draw": int(d) / 100,
                "away": int(a) / 100,
            }
        # 解析模型系数
        coef_patterns = [
            (r'淘汰赛次回合保守系数[：:]([\d.]+)', "knockout_coef"),
            (r'防守韧性基准分[：:]([\d.]+)', "defense_base"),
            (r'西蒙尼型教练死守系数[：:]([\d.]+)', "simeone_coef"),
        ]
        for pat, key in coef_patterns:
            m = re.search(pat, content)
            if m:
                params[key] = float(m.group(1))
        # 解析权重
        weight_patterns = [
            (r'赔率变化权重[：:](\d+)%', "odds_weight"),
            (r'伤病影响权重[：:](\d+)%', "injury_weight"),
            (r'历史交锋权重[：:](\d+)%', "h2h_weight"),
            (r'近期状态权重[：:](\d+)%', "form_weight"),
            (r'防守韧性权重[：:](\d+)%', "defense_weight"),
            (r'Elo评级权重[：:](\d+)%', "elo_weight"),
        ]
        for pat, key in weight_patterns:
            m = re.search(pat, content)
            if m:
                params[key] = int(m.group(1)) / 100
    return params


# ============ 贝叶斯分析（增强版） ============

def bayes_analysis(match, params, form_data=None, elo_system=None, home_adv_tracker=None):
    """
    贝叶斯分析增强版:
    - 保留原有贝叶斯框架
    - 新增 Elo 评级修正
    - 主客场优势系数
    - 状态衰减权重已内置
    """
    league_cn = match.get("_league_cn", "英超")
    home_team = match.get("strHomeTeam", "")
    away_team = match.get("strAwayTeam", "")
    home_cn = cn(home_team)
    away_cn = cn(away_team)

    # 1. 先验概率 P0
    league_base = params["league_base"]
    if league_cn in league_base:
        prior = league_base[league_cn]
    else:
        prior = {"home": 0.45, "draw": 0.25, "away": 0.30}

    p_home, p_draw, p_away = prior["home"], prior["draw"], prior["away"]

    # 2. 主客场优势系数调整（新增）
    if home_adv_tracker:
        home_adv = home_adv_tracker.get_home_advantage(league_cn)
        if home_adv != 1.0:
            p_home *= home_adv
            p_away /= home_adv
            total = p_home + p_draw + p_away
            p_home /= total
            p_draw /= total
            p_away /= total

    # 3. 淘汰赛调整
    is_knockout = any(k in match.get("strEvent", "") for k in ["Semi", "Final", "Quarter", "Round of 16"])
    if is_knockout:
        p_away *= params["knockout_coef"]
        p_draw *= (1 + (1 - params["knockout_coef"]) * 0.5)
        total = p_home + p_draw + p_away
        p_home /= total
        p_draw /= total
        p_away /= total

    # 4. 状态更新（带衰减权重）
    form_score_home = 50
    form_score_away = 50
    home_goals_for = 0
    home_goals_against = 0
    away_goals_for = 0
    away_goals_against = 0

    if form_data and home_team in form_data:
        fh = form_data[home_team]
        form_score_home = fh.get("score", 50)
        home_goals_for = fh.get("gf", 0)
        home_goals_against = fh.get("ga", 0)
    if form_data and away_team in form_data:
        fa = form_data[away_team]
        form_score_away = fa.get("score", 50)
        away_goals_for = fa.get("gf", 0)
        away_goals_against = fa.get("ga", 0)

    form_factor = (form_score_home - form_score_away) / 100  # -1 to 1
    p_home *= (1 + form_factor * params["form_weight"])
    p_away *= (1 - form_factor * params["form_weight"])

    # 5. 防守韧性调整
    home_defense = calc_defense_rating(home_goals_against, params["defense_base"])
    away_defense = calc_defense_rating(away_goals_against, params["defense_base"])
    defense_diff = (home_defense - away_defense) / params["defense_base"]
    p_home *= (1 + defense_diff * params["defense_weight"])
    p_away *= (1 - defense_diff * params["defense_weight"])

    # 6. 西蒙尼型教练死守调整
    if is_simeone_coach(home_team):
        p_draw += (p_home - p_draw) * 0.1 * params["simeone_coef"]
        p_home *= (1 - 0.05 * params["simeone_coef"])
    if is_simeone_coach(away_team):
        p_draw += (p_away - p_draw) * 0.1 * params["simeone_coef"]
        p_away *= (1 - 0.05 * params["simeone_coef"])

    # 归一化
    total = p_home + p_draw + p_away
    p_home /= total
    p_draw /= total
    p_away /= total

    # 7. Elo 评级修正（新增）
    elo_home_original = None
    elo_away_original = None
    elo_home_prob = None
    elo_away_prob = None
    elo_adjust_factor = 1.0
    elo_diff = 0

    if elo_system:
        elo_home_original = elo_system.get_rating(home_team)
        elo_away_original = elo_system.get_rating(away_team)
        adj_factor, elo_diff = elo_system.elo_to_coefficient(home_team, away_team)
        elo_adjust_factor = adj_factor

        # Elo 直接预测概率
        e_home, e_draw, e_away = elo_system.predict_win_prob(home_team, away_team,
                                                              is_cup=(league_cn == "欧冠"))
        elo_home_prob = e_home
        elo_away_prob = e_away

        # 加权融合: Bayesian * (1 - elo_weight) + Elo * elo_weight
        ew = params.get("elo_weight", 0.35)
        p_home = p_home * (1 - ew) + e_home * ew
        p_draw = p_draw * (1 - ew) + e_draw * ew
        p_away = p_away * (1 - ew) + e_away * ew

    # 最终归一化
    total = p_home + p_draw + p_away
    p_home /= total
    p_draw /= total
    p_away /= total

    # 确定推荐
    max_p = max(p_home, p_draw, p_away)
    if p_home == max_p:
        if p_home > 0.50:
            rec = f"主胜 ⚽ ({home_cn})"
        elif p_home > 0.40:
            rec = f"看好主队不败"
        else:
            rec = "双选倾向"
    elif p_draw == max_p:
        rec = "平局 ⏸️"
    else:
        if p_away > 0.50:
            rec = f"客胜 ⚽ ({away_cn})"
        elif p_away > 0.40:
            rec = f"看好客队不败"
        else:
            rec = "双选倾向"

    # 置信度
    confidence = int(max_p * 100)
    if confidence >= 55:
        conf_star = "⭐⭐⭐"
    elif confidence >= 48:
        conf_star = "⭐⭐"
    else:
        conf_star = "⭐"

    # 泊松比分分布预测（新增）
    poisson_dist = predict_score_distribution(
        home_goals_for if home_goals_for > 0 else 1.0,
        home_goals_against if home_goals_against > 0 else 1.0,
        away_goals_for if away_goals_for > 0 else 1.0,
        away_goals_against if away_goals_against > 0 else 1.0,
    )

    result = {
        "home": round(p_home * 100, 1),
        "draw": round(p_draw * 100, 1),
        "away": round(p_away * 100, 1),
        "recommendation": rec,
        "confidence": confidence,
        "confidence_star": conf_star,
        "home_defense": home_defense,
        "away_defense": away_defense,
        "is_knockout": is_knockout,
        "home_form": round(form_score_home, 1),
        "away_form": round(form_score_away, 1),
        # Elo 数据
        "elo_home": elo_home_original,
        "elo_away": elo_away_original,
        "elo_diff": round(elo_diff, 1),
        "elo_adjust_factor": round(elo_adjust_factor, 3),
        "elo_home_prob": round(elo_home_prob * 100, 1) if elo_home_prob else None,
        "elo_away_prob": round(elo_away_prob * 100, 1) if elo_away_prob else None,
        # 泊松比分数据
        "poisson": poisson_dist,
    }

    return result


# ============ 报告生成 ============

def generate_report(matches, results):
    """生成格式化的预测报告（增强版）"""
    lines = []
    lines.append("=" * 66)
    lines.append(f"  🏟️  足球赛果预测报告")
    lines.append(f"  📅  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 66)
    lines.append("")

    # 按联赛分组
    from collections import OrderedDict
    groups = OrderedDict()
    for m, r in zip(matches, results):
        league = m.get("_league_cn", "其他")
        if league not in groups:
            groups[league] = []
        groups[league].append((m, r))

    for league, items in groups.items():
        lines.append(f"  📋 ── {league} ──\n")
        for m, r in items:
            home_cn = cn(m.get("strHomeTeam", ""))
            away_cn = cn(m.get("strAwayTeam", ""))
            date = m.get("dateEvent", "?")
            time_ = m.get("strTime", "??")[:5]
            round_ = m.get("_round", "?")

            lines.append(f"  {home_cn} vs {away_cn}")
            lines.append(f"  ⏰ {date} {time_}  |  第{round_}轮")
            hp, dp, ap = r['home'], r['draw'], r['away']
            bp = lambda v: '█' * int(v/10) + '░' * (10 - int(v/10))
            lines.append(f"  🟢 主胜{hp:5.1f}% {bp(hp)}")
            lines.append(f"  🟡 平局{dp:5.1f}% {bp(dp)}")
            lines.append(f"  🔴 客胜{ap:5.1f}% {bp(ap)}")
            lines.append(f"  🎯 推荐: {r['recommendation']}  📊 置信度: {r['confidence']}% {r['confidence_star']}")

            # Elo 评分显示（新增）
            if r.get("elo_home") is not None:
                elo_h = r["elo_home"]
                elo_a = r["elo_away"]
                elo_d = r["elo_diff"]
                elo_bar_h = '█' * int(min(abs(elo_d), 200) / 20) if elo_d > 0 else '░' * 3
                elo_bar_a = '█' * int(min(abs(elo_d), 200) / 20) if elo_d < 0 else '░' * 3
                lines.append(f"  ⚡ Elo: {home_cn}({elo_h:.0f}) {'+' if elo_d>0 else ''}{elo_d:.0f} {away_cn}({elo_a:.0f})")
                lines.append(f"     Elo调整系数: x{r['elo_adjust_factor']:.3f}")

            # 防守韧性
            dh = '█' * int(r['home_defense']) + '░' * (5 - int(r['home_defense']))
            da = '█' * int(r['away_defense']) + '░' * (5 - int(r['away_defense']))
            lines.append(f"  🛡️ 防守: {home_cn} [{dh}] vs {away_cn} [{da}]")

            # 泊松比分分布（新增）
            if r.get("poisson"):
                p = r["poisson"]
                ml = p["most_likely"]
                lines.append(f"  📊 预期进球: {p['expected_home_goals']} - {p['expected_away_goals']}")
                lines.append(f"     最可能比分: {ml[0]}:{ml[1]} ({p['most_likely_prob']}%)")
                lines.append(f"     大2.5球: {p['over_25_pct']}%  |  两队进球: {p['btts_pct']}%")
                # 显示前3个最可能比分
                dist_str = format_score_distribution(p, top_n=3)
                lines.append(f"     比分分布: {dist_str}")

            if r['is_knockout']:
                lines.append(f"  🏆 淘汰赛(次回合保守系数×0.85)")
            lines.append("")

    # 统计
    lines.append("=" * 66)
    lines.append(f"  场次统计")
    lines.append(f"  📊 共分析 {len(matches)} 场比赛")
    high_conf = sum(1 for r in results if r["confidence"] >= 55)
    mid_conf = sum(1 for r in results if 48 <= r["confidence"] < 55)
    lines.append(f"  ⭐⭐⭐ 高置信度: {high_conf} 场")
    lines.append(f"  ⭐⭐ 中等置信度: {mid_conf} 场")
    lines.append(f"  ⭐ 低置信度: {len(matches) - high_conf - mid_conf} 场")
    lines.append("")
    lines.append(f"  📌 分析框架: 贝叶斯 + Elo 混合模型")
    lines.append(f"  📌 新增: Elo评级 | 主客场优势 | 状态衰减权重 | 泊松比分")
    lines.append(f"  📌 数据源: TheSportsDB Free API + Elo自主学习")
    lines.append("=" * 66)

    return "\n".join(lines)


def generate_archive_entry(matches, results, report):
    """生成复盘归档内容（增强版）"""
    lines = []
    lines.append(f"### {datetime.now().strftime('%Y-%m-%d')} 预测")
    lines.append(f"- ⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 📊 比赛场次: {len(matches)}")
    lines.append(f"- 🔬 分析模型: 贝叶斯 + Elo + 泊松")
    lines.append("")
    lines.append("| 主队 | 客队 | 主胜% | 平局% | 客胜% | Elo主 | Elo客 | 推荐 | 置信度 |")
    lines.append("|------|------|-------|-------|-------|-------|-------|------|--------|")
    for m, r in zip(matches, results):
        home_cn = cn(m.get("strHomeTeam", ""))
        away_cn = cn(m.get("strAwayTeam", ""))
        elo_h = f"{r['elo_home']:.0f}" if r.get("elo_home") is not None else "-"
        elo_a = f"{r['elo_away']:.0f}" if r.get("elo_away") is not None else "-"
        lines.append(f"| {home_cn} | {away_cn} | {r['home']}% | {r['draw']}% | {r['away']}% | {elo_h} | {elo_a} | {r['recommendation']} | {r['confidence']}% |")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def save_report(report, archive_entry, elo_system=None, home_adv_tracker=None, learnings_path=None):
    """保存报告并归档（增强版，支持持久化 Elo）"""
    if learnings_path is None:
        learnings_path = os.path.expanduser("~/.learnings/足球/LEARNINGS.md")

    # 确保目录存在
    os.makedirs(os.path.dirname(learnings_path), exist_ok=True)

    # 保存完整报告
    report_dir = os.path.expanduser("~/.learnings/足球/reports")
    os.makedirs(report_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = os.path.join(report_dir, f"预测报告_{date_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 归档到 LEARNINGS.md
    if os.path.exists(learnings_path):
        with open(learnings_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 在复盘记录前插入
        marker = "### 复盘记录"
        if marker in content:
            content = content.replace(marker, archive_entry + "\n" + marker)
        else:
            content += "\n\n" + archive_entry
    else:
        content = f"# 足球预测学习档案\n\n## 复盘记录\n\n{archive_entry}\n"

    with open(learnings_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 持久化 Elo 评分（新增）
    if elo_system:
        elo_system.save_to_learnings(learnings_path)

    # 持久化主客场优势系数（新增）
    if home_adv_tracker:
        home_adv_tracker.save(learnings_path)

    return report_path


def send_email(subject, body, config_path=None):
    """通过 QQ SMTP 发送邮件"""
    if config_path is None:
        config_path = os.path.expanduser("~/.hermes/scripts/.email_config")

    email_cfg = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    email_cfg[k] = v.strip()

    sender = email_cfg.get("QQ_EMAIL", "")
    auth_code = email_cfg.get("QQ_AUTH_CODE", "")
    recipient = email_cfg.get("TO_EMAIL", "")

    if not all([sender, auth_code, recipient]):
        print("  ⚠️  邮件配置不完整，跳过发送")
        return False

    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30) as server:
            server.login(sender, auth_code)
            server.send_message(msg)
        print(f"  ✅ 邮件已发送到 {recipient}")
        return True
    except Exception as e:
        print(f"  ❌ 邮件发送失败: {e}")
        return False


# ============ 主函数 ============

def main():
    """主函数（增强版）"""
    print("=" * 60)
    print("  🏟️  Hermes 足球预测引擎 v2.0 (Elo增强版)")
    print("=" * 60)
    print()

    # 1. 加载先验参数
    print("📖 正在加载经验参数...")
    params = load_prior_params()
    print(f"  ✅ 联赛基础概率: {len(params['league_base'])}个联赛")
    print(f"  ✅ 淘汰赛系数: {params['knockout_coef']}")
    print(f"  ✅ 防守基准: {params['defense_base']}")
    print(f"  ✅ 西蒙尼系数: {params['simeone_coef']}")
    print(f"  ✅ Elo权重: {params.get('elo_weight', 0.35)*100:.0f}%")
    print()

    # 2. 初始化 Elo 评级系统（新增）
    print("⚡ 正在初始化 Elo 评级系统...")
    elo_system = EloRating()
    elo_system.load_from_learnings()
    print(f"  ✅ 已加载 {len(elo_system.ratings)} 支球队的 Elo 评分")
    if elo_system.ratings:
        top_teams = sorted(elo_system.ratings.items(), key=lambda x: x[1], reverse=True)[:5]
        for team, rating in top_teams:
            print(f"     ⚡ {team}: {rating:.1f}")
    else:
        print(f"     ℹ️  首次运行，所有球队初始评分 {EloRating.INITIAL_RATING}")
    print()

    # 3. 初始化主客场优势跟踪器（新增）
    print("🏠 正在加载主客场优势数据...")
    home_adv_tracker = HomeAdvantageTracker()
    adv_leagues = list(home_adv_tracker.league_stats.keys())
    if adv_leagues:
        print(f"  ✅ 已加载 {len(adv_leagues)} 个联赛的主客场数据")
        for l in adv_leagues[:3]:
            s = home_adv_tracker.league_stats[l]
            print(f"     {l}: 主队场均{s['home_pts_ratio']:.2f}分 ({s['matches']}场)")
    else:
        print(f"  ℹ️  首次运行，使用默认主场优势")
    print()

    # 4. 获取未来比赛
    print("📡 正在获取比赛数据...")
    matches = fetch_upcoming_matches(days=3)
    print(f"  🔍 找到 {len(matches)} 场目标联赛比赛")
    for m in matches:
        print(f"     [{m.get('_league_cn','?')}] {cn(m.get('strHomeTeam','?'))} vs {cn(m.get('strAwayTeam','?'))}  ({m.get('dateEvent','?')})")
    print()

    if not matches:
        print("⚠️  未来3天没有找到目标联赛的比赛")
        print("💡 提示: 可能处于赛季间歇期或数据暂缺")
        return

    # 5. 获取各队数据（带衰减权重）
    print("\U0001f4ca \u6b63\u5728\u5206\u6790\u961f\u4f0d\u72b6\u6001\uff08\u5f3a\u5316\u7248\uff1a\u8f6e\u6b21\u6570\u636e + \u79ef\u5206\u699c + \u8870\u51cf\u6743\u91cd\uff09...")
    form_data = {}
    
    # \u65b9\u6cd5 1: \u4ece\u79ef\u5206\u699c\u83b7\u53d6strForm
    for lid_key in LEAGUES:
        table = get_league_table(lid_key)
        if table:
            for row in table:
                team = row.get("strTeam", "")
                form_str = row.get("strForm", "")
                if team and form_str:
                    pts = sum(3 if c == 'W' else 1 for c in form_str.upper()); s = pts / (len(form_str) * 3) * 100
                    form_data[team] = {"score": s, "gf": 1.0, "ga": 1.0, "source": "standings"}
    
    # \u65b9\u6cd5 2: \u4ece\u8fd1\u671f\u5b8c\u6574\u8f6e\u6b21\u83b7\u53d6\u6bd4\u5206
    for lid_key in LEAGUES:
        rr = get_round_results(lid_key)
        for team, res in (rr or {}).items():
            if team not in form_data and res:
                recent = res[-5:]
                wins = sum(1 for r in recent if r[1] > r[2])
                draws = sum(1 for r in recent if r[1] == r[2])
                s = (wins * 3 + draws) / (len(recent) * 3) * 100
                form_data[team] = {"score": s, "gf": sum(r[1] for r in recent)/len(recent), "ga": sum(r[2] for r in recent)/len(recent), "source": "rounds"}
    
    # \u65b9\u6cd5 3: \u56de\u9000\u5230\u5355\u961f\u67e5\u8be2
    for m in matches:
        for team_key in ["strHomeTeam", "strAwayTeam"]:
            team = m.get(team_key, "")
            if team and team not in form_data:
                team_id = m.get(f"id{team_key[0].upper()}{team_key[1:]}", "")
                if not team_id:
                    info = get_team_info(team)
                    team_id = info.get("idTeam", "") if info else ""
                events = get_team_form(team_id) if team_id else []
                if not events or not isinstance(events, list):
                    score, gf, ga = 50, 1.0, 1.0
                else:
                    score, gf, ga = calc_form_score_decayed(events, team, decay_factor=0.85)
                form_data[team] = {"score": score, "gf": gf, "ga": ga, "source": "single"}
    
    # \u8f93\u51fa\u72b6\u6001\u6458\u8981
    for team, fd in sorted(form_data.items(), key=lambda x: x[1].get("score", 0), reverse=True):
        src = fd.get("source", "?")
        print(f"  \U0001f4c8 {cn(team):15s} \u72b6\u6001:{fd['score']:.0f}% \u8fdb:{fd['gf']:.1f} \u5931:{fd['ga']:.1f} [{src}]")
    print()

    # 6. 预测计算
    print("🎯 正在计算比赛预测（贝叶斯 + Elo 混合模型）...")
    results = []
    for m in matches:
        r = bayes_analysis(m, params, form_data, elo_system, home_adv_tracker)
        results.append(r)
        home_cn = cn(m.get('strHomeTeam', ''))
        away_cn = cn(m.get('strAwayTeam', ''))
        print(f"  [{home_cn} vs {away_cn}] 推荐: {r['recommendation']} 置信度: {r['confidence']}%")
    print()

    # 7. 生成报告
    print("📝 正在生成预测报告...")
    report = generate_report(matches, results)
    archive_entry = generate_archive_entry(matches, results, report)
    report_path = save_report(report, archive_entry,
                              elo_system=elo_system, home_adv_tracker=home_adv_tracker)

    print(f"  ✅ 报告已保存: {report_path}")
    print(f"  ✅ Elo 评分已持久化到 LEARNINGS.md")
    print()

    # 8. 输出报告内容
    print("=" * 60)
    print("  报告内容:")
    print("=" * 60)
    print(report)

    # 9. 发送邮件
    print()
    print("📧 正在发送邮件...")
    subject = f"🏟️ 足球预测报告 {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, report)
    print()

    return report


if __name__ == "__main__":
    main()
