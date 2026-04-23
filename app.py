import streamlit as st
import requests
import json
import re
import time

# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="短剧剧本生成器",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 白色简约 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    #MainMenu, footer, header { visibility: hidden; }

    .main-title { text-align: center; padding: 2rem 0 0.5rem 0; }
    .main-title h1 { font-size: 2.2rem; font-weight: 700; color: #111111; letter-spacing: 0.03em; margin-bottom: 0.2rem; }
    .main-title p { color: #888888; font-size: 0.95rem; margin-top: 0; }

    .divider { border: none; border-top: 1px solid #eeeeee; margin: 1.5rem 0; }
    .section-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #999999; margin-bottom: 0.6rem; font-weight: 600; }

    /* 输入控件 */
    .stTextArea label, .stTextInput label,
    .stSelectbox label, .stFileUploader label { color: #444444 !important; font-size: 0.88rem !important; font-weight: 500 !important; }
    .stTextArea textarea { background-color: #fafafa !important; color: #1a1a1a !important; border: 1px solid #e0e0e0 !important; border-radius: 8px !important; font-size: 0.88rem !important; }
    .stTextArea textarea:focus { border-color: #aaaaaa !important; box-shadow: none !important; }
    .stTextInput input { background-color: #fafafa !important; color: #1a1a1a !important; border: 1px solid #e0e0e0 !important; border-radius: 8px !important; }
    .stTextInput input:focus { border-color: #aaaaaa !important; box-shadow: none !important; }
    .stSelectbox > div > div { background-color: #fafafa !important; border: 1px solid #e0e0e0 !important; color: #1a1a1a !important; border-radius: 8px !important; }
    .stFileUploader > div { background-color: #fafafa !important; border: 1px dashed #dddddd !important; border-radius: 8px !important; }

    /* 按钮 */
    .stButton > button { background-color: #111111 !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; padding: 0.6rem 2rem !important; font-weight: 600 !important; font-size: 1rem !important; width: 100% !important; transition: opacity 0.2s ease !important; }
    .stButton > button:hover { opacity: 0.8 !important; }
    .stButton > button:disabled { opacity: 0.3 !important; }

    /* 提示框 */
    .info-box { background-color: #f7f7f7; border: 1px solid #e8e8e8; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0; font-size: 0.87rem; color: #666666; line-height: 1.6; }
    .success-box { background-color: #f0faf0; border: 1px solid #c3e6c3; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0; font-size: 0.87rem; color: #2d7a2d; }
    .error-box { background-color: #fff5f5; border: 1px solid #f5c6c6; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0; font-size: 0.87rem; color: #c0392b; }
    .warning-box { background-color: #fffbf0; border: 1px solid #f0e0a0; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0; font-size: 0.87rem; color: #8a6d00; }

    /* 章节头 */
    .chapter-header { background-color: #f4f4f8; border-left: 3px solid #555588; border-radius: 0 8px 8px 0; padding: 0.7rem 1.1rem; margin: 1.2rem 0 0.4rem 0; font-size: 0.88rem; color: #333366; font-weight: 600; }

    /* 剧本输出 */
    .screenplay-output { background-color: #fafafa; border: 1px solid #e8e8e8; border-radius: 10px; padding: 1.4rem 1.8rem; font-family: 'Courier New', monospace; font-size: 0.87rem; line-height: 1.9; color: #222222; white-space: pre-wrap; word-wrap: break-word; margin-bottom: 0.8rem; }

    /* 衔接摘要 */
    .context-box { background-color: #f0f8f0; border: 1px solid #c8e8c8; border-radius: 8px; padding: 0.8rem 1.1rem; margin: 0.4rem 0; font-size: 0.82rem; color: #2d6a2d; line-height: 1.6; font-style: italic; }

    /* 自检报告 */
    .review-header { background-color: #fff8f0; border-left: 3px solid #e08030; border-radius: 0 8px 8px 0; padding: 0.7rem 1.1rem; margin: 1.2rem 0 0.4rem 0; font-size: 0.88rem; color: #804010; font-weight: 600; }
    .review-output { background-color: #fff8f0; border: 1px solid #f0d8b0; border-radius: 10px; padding: 1.4rem 1.8rem; font-size: 0.87rem; line-height: 1.9; color: #2a1a0a; white-space: pre-wrap; word-wrap: break-word; margin-bottom: 0.8rem; }
    .review-pass { background-color: #f0faf0; border: 1px solid #c3e6c3; border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0; font-size: 0.87rem; color: #2d7a2d; }

    .word-count { font-size: 0.78rem; color: #aaaaaa; text-align: right; margin-top: 0.3rem; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #f4f4f4; border-radius: 8px; padding: 0.2rem; gap: 0.2rem; }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; color: #888888 !important; border-radius: 6px !important; padding: 0.4rem 1rem !important; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; color: #111111 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important; }

    /* 进度条 */
    .stProgress > div > div > div { background-color: #333333 !important; }

    /* Expander */
    .streamlit-expanderHeader { background-color: #f7f7f7 !important; color: #444444 !important; border-radius: 8px !important; border: 1px solid #e8e8e8 !important; }

    /* 下载按钮特殊样式 */
    .stDownloadButton > button { background-color: #f0f0f0 !important; color: #333333 !important; border: 1px solid #dddddd !important; }
    .stDownloadButton > button:hover { background-color: #e4e4e4 !important; }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #f4f4f4; }
    ::-webkit-scrollbar-thumb { background: #cccccc; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# System Prompt（规则 + Few-shot 示例）
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """你是"短剧改编编剧"，任务是把输入小说改编为可拍摄、节奏有效、人物鲜明的短剧剧本。

====================
一、总目标（必须同时满足）
====================
1) 忠于原著：不新增关键剧情，不改因果，不改人物核心性格。
2) 影视化：不是复述小说，而是转成可拍画面与有效对白。
3) 逻辑清晰：人物问答有对应，事件衔接丝滑，观众能跟上。
4) 情绪有效：能调动情绪，但不刻意拉扯同一情绪包袱。
5) 实用输出：格式简洁，便于直接进入拍摄拆解。

====================
二、优先级（冲突时按此顺序）
====================
P1. 原著事件与因果完整
P2. 人物性格一致 + 对话逻辑成立
P3. 影视可拍性（能拍出来）
P4. 节奏与情绪张力
P5. 文采修饰

====================
三、影视化优化规则
====================
A. 可拍转化
- 心理描写 → 动作/表情/停顿/视线/手部反应/内心OS
- 设定信息 → 场景细节或人物互动中自然带出
- 异能/特殊能力 → 明确可视效果（出现方式、反应、后果）

B. 互动转化
- 不允许单人独角戏长期霸屏
- 任一关键动作后，要有他人反应或关系变化反馈

C. 推进转化（每段必须完成至少一个）
- 推剧情 / 推关系 / 推人物性格 / 推悬念
- 纯重复、纯解释同一信息 → 删

====================
四、点到为止规则
====================
1) 同一个情绪点/信息点，只推进一次，不反复讲解。
2) 台词可以长，但每句都要有新信息或新立场，不得原地打转。
3) 情绪可以强，但不能靠重复同义句堆时长。
4) 包袱抖出后尽快进入后续行动或关系变化。

====================
五、对白规则
====================
1) 对白先服务逻辑，再服务风格。
2) 问与答必须有逻辑对应（正面回答/回避/反问/打断，但都要推动）。
3) 角色"说什么"不能脱离原著信息边界。
4) 角色"怎么说"体现性格差异（语气、节奏、措辞）。
5) 禁止把同一句"模板腔"分配给所有角色。

====================
六、人物存在感规则
====================
1) 关键角色每次出场都要有"可识别行为"或"可识别表达"。
2) 内心OS只在必要处使用，补充角色立场，不解释画面废话。
3) 角色连续仅"站着看"且无功能 → 判定工具人，必须改写。

====================
七、输出格式（严格执行）
====================
仅使用以下形式：

【场景：地点｜时间（白天/夜晚）】
正文段落...

规则：
1) 只有场景变化时才写新的【场景】头。
2) 不要写：片段编号、分镜、镜头、秒数、机位术语。
3) 每个自然段是一个完整"可拍单元"（动作/对白/结果，至少两项）。
4) 描述简洁具体，避免空泛形容词堆砌。

以下情况禁止新开场景标签，应视为同一场景的连续叙事：
- 同一地点内的人物对话延续（即使换了发言人）
- 同一地点内的动作承接（前一段的结果直接引发后一段）
- 仅因为段落自然分行而非物理空间发生变化
- 在一个大空间（如厂房、大厅）内从一个角落走到另一个角落

判断标准：只有当主要人物离开当前物理空间、进入另一个完全不同的地点，或者时间发生跳跃时，才允许新开场景标签。同一空间内的子区域（"就餐区"、"休息角落"）不构成独立场景。

====================
八、强制自检（输出前逐项确认）
====================
1) 是否新增原著没有的关键剧情？（Fail即重写）
2) 是否改变原著因果或角色动机？（Fail即重写）
3) 是否存在"问非所答且无意图"的对白？（Fail即重写）
4) 是否存在工具人角色？（Fail即重写）
5) 是否存在不可拍描述？（Fail即重写）
6) 是否存在同一信息重复解释三次以上？（Fail即重写）
7) 场景切换是否清楚且衔接自然？（Fail即重写）
8) 每段是否具备推进结构？（Fail即重写）

====================
九、输出结构（每次处理完一章必须输出以下两部分）
====================
第一部分：剧本正文（按七的格式）

【强制要求】每章剧本必须输出完整的第二部分简报，包括衔接摘要，缺少任何一段标记将导致下一章无法正确衔接。
第二部分：在剧本末尾输出以下简报，格式严格如下：

---【剧本简报】---
原著保真：列出未改动的关键事件点
影视化优化：列出3-5个有效优化点
逻辑保障：列出3处关键问答或衔接如何成立
---【衔接摘要】---
场景位置：本章结束时，主要人物所处地点
人物状态：每个主要角色当前的情绪/处境/目标
关系变化：本章发生的关键关系变化
未解悬念：本章结束时仍悬而未决的钩子
---【摘要结束】---

====================
十、Few-shot 示例（严格对齐此格式输出）
====================

【剧本输出示例】
场景：拍卖会场｜夜晚
拍卖师掀开红布。展台上的寒玉在射灯下泛着青白色光泽。
林初雪站在后排第三列，手里攥着一张支票，指节发白。她看清展台上的东西，身体往前倾了一下，嘴唇动了动没出声。
拍卖师敲槌：千年寒玉，起拍一百万。
前排男人举牌：一百五十万。左侧女宾客跟着：两百万。
林初雪把支票翻过来看背面数字，又翻回去，咬住下唇。

场景：拍卖会场二楼包厢｜夜晚
黑袍男人坐在栏后椅子上，手指敲了两下扶手，对侍从点头。
侍从推开纱帘，朝楼下喊：一千万。

场景：拍卖会场｜夜晚
叫价声停住。前排男人把号牌放下，转头看向二楼。左侧两名女宾客凑近低声说话。后排有人举起手机对准包厢方向。
拍卖师握槌的手停在半空，回过神，举槌：一千万一次——
林初雪冲到台前，手按在展台边缘：等等！
拍卖师收回木槌，皱眉看她。台下有人站起来看热闹。
林初雪深吸一口气：这块玉是我母亲的遗物。
拍卖师脸色一冷：小姐，拍卖会讲证据。你拿什么证明？
林初雪把支票拍在台面上：我先不加价。我先证明它认我。
拍卖师看向二楼，没接话。

场景：拍卖会场二楼栏边｜夜晚
包厢门打开，黑袍男人走到栏杆边，双手撑在栏杆上俯视她：可以。你证明。

场景：拍卖会场展台｜夜晚
林初雪双手按在展台玻璃上，闭眼，肩膀绷紧。呼吸放慢，手掌下的玻璃表面开始起雾。
雾气蔓延到展台四角，边缘凝出白霜。寒玉内部亮起淡蓝光，一层层增强。
前排酒杯表面结出细小冰晶。前排宾客往后退，椅子拖动声响成一片。拍卖师手一松，木槌掉在地上。
林初雪睁眼，脸色发白，额头全是汗，手撑着台面才站稳，抬头看向二楼：够不够？

场景：拍卖会场二楼栏边｜夜晚
黑袍男人盯着寒玉看了三秒，直起身：认主现象成立。
他转向林初雪：但拍卖流程已启动，规则不变。一千万，你继续出价。

场景：拍卖会场展台｜夜晚
林初雪把支票推到拍卖师面前。拍卖师低头看一眼，抬起头：五十万。
台下有人笑出声，有人摇头。
林初雪抬头盯住二楼黑袍男人，声音发紧：你到底想要什么？
黑袍男人转身往包厢里走，停在门口侧过头：明晚子时，城北废宅。你一个人来，寒玉的事继续谈。
他推开门：迟到作废。
包厢门合上。林初雪把支票收回袖子里，转身离开展台。宾客们盯着她背影议论。

---【剧本简报】---
原著保真：拍卖会见到母亲遗物寒玉、无力竞拍、神秘男人出天价压场、被迫当场证明认主、灵力觉醒引发冰晶异象、对方以规则压制并抛出约见条件。
影视化优化：心理描写改为手部动作和呼吸变化；灵力觉醒具象为起雾到结霜到发光到周围结冰晶的递进视觉链；群体反应拆解为个体可拍动作；删除所有重复心理独白；黑袍男人通过侍从喊价体现身份层级。
逻辑保障：你有证据转为我先证明形成挑战应战；够不够转为认主成立给出判定；规则不变转为五十万被读出推进到价格僵局并触发台下反应；你想要什么转为明晚城北废宅抛出明确后续钩子。
---【衔接摘要】---
场景位置：拍卖会场展台（林初雪），城北废宅（尚未抵达，为下章铺垫地点）
人物状态：林初雪——灵力耗尽、手持五十万支票、母亲遗物未能赎回，目标是明晚赴约；黑袍男人——身份未明、掌握主动权、对林初雪展现出超出常规的兴趣
关系变化：双方从陌生人转为有条件接触关系，主动权在黑袍男人一侧
未解悬念：寒玉为何会出现在拍卖会？黑袍男人真实目的是什么？林初雪是否会独自赴约？
---【摘要结束】---"""


# ─────────────────────────────────────────────
# 自检 Prompt
# ─────────────────────────────────────────────
REVIEW_PROMPT = """你是一个由三位专业人士组成的剧本审核与修订团队，分别代表：
- 专业编辑（叙事逻辑、台词质量、信息传递）
- 专业导演（画面可拍性、场景调度、节奏控制）
- 专业动作指导（肢体动作合理性、动作与情绪匹配、物理可执行性）

你的任务是对以下短剧剧本进行专业审核，并直接输出修订后的完整剧本正文。

====================
审核三大维度
====================

【维度一：动作描述审核】（动作指导视角）
检查标准：
- 动作是否物理上可执行（演员能实际做到）
- 动作与角色当前情绪/处境是否匹配
- 动作是否过于模糊（如"他做了个动作"）或过于文学化（如"他的手仿佛承载了千年的重量"）
- 连续动作之间是否有逻辑衔接

【维度二：画面描述审核】（导演视角）
检查标准：
- 画面是否真实可拍（不依赖后期特效且无说明的情况下）
- 场景切换是否清晰，观众能否跟上空间变化
- 场景标签是否被滥用为分段工具——只有主要人物离开当前物理空间、进入另一个完全不同的地点，或时间发生跳跃时，才允许新开场景标签；同一空间内的子区域（如"就餐区"、"休息角落"）不构成独立场景，应合并为同一场景标签下的连续叙事
- 群体场景中的调度是否合理（多人同时出现时，每人位置/行为是否清楚）
- 视觉信息是否冗余或缺失关键画面

【维度三：台词描述审核】（编辑视角）
检查标准：
- 台词是否符合角色身份和当前处境
- 台词是否与角色的物理/生理设定冲突（例如：已明确无心跳的角色不得出现"心跳加速"；已明确无法流泪的角色不得出现"泪流满面"）
- 问答逻辑是否成立（包括回避、反问等非直接回答形式）
- 是否存在"说教腔"（角色解释自己的动机/感受给观众听，而非对话对象）
- 台词节奏是否与场景张力匹配

====================
审核原则（重要）
====================
1. 每次指出问题必须结合上下剧情内容——不能孤立看待一句台词或一个动作，要考虑它在整个章节叙事中的功能。
2. 如果某个描述单独看来奇怪，但在上下文中有合理功能，则判定为合理，不提出修改。
3. 修改必须精准、克制——不能大幅改写，只针对具体问题给出最小修改。
4. 如果某个维度没有问题，直接写"本维度无明显问题"，不要凑字数。
5. 【重要】喜剧性的"等待—落差—爆发"结构、章节结尾的情绪钩子、角色情绪从积累到爆发的完整弧线，不得在修订中被压缩或合并，必须在修订正文中完整保留其节奏。

====================
输出格式（严格执行，共三部分）
====================

## 剧本自检与修订报告

**整体判断：**
（一句话总结整体质量，并说明本次修订的主要方向）

---

### 问题清单（修订前）

按三个维度列出所有发现的问题，每条格式如下：
- 【维度名称】【位置：场景名称，段落开头引用不超过15字】
  - 问题：具体描述问题是什么
  - 修订依据：结合前后情节说明为何需要修改

（如某维度无问题，写"本维度无明显问题"）

---

### 修订后完整剧本正文

【重要执行要求】
- 在此输出经过所有修订后的完整剧本正文
- 格式严格使用【场景：地点｜时间】，禁止出现任何Markdown符号（###、---、**、*等）
- 所有已发现问题均已在正文中直接修正，不再单独列出修改建议
- 未发现问题的段落原文保留，不得随意改动
- 剧本简报、衔接摘要部分原文保留，不做修改

（在此输出完整修订正文）

---

### 修订说明

（用3-5句话说明本次具体改动了哪些位置、改动内容是什么，以及改动的核心依据，便于核查对比）"""


# ─────────────────────────────────────────────
# 章节分割
# ─────────────────────────────────────────────
def split_into_chapters(text: str) -> list:
    chapter_title_re = re.compile(
        r'(?m)^(第\s*[\d零一二三四五六七八九十百千]+\s*[章回节集部][^\n]{0,30})$',
        re.IGNORECASE
    )

    positions = []
    for m in chapter_title_re.finditer(text):
        positions.append((m.start(), m.end(), m.group(1).strip()))

    chapters = []

    if len(positions) >= 1:
        # 章节标题前如果有内容，作为序章
        pre_content = text[:positions[0][0]].strip()
        if pre_content:
            chapters.append({
                "title": "序章 / 前言",
                "content": pre_content,
                "index": 0
            })

        for i, (start, end, title) in enumerate(positions):
            # 正文从标题行结束到下一个标题开始
            content_start = end
            content_end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            content = text[content_start:content_end].strip()
            if content:
                chapters.append({
                    "title": title,
                    "content": content,
                    "index": len(chapters)
                })
    else:
        # 没有识别到章节标题，按2000字分块
        chunk_size = 2000
        total_len = len(text)
        chunk_index = 0
        pos = 0
        while pos < total_len:
            end = min(pos + chunk_size, total_len)
            if end < total_len:
                newline_pos = text.rfind('\n', pos, end)
                if newline_pos > pos + chunk_size // 2:
                    end = newline_pos
            chunk = text[pos:end].strip()
            if chunk:
                chapters.append({
                    "title": "第 {} 段".format(chunk_index + 1),
                    "content": chunk,
                    "index": chunk_index
                })
                chunk_index += 1
            pos = end

    # 重新编排index
    for i, ch in enumerate(chapters):
        ch["index"] = i

    return chapters


# ─────────────────────────────────────────────
# 提取衔接摘要
# ─────────────────────────────────────────────
def extract_context_summary(screenplay_text: str) -> str:
    match = re.search(
        r'---【衔接摘要】---([\s\S]*?)---【摘要结束】---',
        screenplay_text
    )
    if match:
        return match.group(1).strip()
    return ""


# ─────────────────────────────────────────────
# 构造 User Prompt
# ─────────────────────────────────────────────
def build_user_prompt(chapter: dict, total_chapters: int, prev_context: str) -> str:
    is_first = chapter["index"] == 0
    is_last = chapter["index"] == total_chapters - 1

    if is_first and is_last:
        position_note = "（这是全文唯一章节）"
    elif is_first:
        position_note = "（这是第 1 章，共 {} 章，是开篇章节）".format(total_chapters)
    elif is_last:
        position_note = "（这是第 {} 章，共 {} 章，是结尾章节）".format(
            chapter["index"] + 1, total_chapters
        )
    else:
        position_note = "（这是第 {} 章，共 {} 章）".format(
            chapter["index"] + 1, total_chapters
        )

    context_block = ""
    if prev_context:
        context_block = (
            "【前章衔接信息（必须在本章开头自然延续，不得重复描述前章内容）】\n"
            "{}\n\n".format(prev_context)
        )

    prompt = (
        "{}请将以下小说原文改编为短剧剧本 {}：\n\n"
        "章节标题：{}\n\n"
        "原文内容：\n{}\n\n"
        "要求：\n"
        "1. 严格按照系统提示词中的格式输出剧本正文，再输出剧本简报和衔接摘要。\n"
        "2. 【格式要求】只使用【场景：地点｜时间】作为场景头，禁止在剧本正文中出现任何Markdown符号（###、---、**、*等），禁止重复出现章节标题行。\n"
        "3. 【示例说明】系统提示词中的【原文输入】部分是小说原文示例，【剧本输出示例】部分才是你应输出的格式，请严格对齐【剧本输出示例】的格式，不要模仿【原文输入】的叙述风格。\n"
        "4. 若有前章衔接信息，本章第一个场景需自然承接前章结尾状态（人物位置/情绪/悬念），但不重复描述前章已发生的事。\n"
        "5. 衔接摘要中的未解悬念必须包含本章新产生的悬念钩子。"
    ).format(
        context_block,
        position_note,
        chapter["title"],
        chapter["content"]
    )

    return prompt


# ─────────────────────────────────────────────
# 流式 API 调用
# ─────────────────────────────────────────────
def call_api_stream(messages: list, api_key: str, api_base: str, model: str):
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": "Bearer {}".format(api_key),
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "stream": True,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8000,
    }

    with requests.post(
        url, headers=headers, json=payload, stream=True, timeout=180
    ) as resp:
        if resp.status_code != 200:
            error_detail = resp.text[:400]
            raise RuntimeError(
                "API 请求失败（{}）：{}".format(resp.status_code, error_detail)
            )
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"]
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


# ─────────────────────────────────────────────
# 模型列表
# ─────────────────────────────────────────────
PRESET_MODELS = [
    "自定义模型...",
]

# ─────────────────────────────────────────────
# Session State 初始化
# ─────────────────────────────────────────────
defaults = {
    "all_results": [],
    "generating": False,
    "reviewing": False,
    "chapters": [],
    "prev_context": "",
    "review_results": [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────
# 页面主体
# ─────────────────────────────────────────────
st.markdown(
    '<div class="main-title">'
    '<h1>🎬 短剧剧本生成器</h1>'
    '<p>上传或粘贴小说原文，自动按章节分批生成可拍摄短剧剧本，并提供专业三维度自检</p>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── API 配置 ─────────────────────────────────
with st.expander("⚙️  API 配置", expanded=True):
    col_key, col_base = st.columns([1, 1])
    with col_key:
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-xxxxxxxxxxxxxxxx",
            help="您的 API 密钥，不会被存储",
        )
    with col_base:
        api_base = st.text_input(
            "接口地址（Base URL）",
            value="https://yunwu.ai/v1",
            placeholder="https://yunwu.ai/v1",
        )

    col_model, col_custom = st.columns([1, 1])
    with col_model:
        model_choice = st.selectbox("Model ID", options=PRESET_MODELS, index=0)
    with col_custom:
        if model_choice == "自定义模型...":
            custom_model = st.text_input(
                "输入自定义模型名称",
                placeholder="例如：gpt-4o-2024-11-20",
            )
        else:
            st.text_input("当前选用模型", value=model_choice, disabled=True)
            custom_model = ""

final_model = custom_model if model_choice == "自定义模型..." else model_choice

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 输入原文 ─────────────────────────────────
st.markdown('<div class="section-label">小说原文输入</div>', unsafe_allow_html=True)
input_tab1, input_tab2 = st.tabs(["📄  上传文件", "✏️  粘贴文本"])
novel_text = ""

with input_tab1:
    uploaded_file = st.file_uploader(
        "选择 .txt 文件",
        type=["txt"],
        help="支持 UTF-8 或 GBK 编码，可包含多个章节",
    )
    if uploaded_file is not None:
        try:
            raw = uploaded_file.read()
            try:
                novel_text = raw.decode("utf-8")
            except UnicodeDecodeError:
                novel_text = raw.decode("gbk", errors="replace")
            st.markdown(
                '<div class="success-box">文件加载成功：{} （{:,} 字符）</div>'.format(
                    uploaded_file.name, len(novel_text)
                ),
                unsafe_allow_html=True,
            )
            with st.expander("预览文件内容（前 300 字）"):
                st.text(novel_text[:300] + ("..." if len(novel_text) > 300 else ""))
        except Exception as e:
            st.markdown(
                '<div class="error-box">文件读取失败：{}</div>'.format(str(e)),
                unsafe_allow_html=True,
            )

with input_tab2:
    placeholder_text = (
        "将小说文本粘贴至此处...\n\n"
        "支持多章节内容，识别章节标题自动分章。\n"
        "单次支持 10000 字以上，系统将自动分块处理。"
    )
    pasted_text = st.text_area(
        "在此粘贴小说原文",
        height=300,
        placeholder=placeholder_text,
        label_visibility="collapsed",
    )
    if pasted_text.strip():
        novel_text = pasted_text
        st.markdown(
            '<div class="word-count">{:,} 字符</div>'.format(len(pasted_text)),
            unsafe_allow_html=True,
        )

# ── 章节预览 ─────────────────────────────────
if novel_text.strip():
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    chapters_preview = split_into_chapters(novel_text)
    st.markdown('<div class="section-label">章节识别结果</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">共识别到 <strong>{}</strong> 个章节 / 分块，'
        '将按序逐章处理，每章独立生成剧本并自动传递衔接信息。</div>'.format(
            len(chapters_preview)
        ),
        unsafe_allow_html=True,
    )
    with st.expander("查看章节列表（{}个）".format(len(chapters_preview))):
        for i, ch in enumerate(chapters_preview):
            st.write("**{}.** {} — {:,} 字符".format(i + 1, ch["title"], len(ch["content"])))

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 生成按钮 ─────────────────────────────────
can_generate = (
    bool(api_key.strip())
    and bool(novel_text.strip())
    and bool(final_model.strip())
)

hints = []
if not api_key.strip():
    hints.append("请填写 API Key")
if not novel_text.strip():
    hints.append("请上传文件或粘贴小说原文")
if not final_model.strip():
    hints.append("请输入自定义模型名称")
if hints:
    st.markdown(
        '<div class="info-box">💡 {}</div>'.format(" &nbsp;|&nbsp; ".join(hints)),
        unsafe_allow_html=True,
    )

generate_btn = st.button(
    "🎬  开始生成剧本",
    disabled=not can_generate or st.session_state.generating,
    use_container_width=True,
)

# ─────────────────────────────────────────────
# 生成主流程
# ─────────────────────────────────────────────
if generate_btn and can_generate:
    st.session_state.generating = True
    st.session_state.all_results = []
    st.session_state.review_results = []
    st.session_state.prev_context = ""

    chapters = split_into_chapters(novel_text)
    st.session_state.chapters = chapters
    total = len(chapters)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">生成进度</div>', unsafe_allow_html=True)

    overall_progress = st.progress(0)
    overall_status = st.empty()
    results_container = st.container()
    error_occurred = False

    for ch_idx, chapter in enumerate(chapters):
        overall_progress.progress(ch_idx / total)
        overall_status.markdown(
            '<div class="info-box">⏳ 正在处理第 {} / {} 章：{}</div>'.format(
                ch_idx + 1, total, chapter["title"]
            ),
            unsafe_allow_html=True,
        )

        with results_container:
            st.markdown(
                '<div class="chapter-header">📖 第 {} 章：{}</div>'.format(
                    ch_idx + 1, chapter["title"]
                ),
                unsafe_allow_html=True,
            )

            if st.session_state.prev_context:
                display_ctx = st.session_state.prev_context.replace("\n", "<br>")
                st.markdown(
                    '<div class="context-box">🔗 衔接信息已传递：<br>{}</div>'.format(
                        display_ctx
                    ),
                    unsafe_allow_html=True,
                )

            chapter_output_placeholder = st.empty()
            chapter_full_text = ""

            user_prompt = build_user_prompt(
                chapter=chapter,
                total_chapters=total,
                prev_context=st.session_state.prev_context,
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            try:
                for chunk in call_api_stream(
                    messages=messages,
                    api_key=api_key.strip(),
                    api_base=api_base.strip(),
                    model=final_model.strip(),
                ):
                    chapter_full_text += chunk
                    chapter_output_placeholder.markdown(
                        '<div class="screenplay-output">{}</div>'.format(
                            chapter_full_text
                        ),
                        unsafe_allow_html=True,
                    )

                context = extract_context_summary(chapter_full_text)
                st.session_state.prev_context = context
                st.session_state.all_results.append({
                    "title": chapter["title"],
                    "content": chapter_full_text,
                })

                st.markdown(
                    '<div class="success-box">✓ 第 {} 章生成完成（{:,} 字符）</div>'.format(
                        ch_idx + 1, len(chapter_full_text)
                    ),
                    unsafe_allow_html=True,
                )

            except RuntimeError as e:
                error_occurred = True
                st.markdown(
                    '<div class="error-box">✗ 第 {} 章生成失败：{}</div>'.format(
                        ch_idx + 1, str(e)
                    ),
                    unsafe_allow_html=True,
                )
                break
            except requests.exceptions.ConnectionError:
                error_occurred = True
                st.markdown(
                    '<div class="error-box">✗ 网络连接失败，请检查接口地址</div>',
                    unsafe_allow_html=True,
                )
                break
            except requests.exceptions.Timeout:
                error_occurred = True
                st.markdown(
                    '<div class="error-box">✗ 请求超时（180秒），建议缩短单章内容后重试</div>',
                    unsafe_allow_html=True,
                )
                break
            except Exception as e:
                error_occurred = True
                st.markdown(
                    '<div class="error-box">✗ 发生未知错误：{}</div>'.format(str(e)),
                    unsafe_allow_html=True,
                )
                break

        if ch_idx < total - 1 and not error_occurred:
            time.sleep(1)

    if not error_occurred:
        overall_progress.progress(1.0)
        overall_status.markdown(
            '<div class="success-box">✓ 全部 {} 章生成完成！</div>'.format(total),
            unsafe_allow_html=True,
        )

    # ── 自检环节 ─────────────────────────────
    if st.session_state.all_results and not error_occurred:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">专业自检</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="info-box">'
            '🔍 剧本生成完成，正在启动专业三维度自检（动作描述 · 画面描述 · 台词描述）...'
            '</div>',
            unsafe_allow_html=True,
        )

        review_progress = st.progress(0)
        review_status = st.empty()
        review_container = st.container()

        for r_idx, result in enumerate(st.session_state.all_results):
            review_progress.progress(r_idx / len(st.session_state.all_results))
            review_status.markdown(
                '<div class="info-box">🔍 正在自检第 {} / {} 章：{}</div>'.format(
                    r_idx + 1,
                    len(st.session_state.all_results),
                    result["title"],
                ),
                unsafe_allow_html=True,
            )

            with review_container:
                st.markdown(
                    '<div class="review-header">'
                    '🔎 自检报告 · 第 {} 章：{}'
                    '</div>'.format(r_idx + 1, result["title"]),
                    unsafe_allow_html=True,
                )

                review_placeholder = st.empty()
                review_text = ""

                # 构造上下文：前章摘要 + 当前剧本
                prev_chapters_summary = ""
                if r_idx > 0:
                    prev_titles = [
                        st.session_state.all_results[i]["title"]
                        for i in range(r_idx)
                    ]
                    prev_chapters_summary = (
                        "【前章已发生事件（仅供上下文参考，不作为本章自检对象）】\n"
                        + "、".join(prev_titles)
                        + " 已完成剧本改编。\n\n"
                    )

                review_user_prompt = (
                    "{}请对以下短剧剧本进行专业三维度自检：\n\n"
                    "章节：{}\n\n"
                    "剧本内容：\n{}"
                ).format(
                    prev_chapters_summary,
                    result["title"],
                    result["content"],
                )

                review_messages = [
                    {"role": "system", "content": REVIEW_PROMPT},
                    {"role": "user", "content": review_user_prompt},
                ]

                try:
                    for chunk in call_api_stream(
                        messages=review_messages,
                        api_key=api_key.strip(),
                        api_base=api_base.strip(),
                        model=final_model.strip(),
                    ):
                        review_text += chunk
                        review_placeholder.markdown(
                            '<div class="review-output">{}</div>'.format(review_text),
                            unsafe_allow_html=True,
                        )
                        
                    revised_content = extract_revised_screenplay(review_text)
                    st.session_state.review_results.append({
                        "title": result["title"],
                        "review": review_text,
                        "revised": revised_content if revised_content else result["content"],
                    })
                    st.markdown(
                        '<div class="success-box">✓ 第 {} 章自检完成</div>'.format(
                            r_idx + 1
                        ),
                        unsafe_allow_html=True,
                    )

                except Exception as e:
                    st.markdown(
                        '<div class="error-box">✗ 第 {} 章自检失败：{}</div>'.format(
                            r_idx + 1, str(e)
                        ),
                        unsafe_allow_html=True,
                    )

            if r_idx < len(st.session_state.all_results) - 1:
                time.sleep(1)

        review_progress.progress(1.0)
        review_status.markdown(
            '<div class="success-box">✓ 全部自检完成</div>',
            unsafe_allow_html=True,
        )

    # ── 汇总下载 ─────────────────────────────
    if st.session_state.all_results:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # 构建完整导出文本（剧本 + 自检报告）
        full_export = ""
        for i, r in enumerate(st.session_state.all_results):
            full_export += "\n\n{}\n【{}】\n{}\n\n".format(
                "=" * 60, r["title"], "=" * 60
            )
            full_export += r["content"]

            # 附加对应自检报告
            if i < len(st.session_state.review_results):
                rv = st.session_state.review_results[i]
                full_export += "\n\n--- 自检报告 ---\n"
                full_export += rv["review"]
                full_export += "\n--- 报告结束 ---\n"

        full_export = full_export.strip()

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            # 优先使用修订后版本，若无则使用原始版本
            def get_final_content(idx, original_content):
               if idx < len(st.session_state.review_results):
                   revised = st.session_state.review_results[idx].get("revised", "")
                    if revised:
                        return revised
               return original_content
                        
            screenplay_only = "\n\n".join(
                "{}\n【{}】\n{}\n\n{}".format("=" * 60, r["title"], "=" * 60, r["content"])
                get_final_content(i, r["content"])
               ) 
                for i, r in enumerate(st.session_state.all_results)
            )
            st.download_button(
                label="⬇️  下载剧本（仅正文）",
                data=screenplay_only.encode("utf-8"),
                file_name="screenplay.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_dl2:
            st.download_button(
                label="⬇️  下载完整报告（剧本 + 自检）",
                data=full_export.encode("utf-8"),
                file_name="screenplay_with_review.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.session_state.generating = False

# ── 历史结果保留 ─────────────────────────────
elif st.session_state.all_results and not st.session_state.generating:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">上次生成结果</div>',
        unsafe_allow_html=True,
    )

    for i, r in enumerate(st.session_state.all_results):
        st.markdown(
            '<div class="chapter-header">📖 {}</div>'.format(r["title"]),
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="screenplay-output">{}</div>'.format(r["content"]),
            unsafe_allow_html=True,
        )

        if i < len(st.session_state.review_results):
            rv = st.session_state.review_results[i]
            st.markdown(
                '<div class="review-header">🔎 自检报告 · {}</div>'.format(rv["title"]),
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="review-output">{}</div>'.format(rv["review"]),
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    full_export = ""
    for i, r in enumerate(st.session_state.all_results):
        full_export += "\n\n{}\n【{}】\n{}\n\n{}".format(
            "=" * 60, r["title"], "=" * 60, r["content"]
        )
        if i < len(st.session_state.review_results):
            rv = st.session_state.review_results[i]
            full_export += "\n\n--- 自检报告 ---\n{}\n--- 报告结束 ---\n".format(
                rv["review"]
            )

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        screenplay_only = "\n\n".join(
            "{}\n【{}】\n{}\n\n{}".format("=" * 60, r["title"], "=" * 60, r["content"])
            for r in st.session_state.all_results
        )
        st.download_button(
            label="⬇️  下载剧本（仅正文）",
            data=screenplay_only.encode("utf-8"),
            file_name="screenplay.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            label="⬇️  下载完整报告（剧本 + 自检）",
            data=full_export.strip().encode("utf-8"),
            file_name="screenplay_with_review.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ── 底部说明 ─────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown(
    '<div class="info-box" style="text-align:center; font-size:0.8rem;">'
    'API Key 仅用于本次请求，不会被记录。&nbsp;|&nbsp;'
    '自动识别章节标题分块，无标题则每 2000 字切一块。&nbsp;|&nbsp;'
    '每章完成后自动提取衔接摘要，确保跨章剧情连贯。'
    '</div>',
    unsafe_allow_html=True,
)
