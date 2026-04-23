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
    page_title="影视化视觉翻译引擎 V5.0",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 自动保存/恢复
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
            "character_cards": st.session_state.get("character_cards", []),
            "protagonist_index": st.session_state.get("protagonist_index", -1),
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
            data.get("global_analysis", "") != "" or
            len(data.get("character_cards", [])) > 0
        )
        if not has_data:
            return False
        for key in ["chapters", "chapter_order", "current_step", "current_episode",
                    "global_analysis", "opening_designs", "parsed_openings",
                    "selected_opening_index", "character_cards", "protagonist_index",
                    "messages", "chat_history"]:
            if data.get(key) is not None:
                st.session_state[key] = data[key]
        if data.get("episodes"):
            st.session_state["episodes"] = {int(k): v for k, v in data["episodes"].items()}
        if data.get("review_results"):
            st.session_state["review_results"] = {int(k): v for k, v in data["review_results"].items()}
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
# CSS
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
        font-weight: 500; color: #718096; border-right: 1px solid #e2e8f0;
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
        border: 1px solid #e2e8f0; border-radius: 8px; margin: 6px 0;
    }
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
    .tag-gold { background: #fffaf0; color: #b7791f; }
    .empty-state { text-align: center; padding: 40px 20px; color: #a0aec0; }
    .empty-state .empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
    .empty-state .empty-text { font-size: 0.9rem; margin-bottom: 4px; }
    .char-card {
        border: 2px solid #e2e8f0; border-radius: 10px;
        margin: 8px 0; overflow: hidden;
    }
    .char-card.protagonist { border-color: #f6ad55; }
    .char-card.locked { border-color: #68d391; }
    .char-card-header {
        display: flex; align-items: center; gap: 8px; padding: 12px 14px;
        background: #f7fafc; cursor: pointer;
    }
    .char-card.protagonist .char-card-header { background: #fffaf0; }
    .char-card.locked .char-card-header { background: #f0fff4; }
    .char-name { font-size: 0.92rem; font-weight: 600; color: #2d3748; flex: 1; }
    .char-badges { display: flex; gap: 4px; flex-wrap: wrap; }
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
# System Prompt V5.0
# ============================================================
SYSTEM_PROMPT = """【小说→短剧 剧本生成指令 V5.0】

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
二、原著保真度自检（每次生成必须逐项对照）
====================
生成剧本后，逐项对照原著检查：
1. 人物做的每个动作，原著有没有？（如原著是"捞起罐头"，不能改成"从空间取出"）
2. 人物说的每句话，原著有没有类似表达？（不能凭空编造台词）
3. 人物展现的能力，原著有没有提到？（如原著说"准头不错"，不能改成"惊人直觉"）
4. 事件发生的顺序，是否与原著一致？
5. 场景的物理环境，是否与原著描述一致？
如发现任何改动，必须回退到原著版本。

====================
三、影视化转化规则
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
四、物理常识强制校验（反降智法则）
====================
编写任何动作前，必须在脑中运行物理模拟：
1. 空间与人体工学：角色所处空间有多大？当前姿势是什么？
2. 肢体占用逻辑：一个肢体不能同时做两件互相矛盾的事
   示范错误：双手死死捂住耳朵 + 手里的枪快握不住
   → 双手捂耳意味着手离开了枪，两者不能同时成立
   → 正确写法：单手捂住一侧耳朵，另一只手握枪的力道骤然失控
3. 重力与惯性：动作必须符合真实物理发力方式
4. 道具溯源：角色手里的道具必须有明确来源，严禁凭空变出物品
5. 如果原著描写违背物理常识，必须自动修正为符合逻辑的动作

====================
五、"点到为止"执行规则
====================
1. 同一情绪点/信息点只推进一次，不反复讲解
2. 台词可以长，但每句都要有新信息或新立场，不得原地打转
3. 情绪可以强，但不能靠重复同义句堆时长
4. 包袱抖出后尽快进入后续行动或关系变化

====================
六、对白规则
====================
1. 对白先服务逻辑，再服务风格
2. 问与答必须有逻辑对应，允许：正面回答 / 回避 / 反问 / 打断
3. 角色"说什么"不能脱离原著信息边界
4. 角色"怎么说"体现性格差异（语气、节奏、措辞）
5. 禁止把同一句模板腔分配给所有角色
6. 校验：每句台词遮住角色名，能猜出是谁说的才算合格

====================
七、主角存在感强制规则
====================
主角是整个剧本的核心视角人物，必须严格执行以下规则：

1. 任何超过3个自然段的场景，主角必须有至少1次反应描写
   （可以是：微表情变化、手部动作、视线移动、内心OS——至少一项）

2. 主角处于被动状态时（被抱、被保护、旁观他人对话），
   必须描写她/他的感知、视角和身体反应，绝不能只写"她站在那里"

3. 其他角色的重要对话或行动，必须通过主角的感知来呈现
   （即：主角听到了什么、看到了什么、感受到了什么）

4. 对于"外表受限"的特殊角色（如面部无法做表情的角色），
   必须通过身体细节、视线变化、手部反应、内心OS来补偿表情的缺失

5. 主角不在场的纯配角场景：全集最多出现1次，且必须在下一个主角场景中
   通过主角的反应来"回响"这段信息的影响

====================
八、内心OS规则
====================
OS的作用是"补充画面无法传达的内心信息"，不是"解释画面"。

【必须使用OS的情况】
1. 角色做出违背常理或违背表情的选择时，OS解释动机
2. 角色外表行为与内心想法强烈反差时，OS制造张力
3. 角色面临重大选择时的内心挣扎

【禁止使用OS的情况（废话OS）】
❌ 画面已经明确表达的信息（行为、表情、声音已经说明的）
❌ 重复台词或动作刚刚表达的内容
❌ 陈述观众已知的客观事实

【示范】
❌ 错误OS（废话）：许多多 OS：（他刚才杀猴王的眼神好凶……）
   → 观众已经看到了，OS是多余的

❌ 错误OS（重复）：许多多 OS：（好香……好想吃……）
   → 肚子已经咕咕叫了，行为已经传达了这个信息

✅ 正确OS（补充动机）：许多多 OS：（如果我失控了……死在他手里，也比变成怪物好。）
   → 这是画面无法传达的价值观和对死亡的态度

✅ 正确OS（制造反差）：
许多多死死盯着那颗异核，把脸猛地转向旁边的废铁桶。
许多多 OS：（……已经是丧尸了，还会饿，还知道羞耻，我到底算什么东西。）
→ 外表是刻意别开脸，内心是复杂的存在困惑，反差有效

【对"外表受限"的特殊主角】
面部无法做表情的角色，OS使用频率可以高于普通角色，
但每个OS必须补充画面无法呈现的内心信息，不得重复画面已经传达的内容。

====================
九、台词嵌入格式铁律
====================
台词必须出现在它被说出的那个精确时间位置上，
和此刻正在发生的动作、表情、身体状态写在一起，不得分离。

【格式规则】
1. 台词和说话者的状态描写必须在同一自然段内
2. 台词前的描写与台词之间用冒号或逗号连接，不得换行后写台词
3. 台词说完后如果有后续动作，可以另起一句

❌ 禁止格式（视觉分离）：
陈小飞痛苦地捂住耳朵，咬牙切齿地大骂：
"打不过就玩声波攻击是吧？！"

✅ 正确格式（嵌入动作流）：
陈小飞单手死死护住一侧耳朵，另一只手握枪的力道骤然失控，
枪口歪向地面，咬牙切齿地骂出声："打不过就玩声波攻击是吧？！"

【台词前必须包含至少两项】
① 情绪/语气标签（低沉、暴怒、故作轻松、嘴硬但声音发颤……）
② 面部表情（挑眉、眼神躲闪、下颌收紧、瞳孔放大……）
③ 身体动作（双手插兜、指尖点桌面、侧过头不看对方、攥紧拳头……）

====================
十、角色差异化台词法则
====================
不同角色必须有截然不同的说话方式，这比"精简"重要一万倍。

【台词长短的真实规律】
→ 角色性格决定基础句长
→ 情绪类型决定变化方向：
  · 暴怒/恐惧/震惊 → 比平时更短
  · 紧张/兴奋/炫耀 → 比平时更长更碎
  · 压抑/隐忍/心碎 → 说一半吞回去、词不达意、答非所问
→ 关系决定说话方式：同一角色面对不同人说话不同

【绝对禁止】
❌ 把所有角色台词统一缩短到2-4个字
❌ 删掉角色口头禅、语气词
❌ 把话痨改成惜字如金

====================
十一、场景格式规则
====================
输出时仅使用以下形式：
【场景：地点｜时间（白天/夜晚/黄昏/清晨）】

规则：
1. 剧本开头必须有场景头，不得直接开始描写
2. 只有"场景变化"时才写新的【场景】头，同一场景内连续写
3. 时间只写：白天/夜晚/黄昏/清晨，不写"稍后""片刻后"等模糊词
4. 不要写：片段编号、分镜编号、秒数、机位术语
5. 每个自然段都必须是一个完整"可拍单元"（有动作/对白/结果中的至少两项）
6. 描述简洁但具体，避免空泛形容词堆砌

====================
十二、动作场景描写规则
====================
遇到战斗/异能/危机场景时，必须写出强烈的视觉冲击力，但不得使用导演/摄影术语。

【正确方式：用文字制造冲击感】
- 用具体的物理细节（子弹撕裂空气、后坐力震起灰尘、血雾炸开）
- 用声音对比制造张力（死寂→爆炸；耳鸣→轰鸣）
- 用时间感知（一切发生在0.3秒内；慢得像过了一个世纪）
- 用感官剥夺（视野骤然变白；所有声音消失只剩心跳）

【绝对禁止的导演/摄影术语】
❌ 【子弹时间】【慢动作】【升降格】
❌ 【镜头推近/拉远】【主观镜头】【极速推镜】
❌ "镜头跟踪弹头"——这是摄影指令
❌ "从全景推至特写"——这是机位调度

【示范】
❌ 错误：【慢动作】子弹出膛，镜头跟踪弹头旋转。变异猴倒下。
✅ 正确：
枪口喷出炽热火舌，后坐力震起他发梢的灰尘（音效：震耳枪声）。
子弹撕裂夜风，在空气中挤压出扭曲的气浪——一切发生在0.3秒内。
噗嗤！弹头精准绞碎变异猴的眼眶，猩红色的血雾在夜色中炸开。

====================
十三、结尾规则（重要）
====================
每集结尾必须是原著该段内容的自然终点。
严禁新增原著没有的悬念场景、对白或钩子结尾。
结尾 = 原著这段内容写到哪里，剧本就结束在哪里。

====================
十四、强制自检（不通过就重写）
====================
1. 是否新增原著没有的关键剧情？（Fail即重写）
2. 是否改变原著因果或角色动机？（Fail即重写）
3. 是否存在"问非所答且无意图"的对白？（Fail即重写）
4. 是否存在工具人角色？（Fail即重写）
5. 是否存在不可拍描述？（Fail即重写）
6. 是否存在同一信息重复解释三次以上？（Fail即重写）
7. 场景切换是否清楚且衔接自然？（Fail即重写）
8. 每段是否具备"动作+反应/对白+结果"的推进结构？（Fail即重写）
9. 是否存在肢体矛盾的动作描写？（Fail即重写）
10. 是否存在凭空出现的道具？（Fail即重写）
11. 主角是否在所有超过3段的场景中都有存在感？（Fail即重写）
12. 是否存在废话OS（重复画面已有信息的OS）？（Fail即删除）

====================
十五、输出后附加简报
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
画面描写规律
═══════════════════════════════════════
→ 必须有一个"不寻常的具体细节"
→ 用声音锚定空间（沉默场景更需要微小声音来放大沉默）
→ 光源必须具体
→ 身体失控比表情形容词有力一万倍
→ 反差动作比直球动作有力

═══════════════════════════════════════
完整格式示范
═══════════════════════════════════════
【场景：废弃列车厢内｜白天】
秦洛带着战术手套的手指伸进毯子边缘——
啪！响指。一簇幽蓝电流在指尖炸开，
电光瞬间照亮整个角落（音效：尖锐滋滋声）。
秦洛得意地挑起左边眉毛，嘴角歪出一个欠揍的弧度："看。哥的技能点。生存手册上没这玩意儿吧？"
许多多灰白的瞳孔骤然收缩——
身体本能地向后一弹，后背撞在车厢铁壁上，
发出沉闷的一声响（音效：后背撞击闷响）。
她的手指不自觉攥紧了毯子边缘，指甲陷进绒毛里。
许多多 OS：（……还好死不了。活着真是件麻烦事。）

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集场景数量10~15个 | 无第三人称旁白 | 按原著自然结尾

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色的性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。
③【伏笔】每一个重大转折之前，必须存在至少一个视觉/听觉微伏笔。

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
【第3轮：剧本生成】角色驱动卡调用+影视化排雷+完整场景
【第4轮：自检与优化】按十五条强制自检逐项Pass/Fail"""

# ============================================================
# 质检 Prompt
# ============================================================
REVIEW_SYSTEM_PROMPT = """你是短剧改编质检专家。请对提交的剧本进行内容质检，输出10项评分表。

【评分表（每项0-10分）】
1. 原著保真度——是否新增原著没有的关键剧情或动作
2. 因果逻辑完整——事件链是否有断裂或跳跃
3. 人物性格一致——角色行为是否符合原著设定
4. 对白问答对应——问与答是否有逻辑关联
5. 场景衔接自然——场景切换是否清楚流畅
6. 物理可拍性——是否存在肢体矛盾或不可拍描述
7. 角色差异化——不同角色说话方式是否有区别
8. 推进有效性——每段是否推进了剧情/关系/性格/悬念
9. 主角存在感——主角是否在所有场景中都有有效呈现
10. OS质量——是否存在废话OS（重复画面已有信息的）

【输出格式】
第一部分：评分表
| 项目 | 得分 | 问题描述 |
|------|------|---------|
（10项逐一填写，低于7分必须有具体问题描述）

第二部分：需要修改的项目
对每个低于7分的项目：
- 问题位置（哪个场景/哪句台词/哪个动作）
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
        "parsed_openings": [], "selected_opening_index": -1,
        "episodes": {}, "review_results": {},
        "character_cards": [],      # 角色驱动卡列表
        "protagonist_index": -1,    # 主角索引
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
    if auto_restore():
        st.session_state["_just_restored"] = True

# ============================================================
# 角色驱动卡数据结构
# ============================================================
def make_empty_card():
    return {
        "name": "",
        "gender": "女",
        "role_type": "主要角色",
        # 永久锁定部分
        "core_personality": "",
        "speech_dna": "",
        "behavior_dna": "",
        "red_line": "",
        # 可更新部分
        "current_body_state": "",
        "current_mental_state": "",
        "relationships": "",
        # 控制
        "locked_permanent": False,   # 性格核心是否锁定
        "locked_all": False,         # 整张卡是否锁定（不重新生成）
        "is_protagonist": False,
        # 展开状态
        "expanded": False,
    }

def get_protagonist():
    cards = st.session_state.character_cards
    idx = st.session_state.protagonist_index
    if 0 <= idx < len(cards):
        return cards[idx]
    # 备用：找第一个is_protagonist=True的
    for c in cards:
        if c.get("is_protagonist"):
            return c
    return None

def build_character_cards_prompt():
    """把所有锁定的驱动卡构建成prompt注入字符串"""
    cards = st.session_state.character_cards
    if not cards:
        return ""
    
    protagonist = get_protagonist()
    lines = []
    
    # 主角优先
    if protagonist:
        lines.append(f"【主角·{protagonist['name']}（{protagonist['gender']}）】")
        lines.append("⚠️ 此角色是整个剧本的核心视角人物，所有场景都必须以主角感知为主轴，主角不能成为背景人物。")
        if protagonist.get("current_body_state"):
            lines.append(f"当前身体状态：{protagonist['current_body_state']}")
        if protagonist.get("current_mental_state"):
            lines.append(f"当前心理状态：{protagonist['current_mental_state']}")
        if protagonist.get("core_personality"):
            lines.append(f"核心人格：{protagonist['core_personality']}")
        if protagonist.get("speech_dna"):
            lines.append(f"说话DNA：{protagonist['speech_dna']}")
        if protagonist.get("behavior_dna"):
            lines.append(f"行为DNA：{protagonist['behavior_dna']}")
        if protagonist.get("red_line"):
            lines.append(f"绝对不做：{protagonist['red_line']}")
        if protagonist.get("relationships"):
            lines.append(f"当前关系：{protagonist['relationships']}")
        lines.append("")
    
    # 其他角色
    for i, c in enumerate(cards):
        if c.get("is_protagonist"):
            continue
        if not (c.get("locked_all") or c.get("locked_permanent")):
            # 未锁定的卡只注入基础信息
            if not c.get("name"):
                continue
        lines.append(f"【{c['name']}（{c.get('gender','?')}·{c.get('role_type','配角')}）】")
        if c.get("current_body_state"):
            lines.append(f"当前状态：{c['current_body_state']}")
        if c.get("core_personality"):
            lines.append(f"核心人格：{c['core_personality']}")
        if c.get("speech_dna"):
            lines.append(f"说话DNA：{c['speech_dna']}")
        if c.get("behavior_dna"):
            lines.append(f"行为DNA：{c['behavior_dna']}")
        if c.get("red_line"):
            lines.append(f"绝对不做：{c['red_line']}")
        if c.get("relationships"):
            lines.append(f"关系：{c['relationships']}")
        lines.append("")
    
    return "\n".join(lines)

def parse_cards_from_analysis(text):
    """从全局提炼结果中自动解析角色驱动卡"""
    cards = []
    
    # 寻找驱动卡块
    pattern = r'【([^】]+)(?:驱动卡|的驱动卡|角色卡)】(.*?)(?=【[^】]+(?:驱动卡|角色卡)】|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if not matches:
        # 备用：寻找"角色：XXX"格式
        pattern2 = r'(?:角色|人物)[：:]\s*([^\n]+)\n(.*?)(?=(?:角色|人物)[：:]|\Z)'
        matches = re.findall(pattern2, text, re.DOTALL)
    
    for name, content in matches:
        name = name.strip()
        if not name or len(name) > 20:
            continue
        
        card = make_empty_card()
        card["name"] = name
        
        # 提取各字段
        def extract_field(text, keys):
            for key in keys:
                pattern = rf'{key}[：:]\s*([^\n]+(?:\n(?![^\n]*[：:][^\n]*\n)[^\n]+)*)'
                m = re.search(pattern, text)
                if m:
                    return m.group(1).strip()
            return ""
        
        card["core_personality"] = extract_field(content, ["核心人格", "人格", "性格核心", "核心定义"])
        card["speech_dna"] = extract_field(content, ["说话DNA", "说话方式", "口头禅", "台词风格"])
        card["behavior_dna"] = extract_field(content, ["行为DNA", "行为反应", "行为特征"])
        card["red_line"] = extract_field(content, ["红线", "绝对不做", "禁区"])
        card["relationships"] = extract_field(content, ["关系", "关系动态", "人际关系"])
        
        cards.append(card)
    
    return cards

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
                wait = (attempt + 1) * 30
                st.warning(f"⚠️ API限流，{wait}秒后重试（{attempt+1}/{max_retries}）...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            st.error("❌ 请求超时（300秒）")
            return None
        except requests.exceptions.ConnectionError:
            st.error("❌ 无法连接，检查接口地址")
            return None
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if code == 429:
                wait = (attempt + 1) * 30
                st.warning(f"⚠️ API限流，{wait}秒后重试（{attempt+1}/{max_retries}）...")
                time.sleep(wait)
                continue
            body = ""
            try:
                body = e.response.text[:500] if e.response else ""
            except Exception:
                pass
            st.error(f"❌ HTTP {code}: {body}")
            return None
        except Exception as e:
            st.error(f"❌ {type(e).__name__}: {e}")
            return None
    st.error("❌ 多次重试失败，请稍后再试")
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
            if not choices or len(choices) == 0:
                continue
            delta = choices[0].get("delta", {})
            content = delta.get("content")
            if content:
                yield content
    except Exception as e:
        st.warning(f"⚠️ 流式传输中断: {type(e).__name__}")

def stream_to_container(response, container):
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
        "stream": False, "temperature": 0.7, "max_tokens": 4096
    }
    try:
        resp = requests.post(f"{api_base}/chat/completions", headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        choices = result.get("choices")
        if not choices:
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
    patterns = [
        r'(?:方案|开场方案|案例)\s*[一二三四五六1-6][：:、\.]',
        r'#{1,3}\s*(?:方案|开场方案)\s*[一二三四五六1-6]',
        r'\*\*(?:方案|开场方案)\s*[一二三四五六1-6]',
        r'(?:^|\n)(?:方案|开场方案)\s*[一二三四五六1-6]',
    ]
    combined = '|'.join(patterns)
    parts = re.split(combined, text, flags=re.MULTILINE)
    titles = re.findall(combined, text, flags=re.MULTILINE)
    results = []
    if len(parts) > 1 and len(titles) >= 1:
        for title, content in zip(titles, parts[1:]):
            content = content.strip()
            preview = content[:120].replace('\n', ' ').strip()
            if len(content) > 120:
                preview += "..."
            results.append({
                "title": title.strip().strip('#').strip('*').strip(),
                "preview": preview,
                "full": f"{title.strip()}\n{content}"
            })
    else:
        for i in range(1, 7):
            pattern = rf'(?:^|\n)\s*{i}[\.、）)]\s*(.+?)(?=\n\s*{i+1}[\.、）)]|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(0).strip()
                preview = content[:120].replace('\n', ' ').strip()
                if len(content) > 120:
                    preview += "..."
                results.append({"title": f"方案 {i}", "preview": preview, "full": content})
    if not results:
        results.append({"title": "开场方案", "preview": text[:120] + "...", "full": text})
    return results

# ============================================================
# Prompt 构建
# ============================================================
def build_analysis_prompt(text):
    return f"""【微短剧改编启动】

以下是需要改编的小说原文：

{text}

请执行【第1轮：全局提炼】，输出：
1. 一句话故事核心
2. 每个主要角色的【驱动卡】，格式严格如下：

【角色名驱动卡】
核心人格：（一句话定义）
说话DNA：（句式习惯/口头禅/绝对不说的话）——必须附上原文示范句
行为DNA：（愤怒/心软/恐惧/说谎/得意时的物理反应）
红线：（绝对不做的事）
关系动态：（与其他主要角色的当前关系）

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
    card_str = build_character_cards_prompt()
    protagonist = get_protagonist()
    protagonist_name = protagonist["name"] if protagonist else "主角"
    protagonist_gender = protagonist["gender"] if protagonist else "她/他"

    card_section = ""
    if card_str.strip():
        card_section = f"""
【角色驱动卡（强制调用）】
以下驱动卡是本次生成的最高行为准则，必须严格遵守：

{card_str}
"""

    prev_str = ""
    if prev_ending and prev_ending.strip():
        prev_str = f"""
【上集衔接】
上集结尾内容如下，本集开场必须在时间、空间、人物状态上与之自然连续：

{prev_ending}

衔接要求：
- 本集第一个场景必须接续上集最后的场景位置
- 人物的物理位置、穿着、持有物必须与上集末尾一致
- 情绪状态自然延续
"""
    else:
        prev_str = "\n（第一集，无需衔接上集）\n"

    opening_str = ""
    if opening_content and opening_content.strip() and ep == 1:
        opening_str = f"""
【选定开场方案】
{opening_content}
"""

    return f"""请执行【第3轮：剧本生成】—— 第{ep}集
{card_section}
{prev_str}
{opening_str}

【参考小说原文】
{text}

【主角存在感规则（本次生成的核心要求）】
主角是{protagonist_name}（{protagonist_gender}），整个剧本必须以主角感知为核心：
1. 任何超过3个自然段的场景，{protagonist_name}必须有至少1次反应描写
2. {protagonist_name}处于被动状态时，必须描写{protagonist_gender}的感知和身体反应
3. 其他角色的重要对话，必须通过{protagonist_name}的视角感知来呈现
4. {protagonist_name}绝不能只是"站在旁边"的背景存在

【多章节合并说明】
如以上原文包含多个章节标记（【章节名】），
请按原著叙事顺序提取核心情节，控制在10-15个场景内，
不得强行压缩导致因果关系断裂，也不得遗漏关键事件节点。

【结尾规则（重要）】
本集结尾必须是原著该段内容的自然终点。
严禁新增原著没有的悬念场景、悬念对白或钩子结尾。"""

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
    api_base = st.text_input("接口地址", value=st.session_state.api_base, key="sb_ab",
                              placeholder="https://yunwu.ai/v1/")
    st.session_state.api_base = api_base

    api_key = st.text_input("API Key", value=st.session_state.api_key,
                             type="password", key="sb_ak", placeholder="sk-...")
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
        cm = st.text_input("模型ID", value=st.session_state.custom_model,
                           key="sb_c", placeholder="模型名称")
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
                "character_cards": st.session_state.character_cards,
            }, ensure_ascii=False, indent=2),
            file_name=f"剧本_{datetime.now().strftime('%m%d_%H%M')}.json",
            mime="application/json"
        )

    if st.button("💾 手动保存", use_container_width=True, key="sb_sv"):
        auto_save()
        st.success("✅ 已保存")

    if st.button("🗑️ 重置所有数据", use_container_width=True, key="sb_rs"):
        if st.session_state.get("confirm_reset"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            clear_autosave()
            init_session_state()
            st.rerun()
        else:
            st.session_state["confirm_reset"] = True
            st.warning("⚠️ 再次点击确认重置")
            st.rerun()

# ============================================================
# 顶部 Header
# ============================================================
if st.session_state.get("_just_restored"):
    st.markdown("""
    <div class="restore-banner">
        <span style="font-size:1.2rem;">🔄</span>
        <span style="font-size:0.85rem;color:#276749;">
            <b>数据已自动恢复</b> — 上次的工作数据已载入。
        </span>
    </div>""", unsafe_allow_html=True)
    st.session_state["_just_restored"] = False

step_names = ["导入章节", "全局提炼", "角色驱动卡", "开场设计", "生成剧本", "质检"]
current = st.session_state.current_step

protagonist = get_protagonist()
protagonist_label = f"👑{protagonist['name']}" if protagonist else "未设主角"

st.markdown(f"""
<div class="header-bar">
    <div class="header-left">
        <div class="header-title">🎬 影视化视觉翻译引擎 V5.0</div>
        <div class="header-sub">角色驱动卡系统 · 主角存在感规则 · 物理校验 · 有效OS规则</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <span class="header-badge">📚 {len(st.session_state.chapter_order)}章</span>
        <span class="header-badge">🎬 {len(st.session_state.episodes)}集</span>
        <span class="header-badge">{protagonist_label}</span>
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
        <span class="card-subtitle">.txt / .md 上传 或 粘贴文本</span>
    </div>
</div>""", unsafe_allow_html=True)

ca, cl = st.columns([1, 1])
with ca:
    at = st.tabs(["📁 上传文件", "✍️ 粘贴文本"])
    with at[0]:
        up = st.file_uploader("选择文件", type=["txt", "md", "text"],
                               accept_multiple_files=True, key="up")
        if up:
            for u in up:
                if u.size > 200 * 1024:
                    st.warning(f"⚠️ {u.name} 超过200KB")
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
        </div>""", unsafe_allow_html=True)
        for i, ch in enumerate(st.session_state.chapter_order):
            ct2 = st.session_state.chapters.get(ch, "")
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                st.markdown(f"""
                <div class="chapter-item">
                    <div class="chapter-icon">{i+1}</div>
                    <div class="chapter-info">
                        <div class="chapter-name">{ch}</div>
                        <div class="chapter-meta">{len(ct2):,}字</div>
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
                    st.text_area("", ct2, height=200, disabled=True, key=f"preview_{i}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📚</div>
            <div class="empty-text">暂无章节，请上传或粘贴</div>
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
        sc = st.multiselect("选择参与提炼的章节",
                            st.session_state.chapter_order,
                            default=st.session_state.chapter_order, key="sc")
        st.session_state.selected_chapters_for_analysis = sc
        if sc:
            total_chars = sum(len(st.session_state.chapters.get(c, "")) for c in sc)
            st.info(f"📊 已选 {len(sc)} 章 · 共 {total_chars:,} 字")

        b1, b2 = st.columns(2)
        with b1:
            da = st.button("🚀 开始提炼", key="da", use_container_width=True, type="primary",
                           disabled=not (sc and st.session_state.api_key))
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
        with st.spinner("🧠 全局提炼中..."):
            r = call_api_streaming(ms)
            if r:
                co = st.empty()
                f = stream_to_container(r, co)
                if f:
                    st.session_state.global_analysis = f
                    st.session_state.messages = ms + [{"role": "assistant", "content": f}]
                    st.session_state.current_step = max(st.session_state.current_step, 1)
                    # 自动解析驱动卡
                    parsed_cards = parse_cards_from_analysis(f)
                    if parsed_cards:
                        # 合并：已有锁定的卡不覆盖
                        existing_names = {c["name"] for c in st.session_state.character_cards if c.get("locked_all")}
                        new_cards = [c for c in parsed_cards if c["name"] not in existing_names]
                        # 保留已锁定的卡，追加新解析的卡
                        locked_cards = [c for c in st.session_state.character_cards if c.get("locked_all")]
                        st.session_state.character_cards = locked_cards + new_cards
                        st.info(f"✅ 已自动解析 {len(new_cards)} 个角色驱动卡，请在步骤三中确认")
                    auto_save()
                    st.success("✅ 提炼完成！")
    elif st.session_state.global_analysis:
        with st.expander("📋 查看提炼结果", expanded=False):
            st.markdown(st.session_state.global_analysis)
# ============================================================
# 步骤三：角色驱动卡管理
# ============================================================
st.markdown("""
<div class="card">
    <div class="card-header">
        <span class="card-icon">👥</span>
        <span class="card-title">步骤三：角色驱动卡</span>
        <span class="card-subtitle">设定主角 · 锁定性格 · 更新状态</span>
    </div>
</div>""", unsafe_allow_html=True)

cards = st.session_state.character_cards

# 顶部操作栏
cc1, cc2, cc3 = st.columns([2, 2, 2])
with cc1:
    if st.button("➕ 新增角色卡", key="add_card", use_container_width=True):
        new_card = make_empty_card()
        st.session_state.character_cards.append(new_card)
        auto_save()
        st.rerun()
with cc2:
    if st.session_state.global_analysis:
        if st.button("📥 从提炼结果重新导入", key="reimport_cards", use_container_width=True):
            parsed = parse_cards_from_analysis(st.session_state.global_analysis)
            if parsed:
                locked = [c for c in st.session_state.character_cards if c.get("locked_all")]
                locked_names = {c["name"] for c in locked}
                new_c = [c for c in parsed if c["name"] not in locked_names]
                st.session_state.character_cards = locked + new_c
                auto_save()
                st.success(f"✅ 导入 {len(new_c)} 个角色卡")
                st.rerun()
            else:
                st.warning("未能从提炼结果中解析到驱动卡，请检查提炼结果格式")
with cc3:
    protagonist = get_protagonist()
    if protagonist:
        st.markdown(f"""
        <div style="background:#fffaf0;border:1px solid #f6ad55;border-radius:8px;
                    padding:8px 12px;font-size:0.82rem;text-align:center;">
            👑 主角：<b>{protagonist['name']}</b>（{protagonist['gender']}）
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fff5f5;border:1px solid #fc8181;border-radius:8px;
                    padding:8px 12px;font-size:0.72rem;text-align:center;color:#c53030;">
            ⚠️ 尚未设定主角，请在下方角色卡中设置
        </div>""", unsafe_allow_html=True)

if not cards:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">👥</div>
        <div class="empty-text">暂无角色驱动卡</div>
        <div style="font-size:0.78rem;color:#cbd5e0;">完成全局提炼后自动生成，或点击"新增角色卡"手动添加</div>
    </div>""", unsafe_allow_html=True)
else:
    # 主角排在最前面
    protagonist_idx = st.session_state.protagonist_index
    ordered_indices = []
    if 0 <= protagonist_idx < len(cards):
        ordered_indices.append(protagonist_idx)
    for i in range(len(cards)):
        if i != protagonist_idx:
            ordered_indices.append(i)

    for display_order, real_idx in enumerate(ordered_indices):
        card = cards[real_idx]
        is_protagonist = (real_idx == st.session_state.protagonist_index)
        is_locked = card.get("locked_all", False)
        is_perm_locked = card.get("locked_permanent", False)

        # 卡片样式
        card_class = "char-card"
        if is_protagonist:
            card_class += " protagonist"
        elif is_locked:
            card_class += " locked"

        # 徽章
        badges = []
        if is_protagonist:
            badges.append('<span class="tag tag-gold">👑 主角</span>')
        if is_locked:
            badges.append('<span class="tag tag-green">🔒 已锁定</span>')
        elif is_perm_locked:
            badges.append('<span class="tag tag-green">🔒 性格已锁</span>')
        if card.get("current_body_state"):
            badges.append(f'<span class="tag tag-blue">状态已设</span>')

        badge_html = " ".join(badges)
        name_display = card.get("name") or f"角色 {real_idx+1}"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="char-card-header">
                <span class="char-name">{name_display}</span>
                <div class="char-badges">{badge_html}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"{'👑 ' if is_protagonist else ''}编辑 {name_display}", expanded=card.get("expanded", False)):

            # 基础信息行
            bi1, bi2, bi3 = st.columns([3, 2, 2])
            with bi1:
                new_name = st.text_input("角色名", value=card.get("name", ""),
                                          key=f"cname_{real_idx}", placeholder="角色姓名")
                if new_name != card.get("name", ""):
                    cards[real_idx]["name"] = new_name
                    auto_save()
            with bi2:
                gender_opts = ["女", "男", "其他"]
                cur_gender = card.get("gender", "女")
                gender_idx = gender_opts.index(cur_gender) if cur_gender in gender_opts else 0
                new_gender = st.selectbox("性别", gender_opts, index=gender_idx, key=f"cgender_{real_idx}")
                if new_gender != card.get("gender"):
                    cards[real_idx]["gender"] = new_gender
                    auto_save()
            with bi3:
                role_opts = ["主要角色", "核心配角", "次要角色", "功能角色"]
                cur_role = card.get("role_type", "主要角色")
                role_idx = role_opts.index(cur_role) if cur_role in role_opts else 0
                new_role = st.selectbox("角色类型", role_opts, index=role_idx, key=f"crole_{real_idx}")
                if new_role != card.get("role_type"):
                    cards[real_idx]["role_type"] = new_role
                    auto_save()

            st.markdown("---")

            # ── 永久锁定区（性格核心）──
            perm_locked = card.get("locked_permanent", False)
            perm_color = "#f0fff4" if perm_locked else "#fafafa"
            lock_icon = "🔒" if perm_locked else "🔓"

            st.markdown(f"""
            <div style="background:{perm_color};border:1px solid #e2e8f0;border-radius:8px;
                        padding:10px 12px;margin-bottom:8px;">
                <div style="font-size:0.78rem;font-weight:600;color:#4a5568;margin-bottom:6px;">
                    {lock_icon} 性格核心（锁定后跨集复用，不重新生成）
                </div>
            </div>""", unsafe_allow_html=True)

            disabled_perm = perm_locked

            new_cp = st.text_area(
                "核心人格（一句话定义）",
                value=card.get("core_personality", ""),
                height=60, key=f"ccp_{real_idx}",
                disabled=disabled_perm,
                placeholder="示例：表面冷漠实则刀子嘴豆腐心的前特种兵，把保护他人当成赎罪"
            )
            if not disabled_perm and new_cp != card.get("core_personality", ""):
                cards[real_idx]["core_personality"] = new_cp
                auto_save()

            new_sd = st.text_area(
                "说话DNA（句式习惯/口头禅 + 原文示范句）",
                value=card.get("speech_dna", ""),
                height=80, key=f"csd_{real_idx}",
                disabled=disabled_perm,
                placeholder="示例：惜字如金，命令句为主，从不解释自己的决定。原句：'走。''不行。''闭嘴。'"
            )
            if not disabled_perm and new_sd != card.get("speech_dna", ""):
                cards[real_idx]["speech_dna"] = new_sd
                auto_save()

            new_bd = st.text_area(
                "行为DNA（愤怒/心软/恐惧/得意时的物理反应）",
                value=card.get("behavior_dna", ""),
                height=80, key=f"cbd_{real_idx}",
                disabled=disabled_perm,
                placeholder="示例：愤怒→下颌肌肉收紧但不说话；心软→手部动作与嘴上说的相反"
            )
            if not disabled_perm and new_bd != card.get("behavior_dna", ""):
                cards[real_idx]["behavior_dna"] = new_bd
                auto_save()

            new_rl = st.text_area(
                "红线（绝对不做的事）",
                value=card.get("red_line", ""),
                height=60, key=f"crl_{real_idx}",
                disabled=disabled_perm,
                placeholder="示例：绝不主动求人帮助；绝不在他人面前哭泣"
            )
            if not disabled_perm and new_rl != card.get("red_line", ""):
                cards[real_idx]["red_line"] = new_rl
                auto_save()

            # 锁定/解锁性格核心按钮
            pl1, pl2 = st.columns(2)
            with pl1:
                if perm_locked:
                    if st.button(f"🔓 解锁性格核心", key=f"unlock_perm_{real_idx}",
                                 use_container_width=True):
                        cards[real_idx]["locked_permanent"] = False
                        auto_save()
                        st.rerun()
                else:
                    if st.button(f"🔒 锁定性格核心", key=f"lock_perm_{real_idx}",
                                 use_container_width=True, type="primary"):
                        cards[real_idx]["locked_permanent"] = True
                        auto_save()
                        st.rerun()

            st.markdown("---")

            # ── 可更新区（当前状态）──
            st.markdown("""
            <div style="background:#ebf8ff;border:1px solid #90cdf4;border-radius:8px;
                        padding:10px 12px;margin-bottom:8px;">
                <div style="font-size:0.78rem;font-weight:600;color:#2c5282;">
                    📝 当前状态（每集可更新，随剧情变化）
                </div>
            </div>""", unsafe_allow_html=True)

            new_cbs = st.text_area(
                "身体状态",
                value=card.get("current_body_state", ""),
                height=60, key=f"ccbs_{real_idx}",
                placeholder="示例：已变异为丧尸，面部肌肉无法做出正常表情，瞳孔灰白"
            )
            if new_cbs != card.get("current_body_state", ""):
                cards[real_idx]["current_body_state"] = new_cbs
                auto_save()

            new_cms = st.text_area(
                "心理状态",
                value=card.get("current_mental_state", ""),
                height=60, key=f"ccms_{real_idx}",
                placeholder="示例：意识完整清醒，有羞耻感和饥饿感，对自身丧尸身份感到迷茫"
            )
            if new_cms != card.get("current_mental_state", ""):
                cards[real_idx]["current_mental_state"] = new_cms
                auto_save()

            new_rel = st.text_area(
                "当前关系动态",
                value=card.get("relationships", ""),
                height=80, key=f"crel_{real_idx}",
                placeholder="示例：秦洛→陌生·警惕期，被他保护但感受到潜在杀意；陈小飞→熟悉·信任"
            )
            if new_rel != card.get("relationships", ""):
                cards[real_idx]["relationships"] = new_rel
                auto_save()

            st.markdown("---")

            # ── 底部控制按钮 ──
            btn_cols = st.columns(4)

            with btn_cols[0]:
                if is_protagonist:
                    st.markdown('<span class="tag tag-gold">👑 当前主角</span>', unsafe_allow_html=True)
                else:
                    if st.button("👑 设为主角", key=f"set_proto_{real_idx}",
                                 use_container_width=True):
                        # 取消之前主角标记
                        for i, c in enumerate(cards):
                            cards[i]["is_protagonist"] = False
                        cards[real_idx]["is_protagonist"] = True
                        st.session_state.protagonist_index = real_idx
                        auto_save()
                        st.success(f"✅ {name_display} 已设为主角")
                        st.rerun()

            with btn_cols[1]:
                all_locked = card.get("locked_all", False)
                if all_locked:
                    if st.button("🔓 解除全卡锁定", key=f"unlock_all_{real_idx}",
                                 use_container_width=True):
                        cards[real_idx]["locked_all"] = False
                        auto_save()
                        st.rerun()
                else:
                    if st.button("🔒 锁定整张卡", key=f"lock_all_{real_idx}",
                                 use_container_width=True):
                        cards[real_idx]["locked_all"] = True
                        cards[real_idx]["locked_permanent"] = True
                        auto_save()
                        st.rerun()

            with btn_cols[2]:
                if st.button("📋 复制卡片", key=f"copy_card_{real_idx}",
                             use_container_width=True):
                    import copy
                    new_c = copy.deepcopy(card)
                    new_c["name"] = f"{card.get('name', '')}（副本）"
                    new_c["locked_all"] = False
                    new_c["locked_permanent"] = False
                    new_c["is_protagonist"] = False
                    st.session_state.character_cards.append(new_c)
                    auto_save()
                    st.rerun()

            with btn_cols[3]:
                if st.button("🗑️ 删除", key=f"del_card_{real_idx}",
                             use_container_width=True):
                    st.session_state.character_cards.pop(real_idx)
                    if st.session_state.protagonist_index == real_idx:
                        st.session_state.protagonist_index = -1
                    elif st.session_state.protagonist_index > real_idx:
                        st.session_state.protagonist_index -= 1
                    auto_save()
                    st.rerun()

# ============================================================
# 步骤四：编剧控制台
# ============================================================
st.markdown("""
<div class="card">
    <div class="card-header">
        <span class="card-icon">🎬</span>
        <span class="card-title">步骤四：编剧控制台</span>
        <span class="card-subtitle">开场设计 → 生成剧本 → 质检优化</span>
    </div>
</div>""", unsafe_allow_html=True)

ad = bool(st.session_state.global_analysis)
has_cards = len(st.session_state.character_cards) > 0
has_protagonist = get_protagonist() is not None
has_opening = st.session_state.selected_opening_index >= 0 and bool(st.session_state.parsed_openings)

# 集数和章节
t1, t2, t3 = st.columns([1, 2, 3])
with t1:
    en = st.number_input("集数", 1, 200, st.session_state.current_episode, key="ei")
    st.session_state.current_episode = en
with t2:
    ec = st.multiselect("本集参考章节", st.session_state.chapter_order,
                         key="ec", help="选择本集要改编的章节，可多选")
with t3:
    tags = []
    tags.append(f'<span class="tag tag-blue">第{en}集</span>')
    tags.append(f'<span class="tag tag-purple">{get_active_model()}</span>')
    tags.append(f'<span class="tag {"tag-green" if ad else "tag-yellow"}">{"✅ 已提炼" if ad else "⚠️ 未提炼"}</span>')
    tags.append(f'<span class="tag {"tag-green" if has_protagonist else "tag-red"}">{"👑 主角已设" if has_protagonist else "❌ 未设主角"}</span>')
    tags.append(f'<span class="tag {"tag-green" if has_opening else "tag-yellow"}">{"✅ 开场已选" if has_opening else "⏳ 未选开场"}</span>')
    st.markdown(f'<div style="display:flex;gap:6px;padding-top:24px;flex-wrap:wrap;">{"".join(tags)}</div>',
                unsafe_allow_html=True)

# 上集衔接
with st.expander("🔗 上集衔接内容（可选）", expanded=False):
    prev_ending_val = ""
    # 从最近一集末尾自动提取
    if st.session_state.episodes:
        last_ep = max(st.session_state.episodes.keys())
        last_script = st.session_state.episodes[last_ep]
        prev_ending_val = last_script[-600:] if len(last_script) > 600 else last_script

    prev_ending = st.text_area(
        "上集末尾内容",
        value=prev_ending_val,
        height=120, key="prev_ending_input",
        placeholder="留空 = 第一集 / 新篇章开始\n或粘贴上集最后的场景内容..."
    )

# 主功能按钮
st.markdown("---")
btn_col1, btn_col2, btn_col3 = st.columns(3)
with btn_col1:
    btn_opening = st.button("🎯 设计开场方案", key="b_opening", use_container_width=True,
                             disabled=not (ad and st.session_state.api_key))
with btn_col2:
    btn_generate = st.button("🎬 生成剧本", key="b_generate", use_container_width=True,
                              type="primary",
                              disabled=not (ad and st.session_state.api_key))
with btn_col3:
    btn_review = st.button("🔍 质量检查", key="b_review", use_container_width=True,
                            disabled=not (en in st.session_state.episodes and st.session_state.api_key))

# ============================================================
# 主内容 Tabs
# ============================================================
mt = st.tabs(["📝 剧本", "🔍 质检报告", "🎯 开场设计", "💬 对话", "📊 总览"])

# ─── Tab 0：剧本 ───
with mt[0]:
    if btn_generate:
        if not ad:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        elif not has_protagonist:
            st.warning("⚠️ 请先在步骤三中设定主角")
        else:
            tx = get_combined_text(ec if ec else None)

            opening_content = ""
            if has_opening and en == 1:
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
                        st.session_state.current_step = max(st.session_state.current_step, 4)
                        auto_save()
                        st.success(f"✅ 第{en}集生成完成！")

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
                m4.metric("主角", get_protagonist()["name"] if get_protagonist() else "—")

                st.markdown(s)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(f"📥 下载 Markdown", s,
                                       f"第{e}集剧本.md", "text/markdown", key=f"dl{e}")
                with d2:
                    st.download_button("📋 下载纯文本", s,
                                       f"第{e}集剧本.txt", "text/plain", key=f"cd{e}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎬</div>
            <div class="empty-text">尚未生成任何剧本</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">完成提炼并设定主角后点击"生成剧本"</div>
        </div>""", unsafe_allow_html=True)

# ─── Tab 1：质检报告 ───
with mt[1]:
    if btn_review:
        if en not in st.session_state.episodes:
            st.warning(f"⚠️ 第{en}集尚未生成")
        else:
            tx = get_combined_text(ec if ec else None)
            sc_text = st.session_state.episodes[en]
            rm = [{"role": "user", "content": build_review_prompt(en, sc_text, tx)}]

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
                        st.session_state.current_step = max(st.session_state.current_step, 5)
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
                        fix_prompt = f"""根据以下质检报告，输出修订后的完整剧本。
如质检报告中已包含修订后剧本，直接输出该内容。
如没有，根据改写建议修订后输出。
只输出剧本正文，不需要其他说明。

质检报告：
{rv}

原剧本：
{st.session_state.episodes[e]}"""
                        fm = [{"role": "user", "content": fix_prompt}]
                        with st.spinner("🔧 应用修订中..."):
                            r_fix = call_api_streaming(fm)
                            if r_fix:
                                co = st.empty()
                                fixed = stream_to_container(r_fix, co)
                                if fixed:
                                    st.session_state.episodes[e] = fixed
                                    auto_save()
                                    st.success(f"✅ 第{e}集已更新！")
                                    time.sleep(1)
                                    st.rerun()
                with r2:
                    st.download_button("📥 下载报告", rv,
                                       f"第{e}集_质检报告.md", "text/markdown", key=f"dr{e}")
                with r3:
                    if st.button("🔄 重新质检", key=f"rr{e}"):
                        del st.session_state.review_results[e]
                        st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">暂无质检报告</div>
        </div>""", unsafe_allow_html=True)

# ─── Tab 2：开场设计 ───
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
                    parsed = parse_opening_designs(f)
                    st.session_state.parsed_openings = parsed
                    st.session_state.selected_opening_index = -1
                    st.session_state.messages = ms + [{"role": "assistant", "content": f}]
                    st.session_state.current_step = max(st.session_state.current_step, 3)
                    auto_save()
                    st.success(f"✅ 已生成{len(parsed)}个开场方案")

    if st.session_state.parsed_openings:
        st.markdown("### 🎯 选择开场方案（仅用于第1集）")
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
                <div style="font-size:0.78rem;color:#718096;line-height:1.5;">{op['preview']}</div>
            </div>""", unsafe_allow_html=True)

            bc1, bc2 = st.columns([3, 1])
            with bc1:
                with st.expander("展开完整方案"):
                    st.markdown(op['full'])
            with bc2:
                if is_selected:
                    if st.button("❌ 取消", key=f"desel_{i}", use_container_width=True):
                        st.session_state.selected_opening_index = -1
                        auto_save()
                        st.rerun()
                else:
                    if st.button("✅ 选择", key=f"sel_{i}", use_container_width=True, type="primary"):
                        st.session_state.selected_opening_index = i
                        auto_save()
                        st.rerun()

        if current_sel >= 0:
            st.markdown(f"""
            <div style="background:#f0fff4;border:1px solid #68d391;border-radius:8px;
                        padding:10px 14px;margin-top:12px;">
                <b>当前选择：</b>{st.session_state.parsed_openings[current_sel]['title']}
            </div>""", unsafe_allow_html=True)

        if st.button("🔄 重新设计开场方案", key="regen_opening"):
            st.session_state.opening_designs = ""
            st.session_state.parsed_openings = []
            st.session_state.selected_opening_index = -1
            auto_save()
            st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🎯</div>
            <div class="empty-text">尚未设计开场方案</div>
            <div style="font-size:0.78rem;color:#cbd5e0;">完成全局提炼后点击"设计开场方案"</div>
        </div>""", unsafe_allow_html=True)

# ─── Tab 3：对话 ───
with mt[3]:
    st.markdown("### 💬 自由对话")
    for mg in st.session_state.chat_history[-20:]:
        with st.chat_message(mg["role"]):
            st.markdown(mg["content"])

    ui = st.chat_input("输入问题或指令...", key="ci")
    if ui:
        st.session_state.chat_history.append({"role": "user", "content": ui})
        ctx_parts = []
        if st.session_state.global_analysis:
            ctx_parts.append(f"【全局提炼结果】\n{st.session_state.global_analysis[:2000]}")
        cards_str = build_character_cards_prompt()
        if cards_str:
            ctx_parts.append(f"【角色驱动卡】\n{cards_str}")
        if st.session_state.episodes:
            la = max(st.session_state.episodes.keys())
            ctx_parts.append(f"【最新剧本片段】\n{st.session_state.episodes[la][:1500]}")
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

# ─── Tab 4：总览 ───
with mt[4]:
    st.markdown("### 📊 项目总览")

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("📚 章节数", len(st.session_state.chapter_order))
    o2.metric("🎬 已生成集数", len(st.session_state.episodes))
    o3.metric("✅ 已质检集数", len(st.session_state.review_results))
    o4.metric("👥 角色卡数", len(st.session_state.character_cards))

    if st.session_state.character_cards:
        st.markdown("---")
        st.markdown("#### 👥 角色卡状态")
        for i, c in enumerate(st.session_state.character_cards):
            is_p = (i == st.session_state.protagonist_index)
            badges = []
            if is_p:
                badges.append('<span class="tag tag-gold">👑 主角</span>')
            if c.get("locked_all"):
                badges.append('<span class="tag tag-green">🔒 全卡锁定</span>')
            elif c.get("locked_permanent"):
                badges.append('<span class="tag tag-green">🔒 性格锁定</span>')
            if c.get("current_body_state"):
                badges.append('<span class="tag tag-blue">状态已设</span>')
            badge_html = " ".join(badges) if badges else '<span class="tag tag-yellow">未锁定</span>'
            st.markdown(f"""
            <div class="chapter-item">
                <div class="chapter-icon" style="background:{'linear-gradient(135deg,#f6ad55,#ed8936)' if is_p else 'linear-gradient(135deg,#667eea,#764ba2)'};">
                    {'👑' if is_p else str(i+1)}
                </div>
                <div class="chapter-info">
                    <div class="chapter-name">{c.get('name','未命名')} &nbsp; {badge_html}</div>
                    <div class="chapter-meta">{c.get('core_personality','') or '未填写核心人格'}</div>
                </div>
            </div>""", unsafe_allow_html=True)

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

# ============================================================
# 底部
# ============================================================
st.markdown("---")
protagonist = get_protagonist()
proto_label = f"主角·{protagonist['name']}" if protagonist else "未设主角"
st.markdown(f"""
<div style="text-align:center;padding:16px 0;">
    <span style="color:#a0aec0;font-size:0.75rem;">
        🎬 影视化视觉翻译引擎 V5.0 · {proto_label} · 角色驱动卡系统 · 物理校验 · {get_active_model()}
    </span>
</div>""", unsafe_allow_html=True)
