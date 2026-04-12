import streamlit as st
import json
import time
import re
import requests
from typing import List, Dict, Optional

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
# 自定义CSS样式
# ============================================================
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
    
    /* 步骤标题 */
    .step-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        padding: 0.5rem 0;
        border-bottom: 2px solid #3498db;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* 章节卡片 */
    .chapter-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .chapter-card:hover {
        border-color: #3498db;
        background: #f0f7ff;
    }
    
    /* 分镜卡片 */
    .shot-card {
        background: linear-gradient(135deg, #667eea08, #764ba208);
        border: 1px solid #e0e0e0;
        border-left: 4px solid #3498db;
        border-radius: 0 8px 8px 0;
        padding: 16px;
        margin: 10px 0;
    }
    
    /* 检查结果 */
    .check-pass {
        color: #27ae60;
        font-weight: 600;
    }
    .check-fail {
        color: #e74c3c;
        font-weight: 600;
    }
    .check-warn {
        color: #f39c12;
        font-weight: 600;
    }
    
    /* 按钮行 */
    .button-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 1rem 0;
    }
    
    /* 评分条 */
    .score-bar {
        height: 8px;
        border-radius: 4px;
        background: #ecf0f1;
        overflow: hidden;
        margin: 4px 0;
    }
    .score-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s;
    }
    
    /* 记忆面板 */
    .memory-panel {
        background: #fffbea;
        border: 1px solid #f0d060;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 8px 8px 0 0;
    }
    
    /* 侧边栏分组 */
    .sidebar-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 系统提示词（来自用户上传的txt）
# ============================================================
SYSTEM_PROMPT = """【微短剧生成 3.1 系统指令】

═══════════════════════════════════════
第零法则：视觉翻译（一切规则之上的规则）
═══════════════════════════════════════

小说是给眼睛的——读者靠文字在脑中自己生成画面。
剧本是给画面的——观众只能看到或听到你拍给他看的东西。

所以你的工作不是"把小说搬进剧本"。
你的工作是——

把小说用文字"告诉"读者的一切，
全部翻译成摄像机能拍到的画面,并用人物的台词（声音）来增加代入感！

禁止对角色OOC，人物的台词、行为、举止都必须符合小说里的人设，绝不能做出违背角色性格的任何行为和说话方式！

这是一条凌驾于所有其他规则之上的法则。

【翻译铁律】

铁律一：小说的"叙述"必须翻译为"动作流"
铁律二：小说的"心理描写"必须翻译为"身体反应搭配角色内心独白"
铁律三：小说的"设定/背景交代"必须翻译为"环境展示"
铁律四：台词的正确用法——给剧情赋予活力

【视觉翻译的核心公式】
第一步——识别原文类型：
A. 告诉读者发生了什么事 → 翻译为动作流
B. 告诉读者角色的感受 → 翻译为身体反应
C. 告诉读者世界观/背景 → 翻译为环境展示
D. 告诉读者角色的能力/身份 → 翻译为能力展示的动作场景
E. 告诉读者人物关系 → 翻译为两人互动时的空间距离/肢体语言/视线交汇方式

第二步——台词的适配：
画面呈现张力，台词赋予情感！

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════

你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集分镜数量自由抉择 | 无第三人称旁白 | 集集强钩子。

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色的性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。
③【伏笔】每一个重大转折之前，必须存在至少一个视觉/听觉微伏笔。
④【潜台词】角色嘴上说的话与真实意图之间必须存在缝隙。
⑤【钩子铁律】前15秒必须制造具体的疑问或情绪冲击。每集结尾必须制造悬念。

═══════════════════════════════════════
角色驱动卡系统
═══════════════════════════════════════
为每个主要角色建立驱动卡：核心人格、说话DNA、行为DNA、红线、关系动态。

═══════════════════════════════════════
分镜格式与密度标准
═══════════════════════════════════════
【分镜XX】
场景：地点 · 时间 · 天气 · 光线
内容：画面+台词(内心OS)+音效
衔接点：[本镜最后一帧 → 下一镜接入方式]

每个分镜控制在10-14秒，必须包含：
· ≥3个连续的动作事件
· ≥1个具体的环境/声音细节
· ≥1个角色微表情或身体细节

═══════════════════════════════════════
工作流（严格分轮次）
═══════════════════════════════════════
【第1轮：全局提炼】输出故事核心、角色驱动卡、故事大纲、核心节点等
【第2轮：开场手法设计】输出6条不同开场方案
【第3轮：剧本生成】含编剧内心独白、结构速写、角色驱动卡调用、影视化排雷
【第4轮：自检与优化】五个敌对视角攻击 + 量化打分"""

