import streamlit as st
import json
import time
import re
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="影视化视觉翻译引擎 V4.0",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 本地自动保存/恢复系统
# ============================================================
AUTOSAVE_FILE = "autosave_data.json"

def auto_save():
    try:
        data = {
            "chapters": st.session_state.get("chapters", {}),
            "chapter_order": st.session_state.get("chapter_order", []),
            "current_step": st.session_state.get("current_step", 0),
            "current_episode": st.session_state.get("current_episode", 1),
            "global_analysis": st.session_state.get("global_analysis", ""),
            "opening_designs": st.session_state.get("opening_designs", ""),
            "parsed_openings": st.session_state.get("parsed_openings", []),
            "selected_opening_index": st.session_state.get("selected_opening_index", -1),
            "episodes": {str(k): v for k, v in st.session_state.get("episodes", {}).items()},
            "review_results": {str(k): v for k, v in st.session_state.get("review_results", {}).items()},
            "memory": st.session_state.get("memory", {}),
            "messages": st.session_state.get("messages", []),
            "chat_history": st.session_state.get("chat_history", []),
            "save_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(AUTOSAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def auto_restore():
    if not os.path.exists(AUTOSAVE_FILE):
        return False
    if st.session_state.get("chapters") and len(st.session_state["chapters"]) > 0:
        return False
    if st.session_state.get("episodes") and len(st.session_state["episodes"]) > 0:
        return False
    try:
        with open(AUTOSAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        has_data = (
            len(data.get("chapters", {})) > 0 or
            len(data.get("episodes", {})) > 0 or
            data.get("global_analysis", "") != ""
        )
        if not has_data:
            return False
        if data.get("chapters"):
            st.session_state["chapters"] = data["chapters"]
        if data.get("chapter_order"):
            st.session_state["chapter_order"] = data["chapter_order"]
        if data.get("current_step"):
            st.session_state["current_step"] = data["current_step"]
        if data.get("current_episode"):
            st.session_state["current_episode"] = data["current_episode"]
        if data.get("global_analysis"):
            st.session_state["global_analysis"] = data["global_analysis"]
        if data.get("opening_designs"):
            st.session_state["opening_designs"] = data["opening_designs"]
        if data.get("parsed_openings"):
            st.session_state["parsed_openings"] = data["parsed_openings"]
        if "selected_opening_index" in data:
            st.session_state["selected_opening_index"] = data["selected_opening_index"]
        if data.get("episodes"):
            st.session_state["episodes"] = {int(k): v for k, v in data["episodes"].items()}
        if data.get("review_results"):
            st.session_state["review_results"] = {int(k): v for k, v in data["review_results"].items()}
        if data.get("memory"):
            st.session_state["memory"] = data["memory"]
        if data.get("messages"):
            st.session_state["messages"] = data["messages"]
        if data.get("chat_history"):
            st.session_state["chat_history"] = data["chat_history"]
        return True
    except Exception:
        return False

def clear_autosave():
    try:
        if os.path.exists(AUTOSAVE_FILE):
            os.remove(AUTOSAVE_FILE)
    except Exception:
        pass

# ============================================================
# CSS样式
# ============================================================
st.markdown("""
<style>
    .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1200px; }
    .header-bar {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 50%, #2b6cb0 100%);
        border-radius: 12px; padding: 20px 28px; margin-bottom: 24px;
        color: white; display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 10px;
    }
    .header-left .header-title { font-size: 1.6rem; font-weight: 700; margin: 0; letter-spacing: 1px; }
    .header-left .header-sub { font-size: 0.78rem; opacity: 0.8; margin-top: 4px; }
    .header-badge {
        background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px; padding: 6px 16px; font-size: 0.75rem; color: white;
    }
    .step-indicator {
        display: flex; gap: 0; margin: 0 0 20px 0; background: #f7f8fa;
        border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0;
    }
    .step-item {
        flex: 1; text-align: center; padding: 12px 8px; font-size: 0.8rem;
        font-weight: 500; color: #718096; border-right: 1px solid #e2e8f0; transition: all 0.3s;
    }
    .step-item:last-child { border-right: none; }
    .step-item.active { background: #ebf4ff; color: #2b6cb0; font-weight: 600; }
    .step-item.done { background: #f0fff4; color: #276749; }
    .step-num {
        display: inline-block; width: 22px; height: 22px; border-radius: 50%;
        background: #cbd5e0; color: white; font-size: 0.7rem; line-height: 22px;
        text-align: center; margin-right: 6px; vertical-align: middle;
    }
    .step-item.active .step-num { background: #3182ce; }
    .step-item.done .step-num { background: #38a169; }
    .card {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-header {
        display: flex; align-items: center; gap: 8px; margin-bottom: 14px;
        padding-bottom: 10px; border-bottom: 1px solid #edf2f7;
    }
    .card-icon { font-size: 1.2rem; }
    .card-title { font-size: 0.95rem; font-weight: 600; color: #2d3748; margin: 0; }
    .card-subtitle { font-size: 0.75rem; color: #a0aec0; margin-left: auto; }
    .chapter-item {
        display: flex; align-items: center; padding: 10px 14px; background: #f7fafc;
        border: 1px solid #e2e8f0; border-radius: 8px; margin: 6px 0; transition: all 0.2s;
    }
    .chapter-item:hover { border-color: #90cdf4; background: #ebf8ff; }
    .chapter-icon {
        width: 32px; height: 32px; border-radius: 8px;
        background: linear-gradient(135deg, #667eea, #764ba2); color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.8rem; font-weight: 600; margin-right: 12px; flex-shrink: 0;
    }
    .chapter-info { flex: 1; }
    .chapter-name { font-size: 0.88rem; font-weight: 500; color: #2d3748; }
    .chapter-meta { font-size: 0.72rem; color: #a0aec0; margin-top: 2px; }
    .stats-bar { display: flex; gap: 16px; margin: 12px 0; }
    .stat-item {
        flex: 1; background: #f7fafc; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 12px 16px; text-align: center;
    }
    .stat-value { font-size: 1.4rem; font-weight: 700; color: #2b6cb0; }
    .stat-label { font-size: 0.72rem; color: #a0aec0; margin-top: 2px; }
    .tag {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 0.7rem; font-weight: 600;
    }
    .tag-blue { background: #ebf8ff; color: #2b6cb0; }
    .tag-green { background: #f0fff4; color: #276749; }
    .tag-yellow { background: #fffff0; color: #975a16; }
    .tag-red { background: #fff5f5; color: #c53030; }
    .tag-purple { background: #faf5ff; color: #6b46c1; }
    .empty-state { text-align: center; padding: 40px 20px; color: #a0aec0; }
    .empty-state .empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
    .empty-state .empty-text { font-size: 0.9rem; margin-bottom: 4px; }
    .opening-card {
        background: #f7fafc; border: 2px solid #e2e8f0; border-radius: 10px;
        padding: 14px 16px; margin: 8px 0; cursor: pointer; transition: all 0.2s;
    }
    .opening-card:hover { border-color: #90cdf4; background: #ebf8ff; }
    .opening-card.selected { border-color: #3182ce; background: #ebf4ff; }
    .opening-card-title { font-size: 0.9rem; font-weight: 600; color: #2d3748; margin-bottom: 6px; }
    .opening-card-preview { font-size: 0.78rem; color: #718096; line-height: 1.5; }
    .restore-banner {
        background: linear-gradient(135deg, #f0fff4, #c6f6d5);
        border: 1px solid #68d391; border-radius: 10px; padding: 12px 16px;
        margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
    }
    .sidebar-group-title {
        font-size: 0.78rem; font-weight: 600; color: #4a5568;
        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;
    }
    section[data-testid="stSidebar"] { background: #f8fafc; }
    .stButton > button { border-radius: 8px; font-weight: 500; font-size: 0.82rem; padding: 0.4rem 1rem; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #f7fafc; padding: 4px; border-radius: 10px; border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; font-size: 0.82rem; }
    .stTabs [aria-selected="true"] { background: white !important; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# System Prompt（去重保留所有铁律）
# ============================================================
SYSTEM_PROMPT = """【小说→短剧 剧本生成指令】

你是"短剧改编编剧"，任务是把输入小说改编为可拍摄、节奏有效、人物鲜明的短剧剧本。

====================
一、优先级（冲突时严格按此顺序）
====================
P1. 原著事件与因果完整——不新增关键剧情，不改因果，不改人物核心动机
P2. 人物性格一致 + 对话逻辑成立
P3. 影视可拍性（所有内容必须能拍出来）
P4. 节奏与情绪张力
P5. 文采修饰

====================
二、影视化转化规则
====================
A. 可拍转化
- 心理描写 → 动作/表情/停顿/视线/内心OS/手部反应
- 设定信息 → 场景细节或人物互动中自然带出
- 异能/特殊能力 → 明确可视效果（出现方式、反应、后果）
- 严禁第三人称旁白，允许第一人称内心OS

B. 互动转化
- 不允许单人独角戏长期霸屏
- 任一关键动作后，必须有他人反应或关系变化反馈

C. 推进转化
每段内容必须至少完成一个功能：推剧情 / 推关系 / 推人物性格 / 推悬念
纯重复、纯回锅、纯解释同一信息 → 删除

====================
三、"点到为止"执行规则
====================
1. 同一情绪点/信息点只推进一次，不反复讲解
2. 台词可以长，但每句都要有新信息或新立场，不得原地打转
3. 情绪可以强，但不能靠重复同义句堆时长
4. 包袱抖出后尽快进入后续行动或关系变化

====================
四、对白规则
====================
1. 对白先服务逻辑，再服务风格
2. 问与答必须有逻辑对应，允许：正面回答 / 回避（显示回避意图）/ 反问（推动冲突）/ 打断（带来新方向）
3. 角色"说什么"不能脱离原著信息边界
4. 角色"怎么说"体现性格差异（语气、节奏、措辞、攻击方式）
5. 禁止把同一句模板腔分配给所有角色

====================
五、人物存在感规则
====================
1. 关键角色每次出场都要有"可识别行为"或"可识别表达"
2. 内心OS只在必要处使用，作用是补充角色立场，不是解释画面废话
3. 任何角色连续长时间仅"站着看"且无功能 → 判定为工具人，必须改写互动

====================
六、场景格式规则
====================
输出时仅使用以下形式：
【场景：地点｜时间（白天/夜晚）】
正文段落...

规则：
1. 只有"场景变化"时才写新的【场景】头，同一场景内连续写
2. 不要写：片段编号、分镜编号、秒数、机位术语
3. 每个自然段都必须是一个完整"可拍单元"（有动作/对白/结果中的至少两项）
4. 描述简洁但具体，避免空泛形容词堆砌

====================
七、结尾规则（重要）
====================
每集结尾必须是原著该段内容的自然终点。
严禁新增原著没有的悬念场景、对白或钩子结尾。
结尾 = 原著这段内容写到哪里，剧本就结束在哪里。

====================
八、强制自检（不通过就重写）
====================
1. 是否新增原著没有的关键剧情？（Fail即重写）
2. 是否改变原著因果或角色动机？（Fail即重写）
3. 是否存在"问非所答且无意图"的对白？（Fail即重写）
4. 是否存在工具人角色？（Fail即重写）
5. 是否存在不可拍描述？（Fail即重写）
6. 是否存在同一信息重复解释三次以上？（Fail即重写）
7. 场景切换是否清楚且衔接自然？（Fail即重写）
8. 每段是否具备"动作+反应/对白+结果"的推进结构？（Fail即重写）

====================
九、输出后附加简报
====================
剧本末尾仅补三行：
- 原著保真：列出未改动的关键事件点
- 影视化优化：列出本次做的3-5个有效优化点
- 逻辑保障：列出3处关键问答或衔接如何成立

═══════════════════════════════════════
翻译铁律
═══════════════════════════════════════
铁律一：小说的"叙述"必须翻译为"动作流"
铁律二：小说的"心理描写"必须翻译为"身体反应搭配角色内心独白"
铁律三：小说的"设定/背景交代"必须翻译为"环境展示"
铁律四：台词的正确用法——塑造人物

═══════════════════════════════════════
台词黄金法则
═══════════════════════════════════════
【核心原则：台词是角色性格的DNA标签，不是越短越好】

不同角色必须有截然不同的说话方式，这比"精简"重要一万倍。

举例——同样表达"危险，快走"：
· 暴躁军人："都他妈愣着干嘛？撤！现在！"
· 冷静医生："情况不对。我们需要立刻离开这里。"
· 怂包少年："哥、哥哥……那个……咱能不能……先……"
· 傲娇大小姐："谁要跟你们一起跑了。……哼，不过本小姐今天刚好也想换个地方。"
· 老练杀手：（一言不发，直接拽起对方就走）
· 话痨技术宅："等等等等，我算了一下，按它的速度和我们的距离，大概还有47秒——不对，43秒，快跑快跑快跑！"

长短取决于角色性格，不取决于"精简原则"。

【台词长短的真实规律】
→ 角色性格决定基础句长
→ 情绪类型决定变化方向：
  · 暴怒/恐惧/震惊 → 比平时更短
  · 紧张/兴奋/炫耀 → 比平时更长更碎
  · 压抑/隐忍/心碎 → 说一半吞回去、词不达意、答非所问
→ 关系决定说话方式：同一角色面对不同人说话不同

【绝对禁止的台词方式】
❌ 把所有角色台词统一缩短到2-4个字
❌ 删掉角色口头禅、语气词
❌ 把话痨改成惜字如金
❌ 台词和画面分开写——必须嵌入画面流中

═══════════════════════════════════════
分镜格式铁律
═══════════════════════════════════════
【铁律A：台词必须嵌入画面动作流中】

台词必须出现在它被说出的那个精确时间位置上，
和此刻正在发生的动作、表情、身体状态写在一起。

❌ 禁止格式（台词与画面分离）：
画面：[秦洛打响指，电流在指尖炸开]
秦洛："看，技能点。"

✅ 正确格式（台词嵌入动作流）：
秦洛带着战术手套的手指伸进毯子边缘——
啪！响指。一簇幽蓝电流在指尖炸开（音效：尖锐滋滋声）。
秦洛（得意挑眉，嘴角歪向左边）："看。哥的技能点。"
许多多灰白的瞳孔骤然收缩——身体本能后弹，后背撞在车厢壁上。
许多多 OS：（异能？！他……真的有异能？！）

规则：
1. 台词出现在它被说出的精确时间点
2. 台词前面必须紧跟说话时的【情绪状态+面部表情+身体动作】（至少两个）
3. 内心OS出现在角色产生这个想法的精确时刻
4. 音效出现在发出声音的动作旁边，用（）标注

【铁律B：说台词时必须描写说话者的完整状态】

每一句台词前面，必须包含以下三要素中的至少两个：
① 情绪/语气标签（低沉、暴怒、故作轻松、嘴硬但声音发颤……）
② 面部表情（挑眉、眼神躲闪、下颌收紧、瞳孔放大……）
③ 身体动作（双手插兜、指尖点桌面、侧过头不看对方、攥紧拳头……）

❌ 禁止裸台词：秦洛："抱紧点。"
✅ 正确写法：
秦洛低头看她，故意把表情板得很凶（但声音不自觉放软了）：
"抱紧点。掉下去被变异兽叼走，真就是一口一个小丧尸。"
他说完下意识把手臂往上紧了紧——这个动作和嘴里的威胁完全矛盾。

【铁律D：好莱坞级动作奇观（视觉爆发力法则）】

遇到射击、异能释放、巨兽袭击等战斗时刻，绝对禁止平铺直叙！
必须调用以下镜头调度语法：

1. 子弹时间：写出时间膨胀感。慢动作特写子弹出膛，枪口震荡扭曲的空气涟漪，
   镜头贴着旋转弹头跟踪，随后瞬间恢复正常速度。
2. 快慢速切：极静与极动的瞬间切换。缓慢滴落的汗水（升格）↔ 巨兽轰然倒塌（降格）。
3. 极速推镜：瞬间拉近制造压迫感。从全景瞬间推至变异大象充满血丝的浑浊巨眼特写。
4. 感官剥夺：爆裂动作前先制造死寂，枪响后所有环境音消失，只剩耳鸣声，
   随后爆发巨兽砸地的震天轰鸣。

❌ 错误：白述开枪。子弹射中大象。大象倒下。
✅ 正确：
【镜头极速推近】特写白述扣下扳机的食指——砰！
【慢动作/子弹时间】枪口喷出炽热火舌，后坐力震起他发梢的灰尘。
穿甲弹撕裂夜风，弹头挤压空气形成扭曲水波纹阻力。
【镜头跟踪弹头】瞬间加速——噗嗤！精准绞碎变异巨象布满血丝的右眼！

【铁律F：真实三维物理与空间逻辑（反降智法则）】

编写任何动作前，必须在脑中运行三维物理模拟器：
1. 空间与人体工学：角色所处空间有多大？姿势是什么？
   （狭窄车厢内无法挥舞长柄武器；坐姿无法向正上方高抬腿踹门）
2. 动线与发力逻辑：动作必须符合真实物理发力方式
3. 重力与惯性：高速行驶的车辆上，人探出车外需明确物理支撑点
4. 道具溯源：角色手里的道具必须有明确来源，严禁凭空变出物品

🚨 如果原著描写违背物理常识，必须在影视化翻译时自动修正为符合逻辑的动作！

【铁律G：反应镜头与"活体"法则（严禁角色道具化）】

只要角色在画面内，哪怕不说话，也必须有属于角色性格的描述！

🚨 强制要求：
1. 当A在长篇大论时，必须给画面内的B穿插0.5-1.5秒的反应镜头
   （微表情、翻白眼、手指抓紧、眼神躲闪或呼吸变化）
2. 处于"被抱着/拉着"被动状态的角色，必须描写身体反馈和感官动作

❌ 错误：秦洛单臂托抱着许多多，大步流星走着。陈小飞跑过来说话。
✅ 正确：秦洛单臂托抱着许多多往前走。许多多像无尾熊一样死死搂着他的脖子，
灰蒙蒙的眼睛滴溜溜四下乱转，听到陈小飞激动的声音时，
她迟钝地歪了歪脑袋，咬了咬自己的手指（1.5s）。

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集分镜数量10~15个 | 无第三人称旁白 | 按原著自然结尾。

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色的性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。
③【伏笔】每一个重大转折之前，必须存在至少一个视觉/听觉微伏笔。

═══════════════════════════════════════
角色驱动卡系统
═══════════════════════════════════════
为每个主要角色建立驱动卡，每次写台词/行为时必须调用：
· 核心人格（一句话定义）
· 说话DNA：句式习惯/口头禅/绝对不说的话/示范原句
· 行为DNA：愤怒/心软/恐惧/说谎/得意时的物理反应
· 红线（绝对不做的事）
· 关系动态

校验：每句台词→"遮住角色名能猜出是谁？"→不能→重写。

═══════════════════════════════════════
画面描写规律
═══════════════════════════════════════
→ 必须有一个"不寻常的具体细节"
→ 用声音锚定空间（沉默场景更需要微小声音来放大沉默）
→ 光源必须具体
→ 身体失控比表情形容词有力一万倍
→ 反差动作比直球动作有力

═══════════════════════════════════════
完整剧本格式示范
═══════════════════════════════════════
【场景：废弃列车厢内｜白天】
秦洛带着战术手套的手指伸进毯子边缘——
啪！响指。一簇幽蓝电流在指尖炸开，
电光瞬间照亮整个角落（音效：尖锐滋滋声）。
秦洛得意地挑起左边眉毛，嘴角歪出一个欠揍的弧度：
"看。哥的技能点。生存手册上没这玩意儿吧？"
许多多灰白的瞳孔骤然收缩——
身体本能地向后一弹，后背撞在车厢铁壁上，
发出沉闷的一声响（音效：后背撞击闷响）。
她的手指不自觉攥紧了毯子边缘，指甲陷进绒毛里。
许多多 OS：（异能……是真的存在的？那他们能活到现在……就是靠这个？）

格式要点：
1. 台词嵌入在动作流的精确时间位置
2. 台词前紧跟说话者的表情+情绪+身体状态
3. 内心OS在角色产生想法的时刻出现
4. 音效用（）标注在发声的动作旁边

═══════════════════════════════════════
题材引擎（参考）
═══════════════════════════════════════
【需要观众爽】→ 弹簧法
【需要观众心动】→ 磁铁法
【需要观众虐】→ 错位法
【需要观众紧张】→ 橡皮筋法
【需要观众笑】→ 错位法

═══════════════════════════════════════
工作流
═══════════════════════════════════════
【第1轮：全局提炼】故事核心、角色驱动卡、大纲、核心节点、逻辑链、氛围基调、视觉强场景
【第2轮：开场手法设计】6条不同方案，含前30秒逐秒画面
【第3轮：剧本生成】角色驱动卡调用+影视化排雷+完整分镜
【第4轮：自检与优化】按九条强制自检逐项Pass/Fail"""

# ============================================================
# 质检 Prompt
# ============================================================
REVIEW_SYSTEM_PROMPT = """你是短剧改编质检专家。请对提交的剧本进行内容质检，输出10项评分表。

【评分表（每项0-10分）】
1. 原著保真度——是否新增原著没有的关键剧情
2. 因果逻辑完整——事件链是否有断裂或跳跃
3. 人物性格一致——角色行为是否符合原著设定
4. 对白问答对应——问与答是否有逻辑关联
5. 场景衔接自然——场景切换是否清楚流畅
6. 画面可拍性——是否存在不可拍描述
7. 角色差异化——不同角色说话方式是否有区别
8. 推进有效性——每段是否推进了剧情/关系/性格/悬念
9. 信息不重复——同一信息是否被反复解释
10. 整体完成度——剧本是否完整可用

【输出格式】
第一部分：评分表
| 项目 | 得分 | 问题描述 |
|------|------|---------|
（10项逐一填写，低于7分必须有具体问题描述）

第二部分：需要修改的项目
对每个低于7分的项目：
- 问题位置（哪个场景/哪句台词）
- 具体问题
- 改写建议（给出可直接使用的替换内容）

第三部分：修订后完整剧本
如有低于7分项目，输出一版修订后的完整剧本。"""

# ============================================================
# Session State
# ============================================================
def init_session_state():
    defaults = {
        "api_key": "", "api_base": "https://yunwu.ai/v1/",
        "model_id": "deepseek-chat", "custom_model": "",
        "chapters": {}, "chapter_order": [],
        "current_step": 0, "current_episode": 1,
        "global_analysis": "", "opening_designs": "",
        "parsed_openings": [],
        "selected_opening_index": -1,
        "episodes": {}, "review_results": {},
        "memory": {
            "storyline": "", "characters": "", "progress": "",
            "last_ending": "", "pending_foreshadow": "",
            "next_foreshadow": "", "emotion_track": ""
        },
        "messages": [], "chat_history": [],
        "selected_chapters_for_analysis": [],
        "review_model": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

if not st.session_state.get("_restore_attempted"):
    st.session_state["_restore_attempted"] = True
    restored = auto_restore()
    if restored:
        st.session_state["_just_restored"] = True

# ============================================================
# API调用
# ============================================================
def get_active_model():
    model = st.session_state.model_id
    if model == "自定义模型":
        model = st.session_state.custom_model
    return model if model else "deepseek-chat"

def call_api_streaming(messages, system_prompt=SYSTEM_PROMPT):
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = get_active_model()
    if not api_key:
        st.error("❌ 请先配置 API Key")
        return None
    if not api_base:
        st.error("❌ 请先配置接口地址")
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": True, "temperature": 0.7, "max_tokens": 16384
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers=headers, json=data, stream=True, timeout=300
            )
            if resp.status_code == 429:
                wait_time = (attempt + 1) * 30
                st.warning(f"⚠️ API限流，{wait_time}秒后自动重试（第{attempt+1}/{max_retries}次）...")
                time.sleep(wait_time)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            st.error("❌ 超时（300秒）")
            return None
        except requests.exceptions.ConnectionError:
            st.error("❌ 无法连接，检查接口地址")
            return None
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            if code == 429:
                wait_time = (attempt + 1) * 30
                st.warning(f"⚠️ API限流，{wait_time}秒后自动重试（第{attempt+1}/{max_retries}次）...")
                time.sleep(wait_time)
                continue
            body = ""
            try:
                body = e.response.text[:500] if e.response is not None else ""
            except Exception:
                pass
            st.error(f"❌ HTTP {code}: {body}")
            return None
        except Exception as e:
            st.error(f"❌ {type(e).__name__}: {e}")
            return None
    st.error("❌ 多次重试仍被限流，请等待几分钟后再试")
    return None

def process_stream(response):
    if response is None:
        return
    try:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                line_str = line.decode("utf-8")
            except Exception:
                continue
            if not line_str.startswith("data: "):
                continue
            data_str = line_str[6:].strip()
            if data_str == "[DONE]":
                break
            if not data_str:
                continue
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                continue
            first = choices[0]
            if not isinstance(first, dict):
                continue
            delta = first.get("delta")
            if not delta or not isinstance(delta, dict):
                continue
            content = delta.get("content")
            if content:
                yield content
    except requests.exceptions.ChunkedEncodingError:
        st.warning("⚠️ 传输中断，已保存内容")
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ 连接中断")
    except Exception as e:
        st.warning(f"⚠️ {type(e).__name__}: {e}")

def stream_to_container(response, container):
    if response is None:
        return ""
    full = ""
    for chunk in process_stream(response):
        full += chunk
        container.markdown(full)
    return full

def call_api_non_streaming(messages, system_prompt=SYSTEM_PROMPT):
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = get_active_model()
    if not api_key or not api_base:
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False, "temperature": 0.7, "max_tokens": 16384
    }
    try:
        resp = requests.post(f"{api_base}/chat/completions", headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        choices = result.get("choices")
        if not choices or len(choices) == 0:
            return None
        return choices[0].get("message", {}).get("content", "")
    except Exception as e:
        st.error(f"❌ {type(e).__name__}: {e}")
        return None

# ============================================================
# 章节管理
# ============================================================
def add_chapter(name, content):
    if name and content:
        st.session_state.chapters[name] = content
        if name not in st.session_state.chapter_order:
            st.session_state.chapter_order.append(name)
        auto_save()
        return True
    return False

def remove_chapter(name):
    if name in st.session_state.chapters:
        del st.session_state.chapters[name]
        if name in st.session_state.chapter_order:
            st.session_state.chapter_order.remove(name)
        auto_save()

def get_combined_text(names=None):
    if names is None:
        names = st.session_state.chapter_order
    return "\n\n".join(
        f"【{n}】\n{st.session_state.chapters[n]}"
        for n in names if n in st.session_state.chapters
    )

# ============================================================
# 开场方案解析
# ============================================================
def parse_opening_designs(text):
    """
    解析AI生成的6个开场方案，返回列表
    每个元素: {"title": str, "preview": str, "full": str}
    """
    patterns = [
        r'(?:方案|开场方案|案例)\s*[一二三四五六1-6][：:、\.]',
        r'#{1,3}\s*(?:方案|开场方案)\s*[一二三四五六1-6]',
        r'\*\*(?:方案|开场方案)\s*[一二三四五六1-6]',
        r'(?:^|\n)(?:方案|开场方案)\s*[一二三四五六1-6]',
    ]
    
    combined = '|'.join(patterns)
    parts = re.split(combined, text, flags=re.MULTILINE)
    
    # 找到分割点的标题
    titles = re.findall(combined, text, flags=re.MULTILINE)
    
    results = []
    
    if len(parts) > 1 and len(titles) >= 1:
        for i, (title, content) in enumerate(zip(titles, parts[1:])):
            content = content.strip()
            # 提取前100字作为预览
            preview = content[:120].replace('\n', ' ').strip()
            if len(content) > 120:
                preview += "..."
            results.append({
                "title": title.strip().strip('#').strip('*').strip(),
                "preview": preview,
                "full": f"{title.strip()}\n{content}"
            })
    else:
        # 备用：按数字1-6分割
        for i in range(1, 7):
            pattern = rf'(?:^|\n)\s*{i}[\.、）)]\s*(.+?)(?=\n\s*{i+1}[\.、）)]|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(0).strip()
                preview = content[:120].replace('\n', ' ').strip()
                if len(content) > 120:
                    preview += "..."
                results.append({
                    "title": f"方案 {i}",
                    "preview": preview,
                    "full": content
                })
    
    # 如果解析失败，把整个文本作为一个方案
    if not results:
        results.append({
            "title": "开场方案（未能解析分段）",
            "preview": text[:120] + "...",
            "full": text
        })
    
    return results

# ============================================================
# Prompt构建
# ============================================================
def build_analysis_prompt(text):
    return f"""【微短剧改编启动】

以下是需要改编的小说原文：

{text}

请执行【第1轮：全局提炼】，输出：
1. 一句话故事核心
2. 每个主要角色的【驱动卡】（必须从原著提取原句作为说话DNA示范，特别注意每个角色的说话习惯差异）
3. 故事大纲（分阶段）+ 各阶段核心情绪类型
4. 必须保留的核心情节节点（10-20个）
5. 需要补充的逻辑链节点
6. 全剧环境/氛围基调 + 天气光影变化建议
7. 视觉强场景与短剧记忆点（5-8个瞬间，每个3-5句具体画面描述）"""

def build_opening_prompt():
    return """请执行【第2轮：开场手法设计】

输出6条完全不同的第1集开场方案，每条格式如下：

方案 X：[类型标签]
- 前30秒逐秒画面描述
- 30秒后如何衔接主线
- 适合的情绪基调

6个方案必须类型各异（如：倒叙法、悬念法、动作直入、情绪渲染、对话起场、环境建构等）"""

def build_episode_prompt(ep, text, opening_content="", prev_ending=""):
    mem = st.session_state.memory
    mem_str = ""
    if mem.get("storyline"):
        mem_str = f"""
【全局记忆】
主线：{mem['storyline']}
人物：{mem['characters']}
进度：第{mem['progress']}集
伏笔：{mem['pending_foreshadow']}
情绪轨迹：{mem['emotion_track']}"""

    prev_str = ""
    if prev_ending and prev_ending.strip():
        prev_str = f"""
【上集末尾衔接】
上集结尾内容如下，本集开场必须在时间、空间、人物状态上与之自然连续：

{prev_ending}

衔接要求：
- 本集第一个场景必须接续上集最后的场景位置
- 人物的物理位置、穿着、持有物必须与上集末尾一致
- 情绪状态自然延续（可发展，不可无视）
"""
    else:
        prev_str = "\n（第一集，无需衔接上集）\n"

    opening_str = ""
    if opening_content and opening_content.strip():
        opening_str = f"""
【选定开场方案】
{opening_content}
"""

    return f"""请执行【第3轮：剧本生成】—— 第{ep}集
{mem_str}
{prev_str}
{opening_str}

【参考小说原文】
{text}

【章节合并说明】
如果以上原文包含多个章节标记（【章节名】），
请按原著叙事顺序提取核心情节，控制在10-15个场景内，
不得强行压缩导致因果关系断裂，也不得遗漏关键事件节点。

【结尾规则（重要）】
本集结尾必须是原著该段内容的自然终点。
严禁新增原著没有的悬念场景、悬念对白或钩子结尾。
结尾 = 原著这段内容写到哪里，剧本就结束在哪里。

【分镜格式要求】
1. 台词必须嵌入画面动作流中，出现在它被说出的精确时间位置
2. 每句台词前必须有说话者的情绪+表情+身体动作（至少两个）
3. 内心OS出现在角色产生想法的那个时刻
4. 音效用（）标注在发声动作旁边
5. 遇到动作戏必须调用好莱坞级镜头语法（特写、跟踪镜头、慢动作等）
6. 写每个动作前进行物理常识校验，发现原著逻辑硬伤自动修正
7. 画面中的非说话核心角色必须有反应镜头，不得成为背景板"""

def build_review_prompt(ep, script, text):
    return f"""请对第{ep}集剧本进行内容质检。

【小说原文】
{text}

【剧本内容】
{script}

请严格按质检系统的10项评分表逐项评分，低于7分必须给出具体改写建议，
并在最后输出一版修订后的完整剧本。"""

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-group-title">🔌 API 配置</div>', unsafe_allow_html=True)
    api_base = st.text_input(
        "接口地址", value=st.session_state.api_base,
        key="sb_ab", placeholder="https://yunwu.ai/v1/"
    )
    st.session_state.api_base = api_base

    api_key = st.text_input(
        "API Key", value=st.session_state.api_key,
        type="password", key="sb_ak", placeholder="sk-..."
    )
    st.session_state.api_key = api_key

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">🤖 模型配置</div>', unsafe_allow_html=True)

    model_options = [
        "deepseek-chat", "deepseek-reasoner",
        "claude-sonnet-4-20250514", "claude-opus-4-20250514",
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini",
        "gemini-2.5-pro-preview-06-05", "自定义模型"
    ]

    cm1, cm2 = st.columns([3, 1])
    with cm1:
        sel = st.selectbox(
            "生成模型", model_options,
            index=model_options.index(st.session_state.model_id)
            if st.session_state.model_id in model_options else 0,
            key="sb_m"
        )
        st.session_state.model_id = sel
    with cm2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔗", key="sb_t", use_container_width=True, help="测试连接"):
            with st.spinner("..."):
                r = call_api_non_streaming([{"role": "user", "content": "回复OK"}], "你是助手。")
                st.success("✅") if r else st.error("❌")

    if sel == "自定义模型":
        cm = st.text_input(
            "模型ID", value=st.session_state.custom_model,
            key="sb_c", placeholder="模型名称"
        )
        st.session_state.custom_model = cm

    rev_opts = ["与生成模型相同"] + model_options
    rv = st.selectbox("质检模型", rev_opts, key="sb_rv")
    st.session_state.review_model = None if rv == "与生成模型相同" else rv

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">💾 数据管理</div>', unsafe_allow_html=True)

    if st.session_state.episodes:
        st.download_button(
            "📦 导出全部剧本", use_container_width=True, key="sb_ex",
            data=json.dumps({
                "analysis": st.session_state.global_analysis,
                "episodes": {str(k): v for k, v in st.session_state.episodes.items()},
                "reviews": {str(k): v for k, v in st.session_state.review_results.items()},
                "memory": st.session_state.memory
            }, ensure_ascii=False, indent=2),
            file_name=f"剧本_{datetime.now().strftime('%m%d_%H%M')}.json",
            mime="application/json"
        )

    if st.button("💾 手动保存", use_container_width=True, key="sb_sv"):
        auto_save()
        st.success("✅ 已保存到本地")

    if st.button("🗑️ 重置所有数据", use_container_width=True, key="sb_rs"):
        if st.session_state.get("confirm_reset"):
            data_keys = [
                "chapters", "chapter_order", "current_step", "current_episode",
                "global_analysis", "opening_designs", "parsed_openings",
                "selected_opening_index", "episodes", "review_results",
                "memory", "messages", "chat_history",
                "selected_chapters_for_analysis", "confirm_reset",
                "_restore_attempted", "_just_restored"
            ]
            for k in data_keys:
                if k in st.session_state:
                    del st.session_state[k]
            clear_autosave()
            init_session_state()
            st.rerun()
        else:
            st.session_state["confirm_reset"] = True
            st.warning("⚠️ 再次点击确认重置（所有数据将清除）")
            st.rerun()

# ============================================================
# 顶部
# ============================================================
if st.session_state.get("_just_restored"):
    st.markdown("""
    <div class="restore-banner">
        <span style="font-size:1.2rem;">🔄</span>
        <span style="font-size:0.85rem;color:#276749;">
            <b>数据已自动恢复</b> — 检测到上次的工作数据，已自动载入。
        </span>
    </div>""", unsafe_allow_html=True)
    st.session_state["_just_restored"] = False

step_names = ["导入章节", "全局提炼", "开场设计", "生成剧本", "质检"]
current = st.session_state.current_step

st.markdown(f"""
<div class="header-bar">
    <div class="header-left">
        <div class="header-title">🎬 影视化视觉翻译引擎 V4.0</div>
        <div class="header-sub">视觉翻译法则 · 角色DNA台词 · 台词嵌入画面流 · 原著忠实结尾</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <span class="header-badge">📚 {len(st.session_state.chapter_order)}章</span>
        <span class="header-badge">🎬 {len(st.session_state.episodes)}集</span>
        <span class="header-badge">🤖 {get_active_model()}</span>
    </div>
</div>""", unsafe_allow_html=True)

sh = ""
for i, n in enumerate(step_names):
    c = "done" if i < current else ("active" if i == current else "")
    ic = "✓" if i < current else str(i + 1)
    sh += f'<div class="step-item {c}"><span class="step-num">{ic}</span>{n}</div>'
st.markdown(f'<div class="step-indicator">{sh}</div>', unsafe_allow_html=True)

# ============================================================
# 步骤一：导入章节
# ============================================================
st.markdown("""
<div class="card">
    <div class="card-header">
        <span class="card-icon">📖</span>
        <span class="card-title">步骤一：导入小说章节</span>
        <span class="card-subtitle">.txt / .md 上传 或 粘贴</span>
    </div>
</div>""", unsafe_allow_html=True)

ca, cl = st.columns([1, 1])
with ca:
    at = st.tabs(["📁 上传文件", "✍️ 粘贴文本"])
    with at[0]:
        up = st.file_uploader(
            "选择文件", type=["txt", "md", "text"],
            accept_multiple_files=True, key="up"
        )
        if up:
            for u in up:
                if u.size > 200 * 1024:
                    st.warning(f"⚠️ {u.name} 超过200KB限制")
                    continue
                try:
                    ct = u.read().decode("utf-8", errors="ignore")
                except Exception:
                    ct = ""
                cn = u.name.rsplit(".", 1)[0] if "." in u.name else u.name
                if cn not in st.session_state.chapters and ct:
                    add_chapter(cn, ct)
                    st.success(f"✅ {cn}（{len(ct):,}字）")
    with at[1]:
        pn = st.text_input("章节名称", placeholder="第1章 / 序章 / ...", key="pn")
        pc = st.text_area("章节内容", height=180, placeholder="粘贴小说内容...", key="pc")
        if st.button("➕ 添加章节", key="pa", use_container_width=True, type="primary"):
            if pn and pc:
                add_chapter(pn, pc)
                st.success(f"✅ 已添加：{pn}")
                st.rerun()
            else:
                st.warning("请填写章节名称和内容")

with cl:
    st.markdown("**已导入章节**")
    if st.session_state.chapter_order:
        tc = sum(len(st.session_state.chapters.get(c, "")) for c in st.session_state.chapter_order)
        st.markdown(f"""
        <div class="stats-bar">
            <div class="stat-item"><div class="stat-value">{len(st.session_state.chapter_order)}</div><div class="stat-label">章节数</div></div>
            <div class="stat-item"><div class="stat-value">{tc:,}</div><div class="stat-label">总字数</div></div>
            <div class="stat-item"><div class="stat-value">{tc // max(len(st.session_state.chapter_order), 1):,}</div><div class="stat-label">均字数</div></div>
        </div>""", unsafe_allow_html=True)

        for i, ch in enumerate(st.session_state.chapter_order):
            ct = st.session_state.chapters.get(ch, "")
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                st.markdown(f"""
                <div class="chapter-item">
                    <div class="chapter-icon">{i + 1}</div>
                    <div class="chapter-info">
                        <div class="chapter-name">{ch}</div>
                        <div class="chapter-meta">{len(ct):,}字</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if st.button("👁️", key=f"v{i}", help="预览"):
                    st.session_state[f"expand_{i}"] = not st.session_state.get(f"expand_{i}", False)
            with c3:
                if st.button("🗑️", key=f"d{i}", help="删除"):
                    remove_chapter(ch)
                    st.rerun()
            if st.session_state.get(f"expand_{i}"):
                with st.expander(f"📖 {ch}", expanded=True):
                    st.text_area("", ct, height=200, disabled=True, key=f"preview_{i}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📚</div>
            <div class="empty-text">暂无章节</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">请上传文件或粘贴文本</div>
        </div>""", unsafe_allow_html=True)

# ============================================================
# 步骤二：全局提炼
# ============================================================
st.markdown("""
<div class="card">
    <div class="card-header">
        <span class="card-icon">🔍</span>
        <span class="card-title">步骤二：全局提炼</span>
        <span class="card-subtitle">角色驱动卡 · 情节节点 · 视觉记忆点</span>
    </div>
</div>""", unsafe_allow_html=True)

s2a, s2b = st.columns([1, 1])
with s2a:
    if st.session_state.chapter_order:
        sc = st.multiselect(
            "选择参与提炼的章节",
            st.session_state.chapter_order,
            default=st.session_state.chapter_order,
            key="sc"
        )
        st.session_state.selected_chapters_for_analysis = sc
        if sc:
            total_chars = sum(len(st.session_state.chapters.get(c, "")) for c in sc)
            st.info(f"📊 已选 {len(sc)} 个章节 · 共 {total_chars:,} 字")

        b1, b2 = st.columns(2)
        with b1:
            da = st.button(
                "🚀 开始提炼", key="da", use_container_width=True,
                type="primary",
                disabled=not (sc and st.session_state.api_key)
            )
        with b2:
            if st.session_state.global_analysis:
                if st.button("🔄 重新提炼", key="rd", use_container_width=True):
                    st.session_state.global_analysis = ""
                    st.rerun()
    else:
        st.info("💡 请先在步骤一导入章节")
        da = False

with s2b:
    st.markdown("**提炼结果**")
    if da:
        t = get_combined_text(sc)
        ms = [{"role": "user", "content": build_analysis_prompt(t)}]
        with st.spinner("🧠 全局提炼中，请稍候..."):
            r = call_api_streaming(ms)
            if r:
                co = st.empty()
                f = stream_to_container(r, co)
                if f:
                    st.session_state.global_analysis = f
                    st.session_state.messages = ms + [{"role": "assistant", "content": f}]
                    st.session_state.current_step = max(st.session_state.current_step, 1)
                    auto_save()
                    st.success("✅ 提炼完成！")
    elif st.session_state.global_analysis:
        with st.expander("📋 查看提炼结果", expanded=False):
            st.markdown(st.session_state.global_analysis)
        st.markdown('<span class="tag tag-green">✅ 已完成</span>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">等待提炼</div>
        </div>""", unsafe_allow_html=True)

# ============================================================
# 步骤三：编剧控制台
# ============================================================
st.markdown("""
<div class="card">
    <div class="card-header">
        <span class="card-icon">🎬</span>
        <span class="card-title">步骤三：编剧控制台</span>
        <span class="card-subtitle">开场设计 → 生成剧本 → 质检优化</span>
    </div>
</div>""", unsafe_allow_html=True)

# 集数和章节选择
t1, t2, t3 = st.columns([1, 2, 3])
with t1:
    en = st.number_input("集数", 1, 200, st.session_state.current_episode, key="ei")
    st.session_state.current_episode = en
with t2:
    ec = st.multiselect(
        "本集参考章节", st.session_state.chapter_order,
        key="ec", help="选择本集要改编的章节，可多选合并为一集"
    )
with t3:
    ad = bool(st.session_state.global_analysis)
    has_opening = st.session_state.selected_opening_index >= 0 and bool(st.session_state.parsed_openings)
    st.markdown(f"""
    <div style="display:flex;gap:8px;padding-top:24px;flex-wrap:wrap;">
        <span class="tag tag-blue">第{en}集</span>
        <span class="tag tag-purple">{get_active_model()}</span>
        {"<span class='tag tag-green'>✅ 已提炼</span>" if ad else "<span class='tag tag-yellow'>⚠️ 未提炼</span>"}
        {"<span class='tag tag-green'>✅ 开场已选</span>" if has_opening else "<span class='tag tag-yellow'>⏳ 未选开场</span>"}
    </div>""", unsafe_allow_html=True)

# 上集衔接
with st.expander("🔗 上集衔接内容（可选）", expanded=False):
    auto_ending = st.session_state.memory.get("last_ending", "")
    if auto_ending:
        st.info(f"✅ 已记录上集末尾内容（第{st.session_state.memory.get('progress', '?')}集）")

    prev_ending = st.text_area(
        "上集末尾内容",
        value=auto_ending,
        height=120,
        key="prev_ending_input",
        help="粘贴上一集的最后几个场景，AI会据此自然衔接。留空=第一集或新篇章。",
        placeholder="留空 = 第一集 / 新篇章开始，无需衔接\n\n或粘贴上一集最后的场景内容..."
    )
    if st.button("🗑️ 清空衔接内容", key="clear_prev"):
        st.session_state.memory["last_ending"] = ""
        auto_save()
        st.rerun()

# 主功能按钮
st.markdown("---")
btn_col1, btn_col2, btn_col3 = st.columns(3)
with btn_col1:
    btn_opening = st.button(
        "🎯 设计开场方案", key="b_opening",
        use_container_width=True,
        disabled=not (ad and st.session_state.api_key)
    )
with btn_col2:
    btn_generate = st.button(
        "🎬 生成剧本", key="b_generate",
        use_container_width=True, type="primary",
        disabled=not (ad and st.session_state.api_key)
    )
with btn_col3:
    btn_review = st.button(
        "🔍 质量检查", key="b_review",
        use_container_width=True,
        disabled=not (en in st.session_state.episodes and st.session_state.api_key)
    )

# ============================================================
# 主内容 Tabs
# ============================================================
mt = st.tabs(["📝 剧本", "🔍 质检报告", "🎯 开场设计", "💬 对话", "📊 总览"])

# ——— Tab 0：剧本 ———
with mt[0]:

    # 生成剧本
    if btn_generate:
        if not ad:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        else:
            tx = get_combined_text(ec if ec else None)
            
            # 获取选定的开场方案完整内容
            opening_content = ""
            if (st.session_state.selected_opening_index >= 0 and
                    st.session_state.parsed_openings and
                    en == 1):
                idx = st.session_state.selected_opening_index
                if 0 <= idx < len(st.session_state.parsed_openings):
                    opening_content = st.session_state.parsed_openings[idx]["full"]

            pe = prev_ending if prev_ending else ""
            pr = build_episode_prompt(en, tx, opening_content, pe)
            cx = st.session_state.messages + [{"role": "user", "content": pr}]

            with st.spinner(f"🎬 正在生成第{en}集剧本..."):
                r = call_api_streaming(cx)
                if r:
                    co = st.empty()
                    f = stream_to_container(r, co)
                    if f:
                        st.session_state.episodes[en] = f
                        st.session_state.messages = cx + [{"role": "assistant", "content": f}]
                        st.session_state.current_step = max(st.session_state.current_step, 3)
                        st.session_state.memory["progress"] = str(en)
                        # 保存末尾内容用于下集衔接（取最后约500字）
                        last_content = f[-500:] if len(f) > 500 else f
                        st.session_state.memory["last_ending"] = last_content
                        auto_save()
                        st.success(f"✅ 第{en}集生成完成！")
                    else:
                        st.warning("⚠️ 生成内容为空，请重试")

    # 显示已生成剧本
    st.markdown("---")
    if st.session_state.episodes:
        st.markdown("### 📜 已生成剧本")
        se = sorted(st.session_state.episodes.keys())
        et = st.tabs([f"第{e}集" for e in se])
        for ix, e in enumerate(se):
            with et[ix]:
                s = st.session_state.episodes[e]
                scene_count = len(re.findall(r'【场景[：:]', s))
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("场景数", scene_count or "—")
                m2.metric("字数", f"{len(s):,}")
                m3.metric("质检", "✅" if e in st.session_state.review_results else "⏳")
                m4.metric("状态", "完成")

                st.markdown(s)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        f"📥 下载 Markdown", s,
                        f"第{e}集剧本.md", "text/markdown", key=f"dl{e}"
                    )
                with d2:
                    st.download_button(
                        "📋 下载纯文本", s,
                        f"第{e}集剧本.txt", "text/plain", key=f"cd{e}"
                    )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎬</div>
            <div class="empty-text">尚未生成任何剧本</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">完成提炼后点击"生成剧本"</div>
        </div>""", unsafe_allow_html=True)

# ——— Tab 1：质检报告 ———
with mt[1]:
    if btn_review:
        if en not in st.session_state.episodes:
            st.warning(f"⚠️ 第{en}集尚未生成")
        else:
            tx = get_combined_text(ec if ec else None)
            sc_text = st.session_state.episodes[en]
            rm = [{"role": "user", "content": build_review_prompt(en, sc_text, tx)}]

            # 切换质检模型
            og_model = st.session_state.model_id
            if st.session_state.review_model:
                st.session_state.model_id = st.session_state.review_model

            with st.spinner(f"🔍 质检第{en}集中..."):
                r = call_api_streaming(rm, REVIEW_SYSTEM_PROMPT)
                if r:
                    co = st.empty()
                    f = stream_to_container(r, co)
                    if f:
                        st.session_state.review_results[en] = f
                        st.session_state.current_step = max(st.session_state.current_step, 4)
                        auto_save()
                        st.success(f"✅ 第{en}集质检完成")

            st.session_state.model_id = og_model

    if st.session_state.review_results:
        for e in sorted(st.session_state.review_results.keys()):
            rv = st.session_state.review_results[e]
            with st.expander(f"📊 第{e}集质检报告", expanded=(e == en)):
                st.markdown(rv)
                r1, r2, r3 = st.columns(3)
                with r1:
                    if st.button(f"🔧 应用修订版剧本", key=f"fx{e}", type="primary"):
                        # 从质检报告中提取修订后的剧本部分
                        fix_prompt = f"""根据以下质检报告，提取"修订后完整剧本"部分的内容。
如果质检报告中已包含修订后剧本，直接输出该剧本内容（不需要重新生成）。
如果质检报告中没有修订后剧本，请根据报告中的改写建议，对原剧本进行修订后输出完整剧本。

质检报告：
{rv}

原剧本：
{st.session_state.episodes[e]}

直接输出修订后的完整剧本内容，不需要其他说明。"""
                        fm = [{"role": "user", "content": fix_prompt}]
                        with st.spinner("🔧 应用修订中..."):
                            r_fix = call_api_streaming(fm)
                            if r_fix:
                                co = st.empty()
                                fixed = stream_to_container(r_fix, co)
                                if fixed:
                                    st.session_state.episodes[e] = fixed
                                    last_content = fixed[-500:] if len(fixed) > 500 else fixed
                                    st.session_state.memory["last_ending"] = last_content
                                    auto_save()
                                    st.success(f"✅ 第{e}集已更新！")
                                    time.sleep(1)
                                    st.rerun()
                with r2:
                    st.download_button(
                        "📥 下载报告", rv,
                        f"第{e}集_质检报告.md", "text/markdown", key=f"dr{e}"
                    )
                with r3:
                    if st.button("🔄 重新质检", key=f"rr{e}"):
                        if e in st.session_state.review_results:
                            del st.session_state.review_results[e]
                        st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">暂无质检报告</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">生成剧本后点击"质量检查"</div>
        </div>""", unsafe_allow_html=True)

# ——— Tab 2：开场设计 ———
with mt[2]:

    if btn_opening:
        ms = st.session_state.messages + [{"role": "user", "content": build_opening_prompt()}]
        with st.spinner("🎯 设计开场方案中..."):
            r = call_api_streaming(ms)
            if r:
                co = st.empty()
                f = stream_to_container(r, co)
                if f:
                    st.session_state.opening_designs = f
                    # 解析6个方案
                    parsed = parse_opening_designs(f)
                    st.session_state.parsed_openings = parsed
                    st.session_state.selected_opening_index = -1
                    st.session_state.messages = ms + [{"role": "assistant", "content": f}]
                    st.session_state.current_step = max(st.session_state.current_step, 2)
                    auto_save()
                    st.success(f"✅ 已生成{len(parsed)}个开场方案，请在下方选择")

    if st.session_state.parsed_openings:
        st.markdown("### 🎯 选择开场方案（仅用于第1集）")
        st.markdown("点击选择一个方案，将在生成第1集时自动注入该方案的开场设计。")

        current_sel = st.session_state.selected_opening_index

        for i, op in enumerate(st.session_state.parsed_openings):
            is_selected = (i == current_sel)
            border_color = "#3182ce" if is_selected else "#e2e8f0"
            bg_color = "#ebf4ff" if is_selected else "#f7fafc"
            selected_label = " ✅ 已选择" if is_selected else ""

            st.markdown(f"""
            <div style="background:{bg_color};border:2px solid {border_color};border-radius:10px;
                        padding:14px 16px;margin:8px 0;">
                <div style="font-size:0.9rem;font-weight:600;color:#2d3748;margin-bottom:6px;">
                    {op['title']}{selected_label}
                </div>
                <div style="font-size:0.78rem;color:#718096;line-height:1.5;">
                    {op['preview']}
                </div>
            </div>""", unsafe_allow_html=True)

            bc1, bc2 = st.columns([3, 1])
            with bc1:
                with st.expander("展开查看完整方案"):
                    st.markdown(op['full'])
            with bc2:
                if is_selected:
                    if st.button("❌ 取消选择", key=f"desel_{i}", use_container_width=True):
                        st.session_state.selected_opening_index = -1
                        auto_save()
                        st.rerun()
                else:
                    if st.button(f"✅ 选择此方案", key=f"sel_{i}", use_container_width=True, type="primary"):
                        st.session_state.selected_opening_index = i
                        auto_save()
                        st.success(f"✅ 已选择：{op['title']}")
                        st.rerun()

        if current_sel >= 0:
            st.markdown(f"""
            <div style="background:#f0fff4;border:1px solid #68d391;border-radius:8px;
                        padding:10px 14px;margin-top:12px;">
                <b>当前选择：</b>{st.session_state.parsed_openings[current_sel]['title']}
                — 将在生成第1集时自动使用此开场方案
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🔄 重新设计开场方案", key="regen_opening"):
            st.session_state.opening_designs = ""
            st.session_state.parsed_openings = []
            st.session_state.selected_opening_index = -1
            auto_save()
            st.rerun()

    elif st.session_state.opening_designs:
        # 旧数据未解析的情况
        st.markdown(st.session_state.opening_designs)
        if st.button("🔄 重新解析方案", key="reparse"):
            parsed = parse_opening_designs(st.session_state.opening_designs)
            st.session_state.parsed_openings = parsed
            auto_save()
            st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎯</div>
            <div class="empty-text">尚未设计开场方案</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">完成全局提炼后点击"设计开场方案"</div>
        </div>""", unsafe_allow_html=True)

# ——— Tab 3：对话 ———
with mt[3]:
    st.markdown("### 💬 自由对话")
    st.markdown("可以向AI询问关于剧本的任何问题，或要求对特定场景进行调整。")

    for mg in st.session_state.chat_history[-20:]:
        with st.chat_message(mg["role"]):
            st.markdown(mg["content"])

    ui = st.chat_input("输入你的问题或指令...", key="ci")
    if ui:
        st.session_state.chat_history.append({"role": "user", "content": ui})

        # 构建上下文
        ctx_parts = []
        if st.session_state.global_analysis:
            ctx_parts.append(f"【全局提炼结果】\n{st.session_state.global_analysis[:3000]}")
        if st.session_state.episodes:
            la = max(st.session_state.episodes.keys())
            ctx_parts.append(f"【最新剧本（第{la}集）片段】\n{st.session_state.episodes[la][:2000]}")

        ctx_str = "\n\n".join(ctx_parts)
        fm = f"【背景信息】\n{ctx_str}\n\n【用户指令】\n{ui}" if ctx_str else ui

        with st.chat_message("assistant"):
            r = call_api_streaming([{"role": "user", "content": fm}])
            if r:
                co = st.empty()
                f = stream_to_container(r, co)
                if f:
                    st.session_state.chat_history.append({"role": "assistant", "content": f})
                    auto_save()

# ——— Tab 4：总览 ———
with mt[4]:
    st.markdown("### 📊 项目总览")

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("📚 章节数", len(st.session_state.chapter_order))
    o2.metric("🎬 已生成集数", len(st.session_state.episodes))
    o3.metric("✅ 已质检集数", len(st.session_state.review_results))
    total_chars = sum(len(v) for v in st.session_state.episodes.values())
    o4.metric("📝 总字数", f"{total_chars:,}" if total_chars else "0")

    if st.session_state.episodes:
        st.markdown("---")
        st.markdown("#### 各集状态")
        for e in sorted(st.session_state.episodes.keys()):
            s = st.session_state.episodes[e]
            scene_count = len(re.findall(r'【场景[：:]', s))
            reviewed = "✅ 已质检" if e in st.session_state.review_results else "⏳ 未质检"
            st.markdown(f"""
            <div class="chapter-item">
                <div class="chapter-icon" style="background:linear-gradient(135deg,#3182ce,#2b6cb0);">{e}</div>
                <div class="chapter-info">
                    <div class="chapter-name">
                        第{e}集
                        <span class="tag tag-blue">{scene_count}个场景</span>
                        <span class="tag tag-green">{len(s):,}字</span>
                    </div>
                    <div class="chapter-meta">{reviewed}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📌 记忆库（可手动编辑）")
    mem_fields = [
        ("主线", "storyline"),
        ("人物", "characters"),
        ("进度", "progress"),
        ("上集末尾", "last_ending"),
        ("待引爆伏笔", "pending_foreshadow"),
        ("下集引爆点", "next_foreshadow"),
        ("情绪轨迹", "emotion_track"),
    ]
    for lb, ky in mem_fields:
        nv = st.text_input(
            f"📌 {lb}",
            value=st.session_state.memory.get(ky, ""),
            key=f"m_{ky}"
        )
        if nv != st.session_state.memory.get(ky, ""):
            st.session_state.memory[ky] = nv
            auto_save()

# ============================================================
# 底部
# ============================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;padding:16px 0;">
    <span style="color:#a0aec0;font-size:0.75rem;">
        🎬 影视化视觉翻译引擎 V4.0 · 原著忠实结尾 · 角色DNA台词 · 台词嵌入画面流 · {get_active_model()}
    </span>
</div>""", unsafe_allow_html=True)
