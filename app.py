# -*- coding: utf-8 -*-
import streamlit as st
import json
import time
import re
import requests
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="影视化视觉翻译引擎 V3.2",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
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
    .empty-state .empty-hint { font-size: 0.78rem; color: #cbd5e0; }
    .memory-panel {
        background: linear-gradient(135deg, #fffff0, #fefcbf);
        border: 1px solid #ecc94b; border-radius: 10px; padding: 16px; margin: 8px 0;
    }
    .memory-item { display: flex; gap: 8px; margin: 6px 0; font-size: 0.82rem; }
    .memory-item .memory-key { color: #975a16; font-weight: 600; white-space: nowrap; }
    .memory-item .memory-val { color: #744210; }
    .sidebar-group-title {
        font-size: 0.78rem; font-weight: 600; color: #4a5568;
        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;
        display: flex; align-items: center; gap: 6px;
    }
    section[data-testid="stSidebar"] { background: #f8fafc; }
    .stButton > button { border-radius: 8px; font-weight: 500; font-size: 0.82rem; padding: 0.4rem 1rem; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #f7fafc; padding: 4px; border-radius: 10px; border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; font-size: 0.82rem; }
    .stTabs [aria-selected="true"] { background: white !important; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    @media (max-width: 768px) {
        .header-bar { flex-direction: column; text-align: center; }
        .stats-bar { flex-direction: column; }
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 系统提示词 (三大问题全面修正)
# ============================================================
SYSTEM_PROMPT = """【微短剧生成 3.1 系统指令】

═══════════════════════════════════════
第零法则：视觉翻译（一切规则之上的规则）
═══════════════════════════════════════

小说是给眼睛的——读者靠文字在脑中自己生成画面。
剧本是给画面的——观众只能看到或听到你拍给他看的东西。

你的工作是——把小说用文字"告诉"读者的一切，全部翻译成摄像机能拍到的画面,并用人物的台词（声音）来增加代入感！

禁止对角色OOC，人物的台词、行为、举止都必须符合小说里的人设！
因此在给核心角色编写每一句台词的时候都要参考【角色驱动卡】

═══════════════════════════════════════
翻译铁律
═══════════════════════════════════════

铁律一：小说的"叙述"必须翻译为"动作流"
铁律二：小说的"心理描写"必须翻译为"身体反应搭配角色内心独白"
铁律三：小说的"设定/背景交代"必须翻译为"环境展示"
铁律四：台词的正确用法——给剧情赋予活力

═══════════════════════════════════════
台词的黄金法则
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
  · 暴怒/恐惧/震惊 → 比平时更短（但话痨的"短"可能仍然比沉默角色的"长"要长）
  · 紧张/兴奋/炫耀 → 比平时更长更碎
  · 压抑/隐忍/心碎 → 说一半吞回去、词不达意、答非所问
→ 关系决定说话方式：同一角色面对不同人说话不同

【绝对禁止的台词方式】
❌ 把所有角色台词统一缩短到2-4个字——会让所有角色都像"高冷人设"
❌ 删掉角色口头禅、语气词——那是角色灵魂
❌ 把话痨改成惜字如金——那是OOC
❌ 台词和画面分开写——必须嵌入画面流中

═══════════════════════════════════════
★★★ 分镜格式铁律（最重要的格式规范）★★★
═══════════════════════════════════════

【铁律A：台词必须嵌入画面动作流中】

台词不是单独一行，台词必须出现在它被说出的那个精确时间位置上，
和此刻正在发生的动作、表情、身体状态写在一起。

❌ 绝对禁止的格式（台词与画面分离）：
```
画面：[秦洛打响指，电流在指尖炸开，许多多被吓得后弹]
秦洛："看，技能点。"
许多多OS：（他有异能？！）
音效：电流滋滋声
```
问题：读者/导演不知道"看，技能点"这句话是在打响指前说的？还是后弹之后说的？

✅ 正确格式（台词嵌入动作流的精确时间点）：
```
秦洛带着战术手套的手指伸进毯子边缘——
啪！响指。一簇幽蓝电流在指尖炸开（音效：尖锐滋滋声），
电光照亮整个角落。
秦洛（得意挑眉，嘴角歪向左边）："看。哥的技能点。"
许多多灰白的瞳孔骤然收缩——身体本能后弹，
后背撞在车厢壁上。
许多多OS：（异能？！他……真的有异能？！）
```

规则：
1. 台词出现在它被说出的精确时间点——在哪个动作之后、哪个动作之前
2. 台词前面必须紧跟说话时的【情绪状态+面部表情+身体动作】
3. 内心OS出现在角色产生这个想法的精确时刻
4. 音效出现在发出声音的那个动作旁边，用（）标注

【铁律B：说台词时必须描写说话者的完整状态】

每一句台词前面，必须包含以下三要素中的至少两个：

① 情绪/语气标签：（低沉、暴怒、故作轻松、嘴硬但声音发颤、咬牙切齿……）
② 面部表情：（挑眉、眼神躲闪、下颌收紧、瞳孔放大、嘴角抽搐……）
③ 身体动作：（双手插兜、指尖点桌面、侧过头不看对方、攥紧拳头……）

❌ 禁止的写法（裸台词）：
秦洛："抱紧点。"

✅ 正确的写法：
秦洛低头看她，故意把表情板得很凶（但声音不自觉放软了）："抱紧点。掉下去被变异兽叼走，真就是一口一个小丧尸。"

✅ 更好的写法：
秦洛低头——本来想摆出教训小孩的凶脸，
但看到她灰白大眼睛滴溜溜乱转的样子，
喉结不自觉滚了一下，声音硬拽着往下压：
"抱紧点。掉下去被变异兽叼走，真就是一口一个小丧尸。"
他说完下意识把手臂往上紧了紧——
这个动作和他嘴里的威胁完全矛盾。

→ 观众同时看到：凶脸+放软的声音+收紧的手臂 = 嘴硬心软，全员心动。

【铁律C：分镜时长必须实算，严禁虚标】

每写完一个分镜，必须用以下换算尺实算：

· 一个简单动作（转头/伸手/按按钮）= 0.5-1秒
· 一个完整肢体动作（站起来/走几步/拿起东西喝一口）= 2-3秒
· 一句台词：每3个字≈1.5秒（含说话节奏和气口）
· 一个表情反应（震惊/微笑/皱眉）= 1-1.5秒
· 一个环境展示镜头（摇镜/推镜）= 2-3秒
· 一次复杂连续动作（打斗/奔跑+互动）= 3-5秒
· 沉默/留白/情绪蓄力 = 1-2秒

实算方法：把分镜里每一个动作/台词/反应逐个计时相加。
标注时长与实算偏差必须≤±2秒。

示范——正确的10秒分镜实算：

秦洛手指伸进毯子边缘（1s）——
啪！响指。幽蓝电流在指尖炸开（1.5s），电光照亮角落。
秦洛（得意挑眉，嘴角歪向左边）：
"看。哥的技能点。生存手册上没这玩意儿吧？"（3.5s）
许多多瞳孔骤然收缩（0.5s）——身体本能后弹，
后背撞在车厢壁上（1.5s）。
许多多OS：（异能？！他真的有异能？！）（1.5s内心节奏）
合计：1+1.5+3.5+0.5+1.5+1.5 = 10秒 ✅

❌ 错误示范——标10秒但实际只有4秒：
秦洛打响指（0.5s），电流炸开（1s），许多多后弹（1s），
秦洛说"看，技能点"（1.5s）= 实际4秒，虚标了6秒。

写完每个分镜后，必须在脑中快速实算，如果不够时长→补充动作/表情/环境细节/反应镜头。

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
如果你写出来的台词，换一个角色名字也能说得通，那这句台词就是废的，重写。
如果你写出来的画面，闭上眼睛脑子里看不见具体的图像，那这段描写就是废的，重写。
产品规格：每集分镜数量自由抉择 | 无第三人称旁白 | 集集强钩子。

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色的性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。允许第一人称内心OS，严禁第三人称旁白。
③【伏笔】每一个重大转折之前，必须存在至少一个视觉/听觉微伏笔。
④【潜台词】角色嘴上说的话与真实意图之间必须存在缝隙。台词传递表面意思，身体泄露真相。
⑤【钩子铁律】前15秒必须制造具体的疑问或情绪冲击。每集结尾必须制造悬念。集内至少一次情绪急转。

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
时长感知校准系统
═══════════════════════════════════════
· 一个简单动作 = 0.5-1秒
· 一个完整肢体动作 = 2-3秒
· 一句台词（每3字≈1.5秒）
· 一个表情反应 = 1-1.5秒
· 一个环境镜头 = 2-3秒
· 复杂连续动作 = 3-5秒
· 沉默/留白 = 1-2秒

═══════════════════════════════════════
完整分镜格式示范
═══════════════════════════════════════

【分镜XX】（实算Xs）
场景：地点 · 时间 · 天气 · 光线

秦洛带着战术手套的手指伸进毯子边缘（1s）——
啪！响指。一簇幽蓝电流在指尖炸开，
电光瞬间照亮整个角落（1.5s）（音效：尖锐滋滋声）。
秦洛得意地挑起左边眉毛，嘴角歪出一个欠揍的弧度：
"看。哥的技能点。生存手册上没这玩意儿吧？"（3.5s）
许多多灰白的瞳孔骤然收缩（0.5s）——
身体本能地向后一弹，后背撞在车厢铁壁上，
发出沉闷的一声响（1.5s）（音效：后背撞击闷响）。
她的手指不自觉攥紧了毯子边缘，
指甲陷进绒毛里（0.5s）。
许多多OS：（异能……是真的存在的？
那他们能活到现在……就是靠这个？）（1.5s）

衔接点：[许多多攥紧毯子的手指 → 车窗外突然暗下来的天色]

格式要点：
1. 台词嵌入在动作流的精确时间位置
2. 台词前紧跟说话者的表情+情绪+身体状态
3. 内心OS在角色产生想法的时刻出现
4. 音效用（）标注在发声的动作旁边
5. 每个动作/台词后标注预估秒数用于实算
6. 分镜总时长 = 所有秒数相加

═══════════════════════════════════════
题材引擎
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
【第3轮：剧本生成】编剧内心独白+结构速写+角色调用+影视化排雷+完整分镜
【第4轮：自检与优化】五个敌对视角+量化打分+细节清单"""

REVIEW_SYSTEM_PROMPT = """你是一个专业的微短剧分镜质检专家。对照小说原文，对每一条分镜进行严格的质量检查。

═══════════════════════════════════════
第一部分：12维度逐镜检查
═══════════════════════════════════════

对每一条分镜，检查以下12个维度（每项1-10分）：

1. **角色一致性**：台词+行为是否符合驱动卡？
2. **画面具象度**：是否有不寻常具体细节？闭眼能否看见画面？
3. **台词活人感**：像真人说的话吗？有废话、犹豫、答非所问吗？
4. **台词个性化**：遮住名字能辨别谁说的吗？所有人听起来一样吗？
5. **视觉翻译完成度**：有没有用台词替代画面叙事？
6. **分镜密度**：10-14秒内是否有足够的动作事件？
7. **因果链完整度**：伏笔和转折是否有因果？
8. **情绪过山车强度**：情绪起伏是否到位？
9. **上下镜衔接流畅度**：分镜之间是否连贯？
10. **时长准确度**：逐秒拆解实算，标注时长与实算偏差≤±2秒？
11. **台词嵌入度**：台词是否嵌入画面流的精确时间位置？还是单独分行？
12. **台词情绪描写**：每句台词前是否有说话者的情绪+表情+身体状态？

对每条分镜输出：

## 分镜 [编号] 检查报告
**内容概要：** [一句话]
| 维度 | 评分 | 状态 | 问题 |
|------|------|------|------|
| 角色一致性 | X/10 | ✅/⚠️/❌ | ... |
| ... | ... | ... | ... |
**综合分：** X/120
**关键问题：** 1. ... 2. ...
**修改建议：** 1. ... 2. ...

═══════════════════════════════════════
第二部分：五个敌对视角攻击
═══════════════════════════════════════

质检完所有分镜后，必须切换为以下五个敌对视角，逐一对整集发起攻击：

【视角1：普通观众（刷短视频的路人）】
- 前3秒能不能抓住我？我会不会划走？
- 哪里看不懂？哪里无聊想跳过？
- 我能不能在完全不知道原著的情况下看懂这一集？
- 结尾够不够让我点"下一集"？
- 输出：作为路人观众，我会在第X秒划走，因为______

【视角2：竞品编剧（想找你毛病的同行）】
- 哪些情绪转折是"硬拗"的？（缺少铺垫就突然转变）
- 整体节奏有没有拖沓或跳跃？
- 输出：如果我是竞品，我会攻击你的______，并且用______方式做得更好

【视角3：原著粉（对人设极度敏感的读者）】
- 哪个角色被OOC了？具体哪句话/哪个行为违背原著？
- 哪些核心情节被改掉了？改得合不合理？
- 角色关系的化学反应够不够？
- 原著中最打动人的情感核心有没有被保留？
- 输出：作为原著粉，我最不能接受的是______，因为原著中______

【视角4：剪辑师（负责后期剪辑的技术人员）】
- 哪些分镜时长虚标？（标10秒但内容只够5秒，或标10秒但内容需要20秒）
- 哪些分镜之间缺少衔接点？（上一镜结尾画面和下一镜开头画面接不上）
- 哪些分镜的动作描写不够精确，导致我无法判断镜头怎么拍？
- 有没有分镜的画面信息过载（一个镜头里塞了太多东西）？
- 台词和画面的时间关系清楚吗？我能判断台词在哪个动作时说出吗？
- 输出：作为剪辑师，我剪不动的地方是______，因为______

【视角5：导演（对整体质量负责的决策者）】
- 这集的"记忆点"是什么？观众看完能记住的画面是什么？
- 情绪曲线画出来是什么形状？有没有平坦段？
- 演员拿到这个剧本，能不能直接演？还是会来问我"这里怎么演"？
- 整集的视觉风格统一吗？有没有某个分镜画风突变？
- 输出：作为导演，我最想重拍的是分镜______，最满意的是分镜______

═══════════════════════════════════════
第三部分：细节自检清单
═══════════════════════════════════════

逐项打勾（✅/❌）：

□ 每句台词前都有说话者的情绪+表情+身体描写（至少两个）
□ 台词全部嵌入画面动作流的精确时间位置（无单独分行的台词）
□ 每个分镜标注时长与实算时长偏差≤±2秒
□ 遮住所有角色名，仅凭说话方式可辨别至少80%的台词归属
□ 无第三人称旁白
□ 开场15秒内有具体疑问或情绪冲击
□ 结尾有悬念钩子（观众不看下集会难受）
□ 集内至少一次情绪急转
□ 每个分镜有≥1个不寻常的具体细节
□ 每个分镜有≥1个具体声音
□ 重大转折前有至少一个伏笔
□ 无"死掉的台词"（换角色名也通的废台词）
□ 无"死掉的画面"（闭眼看不见具体图像的抽象描写）
□ 角色情绪变化有铺垫、不突兀
□ ≥65%的情绪转折来自人物互动/环境碰撞（非独白驱动）

═══════════════════════════════════════
第四部分：整集汇总报告
═══════════════════════════════════════

1. **总分：** X/120（12维度平均分×12）
2. **7分以下项目列表**（按修改优先级排序）
3. **五个敌对视角的核心攻击点汇总**
4. **全局性问题**（如所有分镜共同的毛病）
5. **优秀之处**（值得保留的亮点）
6. **修改优先级排序**（先改什么、后改什么）"""

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
        "episodes": {}, "review_results": {},
        "memory": {
            "storyline": "", "characters": "", "progress": "",
            "last_ending": "", "pending_foreshadow": "",
            "next_foreshadow": "", "emotion_track": ""
        },
        "messages": [], "chat_history": [],
        "mode": "默认", "selected_chapters_for_analysis": [],
        "review_model": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

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
    try:
        resp = requests.post(f"{api_base}/chat/completions", headers=headers, json=data, stream=True, timeout=300)
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
        body = ""
        try: body = e.response.text[:500] if e.response is not None else ""
        except: pass
        st.error(f"❌ HTTP {code}: {body}")
        return None
    except Exception as e:
        st.error(f"❌ {type(e).__name__}: {e}")
        return None

def process_stream(response):
    if response is None: return
    try:
        for line in response.iter_lines():
            if not line: continue
            try: line_str = line.decode("utf-8")
            except: continue
            if not line_str.startswith("data: "): continue
            data_str = line_str[6:].strip()
            if data_str == "[DONE]": break
            if not data_str: continue
            try: data = json.loads(data_str)
            except json.JSONDecodeError: continue
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0: continue
            first = choices[0]
            if not isinstance(first, dict): continue
            delta = first.get("delta")
            if not delta or not isinstance(delta, dict): continue
            content = delta.get("content")
            if content: yield content
    except requests.exceptions.ChunkedEncodingError:
        st.warning("⚠️ 传输中断，已保存内容")
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ 连接中断")
    except Exception as e:
        st.warning(f"⚠️ {type(e).__name__}: {e}")

def stream_to_container(response, container):
    if response is None: return ""
    full = ""
    for chunk in process_stream(response):
        full += chunk
        container.markdown(full)
    return full

def call_api_non_streaming(messages, system_prompt=SYSTEM_PROMPT):
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = get_active_model()
    if not api_key or not api_base: return None
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
        if not choices or len(choices) == 0: return None
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
        return True
    return False

def remove_chapter(name):
    if name in st.session_state.chapters:
        del st.session_state.chapters[name]
        if name in st.session_state.chapter_order:
            st.session_state.chapter_order.remove(name)

def get_combined_text(names=None):
    if names is None: names = st.session_state.chapter_order
    return "\n\n".join(f"【{n}】\n{st.session_state.chapters[n]}" for n in names if n in st.session_state.chapters)
def extract_last_shot(episode_text):
    """从剧本文本中提取最后一个分镜的内容"""
    if not episode_text:
        return ""
    # 匹配所有分镜标记
    shots = re.split(r'(【分镜\s*\d+】)', episode_text)
    if len(shots) < 2:
        # 没找到分镜标记，取最后500字
        return episode_text[-500:].strip()
    # 取最后一个分镜标记及其后面的内容
    last_shot_header = ""
    last_shot_content = ""
    for i in range(len(shots) - 1, -1, -1):
        if re.match(r'【分镜\s*\d+】', shots[i]):
            last_shot_header = shots[i]
            last_shot_content = shots[i + 1] if i + 1 < len(shots) else ""
            break
    result = (last_shot_header + last_shot_content).strip()
    # 如果结果太长，截断
    if len(result) > 800:
        result = result[:800] + "..."
    return result
    
# ============================================================
# Prompt构建
# ============================================================
def build_analysis_prompt(text):
    return f"""【微短剧3.1启动】

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

输出6条完全不同的第1集开场方案，每条包含：
- 开场类型标签
- 前30秒逐秒画面描述
- 30秒后如何衔接主线"""

def build_episode_prompt(ep, text, opening="", last_shot=""):
    mem = st.session_state.memory
    mem_str = ""
    if mem.get("storyline"):
        mem_str = f"""
📌 主线：{mem['storyline']}
📌 人物：{mem['characters']}
📌 进度：第{mem['progress']}集
📌 上集结尾：{mem['last_ending']}
📌 伏笔：{mem['pending_foreshadow']}
📌 引爆：{mem['next_foreshadow']}
📌 情绪：{mem['emotion_track']}"""

    # 构建衔接指令
    bridging = ""
    if last_shot and last_shot.strip():
        bridging = f"""
═══════════════════════════════════════
🔗 上集衔接（必须遵守）
═══════════════════════════════════════
以下是上一集（第{ep-1}集）的最后一个分镜：

{last_shot.strip()}

【衔接要求】
1. 本集第一个分镜必须在时间/空间/情绪上承接上面这个镜头
2. 上一镜的「衔接点」描述的画面，就是本集第一个分镜的开场画面
3. 不能出现时间跳跃或场景突变（除非上一镜的衔接点明确指向了场景转换）
4. 上集结尾的情绪基调要延续到本集开头，再自然地发展或转变
5. 如果上一镜埋了伏笔或悬念，本集前3个分镜内必须有回应或推进
"""
    else:
        if ep > 1:
            bridging = """
═══════════════════════════════════════
🔗 衔接说明
═══════════════════════════════════════
用户未提供上集末尾内容。本集视为新篇章开头，可以自由设计开场。
但仍需参考全局记忆中的进度和伏笔信息。
"""

    return f"""请执行【第3轮：剧本生成】—— 第{ep}集
{mem_str}
{bridging}
{"选择的开场方案：" + opening if opening else ""}

参考小说原文：
{text}

严格执行前置ABCD，然后输出完整分镜剧本。

【分镜格式强制要求】
1. 台词必须嵌入画面动作流，出现在被说出的精确时间位置
2. 每句台词前紧跟说话者的情绪/表情/身体状态（至少两个）
3. 每个分镜实算时长（逐项相加，目标10-14秒）
4. 内心OS出现在角色产生想法的那个时刻
5. 音效用（）标注在发声动作旁

示范格式：
【分镜XX】（实算Xs）
场景：地点 · 时间 · 天气 · 光线

[角色动作]（Xs）——
[变化/发展]（Xs）（音效：xxx）。
角色A（情绪+表情+身体）："台词"（Xs）
[另一角色反应]（Xs）。
角色B OS：（内心独白）（Xs）

衔接点：[最后画面 → 下一镜]"""

def build_review_prompt(ep, script, text):
    return f"""请对第{ep}集剧本逐条分镜进行详细质检。

【小说原文】
{text}

【剧本分镜】
{script}

逐镜检查12个维度（1-10分），特别注意三个重点项：

【重点1：时长实算】
对每个分镜逐秒拆解（列出每个动作/台词的秒数，求和），
检查标注时长与实算时长偏差是否≤±2秒。

【重点2：台词嵌入度】
每句台词是否嵌入在画面动作流的精确位置？
还是单独另起一行与画面分离？

【重点3：台词情绪描写】
每句台词前面是否描写了说话者当时的情绪+表情+身体状态？
还是"裸台词"（只有角色名+台词内容）？

输出检查报告+汇总。7分以下必须给修改方案。"""

def build_dialogue_optimization_prompt(ep, script, global_analysis=""):
    character_info = ""
    if global_analysis:
        character_info = f"\n【角色驱动卡参考】\n{global_analysis[:4000]}\n"
    return f"""台词优化第{ep}集。

{character_info}

【核心：台词优化≠精简！而是个性化+潜台词化+情绪匹配】

优化步骤：
1. 确认每个角色的说话DNA
2. 逐句检查：个性标签、情绪匹配、潜台词深度、关系动态
3. 补充台词前的情绪/表情/身体描写（如果缺失）
4. 确保台词嵌入在画面动作流的正确时间位置

❌ 禁止：统一缩短/删口头禅/让话痨变沉默/台词与画面分离
✅ 要求：每处修改标注原因+关联角色DNA

当前剧本：
{script}

输出优化后完整剧本。"""

def build_visual_optimization_prompt(ep, script):
    return f"""画面优化第{ep}集。

要求：
1. 不寻常具体细节（声音/光影/微动作）
2. 声音锚定空间
3. 光源具体化
4. 身体失控＞表情形容词
5. 反差动作＞直球动作
6. 每分镜≥5个动作事件（有时间流动感）
7. 台词保持嵌入式格式不变
8. 实算时长不变

当前剧本：
{script}

输出优化后完整剧本，修改处标注【🎨】。"""

def build_emotion_optimization_prompt(ep, script):
    return f"""情绪优化第{ep}集。

要求：
1. 开场15秒足够冲击
2. 集内至少一次情绪急转
3. 结尾悬念钩子
4. 情绪曲线有起伏
5. 题材引擎（弹簧法/磁铁法/错位法/橡皮筋法）
6. ≥65%转折来自互动
7. 台词格式和嵌入方式不变

当前剧本：
{script}

输出优化后完整剧本，修改处标注【❤️】。"""

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-group-title">🔌 API 配置</div>', unsafe_allow_html=True)
    api_base = st.text_input("接口地址", value=st.session_state.api_base, key="sb_ab", placeholder="https://yunwu.ai/v1/")
    st.session_state.api_base = api_base
    api_key = st.text_input("API Key", value=st.session_state.api_key, type="password", key="sb_ak", placeholder="sk-...")
    st.session_state.api_key = api_key

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">🤖 模型</div>', unsafe_allow_html=True)
    model_options = [
        "deepseek-chat", "deepseek-reasoner",
        "claude-sonnet-4-20250514", "claude-opus-4-20250514",
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini",
        "gemini-2.5-pro-preview-06-05", "自定义模型"
    ]
    cm1, cm2 = st.columns([3,1])
    with cm1:
        sel = st.selectbox("生成模型", model_options,
            index=model_options.index(st.session_state.model_id) if st.session_state.model_id in model_options else 0, key="sb_m")
        st.session_state.model_id = sel
    with cm2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔗", key="sb_t", use_container_width=True, help="测试"):
            with st.spinner("..."):
                r = call_api_non_streaming([{"role":"user","content":"回复OK"}], "你是助手。")
                st.success("✅") if r else st.error("❌")
    if sel == "自定义模型":
        cm = st.text_input("模型ID", value=st.session_state.custom_model, key="sb_c", placeholder="deepseek-v3")
        st.session_state.custom_model = cm
    rev_opts = ["与生成模型相同"] + model_options
    rv = st.selectbox("质检模型", rev_opts, key="sb_rv")
    st.session_state.review_model = None if rv == "与生成模型相同" else rv

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">🎯 模式</div>', unsafe_allow_html=True)
    md = st.radio("", ["📋 默认", "⚡ 快速"], key="sb_md", label_visibility="collapsed")
    st.session_state.mode = "默认" if "默认" in md else "快速"

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">💾 数据</div>', unsafe_allow_html=True)
    if st.button("📌 全局记忆", use_container_width=True, key="sb_me"):
        st.session_state["show_memory_modal"] = True
    if st.session_state.episodes:
        st.download_button("📦 导出全部", use_container_width=True, key="sb_ex",
            data=json.dumps({"analysis":st.session_state.global_analysis,
                "episodes":{str(k):v for k,v in st.session_state.episodes.items()},
                "reviews":{str(k):v for k,v in st.session_state.review_results.items()},
                "memory":st.session_state.memory}, ensure_ascii=False, indent=2),
            file_name=f"剧本_{datetime.now().strftime('%m%d_%H%M')}.json", mime="application/json")
    if st.button("🗑️ 重置", use_container_width=True, key="sb_rs"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        init_session_state(); st.rerun()

# ============================================================
# 顶部
# ============================================================
step_names = ["导入章节","全局提炼","开场设计","生成剧本","质检优化"]
current = st.session_state.current_step
st.markdown(f"""<div class="header-bar"><div class="header-left">
<div class="header-title">🎬 影视化视觉翻译引擎 V3.2</div>
<div class="header-sub">视觉翻译法则 · 角色DNA台词 · 台词嵌入画面流 · 实算时长</div></div>
<div style="display:flex;gap:8px;flex-wrap:wrap;">
<span class="header-badge">📚 {len(st.session_state.chapter_order)}章</span>
<span class="header-badge">🎬 {len(st.session_state.episodes)}集</span>
<span class="header-badge">🤖 {get_active_model()}</span></div></div>""", unsafe_allow_html=True)

sh = ""
for i,n in enumerate(step_names):
    c = "done" if i<current else ("active" if i==current else "")
    ic = "✓" if i<current else str(i+1)
    sh += f'<div class="step-item {c}"><span class="step-num">{ic}</span>{n}</div>'
st.markdown(f'<div class="step-indicator">{sh}</div>', unsafe_allow_html=True)

if st.session_state.get("show_memory_modal"):
    mem = st.session_state.memory
    with st.expander("📌 全局记忆", expanded=True):
        st.markdown(f"""<div class="memory-panel">
<div class="memory-item"><span class="memory-key">📌 主线：</span><span class="memory-val">{mem.get('storyline') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">👥 人物：</span><span class="memory-val">{mem.get('characters') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">📍 进度：</span><span class="memory-val">{mem.get('progress') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">🔚 结尾：</span><span class="memory-val">{mem.get('last_ending') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">🔮 伏笔：</span><span class="memory-val">{mem.get('pending_foreshadow') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">💥 引爆：</span><span class="memory-val">{mem.get('next_foreshadow') or '—'}</span></div>
<div class="memory-item"><span class="memory-key">❤️ 情绪：</span><span class="memory-val">{mem.get('emotion_track') or '—'}</span></div>
</div>""", unsafe_allow_html=True)
        if st.button("关闭",key="cmm"): st.session_state["show_memory_modal"]=False; st.rerun()

# ============================================================
# 步骤一
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">📖</span><span class="card-title">步骤一：导入小说章节</span>
<span class="card-subtitle">.txt/.md 上传 或 粘贴</span></div></div>""", unsafe_allow_html=True)

ca, cl = st.columns([1,1])
with ca:
    at = st.tabs(["📁 上传","✍️ 粘贴"])
    with at[0]:
        up = st.file_uploader("选择",type=["txt","md","text"],accept_multiple_files=True,key="up")
        if up:
            for u in up:
                if u.size>200*1024: st.warning(f"⚠️ {u.name}>200KB"); continue
                try: ct=u.read().decode("utf-8",errors="ignore")
                except: ct=""
                cn=u.name.rsplit(".",1)[0] if "." in u.name else u.name
                if cn not in st.session_state.chapters and ct:
                    add_chapter(cn,ct); st.success(f"✅ {cn} ({len(ct)}字)")
    with at[1]:
        pn=st.text_input("名称",placeholder="第1章",key="pn")
        pc=st.text_area("内容",height=180,placeholder="粘贴...",key="pc")
        if st.button("➕ 添加",key="pa",use_container_width=True,type="primary"):
            if pn and pc: add_chapter(pn,pc); st.success(f"✅ {pn}"); st.rerun()
            else: st.warning("请填写")

with cl:
    st.markdown("**已导入**")
    if st.session_state.chapter_order:
        tc=sum(len(st.session_state.chapters.get(c,"")) for c in st.session_state.chapter_order)
        st.markdown(f"""<div class="stats-bar">
<div class="stat-item"><div class="stat-value">{len(st.session_state.chapter_order)}</div><div class="stat-label">章节</div></div>
<div class="stat-item"><div class="stat-value">{tc:,}</div><div class="stat-label">总字</div></div>
<div class="stat-item"><div class="stat-value">{tc//max(len(st.session_state.chapter_order),1):,}</div><div class="stat-label">均字</div></div>
</div>""", unsafe_allow_html=True)
        for i,ch in enumerate(st.session_state.chapter_order):
            ct=st.session_state.chapters.get(ch,"")
            c1,c2,c3=st.columns([5,1,1])
            with c1: st.markdown(f"""<div class="chapter-item"><div class="chapter-icon">{i+1}</div>
<div class="chapter-info"><div class="chapter-name">{ch}</div><div class="chapter-meta">{len(ct):,}字</div></div></div>""", unsafe_allow_html=True)
            with c2:
                if st.button("👁️",key=f"v{i}",help="看"):
                    st.session_state[f"e{i}"]=not st.session_state.get(f"e{i}",False)
            with c3:
                if st.button("🗑️",key=f"d{i}",help="删"): remove_chapter(ch); st.rerun()
            if st.session_state.get(f"e{i}"):
                with st.expander(f"📖 {ch}",expanded=True): st.text_area("",ct,height=200,disabled=True,key=f"p{i}")
    else:
        st.markdown("""<div class="empty-state"><div class="empty-icon">📚</div><div class="empty-text">暂无</div></div>""", unsafe_allow_html=True)

# ============================================================
# 步骤二
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">🔍</span><span class="card-title">步骤二：全局提炼</span>
<span class="card-subtitle">角色驱动卡 · 情节 · 视觉</span></div></div>""", unsafe_allow_html=True)

s2a,s2b=st.columns([1,1])
with s2a:
    if st.session_state.chapter_order:
        sc=st.multiselect("选择章节",st.session_state.chapter_order,default=st.session_state.chapter_order,key="sc",label_visibility="collapsed")
        st.session_state.selected_chapters_for_analysis=sc
        if sc: st.info(f"📊 {len(sc)}章 · {sum(len(st.session_state.chapters.get(c,'')) for c in sc):,}字")
        b1,b2=st.columns(2)
        with b1: da=st.button("🚀 提炼",key="da",use_container_width=True,type="primary",disabled=not(sc and st.session_state.api_key))
        with b2:
            if st.session_state.global_analysis:
                if st.button("🔄 重做",key="rd",use_container_width=True): st.session_state.global_analysis=""; st.rerun()
    else: st.info("💡 先导入"); da=False

with s2b:
    st.markdown("**结果**")
    if da:
        t=get_combined_text(sc); ms=[{"role":"user","content":build_analysis_prompt(t)}]
        with st.spinner("🧠 分析中..."):
            r=call_api_streaming(ms)
            if r:
                co=st.empty(); f=stream_to_container(r,co)
                if f:
                    st.session_state.global_analysis=f
                    st.session_state.messages=ms+[{"role":"assistant","content":f}]
                    st.session_state.current_step=max(st.session_state.current_step,1)
                    st.success("✅ 完成！")
    elif st.session_state.global_analysis:
        with st.expander("📋 查看",expanded=False): st.markdown(st.session_state.global_analysis)
        st.markdown('<span class="tag tag-green">✅ 完成</span>',unsafe_allow_html=True)
    else:
        st.markdown("""<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">等待</div></div>""",unsafe_allow_html=True)

# ============================================================
# 步骤三
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">🎬</span><span class="card-title">步骤三：编剧控制台</span>
<span class="card-subtitle">开场→生成→质检→优化</span></div></div>""", unsafe_allow_html=True)

t1,t2,t3=st.columns([1,2,3])
with t1:
    en=st.number_input("集",1,200,st.session_state.current_episode,key="ei")
    st.session_state.current_episode=en
with t2:
    ec=st.multiselect("章节",st.session_state.chapter_order,key="ec",help="本集参考")
with t3:
    ad=bool(st.session_state.global_analysis)
    tag_status = "<span class='tag tag-green'>✅</span>" if ad else "<span class='tag tag-yellow'>⚠️</span>"
    st.markdown(
        f'<div style="display:flex;gap:8px;padding-top:24px;flex-wrap:wrap;">'
        f'<span class="tag tag-blue">第{en}集</span>'
        f'<span class="tag tag-purple">{get_active_model()}</span>'
        f'{tag_status}</div>',
        unsafe_allow_html=True
    )

# ─── 上集衔接区 ───
auto_last_shot = ""
prev_ep = en - 1
if prev_ep > 0 and prev_ep in st.session_state.episodes:
    auto_last_shot = extract_last_shot(st.session_state.episodes[prev_ep])

with st.expander(f"🔗 上集衔接（第{prev_ep}集 → 第{en}集）", expanded=bool(auto_last_shot)):
    if auto_last_shot:
        st.caption(f"✅ 已自动提取第{prev_ep}集最后一个分镜，你可以编辑或清空")
    else:
        st.caption("💡 留空 = 第一集或新篇章开始，不需要衔接上集")
    last_shot_input = st.text_area(
        "上集末尾分镜内容",
        value=auto_last_shot,
        height=120,
        key="last_shot_input",
        placeholder="粘贴上一集最后一个分镜的内容...\n留空则视为新篇章开头，不做衔接。",
        help="系统会自动提取已生成的上一集末尾分镜。你也可以手动粘贴外部剧本的末尾内容。"
    )
<span class="tag tag-blue">第{en}集</span><span class="tag tag-purple">{get_active_model()}</span>
{"<span class='tag tag-green'>✅提炼</span>" if ad else "<span class='tag tag-yellow'>⚠️未提炼</span>"}</div>""",unsafe_allow_html=True)

bc=st.columns(7)
bd=[("🎯","设计开场"),("🎬","生成剧本"),("🔍","质量检查"),("💬","优化台词"),("🎨","优化画面"),("❤️","优化情绪"),("📦","批量生成")]
bt={}
for i,(ic,lb) in enumerate(bd):
    with bc[i]: bt[lb]=st.button(f"{ic} {lb}",key=f"b_{lb}",use_container_width=True,type="primary" if lb=="生成剧本" else "secondary")

# ============================================================
# 主Tabs
# ============================================================
mt=st.tabs(["📝 剧本","🔍 质检","🎯 开场","💬 对话","📊 总览"])

with mt[0]:
    if bt["设计开场"]:
        if not ad: st.warning("⚠️ 先提炼")
        else:
            ms=st.session_state.messages+[{"role":"user","content":build_opening_prompt()}]
            with st.spinner("🎯..."): 
                r=call_api_streaming(ms)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.opening_designs=f; st.session_state.messages=ms+[{"role":"assistant","content":f}]; st.session_state.current_step=max(st.session_state.current_step,2); st.success("✅")

    if bt["生成剧本"]:
        if not ad: st.warning("⚠️ 先提炼")
        else:
            tx=get_combined_text(ec if ec else None); op=st.session_state.get("selected_opening","")
            last_shot = st.session_state.get("last_shot_input", "")  # 读取衔接框内容
pr=build_episode_prompt(en, tx, op, last_shot); cx=st.session_state.messages+[{"role":"user","content":pr}]
            with st.spinner(f"🎬 第{en}集..."):
                r=call_api_streaming(cx)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.episodes[en]=f; st.session_state.messages=cx+[{"role":"assistant","content":f}]; st.session_state.current_step=max(st.session_state.current_step,3); st.session_state.memory["progress"]=str(en); st.success(f"✅ 第{en}集完成！")
                    else: st.warning("⚠️ 空")

    if bt["批量生成"]:
        if not ad: st.warning("⚠️")
        else:
            b1,b2=st.columns(2)
            with b1: bs=st.number_input("起始",1,200,en,key="bs")
            with b2: be=st.number_input("结束",1,200,min(en+2,200),key="be")
            if st.button("🚀 开始",key="bg",type="primary"):
                tx=get_combined_text(ec if ec else None)
                for e in range(int(bs),int(be)+1):
                    st.markdown(f"---\n### 🎬 第{e}集")
                    # 批量生成时，自动从上一集提取衔接
batch_last_shot = ""
if e > 1 and (e-1) in st.session_state.episodes:
    batch_last_shot = extract_last_shot(st.session_state.episodes[e-1])
cx=st.session_state.messages+[{"role":"user","content":build_episode_prompt(e, tx, "", batch_last_shot)}]
                    r=call_api_streaming(cx)
                    if r:
                        co=st.empty();f=stream_to_container(r,co)
                        if f: st.session_state.episodes[e]=f; st.session_state.messages=cx+[{"role":"assistant","content":f}]; st.session_state.memory["progress"]=str(e); st.success(f"✅ 第{e}集")
                        else: st.warning(f"⚠️ 第{e}集空"); break
                    else: st.error(f"❌ 第{e}集失败"); break

    if bt["优化台词"]:
        if en in st.session_state.episodes:
            pr=build_dialogue_optimization_prompt(en,st.session_state.episodes[en],st.session_state.global_analysis)
            ms=st.session_state.messages+[{"role":"user","content":pr}]
            with st.spinner("💬 角色DNA台词优化..."):
                r=call_api_streaming(ms)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.episodes[en]=f; st.session_state.messages=ms+[{"role":"assistant","content":f}]; st.success("✅ 台词优化完成（角色DNA驱动）")
        else: st.warning(f"⚠️ 第{en}集未生成")

    if bt["优化画面"]:
        if en in st.session_state.episodes:
            pr=build_visual_optimization_prompt(en,st.session_state.episodes[en])
            ms=st.session_state.messages+[{"role":"user","content":pr}]
            with st.spinner("🎨..."):
                r=call_api_streaming(ms)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.episodes[en]=f; st.session_state.messages=ms+[{"role":"assistant","content":f}]; st.success("✅ 画面优化完成")
        else: st.warning(f"⚠️ 第{en}集未生成")

    if bt["优化情绪"]:
        if en in st.session_state.episodes:
            pr=build_emotion_optimization_prompt(en,st.session_state.episodes[en])
            ms=st.session_state.messages+[{"role":"user","content":pr}]
            with st.spinner("❤️..."):
                r=call_api_streaming(ms)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.episodes[en]=f; st.session_state.messages=ms+[{"role":"assistant","content":f}]; st.success("✅ 情绪优化完成")
        else: st.warning(f"⚠️ 第{en}集未生成")

    st.markdown("---")
    if st.session_state.episodes:
        st.markdown("### 📜 已生成剧本")
        se=sorted(st.session_state.episodes.keys())
        et=st.tabs([f"第{e}集" for e in se])
        for ix,e in enumerate(se):
            with et[ix]:
                s=st.session_state.episodes[e]; sh=len(re.findall(r'【分镜\s*\d+】',s))
                m1,m2,m3,m4=st.columns(4)
                m1.metric("分镜",sh or "—"); m2.metric("时长",f"~{sh*12}s" if sh else "—")
                m3.metric("字数",f"{len(s):,}"); m4.metric("质检","✅" if e in st.session_state.review_results else "⏳")
                st.markdown(s)
                d1,d2=st.columns(2)
                with d1: st.download_button(f"📥 导出",s,f"第{e}集.md","text/markdown",key=f"dl{e}")
                with d2:
                    if st.button("📋 纯文本",key=f"cd{e}"): st.code(s,language="markdown")
    else:
        st.markdown("""<div class="empty-state"><div class="empty-icon">&#128230;</div><div class="empty-text">尚未生成</div></div>""",unsafe_allow_html=True)

with mt[1]:
    if bt["质量检查"]:
        if en not in st.session_state.episodes: st.warning(f"⚠️第{en}集未生成")
        else:
            tx=get_combined_text(ec if ec else None); sc=st.session_state.episodes[en]
            rm=[{"role":"user","content":build_review_prompt(en,sc,tx)}]
            og=st.session_state.model_id
            if st.session_state.review_model: st.session_state.model_id=st.session_state.review_model
            with st.spinner(f"🔍质检第{en}集（12维度+5视角攻击）..."):
                r=call_api_streaming(rm,REVIEW_SYSTEM_PROMPT)
                if r:
                    co=st.empty();f=stream_to_container(r,co)
                    if f: st.session_state.review_results[en]=f; st.session_state.current_step=max(st.session_state.current_step,4); st.success(f"✅第{en}集质检完成")
            st.session_state.model_id=og

    if st.session_state.review_results:
        for e in sorted(st.session_state.review_results.keys()):
            rv=st.session_state.review_results[e]
            with st.expander(f"📊第{e}集质检（12维度+5视角）",expanded=(e==en)):
                st.markdown(rv)
                f1,f2,f3=st.columns(3)
                with f1:
                    if st.button(f"🔧自动修改",key=f"fx{e}",type="primary"):
                        fp=f"""根据质检报告修改第{e}集所有7分以下项+五个敌对视角指出的问题。

【修改格式强制要求】
1. 台词必须嵌入画面动作流
2. 每句台词前必须有情绪+表情+身体描写
3. 时长必须实算
4. 台词个性化（不能统一精简）
5. 针对五个敌对视角的攻击点逐一回应和修改

质检：\n{rv}\n原剧本：\n{st.session_state.episodes[e]}\n输出修改后完整剧本。"""
                        fm=st.session_state.messages+[{"role":"user","content":fp}]
                        with st.spinner("🔧..."):
                            r=call_api_streaming(fm)
                            if r:
                                co=st.empty();f=stream_to_container(r,co)
                                if f: st.session_state.episodes[e]=f; st.success(f"✅ 已修改")
                with f2: st.download_button("📥",rv,f"第{e}集_质检.md","text/markdown",key=f"dr{e}")
                with f3:
                    if st.button("🔄 重检",key=f"rr{e}"):
                        if e in st.session_state.review_results: del st.session_state.review_results[e]
                        st.rerun()
    else:
        st.markdown("""<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">暂无质检</div></div>""",unsafe_allow_html=True)

with mt[2]:
    if st.session_state.opening_designs:
        st.markdown("### 🎯 6套方案"); st.markdown(st.session_state.opening_designs); st.markdown("---")
        o1,o2=st.columns([3,1])
        with o1: ch=st.text_input("选择",placeholder="1-6或自定义",key="oc")
        with o2:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("✅",key="cf",use_container_width=True,type="primary"):
                if ch: st.session_state["selected_opening"]=ch; st.success(f"✅ {ch}")
    else:
        st.markdown("""<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-text">待设计</div></div>""",unsafe_allow_html=True)

with mt[3]:
    st.markdown("### 💬 自由对话")
    for mg in st.session_state.chat_history[-20:]:
        with st.chat_message(mg["role"]): st.markdown(mg["content"])
    ui=st.chat_input("输入...",key="ci")
    if ui:
        st.session_state.chat_history.append({"role":"user","content":ui})
        cx=""
        if st.session_state.global_analysis: cx+=f"\n【提炼】{st.session_state.global_analysis[:3000]}"
        if st.session_state.episodes:
            la=max(st.session_state.episodes.keys()); cx+=f"\n【第{la}集】{st.session_state.episodes[la][:2000]}"
        fm=f"背景：{cx}\n\n指令：{ui}" if cx else ui
        with st.chat_message("assistant"):
            r=call_api_streaming([{"role":"user","content":fm}])
            if r:
                co=st.empty();f=stream_to_container(r,co)
                if f: st.session_state.chat_history.append({"role":"assistant","content":f})

with mt[4]:
    st.markdown("### 📊 总览")
    o1,o2,o3,o4=st.columns(4)
    o1.metric("📚",len(st.session_state.chapter_order)); o2.metric("🎬",len(st.session_state.episodes))
    o3.metric("✅",len(st.session_state.review_results))
    o4.metric("📝",f"{sum(len(v) for v in st.session_state.episodes.values()):,}" if st.session_state.episodes else "0")
    st.markdown("---")
    if st.session_state.episodes:
        for e in sorted(st.session_state.episodes.keys()):
            s=st.session_state.episodes[e]; sh=len(re.findall(r'【分镜\s*\d+】',s))
            st.markdown(f"""<div class="chapter-item"><div class="chapter-icon" style="background:linear-gradient(135deg,#3182ce,#2b6cb0);">{e}</div>
<div class="chapter-info"><div class="chapter-name">第{e}集 <span class="tag tag-blue">{sh}镜</span> <span class="tag tag-green">~{sh*12}s</span></div>
<div class="chapter-meta">{len(s):,}字 · {"✅" if e in st.session_state.review_results else "⏳"}</div></div></div>""",unsafe_allow_html=True)
    st.markdown("---"); st.markdown("#### 📌 记忆（可编辑）")
    for lb,ky in [("主线","storyline"),("人物","characters"),("进度","progress"),("结尾","last_ending"),("伏笔","pending_foreshadow"),("引爆","next_foreshadow"),("情绪","emotion_track")]:
        nv=st.text_input(f"📌 {lb}",value=st.session_state.memory.get(ky,""),key=f"m_{ky}")
        st.session_state.memory[ky]=nv

st.markdown("---")
st.markdown(f"""<div style="text-align:center;padding:16px 0;"><span style="color:#a0aec0;font-size:0.75rem;">
🎬 影视化视觉翻译引擎 V3.2 · 台词嵌入画面流 · 实算时长 · 角色DNA · {get_active_model()}</span></div>""",unsafe_allow_html=True)