# ============================================================
# 分镜检查系统提示词
# ============================================================
REVIEW_SYSTEM_PROMPT = """你是一个专业的微短剧分镜质检专家。你的任务是对照小说原文，对每一条分镜进行严格的质量检查。

你必须检查以下维度，并给出具体的评分和修改建议：

【检查维度】

1. **角色一致性（1-10分）**
   - 台词是否符合角色驱动卡中的说话DNA？
   - 遮住角色名，能否通过说话方式猜出是谁？
   - 行为是否符合角色行为DNA？
   - 是否存在OOC（Out of Character）？

2. **画面具象度（1-10分）**
   - 每个分镜是否有具体的不寻常细节？
   - 闭上眼能否在脑中看到这个画面？
   - 是否有光源、声音、微动作等细节？
   - 是否存在"死掉的画面描写"？

3. **台词活人感（1-10分）**
   - 台词是否像真人说的话？
   - 情绪越强烈台词是否越短？
   - 是否存在"死掉的台词"？
   - 潜台词是否到位？

4. **视觉翻译完成度（1-10分）**
   - 叙述是否翻译为动作流？
   - 心理描写是否翻译为身体反应？
   - 背景设定是否翻译为环境展示？
   - 是否存在用台词替代画面叙事的情况？

5. **分镜密度（1-10分）**
   - 每个10-14秒分镜是否≥3个动作事件？
   - 是否有≥1个环境/声音细节？
   - 是否有≥1个角色微表情或身体细节？
   - 标注时长与内容实算时长偏差是否≤±2秒？

6. **因果链完整度（1-10分）**
   - 重大转折前是否有伏笔？
   - 观众不看原著时因果链是否完全成立？
   - 是否有逻辑跳跃？

7. **情绪过山车强度（1-10分）**
   - 集内是否有情绪急转？
   - 开场15秒是否有情绪冲击？
   - 结尾是否有悬念钩子？

8. **上下镜衔接流畅度（1-10分）**
   - 分镜之间是否有跳跃？
   - 衔接点是否合理？

9. **无旁白叙事清晰度（1-10分）**
   - 删掉所有台词后，观众是否仍能看懂基本剧情？
   - 是否依赖旁白交代信息？

10. **原著还原度（1-10分）**
    - 核心情节是否保留？
    - 角色关系是否准确？
    - 情感基调是否一致？

【输出格式要求】
对每一条分镜逐一检查，输出格式如下：

## 分镜 [编号] 检查报告

**场景概要：** [简述该分镜内容]

| 检查维度 | 评分 | 状态 | 问题描述 |
|---------|------|------|---------|
| 角色一致性 | X/10 | ✅/⚠️/❌ | 具体问题 |
| 画面具象度 | X/10 | ✅/⚠️/❌ | 具体问题 |
| ... | ... | ... | ... |

**综合评分：** X/100

**关键问题：**
1. [最严重的问题]
2. [次严重的问题]

**修改建议：**
1. [具体的修改建议]
2. [具体的修改建议]

---

最后给出整集的汇总报告：
- 总体评分
- 7分以下的项目列表及修改优先级
- 全局性问题（如角色一致性、节奏等）
- 优秀之处（值得保留的部分）
"""

