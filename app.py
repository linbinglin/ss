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
# 自定义 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; color: #e8e8e8; }
    #MainMenu, footer, header { visibility: hidden; }

    .main-title { text-align: center; padding: 2rem 0 0.5rem 0; }
    .main-title h1 { font-size: 2.2rem; font-weight: 700; color: #ffffff; letter-spacing: 0.05em; margin-bottom: 0.2rem; }
    .main-title p { color: #888888; font-size: 0.95rem; margin-top: 0; }

    .divider { border: none; border-top: 1px solid #2a2a2a; margin: 1.5rem 0; }
    .section-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.12em; color: #666666; margin-bottom: 0.5rem; font-weight: 600; }

    .stTextArea label, .stTextInput label, .stSelectbox label, .stFileUploader label { color: #cccccc !important; font-size: 0.9rem !important; font-weight: 500 !important; }
    .stTextArea textarea { background-color: #1a1a1a !important; color: #e8e8e8 !important; border: 1px solid #333333 !important; border-radius: 8px !important; font-size: 0.9rem !important; }
    .stTextArea textarea:focus { border-color: #555555 !important; box-shadow: none !important; }
    .stTextInput input { background-color: #1a1a1a !important; color: #e8e8e8 !important; border: 1px solid #333333 !important; border-radius: 8px !important; }
    .stSelectbox > div > div { background-color: #1a1a1a !important; border: 1px solid #333333 !important; color: #e8e8e8 !important; border-radius: 8px !important; }
    .stFileUploader > div { background-color: #1a1a1a !important; border: 1px dashed #333333 !important; border-radius: 8px !important; }

    .stButton > button { background-color: #ffffff !important; color: #000000 !important; border: none !important; border-radius: 8px !important; padding: 0.6rem 2rem !important; font-weight: 600 !important; font-size: 1rem !important; width: 100% !important; transition: opacity 0.2s ease !important; }
    .stButton > button:hover { opacity: 0.85 !important; }
    .stButton > button:disabled { opacity: 0.4 !important; }

    .info-box { background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.88rem; color: #aaaaaa; line-height: 1.6; }
    .success-box { background-color: #0d1f0d; border: 1px solid #1a4a1a; border-radius: 8px; padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.88rem; color: #88cc88; }
    .error-box { background-color: #1f0d0d; border: 1px solid #4a1a1a; border-radius: 8px; padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.88rem; color: #cc8888; }
    .warning-box { background-color: #1f1a0d; border: 1px solid #4a3a1a; border-radius: 8px; padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.88rem; color: #ccaa88; }

    .chapter-header { background-color: #1a1a2a; border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 1rem 0 0.3rem 0; font-size: 0.85rem; color: #8888cc; font-weight: 600; }
    .screenplay-output { background-color: #141414; border: 1px solid #2a2a2a; border-radius: 10px; padding: 1.5rem 2rem; font-family: 'Courier New', monospace; font-size: 0.88rem; line-height: 1.8; color: #ddd; white-space: pre-wrap; word-wrap: break-word; margin-bottom: 1rem; }
    .context-box { background-color: #141a14; border: 1px solid #1a3a1a; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 0.5rem 0; font-size: 0.82rem; color: #779977; line-height: 1.5; font-style: italic; }
    .word-count { font-size: 0.78rem; color: #555555; text-align: right; margin-top: 0.3rem; }

    .stTabs [data-baseweb="tab-list"] { background-color: #1a1a1a; border-radius: 8px; padding: 0.2rem; gap: 0.2rem; }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; color: #888888 !important; border-radius: 6px !important; padding: 0.4rem 1rem !important; }
    .stTabs [aria-selected="true"] { background-color: #2a2a2a !important; color: #ffffff !important; }

    .stProgress > div > div > div { background-color: #ffffff !important; }
    .streamlit-expanderHeader { background-color: #1a1a1a !important; color: #cccccc !important; border-radius: 8px !important; border: 1px solid #2a2a2a !important; }
    ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #111; } ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
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

第二部分：在剧本末尾输出以下简报，格式严格如下：

---【剧本简报】---
原著保真：〔列出未改动的关键事件点〕
影视化优化：〔列出3-5个有效优化点〕
逻辑保障：〔列出3处关键问答或衔接如何成立〕
---【衔接摘要】---
场景位置：〔本章结束时，主要人物所处地点〕
人物状态：〔每个主要角色当前的情绪/处境/目标〕
关系变化：〔本章发生的关键关系变化〕
未解悬念：〔本章结束时仍悬而未决的钩子〕
---【摘要结束】---

====================
十、Few-shot 示例（严格对齐此格式输出）
====================

【输入示例】
林初雪站在拍卖会场中央，心跳如擂鼓。她知道，今天这场拍卖会将决定她的命运。她的手心全是汗，紧张得几乎无法呼吸。
"各位贵宾，接下来这件拍品非同寻常。"拍卖师故作神秘地说，"这是一枚千年寒玉，传说中能够觉醒灵力的至宝！"
林初雪的瞳孔骤然收缩。千年寒玉？那不正是她母亲临终前托付给她的东西吗？她明明藏得很好，怎么会出现在这里？
"一百万！"台下有人出价。"两百万！"又有人喊价。
林初雪咬紧嘴唇，她知道自己必须拿回那枚寒玉，可是她身上只有五十万，根本不够。
就在这时，包厢里传来一个慵懒的男声："一千万。"
全场哗然。林初雪抬头看向二楼包厢，透过薄纱帘幕，她隐约看到一个修长的身影。
"一千万一次，一千万两次——"拍卖师举起木槌。
林初雪再也忍不住了，她冲上前大喊："等等！那是我的东西！"
"小姐，拍卖会有拍卖会的规矩。"拍卖师皮笑肉不笑地说，"你说是你的，有证据吗？"
就在这时，二楼包厢的门打开了。一个穿着黑色长袍的男人缓缓走出来，容貌俊美，居高临下地看着林初雪，嘴角勾起玩味的笑容。
"有意思。"他开口道，"既然这位小姐说寒玉是她的，不如让她证明一下？"
林初雪闭上眼睛，开始调动体内沉睡已久的灵力。突然，展台上的寒玉开始发光！淡蓝色的光芒越来越亮，整个拍卖厅都被照得如同白昼，空气中飘出白色雾气，前排酒杯表面结出细小冰晶。
"这……这怎么可能？"拍卖师结结巴巴地说。
黑袍男人的眼神从玩味变成认真，盯着林初雪，仿佛要把她看穿。
林初雪感到头晕目眩，勉强支撑着身体，抬头看向二楼："够不够？"
"看来，"黑袍男人缓缓开口，"这位小姐确实与寒玉有缘。不过，既然寒玉已经流入拍卖会，就该按规矩来。我出一千万，小姐若是拿不出更高的价格，寒玉就归我了。"
林初雪把支票拍在台面上，拍卖师低头一看："五十万。"台下有人笑出声。
林初雪抬头盯住二楼："你到底想要什么？"
黑袍男人转身往包厢里走，停在门口侧过头："明晚子时，城北废宅。你一个人来，寒玉的事继续谈。迟到作废。"

【正确输出示例】
【场景：拍卖会场｜夜晚】
拍卖师掀开红布。展台上的寒玉在射灯下泛着青白色光泽。
林初雪站在后排第三列，手里攥着一张支票，指节发白。她看清展台上的东西，身体往前倾了一下，嘴唇动了动没出声。
拍卖师敲槌："千年寒玉，起拍一百万。"
前排男人举牌："一百五十万。"左侧女宾客跟着："两百万。"
林初雪把支票翻过来看背面数字，又翻回去，咬住下唇。

【场景：拍卖会场二楼包厢｜夜晚】
黑袍男人坐在栏后椅子上，手指敲了两下扶手，对侍从点头。
侍从推开纱帘，朝楼下喊："一千万。"

【场景：拍卖会场｜夜晚】
叫价声停住。前排男人把号牌放下，转头看向二楼。左侧两名女宾客凑近低声说话。后排有人举起手机对准包厢方向。
拍卖师握槌的手停在半空，回过神，举槌："一千万一次——"
林初雪冲到台前，手按在展台边缘："等等！"
拍卖师收回木槌，皱眉看她。台下有人站起来看热闹。
林初雪深吸一口气："这块玉是我母亲的遗物。"
拍卖师脸色一冷："小姐，拍卖会讲证据。你拿什么证明？"
林初雪把支票拍在台面上："我先不加价。我先证明它认我。"
拍卖师看向二楼，没接话。

【场景：拍卖会场二楼栏边｜夜晚】
包厢门打开，黑袍男人走到栏杆边，双手撑在栏杆上俯视她："可以。你证明。"

【场景：拍卖会场展台｜夜晚】
林初雪双手按在展台玻璃上，闭眼，肩膀绷紧。呼吸放慢，手掌下的玻璃表面开始起雾。
雾气蔓延到展台四角，边缘凝出白霜。寒玉内部亮起淡蓝光，一层层增强。
前排酒杯表面结出细小冰晶。前排宾客往后退，椅子拖动声响成一片。拍卖师手一松，木槌掉在地上。
林初雪睁眼，脸色发白，额头全是汗，手撑着台面才站稳，抬头看向二楼："够不够？"

【场景：拍卖会场二楼栏边｜夜晚】
黑袍男人盯着寒玉看了三秒，直起身："认主现象成立。"
他转向林初雪："但拍卖流程已启动，规则不变。一千万，你继续出价。"

【场景：拍卖会场展台｜夜晚】
林初雪把支票推到拍卖师面前。拍卖师低头看一眼，抬起头："五十万。"
台下有人笑出声，有人摇头。
林初雪抬头盯住二楼黑袍男人，声音发紧："你到底想要什么？"
黑袍男人转身往包厢里走，停在门口侧过头："明晚子时，城北废宅。你一个人来，寒玉的事继续谈。"他推开门："迟到作废。"
包厢门合上。林初雪把支票收回袖子里，转身离开展台。宾客们盯着她背影议论。

---【剧本简报】---
原著保真：拍卖会见到母亲遗物寒玉、无力竞拍、神秘男人出天价压场、被迫当场证明认主、灵力觉醒引发冰晶异象、对方以规则压制并抛出约见条件。
影视化优化：心理描写改为手部动作和呼吸变化；灵力觉醒具象为"起雾→结霜→发光→周围结冰晶"递进视觉链；群体反应拆解为个体可拍动作；删除所有重复心理独白；黑袍男人通过侍从喊价体现身份层级。
逻辑保障："你有证据"→"我先证明"形成挑战-应战；"够不够"→"认主成立"给出判定；"规则不变"→"五十万被读出"推进到价格僵局并触发台下反应；"你想要什么"→"明晚城北废宅"抛出明确后续钩子。
---【衔接摘要】---
场景位置：拍卖会场展台（林初雪），城北废宅（尚未抵达，为下章铺垫地点）
人物状态：林初雪——灵力耗尽、手持五十万支票、母亲遗物未能赎回，目标是明晚赴约；黑袍男人——身份未明、掌握主动权、对林初雪展现出超出常规的兴趣
关系变化：双方从陌生人转为"有条件接触"关系，主动权在黑袍男人一侧
未解悬念：寒玉为何会出现在拍卖会？黑袍男人真实目的是什么？林初雪是否会独自赴约？
---【摘要结束】---"""

# ─────────────────────────────────────────────
# 章节分割函数
# ─────────────────────────────────────────────
def split_into_chapters(text: str) -> list[dict]:
    """
    智能识别章节边界，返回章节列表。
    每个元素：{"title": str, "content": str, "index": int}
    支持多种章节标题格式：第X章、Chapter X、第X回、===分隔线等。
    """
    chapter_patterns = [
        r'第[零一二三四五六七八九十百千\d]+[章回节集部][\s\S]*?(?=第[零一二三四五六七八九十百千\d]+[章回节集部]|$)',
        r'Chapter\s*\d+[\s\S]*?(?=Chapter\s*\d+|$)',
        r'CHAPTER\s*\d+[\s\S]*?(?=CHAPTER\s*\d+|$)',
    ]

    # 尝试按标准章节标题分割
    chapter_title_re = re.compile(
        r'(第[零一二三四五六七八九十百千\d]+[章回节集部][^\n]*|'
        r'Chapter\s*\d+[^\n]*|'
        r'CHAPTER\s*\d+[^\n]*|'
        r'={3,}[^\n]*={3,}|'
        r'-{3,}[^\n]*-{3,})',
        re.IGNORECASE
    )

    parts = chapter_title_re.split(text)
    titles = chapter_title_re.findall(text)

    chapters = []

    if len(titles) >= 2:
        # 有明确章节标题
        # parts[0] 是第一个标题前的内容（前言/序等）
        if parts[0].strip():
            chapters.append({
                "title": "前言 / 序章",
                "content": parts[0].strip(),
                "index": 0
            })
        for i, title in enumerate(titles):
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if content:
                chapters.append({
                    "title": title.strip(),
                    "content": content,
                    "index": len(chapters)
                })
    else:
        # 没有章节标题，按字数切分（每块约 2000 字）
        chunk_size = 2000
        total = len(text)
        chunk_index = 0
        pos = 0
        while pos < total:
            end = min(pos + chunk_size, total)
            # 尝试在段落边界切割
            if end < total:
                newline_pos = text.rfind('\n', pos, end)
                if newline_pos > pos + chunk_size // 2:
                    end = newline_pos
            chunk = text[pos:end].strip()
            if chunk:
                chapters.append({
                    "title": f"第 {chunk_index + 1} 段",
                    "content": chunk,
                    "index": chunk_index
                })
                chunk_index += 1
            pos = end

    return chapters


# ─────────────────────────────────────────────
# 提取衔接摘要
# ─────────────────────────────────────────────
def extract_context_summary(screenplay_text: str) -> str:
    """从上一章剧本输出中提取【衔接摘要】部分。"""
    match = re.search(
        r'---【衔接摘要】---([\s\S]*?)---【摘要结束】---',
        screenplay_text
    )
    if match:
        return match.group(1).strip()
    return ""


# ─────────────────────────────────────────────
# 构造每章的 User Prompt
# ─────────────────────────────────────────────
def build_user_prompt(chapter: dict, total_chapters: int, prev_context: str) -> str:
    is_first = chapter["index"] == 0
    is_last = chapter["index"] == total_chapters - 1

    position_note = ""
    if is_first and is_last:
        position_note = "（这是全文唯一章节）"
    elif is_first:
        position_note = f"（这是第 1 章，共 {total_chapters} 章，是开篇章节）"
    elif is_last:
        position_note = f"（这是第 {chapter['index'] + 1} 章，共 {total_chapters} 章，是结尾章节）"
    else:
        position_note = f"（这是第 {chapter['index'] + 1} 章，共 {total_chapters} 章）"

    context_block = ""
    if prev_context:
        context_block = f"""
【前章衔接信息（必须在本章开头自然延续，不得重复描述前章内容）】
{prev_context}

"""

    prompt = f"""{context_block}请将以下小说原文改编为短剧剧本 {position_note}：

章节标题：{chapter['title']}

原文内容：
{chapter['content']}

要求：
1. 严格按照系统提示词中的格式输出剧本正文，再输出剧本简报和衔接摘要。
2. 若有前章衔接信息，本章第一个场景需自然承接前章结尾状态（人物位置/情绪/悬念），但不重复描述前章已发生的事。
3. 衔接摘要中的"未解悬念"必须包含本章新产生的悬念钩子。"""

    return prompt


# ─────────────────────────────────────────────
# 流式 API 调用
# ─────────────────────────────────────────────
def call_api_stream(messages: list, api_key: str, api_base: str, model: str):
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "stream": True,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8000,
    }

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=180) as resp:
        if resp.status_code != 200:
            error_detail = resp.text[:400]
            raise RuntimeError(f"API 请求失败（{resp.status_code}）：{error_detail}")

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
# 常用模型列表
# ─────────────────────────────────────────────
PRESET_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4-turbo",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-haiku-20241022",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "deepseek-chat",
    "deepseek-reasoner",
    "自定义模型...",
]

# ─────────────────────────────────────────────
# Session State 初始化
# ─────────────────────────────────────────────
for key, default in {
    "all_results": [],        # List[{"title": str, "content": str}]
    "generating": False,
    "chapters": [],
    "prev_context": "",
    "current_chapter_idx": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# 页面主体
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-title">
    <h1>🎬 短剧剧本生成器</h1>
    <p>上传或粘贴小说原文，自动按章节分批生成可拍摄短剧剧本</p>
</div>
""", unsafe_allow_html=True)

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
            custom_model = st.text_input("输入自定义模型名称", placeholder="例如：gpt-4o-2024-11-20")
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
        help="支持 UTF-8 或 GBK 编码；可包含多个章节",
    )
    if uploaded_file is not None:
        try:
            raw = uploaded_file.read()
            try:
                novel_text = raw.decode("utf-8")
            except UnicodeDecodeError:
                novel_text = raw.decode("gbk", errors="replace")
            st.markdown(
                f'<div class="success-box">✓ 文件加载成功：{uploaded_file.name}（{len(novel_text):,} 字符）</div>',
                unsafe_allow_html=True,
            )
            with st.expander("预览文件内容（前 300 字）"):
                st.text(novel_text[:300] + ("..." if len(novel_text) > 300 else ""))
        except Exception as e:
            st.markdown(f'<div class="error-box">✗ 文件读取失败：{str(e)}</div>', unsafe_allow_html=True)

with input_tab2:
    pasted_text = st.text_area(
        "在此粘贴小说原文",
        height=300,
        placeholder="将小说文本粘贴至此处...\n\n支持多章节内容（识别"第X章"等标题自动分章）\n单次支持 10000 字以上，系统将自动分块处理。",
        label_visibility="collapsed",
    )
    if pasted_text.strip():
        novel_text = pasted_text
        st.markdown(f'<div class="word-count">{len(pasted_text):,} 字符</div>', unsafe_allow_html=True)

# ── 章节预览 ─────────────────────────────────
if novel_text.strip():
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    chapters_preview = split_into_chapters(novel_text)

    st.markdown('<div class="section-label">章节识别结果</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="info-box">🔍 共识别到 <strong>{len(chapters_preview)}</strong> 个章节 / 分块，将按序逐章处理，每章独立生成剧本并自动传递衔接信息。</div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"查看 {len(chapters_preview)} 个章节列表"):
        for i, ch in enumerate(chapters_preview):
            st.markdown(
                f"**{i + 1}.** {ch['title']} — {len(ch['content']):,} 字符",
                unsafe_allow_html=False,
            )

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 生成按钮 ─────────────────────────────────
can_generate = bool(api_key.strip()) and bool(novel_text.strip()) and bool(final_model.strip())

hints = []
if not api_key.strip():
    hints.append("请填写 API Key")
if not novel_text.strip():
    hints.append("请上传文件或粘贴小说原文")
if not final_model.strip():
    hints.append("请输入自定义模型名称")

if hints:
    st.markdown(
        f'<div class="info-box">💡 {" &nbsp;|&nbsp; ".join(hints)}</div>',
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
        chapter_progress_val = ch_idx / total
        overall_progress.progress(chapter_progress_val)
        overall_status.markdown(
            f'<div class="info-box">⏳ 正在处理第 {ch_idx + 1} / {total} 章：{chapter["title"]}</div>',
            unsafe_allow_html=True,
        )

        with results_container:
            st.markdown(
                f'<div class="chapter-header">📖 第 {ch_idx + 1} 章：{chapter["title"]}</div>',
                unsafe_allow_html=True,
            )

            # 若有衔接摘要，展示给用户
            if st.session_state.prev_context:
                st.markdown(
                    f'<div class="context-box">🔗 衔接信息已传递：<br>{st.session_state.prev_context.replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True,
                )

            chapter_output_placeholder = st.empty()
            chapter_full_text = ""

            # 构造 messages
            user_prompt = build_user_prompt(
                chapter=chapter,
                total_chapters=total,
                prev_context=st.session_state.prev_context,
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # 流式生成
            try:
                for chunk in call_api_stream(
                    messages=messages,
                    api_key=api_key.strip(),
                    api_base=api_base.strip(),
                    model=final_model.strip(),
                ):
                    chapter_full_text += chunk
                    chapter_output_placeholder.markdown(
                        f'<div class="screenplay-output">{chapter_full_text}</div>',
                        unsafe_allow_html=True,
                    )

                # 提取衔接摘要，传递给下一章
                context = extract_context_summary(chapter_full_text)
                st.session_state.prev_context = context

                # 保存结果
                st.session_state.all_results.append({
                    "title": chapter["title"],
                    "content": chapter_full_text,
                })

                st.markdown(
                    f'<div class="success-box">✓ 第 {ch_idx + 1} 章生成完成（{len(chapter_full_text):,} 字符）</div>',
                    unsafe_allow_html=True,
                )

            except RuntimeError as e:
                error_occurred = True
                st.markdown(f'<div class="error-box">✗ 第 {ch_idx + 1} 章生成失败：{str(e)}</div>', unsafe_allow_html=True)
                break
            except requests.exceptions.ConnectionError:
                error_occurred = True
                st.markdown('<div class="error-box">✗ 网络连接失败，请检查接口地址</div>', unsafe_allow_html=True)
                break
            except requests.exceptions.Timeout:
                error_occurred = True
                st.markdown('<div class="error-box">✗ 请求超时（180秒），建议缩短单章内容后重试</div>', unsafe_allow_html=True)
                break
            except Exception as e:
                error_occurred = True
                st.markdown(f'<div class="error-box">✗ 发生未知错误：{str(e)}</div>', unsafe_allow_html=True)
                break

        # 章节间短暂间隔，避免频繁请求
        if ch_idx < total - 1 and not error_occurred:
            time.sleep(1)

    # 全部完成
    if not error_occurred:
        overall_progress.progress(1.0)
        overall_status.markdown(
            f'<div class="success-box">✓ 全部 {total} 章生成完成！</div>',
            unsafe_allow_html=True,
        )

    # 汇总下载
    if st.session_state.all_results:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        full_export = ""
        for r in st.session_state.all_results:
            full_export += f"\n\n{'='*60}\n【{r['title']}】\n{'='*60}\n\n"
            full_export += r["content"]
        full_export = full_export.strip()

        st.download_button(
            label="⬇️  下载完整剧本（全部章节 .txt）",
            data=full_export.encode("utf-8"),
            file_name="screenplay_full.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.session_state.generating = False

# ── 历史结果保留展示 ─────────────────────────
elif st.session_state.all_results and not st.session_state.generating:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">上次生成结果</div>', unsafe_allow_html=True)

    for r in st.session_state.all_results:
        st.markdown(f'<div class="chapter-header">📖 {r["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="screenplay-output">{r["content"]}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    full_export = ""
    for r in st.session_state.all_results:
        full_export += f"\n\n{'='*60}\n【{r['title']}】\n{'='*60}\n\n"
        full_export += r["content"]

    st.download_button(
        label="⬇️  下载完整剧本（全部章节 .txt）",
        data=full_export.strip().encode("utf-8"),
        file_name="screenplay_full.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ── 底部说明 ─────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<div class="info-box" style="text-align:center; font-size:0.8rem;">
    API Key 仅用于本次请求，不会被记录。&nbsp;|&nbsp;
    自动识别"第X章"等标题分块，无标题则每 2000 字切一块。&nbsp;|&nbsp;
    每章完成后自动提取衔接摘要传递给下一章，确保剧情连贯。
</div>
""", unsafe_allow_html=True)