# ============================================================
# 初始化Session State
# ============================================================
def init_session_state():
    defaults = {
        # API配置
        "api_key": "",
        "api_base": "https://yunwu.ai/v1/",
        "model_id": "deepseek-chat",
        "custom_model": "",
        
        # 章节管理
        "chapters": {},  # {chapter_name: chapter_content}
        "chapter_order": [],  # 章节顺序
        
        # 工作流状态
        "current_step": 0,  # 0=未开始, 1=全局提炼, 2=开场设计, 3=剧本生成, 4=自检
        "current_episode": 1,
        
        # 生成结果
        "global_analysis": "",  # 全局提炼结果
        "opening_designs": "",  # 开场设计
        "episodes": {},  # {ep_num: script_content}
        "review_results": {},  # {ep_num: review_content}
        
        # 全局记忆
        "memory": {
            "storyline": "",
            "characters": "",
            "progress": "",
            "last_ending": "",
            "pending_foreshadow": "",
            "next_foreshadow": "",
            "emotion_track": ""
        },
        
        # 消息历史
        "messages": [],
        
        # UI状态
        "mode": "默认",
        "show_review": False,
        "selected_chapters_for_analysis": [],
        "streaming_content": "",
        "is_generating": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================
# API调用函数
# ============================================================
def call_api_streaming(messages: List[Dict], system_prompt: str = SYSTEM_PROMPT):
    """流式调用API"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    
    model = st.session_state.model_id
    if model == "自定义模型":
        model = st.session_state.custom_model
    
    if not api_key:
        st.error("❌ 请先在侧边栏配置API Key")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    data = {
        "model": model,
        "messages": full_messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 8192
    }
    
    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API调用失败: {str(e)}")
        return None

def process_stream(response):
    """处理流式响应"""
    full_content = ""
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_content += content
                        yield content
                except json.JSONDecodeError:
                    continue
    return full_content

def call_api_non_streaming(messages: List[Dict], system_prompt: str = SYSTEM_PROMPT):
    """非流式调用API"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    
    model = st.session_state.model_id
    if model == "自定义模型":
        model = st.session_state.custom_model
    
    if not api_key:
        st.error("❌ 请先在侧边栏配置API Key")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    data = {
        "model": model,
        "messages": full_messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 8192
    }
    
    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API调用失败: {str(e)}")
        return None

# ============================================================
# 章节管理函数
# ============================================================
def add_chapter(name: str, content: str):
    """添加章节"""
    if name and content:
        st.session_state.chapters[name] = content
        if name not in st.session_state.chapter_order:
            st.session_state.chapter_order.append(name)
        return True
    return False

def remove_chapter(name: str):
    """删除章节"""
    if name in st.session_state.chapters:
        del st.session_state.chapters[name]
        st.session_state.chapter_order.remove(name)

def get_combined_novel_text(chapter_names: List[str] = None) -> str:
    """获取合并的小说文本"""
    if chapter_names is None:
        chapter_names = st.session_state.chapter_order
    
    texts = []
    for name in chapter_names:
        if name in st.session_state.chapters:
            texts.append(f"【{name}】\n{st.session_state.chapters[name]}")
    
    return "\n\n".join(texts)

# ============================================================
# 构建提示词函数
# ============================================================
def build_global_analysis_prompt(novel_text: str) -> str:
    return f"""【微短剧3.1启动】

以下是需要改编的小说原文内容：

{novel_text}

请执行【第1轮：全局提炼】，输出以下内容（不输出任何剧本）：

1. 一句话故事核心
2. 每个主要角色的【驱动卡】（必须从原著中提取原句作为说话DNA示范）
3. 故事大纲（分阶段）+ 各阶段核心情绪类型
4. 必须保留的核心情节节点（10-20个）
5. 需要补充的逻辑链节点（列出+补全方式）
6. 全剧环境/氛围基调 + 天气光影变化建议
7. 视觉强场景与短剧记忆点（最有冲击力的5-8个瞬间，每个用3-5句话描述具体画面）

输出完毕后提示确认。"""

def build_opening_design_prompt() -> str:
    return """请执行【第2轮：开场手法设计】

输出6条完全不同的第1集开场方案，每条必须包含：
- 开场类型标签
- 前30秒的逐秒画面描述（具体到：第1-3秒观众看到什么、听到什么；第4-10秒发生什么；第11-20秒情绪转向什么；第21-30秒钩子落在哪里）
- 30秒后如何衔接到主线

输出完毕后提示选择。"""

def build_episode_prompt(episode_num: int, novel_text: str, opening_choice: str = "") -> str:
    memory_str = ""
    if st.session_state.memory["storyline"]:
        memory_str = f"""
📌 一句话主线：{st.session_state.memory['storyline']}
📌 核心人物及其驱动卡摘要：{st.session_state.memory['characters']}
📌 当前进度：已生成到第{st.session_state.memory['progress']}集
📌 上集结尾画面+悬念：{st.session_state.memory['last_ending']}
📌 已埋未引爆的伏笔：{st.session_state.memory['pending_foreshadow']}
📌 下集必须引爆的伏笔：{st.session_state.memory['next_foreshadow']}
📌 角色情绪轨迹：{st.session_state.memory['emotion_track']}
"""
    
    opening_info = ""
    if opening_choice:
        opening_info = f"\n用户选择的开场方案：{opening_choice}\n"
    
    return f"""请执行【第3轮：剧本生成】—— 第{episode_num}集
{memory_str}
{opening_info}

参考的小说原文：
{novel_text}

请严格按照以下流程生成：

前置A——编剧内心独白（必须输出）：
"这集里谁最痛？痛在哪里？观众看完这集胸口什么感觉？观众看到哪里会想骂人？哪里会心疼？这集最强的一个画面是什么？"

前置B——本集结构速写：
· 开场钩子（前15秒）
· 中段高潮
· 结尾钩子
· 本集埋下的伏笔 → 将在第X集爆发
· 本集引爆的伏笔 ← 来自第X集

前置C——角色驱动卡调用声明

前置D——影视化排雷扫描

然后输出完整分镜剧本（每镜10-14秒）。

每个分镜格式：
【分镜XX】
场景：地点 · 时间 · 天气 · 光线
内容：[画面+台词(内心OS)+音效]
衔接点：[本镜最后一帧 → 下一镜接入方式]

最后更新全局记忆。"""

def build_review_prompt(episode_num: int, script: str, novel_text: str) -> str:
    return f"""请对以下第{episode_num}集的剧本分镜进行详细的质量检查。

【对照的小说原文】
{novel_text}

【需要检查的剧本分镜】
{script}

请逐一检查每条分镜，按照以下维度评分（每项1-10分）：
1. 角色一致性（台词+行为是否符合驱动卡）
2. 画面具象度（每个分镜是否有具体的不寻常细节）
3. 台词活人感
4. 视觉翻译完成度（是否有任何一处在用台词替代画面叙事）
5. 分镜密度（每个10-14秒分镜是否≥3个动作事件）
6. 因果链完整度
7. 情绪过山车强度
8. 上下镜衔接流畅度
9. 无旁白叙事清晰度
10. 原著还原度

对每条分镜输出检查报告，然后给出整集汇总。
7分以下的项目必须指出具体问题和修改建议。

同时执行五个敌对视角攻击：
视角1——普通观众
视角2——竞品编剧
视角3——原著粉
视角4——剪辑师
视角5——导演

最后给出【细节自检清单】逐项打勾。"""

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("### 🔌 API配置中心")
    
    # API基础地址
    st.text_input(
        "🌐 接口地址",
        value=st.session_state.api_base,
        key="api_base_input",
        placeholder="https://yunwu.ai/v1/",
        on_change=lambda: setattr(st.session_state, 'api_base', st.session_state.api_base_input)
    )
    st.session_state.api_base = st.session_state.api_base_input
    
    # API Key
    st.text_input(
        "🔑 API Key",
        value=st.session_state.api_key,
        type="password",
        key="api_key_input",
        placeholder="输入你的API Key"
    )
    st.session_state.api_key = st.session_state.api_key_input
    
    st.markdown("---")
    st.markdown("### 🤖 模型选择")
    
    # 模型选择
    model_options = [
        "deepseek-chat",
        "deepseek-reasoner", 
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "o3-mini",
        "gemini-2.5-pro-preview-06-05",
        "自定义模型"
    ]
    
    selected_model = st.selectbox(
        "选择模型",
        model_options,
        index=model_options.index(st.session_state.model_id) if st.session_state.model_id in model_options else 0,
        key="model_select"
    )
    st.session_state.model_id = selected_model
    
    # 自定义模型ID
    if selected_model == "自定义模型":
        custom = st.text_input(
            "输入模型ID",
            value=st.session_state.custom_model,
            placeholder="例如: deepseek-v3",
            key="custom_model_input"
        )
        st.session_state.custom_model = custom
    
    # 指向模型
    st.markdown("---")
    st.markdown("### 🧠 指向模型")
    
    review_model_options = ["与生成模型相同"] + model_options
    review_model = st.selectbox(
        "质检模型",
        review_model_options,
        key="review_model_select"
    )
    
    if review_model != "与生成模型相同":
        st.session_state["review_model"] = review_model
    else:
        st.session_state["review_model"] = None
    
    # 测试连接
    st.markdown("---")
    if st.button("🔗 测试连接", use_container_width=True):
        with st.spinner("测试中..."):
            test_messages = [{"role": "user", "content": "请回复'连接成功'四个字"}]
            result = call_api_non_streaming(test_messages, "你是一个助手。")
            if result:
                st.success(f"✅ 连接成功！模型: {st.session_state.model_id}")
                st.info(f"回复: {result[:100]}")
            else:
                st.error("❌ 连接失败，请检查配置")
    
    st.markdown("---")
    st.markdown("### 🎯 模式")
    mode = st.radio(
        "工作模式",
        ["📋 默认模式", "⚡ 快速模式"],
        key="mode_radio"
    )
    st.session_state.mode = "默认" if "默认" in mode else "快速"
    
    # 全局记忆
    st.markdown("---")
    st.markdown("### 💾 全局记忆")
    
    if st.button("📋 查看全局记忆状态", use_container_width=True):
        st.session_state["show_memory"] = True
    
    if st.button("🗑️ 清除所有数据", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()

# ============================================================
# 主界面
# ============================================================
st.markdown('<div class="main-title">🎬 影视化视觉翻译引擎 V3.2</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">小说改编微短剧系统 | 严格遵循视觉翻译法则 | 杜绝文字转文字的低级逻辑 | 台词给剧情赋活力</div>', unsafe_allow_html=True)

# 显示全局记忆（如果触发）
if st.session_state.get("show_memory", False):
    with st.expander("📌 全局记忆面板", expanded=True):
        mem = st.session_state.memory
        st.markdown(f"""
**📌 一句话主线：** {mem['storyline'] or '未设定'}  
**📌 核心人物：** {mem['characters'] or '未设定'}  
**📌 当前进度：** {mem['progress'] or '未开始'}  
**📌 上集结尾：** {mem['last_ending'] or '无'}  
**📌 已埋伏笔：** {mem['pending_foreshadow'] or '无'}  
**📌 下集引爆：** {mem['next_foreshadow'] or '无'}  
**📌 情绪轨迹：** {mem['emotion_track'] or '无'}
        """)
        if st.button("关闭记忆面板"):
            st.session_state["show_memory"] = False
            st.rerun()

# ============================================================
# 步骤一：导入小说章节原文
# ============================================================
st.markdown('<div class="step-header">📖 步骤一：导入小说章节原文</div>', unsafe_allow_html=True)

tab_add, tab_imported = st.tabs(["📝 添加章节", "📚 已导入章节"])

with tab_add:
    col_upload, col_paste = st.columns(2)
    
    with col_upload:
        st.markdown("**📁 从文件导入**")
        uploaded_files = st.file_uploader(
            "选择文件",
            type=["txt", "md", "text"],
            accept_multiple_files=True,
            key="file_uploader",
            help="支持 .txt, .md 格式，最大 200KB/文件"
        )
        
        if uploaded_files:
            for uf in uploaded_files:
                if uf.size > 200 * 1024:
                    st.warning(f"⚠️ 文件 {uf.name} 超过200KB限制")
                    continue
                content = uf.read().decode("utf-8", errors="ignore")
                chapter_name = uf.name.rsplit(".", 1)[0]
                if add_chapter(chapter_name, content):
                    st.success(f"✅ 已导入: {chapter_name} ({len(content)}字)")
    
    with col_paste:
        st.markdown("**✍️ 粘贴文本**")
        paste_name = st.text_input("章节名称", placeholder="例如：第1章 重生归来", key="paste_name")
        paste_content = st.text_area(
            "章节内容",
            height=200,
            placeholder="在此粘贴小说章节原文...",
            key="paste_content"
        )
        if st.button("➕ 添加此章节", key="add_paste"):
            if paste_name and paste_content:
                if add_chapter(paste_name, paste_content):
                    st.success(f"✅ 已添加: {paste_name} ({len(paste_content)}字)")
                    st.rerun()
            else:
                st.warning("⚠️ 请填写章节名称和内容")

with tab_imported:
    if st.session_state.chapter_order:
        st.markdown(f"**共导入 {len(st.session_state.chapter_order)} 个章节**")
        
        for i, ch_name in enumerate(st.session_state.chapter_order):
            ch_content = st.session_state.chapters[ch_name]
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"📄 **{ch_name}** ({len(ch_content)}字)")
            with col2:
                if st.button("👁️ 查看", key=f"view_{i}"):
                    st.session_state[f"expand_{i}"] = not st.session_state.get(f"expand_{i}", False)
            with col3:
                if st.button("🗑️ 删除", key=f"del_{i}"):
                    remove_chapter(ch_name)
                    st.rerun()
            
            if st.session_state.get(f"expand_{i}", False):
                with st.expander(f"📖 {ch_name} 内容预览", expanded=True):
                    st.text_area(
                        "内容",
                        value=ch_content,
                        height=300,
                        key=f"preview_{i}",
                        disabled=True
                    )
    else:
        st.info("💡 暂无章节，请从左侧添加")

# ============================================================
# 步骤二：章节拆解与取舍决策
# ============================================================
st.markdown('<div class="step-header">🔍 步骤二：章节拆解与取舍决策 (全局提炼)</div>', unsafe_allow_html=True)

col_select, col_result = st.columns([1, 1])

with col_select:
    st.markdown("**选择参与分析的章节**")
    if st.session_state.chapter_order:
        selected_chapters = st.multiselect(
            "选择章节",
            st.session_state.chapter_order,
            default=st.session_state.chapter_order,
            key="chapter_multiselect"
        )
        st.session_state.selected_chapters_for_analysis = selected_chapters
        
        if selected_chapters:
            total_chars = sum(len(st.session_state.chapters[ch]) for ch in selected_chapters)
            st.info(f"📊 已选择 {len(selected_chapters)} 个章节，共 {total_chars} 字")
        
        if st.button("🚀 启动全局提炼", key="start_analysis", use_container_width=True, type="primary"):
            if not selected_chapters:
                st.warning("⚠️ 请至少选择一个章节")
            elif not st.session_state.api_key:
                st.error("❌ 请先在侧边栏配置API Key")
            else:
                st.session_state["trigger_analysis"] = True
                st.session_state.current_step = 1
    else:
        st.info("💡 请先在步骤一中导入小说章节")

with col_result:
    st.markdown("**提炼结果**")
    
    if st.session_state.get("trigger_analysis", False):
        novel_text = get_combined_novel_text(st.session_state.selected_chapters_for_analysis)
        prompt = build_global_analysis_prompt(novel_text)
        messages = [{"role": "user", "content": prompt}]
        
        with st.spinner("🔄 AI正在进行全局提炼..."):
            response = call_api_streaming(messages)
            if response:
                result_container = st.empty()
                full_text = ""
                for chunk in process_stream(response):
                    full_text += chunk
                    result_container.markdown(full_text)
                
                st.session_state.global_analysis = full_text
                st.session_state.messages = messages + [{"role": "assistant", "content": full_text}]
                st.session_state["trigger_analysis"] = False
                st.success("✅ 全局提炼完成！请确认角色驱动卡是否准确。")
    
    elif st.session_state.global_analysis:
        with st.expander("📋 查看全局提炼结果", expanded=False):
            st.markdown(st.session_state.global_analysis)
        
        if st.button("🔄 重新提炼", key="redo_analysis"):
            st.session_state.global_analysis = ""
            st.session_state["trigger_analysis"] = True
            st.rerun()
    else:
        st.info("💡 请先选择章节，然后点击「启动全局提炼」生成提炼结果")

# ============================================================
# 步骤三：编剧工作流控制台
# ============================================================
st.markdown('<div class="step-header">🎬 步骤三：编剧工作流控制台</div>', unsafe_allow_html=True)

# 工具栏
toolbar_cols = st.columns([1, 1, 2, 3])

with toolbar_cols[0]:
    episode_num = st.number_input(
        "集数编号",
        min_value=1,
        max_value=100,
        value=st.session_state.current_episode,
        key="ep_num_input"
    )
    st.session_state.current_episode = episode_num

with toolbar_cols[1]:
    ep_chapter_select = st.multiselect(
        "对应章节 (可选)",
        st.session_state.chapter_order,
        key="ep_chapter_select",
        help="选择本集对应的小说章节，可节省token"
    )

with toolbar_cols[2]:
    st.markdown("**操作面板**")
    st.caption("💡 按顺序：节前准备、开场设计、生成剧本、质检修改")

# ============================================================
# 功能按钮行
# ============================================================
btn_cols = st.columns(6)

with btn_cols[0]:
    btn_opening = st.button("🎯 设计开场", key="btn_opening", use_container_width=True)

with btn_cols[1]:
    btn_generate = st.button("🎬 生成剧本", key="btn_generate", use_container_width=True, type="primary")

with btn_cols[2]:
    btn_review = st.button("🔍 质量检查", key="btn_review", use_container_width=True)

with btn_cols[3]:
    btn_optimize_dialogue = st.button("💬 优化台词", key="btn_opt_dialogue", use_container_width=True)

with btn_cols[4]:
    btn_optimize_visual = st.button("🎨 优化画面", key="btn_opt_visual", use_container_width=True)

with btn_cols[5]:
    btn_optimize_emotion = st.button("❤️ 优化情绪", key="btn_opt_emotion", use_container_width=True)

# ============================================================
# 主内容区 - 使用tabs
# ============================================================
main_tabs = st.tabs(["📝 剧本编辑区", "🔍 质检报告", "📜 开场方案", "💬 自由对话"])

# ============================================================
# Tab 1: 剧本编辑区
# ============================================================
with main_tabs[0]:
    # 开场设计处理
    if btn_opening:
        if not st.session_state.global_analysis:
            st.warning("⚠️ 请先完成全局提炼（步骤二）")
        else:
            prompt = build_opening_design_prompt()
            messages = st.session_state.messages + [{"role": "user", "content": prompt}]
            
            with st.spinner("🔄 正在设计开场方案..."):
                response = call_api_streaming(messages)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    
                    st.session_state.opening_designs = full_text
                    st.session_state.messages = messages + [{"role": "assistant", "content": full_text}]
                    st.session_state.current_step = 2
    
    # 剧本生成处理
    if btn_generate:
        if not st.session_state.global_analysis:
            st.warning("⚠️ 请先完成全局提炼（步骤二）")
        else:
            # 获取对应章节文本
            if ep_chapter_select:
                novel_text = get_combined_novel_text(ep_chapter_select)
            else:
                novel_text = get_combined_novel_text()
            
            prompt = build_episode_prompt(episode_num, novel_text)
            
            # 构建消息上下文
            context_messages = st.session_state.messages.copy()
            context_messages.append({"role": "user", "content": prompt})
            
            with st.spinner(f"🔄 正在生成第{episode_num}集剧本..."):
                response = call_api_streaming(context_messages)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    
                    st.session_state.episodes[episode_num] = full_text
                    st.session_state.messages = context_messages + [
                        {"role": "assistant", "content": full_text}
                    ]
                    st.session_state.current_step = 3
                    st.session_state.memory["progress"] = str(episode_num)
                    st.success(f"✅ 第{episode_num}集剧本生成完成！")
    
    # 优化台词
    if btn_optimize_dialogue:
        ep = episode_num
        if ep in st.session_state.episodes:
            optimize_prompt = f"""请只优化第{ep}集剧本的台词部分。

要求：
1. 检查每句台词是否符合角色驱动卡的说话DNA
2. 遮住角色名能否猜出是谁说的？不能则重写
3. 情绪越强烈台词越短
4. 消除"死掉的台词"，替换为"活着的台词"
5. 确保潜台词到位
6. 台词字数与标注时长匹配

当前剧本：
{st.session_state.episodes[ep]}

请输出优化后的完整剧本。"""
            
            messages = st.session_state.messages + [{"role": "user", "content": optimize_prompt}]
            with st.spinner("🔄 正在优化台词..."):
                response = call_api_streaming(messages)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    st.session_state.episodes[ep] = full_text
                    st.session_state.messages = messages + [{"role": "assistant", "content": full_text}]
                    st.success("✅ 台词优化完成！")
        else:
            st.warning(f"⚠️ 第{ep}集剧本尚未生成")
    
    # 优化画面
    if btn_optimize_visual:
        ep = episode_num
        if ep in st.session_state.episodes:
            optimize_prompt = f"""请只优化第{ep}集剧本的画面描写部分。

要求：
1. 每个分镜必须有一个"不寻常的具体细节"
2. 用声音锚定空间
3. 光源必须具体
4. 身体的失控比表情形容词有力
5. 反差动作比直球动作有力
6. 消除"死掉的画面描写"
7. 每个分镜≥3个连续动作事件
8. 确保每个分镜有时间流动感

当前剧本：
{st.session_state.episodes[ep]}

请输出优化后的完整剧本。"""
            
            messages = st.session_state.messages + [{"role": "user", "content": optimize_prompt}]
            with st.spinner("🔄 正在优化画面..."):
                response = call_api_streaming(messages)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    st.session_state.episodes[ep] = full_text
                    st.session_state.messages = messages + [{"role": "assistant", "content": full_text}]
                    st.success("✅ 画面优化完成！")
        else:
            st.warning(f"⚠️ 第{ep}集剧本尚未生成")
    
    # 优化情绪
    if btn_optimize_emotion:
        ep = episode_num
        if ep in st.session_state.episodes:
            optimize_prompt = f"""请只优化第{ep}集剧本的情绪节奏部分。

要求：
1. 检查情绪过山车强度是否足够
2. 开场15秒是否有情绪冲击
3. 结尾悬念钩子是否足够强
4. 集内是否有足够的情绪急转
5. 根据题材引擎选用合适的情绪手法（弹簧法/磁铁法/错位法/橡皮筋法）
6. 确保≥65%情绪转折来自人物互动/环境碰撞

当前剧本：
{st.session_state.episodes[ep]}

请输出优化后的完整剧本。"""
            
            messages = st.session_state.messages + [{"role": "user", "content": optimize_prompt}]
            with st.spinner("🔄 正在优化情绪..."):
                response = call_api_streaming(messages)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    st.session_state.episodes[ep] = full_text
                    st.session_state.messages = messages + [{"role": "assistant", "content": full_text}]
                    st.success("✅ 情绪优化完成！")
        else:
            st.warning(f"⚠️ 第{ep}集剧本尚未生成")
    
    # 显示已生成的剧本
    st.markdown("---")
    if st.session_state.episodes:
        st.markdown("### 📜 已生成剧本")
        ep_list = sorted(st.session_state.episodes.keys())
        
        for ep in ep_list:
            with st.expander(f"🎬 第{ep}集", expanded=(ep == episode_num)):
                st.markdown(st.session_state.episodes[ep])
                
                # 导出按钮
                export_content = st.session_state.episodes[ep]
                st.download_button(
                    f"📥 导出第{ep}集",
                    data=export_content,
                    file_name=f"第{ep}集_剧本.md",
                    mime="text/markdown",
                    key=f"export_ep_{ep}"
                )
    else:
        st.info("💡 尚未生成任何剧本。请先完成全局提炼，然后点击「生成剧本」。")

# ============================================================
# Tab 2: 质检报告
# ============================================================
with main_tabs[1]:
    if btn_review:
        ep = episode_num
        if ep not in st.session_state.episodes:
            st.warning(f"⚠️ 第{ep}集剧本尚未生成，无法进行质检")
        else:
            # 获取对应章节文本
            if ep_chapter_select:
                novel_text = get_combined_novel_text(ep_chapter_select)
            else:
                novel_text = get_combined_novel_text()
            
            script = st.session_state.episodes[ep]
            review_prompt = build_review_prompt(ep, script, novel_text)
            
            # 使用质检模型（如果设定了）
            review_messages = [{"role": "user", "content": review_prompt}]
            
            # 如果有单独的质检模型，临时切换
            original_model = st.session_state.model_id
            if st.session_state.get("review_model"):
                st.session_state.model_id = st.session_state["review_model"]
            
            with st.spinner(f"🔍 正在对第{ep}集进行详细质检..."):
                response = call_api_streaming(review_messages, REVIEW_SYSTEM_PROMPT)
                if response:
                    container = st.empty()
                    full_text = ""
                    for chunk in process_stream(response):
                        full_text += chunk
                        container.markdown(full_text)
                    
                    st.session_state.review_results[ep] = full_text
                    st.success(f"✅ 第{ep}集质检完成！")
            
            # 恢复模型
            st.session_state.model_id = original_model
    
    # 显示质检结果
    if st.session_state.review_results:
        st.markdown("### 📊 质检报告列表")
        for ep, review in sorted(st.session_state.review_results.items()):
            with st.expander(f"🔍 第{ep}集 质检报告", expanded=(ep == episode_num)):
                st.markdown(review)
                
                # 基于质检结果的快速修改
                col_fix1, col_fix2 = st.columns(2)
                with col_fix1:
                    if st.button(f"🔧 根据质检自动修改第{ep}集", key=f"auto_fix_{ep}"):
                        fix_prompt = f"""根据以下质检报告，修改第{ep}集剧本中所有7分以下的问题项。

质检报告：
{review}

原剧本：
{st.session_state.episodes[ep]}

请输出修改后的完整剧本，并在修改的地方用【修改】标注说明改了什么。"""
                        
                        fix_messages = st.session_state.messages + [
                            {"role": "user", "content": fix_prompt}
                        ]
                        
                        with st.spinner("🔄 正在根据质检报告修改..."):
                            response = call_api_streaming(fix_messages)
                            if response:
                                fix_container = st.empty()
                                full_text = ""
                                for chunk in process_stream(response):
                                    full_text += chunk
                                    fix_container.markdown(full_text)
                                st.session_state.episodes[ep] = full_text
                                st.success(f"✅ 第{ep}集已根据质检报告修改！")
                
                with col_fix2:
                    st.download_button(
                        f"📥 导出质检报告",
                        data=review,
                        file_name=f"第{ep}集_质检报告.md",
                        mime="text/markdown",
                        key=f"export_review_{ep}"
                    )
    else:
        st.info("💡 尚无质检报告。请先生成剧本，然后点击「质量检查」。")

# ============================================================
# Tab 3: 开场方案
# ============================================================
with main_tabs[2]:
    if st.session_state.opening_designs:
        st.markdown("### 🎯 开场方案（6套）")
        st.markdown(st.session_state.opening_designs)
        
        st.markdown("---")
        opening_choice = st.text_input(
            "请选择开场方案编号（1-6），或输入自定义要求",
            placeholder="例如：3 或 '结合方案2和5的元素'",
            key="opening_choice_input"
        )
        
        if opening_choice and st.button("✅ 确认开场方案", key="confirm_opening"):
            st.session_state["selected_opening"] = opening_choice
            st.success(f"✅ 已选择开场方案：{opening_choice}")
    else:
        st.info("💡 点击「设计开场」生成6套开场方案")

# ============================================================
# Tab 4: 自由对话
# ============================================================
with main_tabs[3]:
    st.markdown("### 💬 与AI编剧自由对话")
    st.caption("可以讨论剧本细节、修改特定分镜、调整角色设定等")
    
    # 显示对话历史（仅用户消息和AI回复的最近几轮）
    chat_display = st.session_state.get("chat_history", [])
    for msg in chat_display[-10:]:  # 显示最近10轮
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"][:500] + ("..." if len(msg["content"]) > 500 else ""))
        else:
            st.chat_message("assistant").markdown(msg["content"])
    
    # 输入框
    user_input = st.chat_input("输入你的问题或指令...", key="chat_input")
    
    if user_input:
        # 初始化chat_history
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        
        # 构建上下文
        context = ""
        if st.session_state.global_analysis:
            context += f"\n\n【全局提炼结果摘要】\n{st.session_state.global_analysis[:2000]}"
        if st.session_state.episodes:
            latest_ep = max(st.session_state.episodes.keys())
            context += f"\n\n【最新剧本（第{latest_ep}集）摘要】\n{st.session_state.episodes[latest_ep][:2000]}"
        
        full_user_msg = f"""当前项目背景信息：{context}

用户问题/指令：{user_input}"""
        
        chat_messages = [{"role": "user", "content": full_user_msg}]
        
        with st.chat_message("assistant"):
            response = call_api_streaming(chat_messages)
            if response:
                container = st.empty()
                full_text = ""
                for chunk in process_stream(response):
                    full_text += chunk
                    container.markdown(full_text)
                
                st.session_state["chat_history"].append({"role": "assistant", "content": full_text})

# ============================================================
# 页脚信息
# ============================================================
st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.8rem;">
    🎬 影视化视觉翻译引擎 V3.2 | 基于微短剧生成3.1系统指令 | 
    接入第三方AI模型 | 支持Streamlit Cloud在线运行
    </div>""",
    unsafe_allow_html=True
)
