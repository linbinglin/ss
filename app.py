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
# 系统提示词
# ============================================================
SYSTEM_PROMPT = """【微短剧生成 3.1 系统指令】

═══════════════════════════════════════
第零法则：视觉翻译（一切规则之上的规则）
═══════════════════════════════════════

小说是给眼睛的——读者靠文字在脑中自己生成画面。
剧本是给画面的——观众只能看到或听到你拍给他看的东西。

你的工作是——把小说用文字"告诉"读者的一切，全部翻译成摄像机能拍到的画面,并搭配人物的台词（音效）来增加代入感！

禁止对角色OOC，人物的台词、行为、举止都必须符合小说里的人设，绝不能做出违背角色性格的任何行为和说话方式！

【翻译铁律】
铁律一：小说的"叙述"必须翻译为"动作流"
铁律二：小说的"心理描写"必须翻译为"身体反应搭配角色内心独白"
铁律三：小说的"设定/背景交代"必须翻译为"环境展示"
铁律四：台词的正确用法——给画面增加代入感

【视觉翻译的核心公式】
第一步——识别原文类型：
A. 告诉读者发生了什么事 → 翻译为动作流
B. 告诉读者角色的感受 → 翻译为身体反应
C. 告诉读者世界观/背景 → 翻译为环境展示
D. 告诉读者角色的能力/身份 → 翻译为能力展示的动作场景
E. 告诉读者人物关系 → 翻译为两人互动时的空间距离/肢体语言/视线交汇方式

第二步——台词的适配：画面呈现张力，台词赋予情感！

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集分镜数量自由抉择 | 无第三人称旁白 | 集集强钩子。

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色的性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。允许角色用第一人称内心OS展现性格，严禁第三人称旁白。
③【伏笔】每一个重大转折之前，必须存在至少一个视觉/听觉微伏笔。
④【潜台词】角色嘴上说的话与真实意图之间必须存在缝隙。台词传递表面意思，身体泄露真相。
⑤【钩子铁律】前15秒必须制造具体的疑问或情绪冲击。每集结尾必须制造悬念。集内至少一次情绪急转。

═══════════════════════════════════════
角色驱动卡系统
═══════════════════════════════════════
为每个主要角色建立驱动卡：核心人格、说话DNA（句式习惯、口头禅、绝对不会说的话、示范台词）、行为DNA（愤怒/心软/恐惧/说谎/得意时的物理反应）、红线、关系动态。

═══════════════════════════════════════
画面描写的血肉感
═══════════════════════════════════════
画面规律：
→ 必须有一个"不寻常的具体细节"
→ 用声音锚定空间
→ 光源必须具体
→ 身体的失控比表情形容词有力一万倍
→ 反差动作比直球动作有力

台词规律：
→ 情绪越强烈，台词越短。暴怒时沉默或单字。
→ 人经常答非所问——问A答B，因为脑子里在想C。
→ 真正伤人的话说得很平静。真正心软的话藏在骂人里。
→ 真人会说废话、说一半咽回去、词不达意。

═══════════════════════════════════════
时长感知校准系统
═══════════════════════════════════════
【2秒】一个快速表情+简短动作+1-3字台词+一个音效
【5秒】一个完整肢体动作 / 5-12字短台词+表情
【10秒】一段对话交锋+复杂连续动作+环境氛围+微型情绪转折
【14秒】2-3句对话+双方反应+铺垫→触发→爆发的完整微型事件

═══════════════════════════════════════
分镜格式与密度标准
═══════════════════════════════════════
【分镜XX】
场景：地点 · 时间 · 天气 · 光线
内容：画面+台词(内心OS)+音效
衔接点：[本镜最后一帧 → 下一镜第一帧画面]

每个分镜10-14秒，必须包含：≥3个连续动作事件、≥1个环境/声音细节、≥1个角色微表情或身体细节。

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

检查10个维度（每项1-10分）：
1. 角色一致性 2. 画面具象度 3. 台词活人感 4. 视觉翻译完成度 
5. 分镜密度 6. 因果链完整度 7. 情绪过山车强度 8. 上下镜衔接流畅度 
9. 无旁白叙事清晰度 10. 原著还原度

对每条分镜逐一输出检查报告（含评分表格+关键问题+修改建议），最后给出整集汇总。
同时执行五个敌对视角攻击（普通观众/竞品编剧/原著粉/剪辑师/导演）。
7分以下的项目必须指出具体问题和修改建议。"""

# ============================================================
# Session State 初始化
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
# API调用 (修复核心)
# ============================================================
def get_active_model():
    model = st.session_state.model_id
    if model == "自定义模型":
        model = st.session_state.custom_model
    return model if model else "deepseek-chat"

def call_api_streaming(messages, system_prompt=SYSTEM_PROMPT):
    """流式调用API - 增强错误处理"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = get_active_model()
    
    if not api_key:
        st.error("❌ 请先在侧边栏配置 API Key")
        return None
    if not api_base:
        st.error("❌ 请先在侧边栏配置接口地址")
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
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=180
        )
        resp.raise_for_status()
        return resp
    except requests.exceptions.Timeout:
        st.error("❌ API请求超时（180秒），请检查网络或稍后重试")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到API服务器，请检查接口地址是否正确")
        return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "未知"
        error_body = ""
        try:
            error_body = e.response.text[:500] if e.response is not None else ""
        except Exception:
            pass
        st.error(f"❌ API返回错误 (HTTP {status_code}): {error_body}")
        return None
    except Exception as e:
        st.error(f"❌ API调用异常: {type(e).__name__}: {str(e)}")
        return None

def process_stream(response):
    """处理流式响应 - 修复IndexError和各种边界情况"""
    if response is None:
        return
    
    try:
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
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
            
            # 安全地提取content - 修复IndexError的核心
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                continue
            
            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                continue
            
            delta = first_choice.get("delta")
            if not delta or not isinstance(delta, dict):
                continue
            
            content = delta.get("content")
            if content:
                yield content
                
    except requests.exceptions.ChunkedEncodingError:
        st.warning("⚠️ 流式传输中断，已保存已接收的内容")
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ 连接中断，已保存已接收的内容")
    except Exception as e:
        st.warning(f"⚠️ 流式处理异常: {type(e).__name__}: {str(e)}")

def stream_to_container(response, container):
    """统一的流式输出到容器的函数"""
    if response is None:
        return ""
    full_text = ""
    for chunk in process_stream(response):
        full_text += chunk
        container.markdown(full_text)
    return full_text

def call_api_non_streaming(messages, system_prompt=SYSTEM_PROMPT):
    """非流式调用API"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = get_active_model()
    
    if not api_key or not api_base:
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 8192
    }
    
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        resp.raise_for_status()
        result = resp.json()
        
        choices = result.get("choices")
        if not choices or len(choices) == 0:
            st.error("❌ API返回了空的choices")
            return None
        
        message = choices[0].get("message", {})
        return message.get("content", "")
        
    except requests.exceptions.Timeout:
        st.error("❌ API请求超时")
        return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "未知"
        st.error(f"❌ API错误 (HTTP {status_code})")
        return None
    except Exception as e:
        st.error(f"❌ 调用失败: {type(e).__name__}: {str(e)}")
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
    if names is None:
        names = st.session_state.chapter_order
    parts = []
    for n in names:
        if n in st.session_state.chapters:
            parts.append(f"【{n}】\n{st.session_state.chapters[n]}")
    return "\n\n".join(parts)

# ============================================================
# Prompt构建
# ============================================================
def build_analysis_prompt(text):
    return f"""【微短剧3.1启动】

以下是需要改编的小说原文：

{text}

请执行【第1轮：全局提炼】，输出：
1. 一句话故事核心
2. 每个主要角色的【驱动卡】（必须从原著提取原句作为说话DNA示范）
3. 故事大纲（分阶段）+ 各阶段核心情绪类型
4. 必须保留的核心情节节点（10-20个）
5. 需要补充的逻辑链节点
6. 全剧环境/氛围基调 + 天气光影变化建议
7. 视觉强场景与短剧记忆点（5-8个瞬间，每个3-5句具体画面描述）"""

def build_opening_prompt():
    return """请执行【第2轮：开场手法设计】

输出6条完全不同的第1集开场方案，每条包含：
- 开场类型标签
- 前30秒逐秒画面描述（1-3秒/4-10秒/11-20秒/21-30秒）
- 30秒后如何衔接主线"""

def build_episode_prompt(ep, text, opening=""):
    mem = st.session_state.memory
    mem_str = ""
    if mem.get("storyline"):
        mem_str = f"""
📌 一句话主线：{mem['storyline']}
📌 核心人物：{mem['characters']}
📌 当前进度：第{mem['progress']}集
📌 上集结尾：{mem['last_ending']}
📌 已埋伏笔：{mem['pending_foreshadow']}
📌 下集引爆：{mem['next_foreshadow']}
📌 情绪轨迹：{mem['emotion_track']}"""

    return f"""请执行【第3轮：剧本生成】—— 第{ep}集
{mem_str}
{"选择的开场方案：" + opening if opening else ""}

参考小说原文：
{text}

严格执行：
前置A——编剧内心独白
前置B——本集结构速写（开场钩子/中段高潮/结尾钩子/伏笔）
前置C——角色驱动卡调用声明
前置D——影视化排雷扫描

然后输出完整分镜剧本，每镜10-14秒。

分镜格式：
【分镜XX】
场景：地点 · 时间 · 天气 · 光线
画面：[内容+台词(内心OS)+音效]
衔接点：[本镜最后一帧 → 下一镜第一帧画面]

最后更新全局记忆。"""

def build_review_prompt(ep, script, text):
    return f"""请对第{ep}集剧本逐条分镜进行详细质检。

【小说原文】
{text}

【剧本分镜】
{script}

逐镜检查10个维度（1-10分），输出每条分镜的检查报告表格+关键问题+修改建议。
然后五个敌对视角攻击+整集汇总+细节自检清单。
7分以下必须给出具体修改方案。"""

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-group-title">🔌 API 配置</div>', unsafe_allow_html=True)

    api_base = st.text_input("接口地址", value=st.session_state.api_base,
                             key="sb_api_base", placeholder="https://yunwu.ai/v1/")
    st.session_state.api_base = api_base

    api_key = st.text_input("API Key", value=st.session_state.api_key,
                            type="password", key="sb_api_key", placeholder="sk-...")
    st.session_state.api_key = api_key

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">🤖 模型配置</div>', unsafe_allow_html=True)

    model_options = [
        "deepseek-chat", "deepseek-reasoner",
        "claude-sonnet-4-20250514", "claude-opus-4-20250514",
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini",
        "gemini-2.5-pro-preview-06-05", "自定义模型"
    ]

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        sel_model = st.selectbox("生成模型", model_options,
            index=model_options.index(st.session_state.model_id) if st.session_state.model_id in model_options else 0,
            key="sb_model")
        st.session_state.model_id = sel_model
    with col_m2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔗", key="sb_test", use_container_width=True, help="测试API连接"):
            with st.spinner("..."):
                r = call_api_non_streaming([{"role": "user", "content": "回复OK两个字"}], "你是助手。")
                if r:
                    st.success(f"✅ 成功")
                else:
                    st.error("❌ 失败")

    if sel_model == "自定义模型":
        cm = st.text_input("模型ID", value=st.session_state.custom_model, key="sb_custom",
                           placeholder="例如: deepseek-v3")
        st.session_state.custom_model = cm

    review_opts = ["与生成模型相同"] + model_options
    rev_model = st.selectbox("质检模型", review_opts, key="sb_rev_model")
    st.session_state.review_model = None if rev_model == "与生成模型相同" else rev_model

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">🎯 模式</div>', unsafe_allow_html=True)

    mode = st.radio("工作模式", ["📋 默认模式", "⚡ 快速模式"],
                    key="sb_mode", label_visibility="collapsed")
    st.session_state.mode = "默认" if "默认" in mode else "快速"

    st.markdown("---")
    st.markdown('<div class="sidebar-group-title">💾 数据管理</div>', unsafe_allow_html=True)

    if st.button("📌 查看全局记忆", use_container_width=True, key="sb_mem"):
        st.session_state["show_memory_modal"] = True

    if st.session_state.episodes:
        all_data = {
            "global_analysis": st.session_state.global_analysis,
            "episodes": {str(k): v for k, v in st.session_state.episodes.items()},
            "reviews": {str(k): v for k, v in st.session_state.review_results.items()},
            "memory": st.session_state.memory
        }
        st.download_button(
            "📦 导出全部数据", use_container_width=True, key="sb_export",
            data=json.dumps(all_data, ensure_ascii=False, indent=2),
            file_name=f"剧本数据_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

    if st.button("🗑️ 重置所有数据", use_container_width=True, key="sb_reset"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_session_state()
        st.rerun()

# ============================================================
# 顶部标题栏
# ============================================================
step_names = ["导入章节", "全局提炼", "开场设计", "生成剧本", "质检优化"]
current = st.session_state.current_step

st.markdown(f"""
<div class="header-bar">
    <div class="header-left">
        <div class="header-title">🎬 影视化视觉翻译引擎 V3.2</div>
        <div class="header-sub">小说改编微短剧系统 · 严格遵循视觉翻译法则 · 杜绝文字转文字 · 台词给画面增加代入感</div>
    </div>
    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
        <span class="header-badge">📚 {len(st.session_state.chapter_order)} 章</span>
        <span class="header-badge">🎬 {len(st.session_state.episodes)} 集</span>
        <span class="header-badge">🤖 {get_active_model()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 步骤指示器
steps_html = ""
for i, name in enumerate(step_names):
    cls = "done" if i < current else ("active" if i == current else "")
    icon = "✓" if i < current else str(i + 1)
    steps_html += f'<div class="step-item {cls}"><span class="step-num">{icon}</span>{name}</div>'
st.markdown(f'<div class="step-indicator">{steps_html}</div>', unsafe_allow_html=True)

# 全局记忆弹窗
if st.session_state.get("show_memory_modal"):
    mem = st.session_state.memory
    with st.expander("📌 全局记忆面板", expanded=True):
        st.markdown(f"""
<div class="memory-panel">
<div class="memory-item"><span class="memory-key">📌 主线：</span><span class="memory-val">{mem.get('storyline') or '未设定'}</span></div>
<div class="memory-item"><span class="memory-key">👥 人物：</span><span class="memory-val">{mem.get('characters') or '未设定'}</span></div>
<div class="memory-item"><span class="memory-key">📍 进度：</span><span class="memory-val">{mem.get('progress') or '未开始'}</span></div>
<div class="memory-item"><span class="memory-key">🔚 上集结尾：</span><span class="memory-val">{mem.get('last_ending') or '无'}</span></div>
<div class="memory-item"><span class="memory-key">🔮 埋下伏笔：</span><span class="memory-val">{mem.get('pending_foreshadow') or '无'}</span></div>
<div class="memory-item"><span class="memory-key">💥 下集引爆：</span><span class="memory-val">{mem.get('next_foreshadow') or '无'}</span></div>
<div class="memory-item"><span class="memory-key">❤️ 情绪轨迹：</span><span class="memory-val">{mem.get('emotion_track') or '无'}</span></div>
</div>
""", unsafe_allow_html=True)
        if st.button("关闭", key="close_mem"):
            st.session_state["show_memory_modal"] = False
            st.rerun()

# ============================================================
# 步骤一：导入小说章节
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">📖</span><span class="card-title">步骤一：导入小说章节原文</span>
<span class="card-subtitle">支持 .txt / .md 文件上传和文本粘贴</span>
</div></div>""", unsafe_allow_html=True)

col_add, col_list = st.columns([1, 1])

with col_add:
    add_tabs = st.tabs(["📁 上传文件", "✍️ 粘贴文本"])

    with add_tabs[0]:
        uploaded = st.file_uploader(
            "选择文件", type=["txt", "md", "text"],
            accept_multiple_files=True, key="uploader",
            help="200KB/文件上限，支持批量上传"
        )
        if uploaded:
            for uf in uploaded:
                if uf.size > 200 * 1024:
                    st.warning(f"⚠️ {uf.name} 超过200KB")
                    continue
                try:
                    content = uf.read().decode("utf-8", errors="ignore")
                except Exception:
                    content = ""
                ch_name = uf.name.rsplit(".", 1)[0] if "." in uf.name else uf.name
                if ch_name not in st.session_state.chapters and content:
                    add_chapter(ch_name, content)
                    st.success(f"✅ {ch_name} ({len(content)}字)")

    with add_tabs[1]:
        pname = st.text_input("章节名称", placeholder="第1章 重生归来", key="p_name")
        pcontent = st.text_area("章节内容", height=180, placeholder="粘贴小说原文...", key="p_content")
        if st.button("➕ 添加章节", key="p_add", use_container_width=True, type="primary"):
            if pname and pcontent:
                add_chapter(pname, pcontent)
                st.success(f"✅ 已添加 {pname}")
                st.rerun()
            else:
                st.warning("请填写名称和内容")

with col_list:
    st.markdown("**已导入章节**")
    if st.session_state.chapter_order:
        total_chars = sum(len(st.session_state.chapters.get(c, "")) for c in st.session_state.chapter_order)

        st.markdown(f"""
<div class="stats-bar">
<div class="stat-item"><div class="stat-value">{len(st.session_state.chapter_order)}</div><div class="stat-label">章节数</div></div>
<div class="stat-item"><div class="stat-value">{total_chars:,}</div><div class="stat-label">总字数</div></div>
<div class="stat-item"><div class="stat-value">{total_chars // max(len(st.session_state.chapter_order), 1):,}</div><div class="stat-label">平均字数</div></div>
</div>
""", unsafe_allow_html=True)

        for i, ch in enumerate(st.session_state.chapter_order):
            ct = st.session_state.chapters.get(ch, "")
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                st.markdown(f"""<div class="chapter-item">
<div class="chapter-icon">{i + 1}</div>
<div class="chapter-info"><div class="chapter-name">{ch}</div>
<div class="chapter-meta">{len(ct):,}字</div></div>
</div>""", unsafe_allow_html=True)
            with c2:
                if st.button("👁️", key=f"v_{i}", help="预览内容"):
                    k = f"exp_{i}"
                    st.session_state[k] = not st.session_state.get(k, False)
            with c3:
                if st.button("🗑️", key=f"d_{i}", help="删除章节"):
                    remove_chapter(ch)
                    st.rerun()

            if st.session_state.get(f"exp_{i}"):
                with st.expander(f"📖 {ch}", expanded=True):
                    st.text_area("", ct, height=200, disabled=True, key=f"pv_{i}")
    else:
        st.markdown("""<div class="empty-state">
<div class="empty-icon">📚</div>
<div class="empty-text">暂无章节</div>
<div class="empty-hint">从左侧上传文件或粘贴文本</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# 步骤二：全局提炼
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">🔍</span><span class="card-title">步骤二：章节拆解与取舍决策（全局提炼）</span>
<span class="card-subtitle">AI深度分析小说结构、角色、情节</span>
</div></div>""", unsafe_allow_html=True)

col_s2a, col_s2b = st.columns([1, 1])

with col_s2a:
    st.markdown("**选择参与分析的章节**")
    if st.session_state.chapter_order:
        sel_chs = st.multiselect(
            "选择章节", st.session_state.chapter_order,
            default=st.session_state.chapter_order, key="sel_chs",
            label_visibility="collapsed"
        )
        st.session_state.selected_chapters_for_analysis = sel_chs

        if sel_chs:
            sel_chars = sum(len(st.session_state.chapters.get(c, "")) for c in sel_chs)
            st.info(f"📊 已选 {len(sel_chs)} 章 · {sel_chars:,} 字")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            can_analyze = bool(sel_chs) and bool(st.session_state.api_key)
            do_analysis = st.button("🚀 启动全局提炼", key="do_analysis",
                                    use_container_width=True, type="primary",
                                    disabled=not can_analyze)
        with c_btn2:
            if st.session_state.global_analysis:
                if st.button("🔄 重新提炼", key="redo_analysis", use_container_width=True):
                    st.session_state.global_analysis = ""
                    st.rerun()
    else:
        st.info("💡 请先在步骤一导入章节")
        do_analysis = False

with col_s2b:
    st.markdown("**提炼结果**")

    if do_analysis:
        text = get_combined_text(sel_chs)
        prompt = build_analysis_prompt(text)
        msgs = [{"role": "user", "content": prompt}]

        with st.spinner("🧠 AI正在深度分析小说结构..."):
            resp = call_api_streaming(msgs)
            if resp:
                container = st.empty()
                full = stream_to_container(resp, container)
                if full:
                    st.session_state.global_analysis = full
                    st.session_state.messages = msgs + [{"role": "assistant", "content": full}]
                    st.session_state.current_step = max(st.session_state.current_step, 1)
                    st.success("✅ 全局提炼完成！请确认角色驱动卡后进入下一步。")
                else:
                    st.warning("⚠️ 未收到有效内容，请重试")

    elif st.session_state.global_analysis:
        with st.expander("📋 查看全局提炼结果", expanded=False):
            st.markdown(st.session_state.global_analysis)
        st.markdown('<span class="tag tag-green">✅ 已完成</span>', unsafe_allow_html=True)
    else:
        st.markdown("""<div class="empty-state">
<div class="empty-icon">🔍</div>
<div class="empty-text">等待提炼</div>
<div class="empty-hint">选择章节后点击「启动全局提炼」</div>
</div>""", unsafe_allow_html=True)

# ============================================================
# 步骤三：编剧工作流控制台
# ============================================================
st.markdown("""<div class="card"><div class="card-header">
<span class="card-icon">🎬</span><span class="card-title">步骤三：编剧工作流控制台</span>
<span class="card-subtitle">设计开场 → 生成剧本 → 质检 → 优化迭代</span>
</div></div>""", unsafe_allow_html=True)

# 工具栏
tb1, tb2, tb3 = st.columns([1, 2, 3])
with tb1:
    ep_num = st.number_input("集数", min_value=1, max_value=200,
                             value=st.session_state.current_episode, key="ep_in")
    st.session_state.current_episode = ep_num
with tb2:
    ep_chs = st.multiselect("本集对应章节", st.session_state.chapter_order, key="ep_chs",
                            help="限定参考范围，可节省token")
with tb3:
    analysis_done = bool(st.session_state.global_analysis)
    st.markdown(f"""
<div style="display:flex; gap:8px; align-items:center; padding-top:24px; flex-wrap:wrap;">
<span class="tag tag-blue">📝 第{ep_num}集</span>
<span class="tag tag-purple">🤖 {get_active_model()}</span>
{"<span class='tag tag-green'>✅ 提炼完成</span>" if analysis_done else "<span class='tag tag-yellow'>⚠️ 请先完成提炼</span>"}
</div>
""", unsafe_allow_html=True)

# 功能按钮
bcols = st.columns(7)
btn_labels = [
    ("🎯", "设计开场"), ("🎬", "生成剧本"), ("🔍", "质量检查"),
    ("💬", "优化台词"), ("🎨", "优化画面"), ("❤️", "优化情绪"), ("📦", "批量生成"),
]
btns = {}
for i, (icon, label) in enumerate(btn_labels):
    with bcols[i]:
        btns[label] = st.button(f"{icon} {label}", key=f"btn_{label}",
                                use_container_width=True,
                                type="primary" if label == "生成剧本" else "secondary")

# ============================================================
# 主内容Tabs
# ============================================================
main_tabs = st.tabs(["📝 剧本编辑", "🔍 质检报告", "🎯 开场方案", "💬 自由对话", "📊 数据总览"])

# ─── Tab 1: 剧本编辑 ───
with main_tabs[0]:

    # 设计开场
    if btns["设计开场"]:
        if not analysis_done:
            st.warning("⚠️ 请先完成步骤二（全局提炼）")
        else:
            prompt = build_opening_prompt()
            msgs = st.session_state.messages + [{"role": "user", "content": prompt}]
            with st.spinner("🎯 设计开场方案中..."):
                resp = call_api_streaming(msgs)
                if resp:
                    container = st.empty()
                    full = stream_to_container(resp, container)
                    if full:
                        st.session_state.opening_designs = full
                        st.session_state.messages = msgs + [{"role": "assistant", "content": full}]
                        st.session_state.current_step = max(st.session_state.current_step, 2)
                        st.success("✅ 6套开场方案已生成，请在「开场方案」Tab中查看选择")

    # 生成剧本
    if btns["生成剧本"]:
        if not analysis_done:
            st.warning("⚠️ 请先完成步骤二")
        else:
            text = get_combined_text(ep_chs if ep_chs else None)
            opening = st.session_state.get("selected_opening", "")
            prompt = build_episode_prompt(ep_num, text, opening)
            ctx = st.session_state.messages + [{"role": "user", "content": prompt}]

            with st.spinner(f"🎬 正在生成第{ep_num}集剧本..."):
                resp = call_api_streaming(ctx)
                if resp:
                    container = st.empty()
                    full = stream_to_container(resp, container)
                    if full:
                        st.session_state.episodes[ep_num] = full
                        st.session_state.messages = ctx + [{"role": "assistant", "content": full}]
                        st.session_state.current_step = max(st.session_state.current_step, 3)
                        st.session_state.memory["progress"] = str(ep_num)
                        st.success(f"✅ 第{ep_num}集生成完成！建议点击「质量检查」进行检验。")
                    else:
                        st.warning("⚠️ 未收到有效内容，请重试")

    # 批量生成
    if btns["批量生成"]:
        if not analysis_done:
            st.warning("⚠️ 请先完成步骤二")
        else:
            bc1, bc2 = st.columns(2)
            with bc1:
                batch_start = st.number_input("起始集", 1, 200, ep_num, key="batch_s")
            with bc2:
                batch_end = st.number_input("结束集", 1, 200, min(ep_num + 2, 200), key="batch_e")

            if st.button("🚀 开始批量生成", key="batch_go", type="primary"):
                text = get_combined_text(ep_chs if ep_chs else None)
                for e in range(int(batch_start), int(batch_end) + 1):
                    st.markdown(f"---\n### 🎬 正在生成第{e}集...")
                    prompt = build_episode_prompt(e, text)
                    ctx = st.session_state.messages + [{"role": "user", "content": prompt}]
                    resp = call_api_streaming(ctx)
                    if resp:
                        container = st.empty()
                        full = stream_to_container(resp, container)
                        if full:
                            st.session_state.episodes[e] = full
                            st.session_state.messages = ctx + [{"role": "assistant", "content": full}]
                            st.session_state.memory["progress"] = str(e)
                            st.success(f"✅ 第{e}集完成")
                        else:
                            st.warning(f"⚠️ 第{e}集未收到内容，跳过")
                    else:
                        st.error(f"❌ 第{e}集生成失败，停止批量")
                        break

    # 优化功能
    optimization_configs = {
        "优化台词": ("只优化台词", lambda ep, s: f"""只优化第{ep}集台词。要求：
1. 符合角色说话DNA 2. 遮名可辨 3. 情绪强→台词短 4. 消除死台词 5. 潜台词到位
当前剧本：\n{s}\n输出优化后完整剧本。"""),
        "优化画面": ("只优化画面", lambda ep, s: f"""只优化第{ep}集画面描写。要求：
1. 不寻常具体细节 2. 声音锚定空间 3. 具体光源 4. 身体失控＞表情形容 5. 反差动作 6. ≥3连续动作事件
当前剧本：\n{s}\n输出优化后完整剧本。"""),
        "优化情绪": ("只优化情绪", lambda ep, s: f"""只优化第{ep}集情绪节奏。要求：
1. 过山车强度 2. 开场15秒冲击 3. 结尾悬念 4. 情绪急转 5. 题材引擎手法 6. ≥65%转折来自互动
当前剧本：\n{s}\n输出优化后完整剧本。"""),
    }

    for opt_name, (desc, prompt_fn) in optimization_configs.items():
        if btns[opt_name]:
            if ep_num in st.session_state.episodes:
                prompt = prompt_fn(ep_num, st.session_state.episodes[ep_num])
                msgs = st.session_state.messages + [{"role": "user", "content": prompt}]
                with st.spinner(f"✨ {desc}中..."):
                    resp = call_api_streaming(msgs)
                    if resp:
                        container = st.empty()
                        full = stream_to_container(resp, container)
                        if full:
                            st.session_state.episodes[ep_num] = full
                            st.session_state.messages = msgs + [{"role": "assistant", "content": full}]
                            st.success(f"✅ {opt_name}完成！")
                        else:
                            st.warning("⚠️ 未收到有效内容")
            else:
                st.warning(f"⚠️ 第{ep_num}集尚未生成")

    # 已生成剧本列表
    st.markdown("---")
    if st.session_state.episodes:
        st.markdown("### 📜 已生成剧本")
        sorted_eps = sorted(st.session_state.episodes.keys())
        ep_tab_labels = [f"第{e}集" for e in sorted_eps]
        ep_tabs = st.tabs(ep_tab_labels)

        for idx, e in enumerate(sorted_eps):
            with ep_tabs[idx]:
                script = st.session_state.episodes[e]
                shot_count = len(re.findall(r'【分镜\s*\d+】', script))

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("分镜数", shot_count if shot_count else "—")
                mc2.metric("预估时长", f"{shot_count * 12}s" if shot_count else "—")
                mc3.metric("字数", f"{len(script):,}")
                mc4.metric("质检", "✅ 已检" if e in st.session_state.review_results else "⏳ 待检")

                st.markdown(script)

                dl1, dl2 = st.columns(2)
                with dl1:
                    st.download_button(f"📥 导出第{e}集", script,
                                       f"第{e}集_剧本.md", "text/markdown", key=f"dl_ep_{e}")
                with dl2:
                    if st.button(f"📋 显示纯文本", key=f"code_{e}"):
                        st.code(script, language="markdown")
    else:
        st.markdown("""<div class="empty-state">
<div class="empty-icon">🎬</div>
<div class="empty-text">尚未生成剧本</div>
<div class="empty-hint">完成全局提炼后，点击「生成剧本」开始创作</div>
</div>""", unsafe_allow_html=True)

# ─── Tab 2: 质检报告 ───
with main_tabs[1]:
    if btns["质量检查"]:
        if ep_num not in st.session_state.episodes:
            st.warning(f"⚠️ 第{ep_num}集尚未生成")
        else:
            text = get_combined_text(ep_chs if ep_chs else None)
            script = st.session_state.episodes[ep_num]
            rprompt = build_review_prompt(ep_num, script, text)
            rmsgs = [{"role": "user", "content": rprompt}]

            # 临时切换质检模型
            orig_model = st.session_state.model_id
            if st.session_state.review_model:
                st.session_state.model_id = st.session_state.review_model

            with st.spinner(f"🔍 对照原文逐镜质检第{ep_num}集..."):
                resp = call_api_streaming(rmsgs, REVIEW_SYSTEM_PROMPT)
                if resp:
                    container = st.empty()
                    full = stream_to_container(resp, container)
                    if full:
                        st.session_state.review_results[ep_num] = full
                        st.session_state.current_step = max(st.session_state.current_step, 4)
                        st.success(f"✅ 第{ep_num}集质检完成！")
                    else:
                        st.warning("⚠️ 未收到质检内容")

            # 恢复模型
            st.session_state.model_id = orig_model

    if st.session_state.review_results:
        for e in sorted(st.session_state.review_results.keys()):
            review = st.session_state.review_results[e]
            with st.expander(f"📊 第{e}集 质检报告", expanded=(e == ep_num)):
                st.markdown(review)

                fix_c1, fix_c2, fix_c3 = st.columns(3)
                with fix_c1:
                    if st.button(f"🔧 自动修改第{e}集", key=f"fix_{e}", type="primary"):
                        fix_prompt = f"""根据质检报告修改第{e}集所有7分以下项目。
质检报告：\n{review}\n\n原剧本：\n{st.session_state.episodes[e]}\n
输出修改后完整剧本，修改处用【✏️修改】标注。"""
                        fix_msgs = st.session_state.messages + [{"role": "user", "content": fix_prompt}]
                        with st.spinner("🔧 修改中..."):
                            resp = call_api_streaming(fix_msgs)
                            if resp:
                                ct = st.empty()
                                full = stream_to_container(resp, ct)
                                if full:
                                    st.session_state.episodes[e] = full
                                    st.success(f"✅ 第{e}集已修改")
                with fix_c2:
                    st.download_button(f"📥 导出报告", review,
                                       f"第{e}集_质检.md", "text/markdown", key=f"dl_rv_{e}")
                with fix_c3:
                    if st.button(f"🔄 重新质检", key=f"re_rv_{e}"):
                        if e in st.session_state.review_results:
                            del st.session_state.review_results[e]
                        st.rerun()
    else:
        st.markdown("""<div class="empty-state">
<div class="empty-icon">🔍</div>
<div class="empty-text">暂无质检报告</div>
<div class="empty-hint">生成剧本后点击「质量检查」，AI将对照原文逐条分镜检查</div>
</div>""", unsafe_allow_html=True)

# ─── Tab 3: 开场方案 ───
with main_tabs[2]:
    if st.session_state.opening_designs:
        st.markdown("### 🎯 6套开场方案")
        st.markdown(st.session_state.opening_designs)
        st.markdown("---")
        oc1, oc2 = st.columns([3, 1])
        with oc1:
            choice = st.text_input("选择方案编号或自定义",
                                   placeholder="输入 1-6 或自定义描述", key="open_choice")
        with oc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ 确认", key="confirm_open", use_container_width=True, type="primary"):
                if choice:
                    st.session_state["selected_opening"] = choice
                    st.success(f"✅ 已选方案：{choice}")
    else:
        st.markdown("""<div class="empty-state">
<div class="empty-icon">🎯</div>
<div class="empty-text">等待设计</div>
<div class="empty-hint">点击「设计开场」生成6套方案</div>
</div>""", unsafe_allow_html=True)

# ─── Tab 4: 自由对话 ───
with main_tabs[3]:
    st.markdown("### 💬 与AI编剧自由对话")
    st.caption("讨论剧本细节、修改分镜、调整角色、任何创作问题")

    for msg in st.session_state.chat_history[-20:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("输入问题或指令...", key="chat_in")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        ctx_parts = []
        if st.session_state.global_analysis:
            ctx_parts.append(f"【全局提炼摘要】{st.session_state.global_analysis[:3000]}")
        if st.session_state.episodes:
            latest = max(st.session_state.episodes.keys())
            ctx_parts.append(f"【最新第{latest}集摘要】{st.session_state.episodes[latest][:2000]}")

        if ctx_parts:
            full_msg = f"项目背景：\n{''.join(ctx_parts)}\n\n用户指令：{user_input}"
        else:
            full_msg = user_input

        msgs = [{"role": "user", "content": full_msg}]

        with st.chat_message("assistant"):
            resp = call_api_streaming(msgs)
            if resp:
                ct = st.empty()
                full = stream_to_container(resp, ct)
                if full:
                    st.session_state.chat_history.append({"role": "assistant", "content": full})

# ─── Tab 5: 数据总览 ───
with main_tabs[4]:
    st.markdown("### 📊 项目数据总览")

    ov1, ov2, ov3, ov4 = st.columns(4)
    ov1.metric("📚 导入章节", len(st.session_state.chapter_order))
    ov2.metric("🎬 已生成集数", len(st.session_state.episodes))
    ov3.metric("✅ 已质检集数", len(st.session_state.review_results))
    total_ep_chars = sum(len(v) for v in st.session_state.episodes.values()) if st.session_state.episodes else 0
    ov4.metric("📝 总字数", f"{total_ep_chars:,}")

    st.markdown("---")

    if st.session_state.episodes:
        st.markdown("#### 📋 各集概要")
        for e in sorted(st.session_state.episodes.keys()):
            script = st.session_state.episodes[e]
            shots = len(re.findall(r'【分镜\s*\d+】', script))
            reviewed = "✅" if e in st.session_state.review_results else "⏳"
            st.markdown(f"""<div class="chapter-item">
<div class="chapter-icon" style="background:linear-gradient(135deg, #3182ce, #2b6cb0);">{e}</div>
<div class="chapter-info">
<div class="chapter-name">第{e}集 <span class="tag tag-blue">{shots}个分镜</span> <span class="tag tag-green">~{shots * 12}s</span></div>
<div class="chapter-meta">{len(script):,}字 · 质检: {reviewed}</div>
</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📌 全局记忆（可编辑）")
    mem = st.session_state.memory
    for label, key in [
        ("一句话主线", "storyline"), ("核心人物", "characters"),
        ("当前进度", "progress"), ("上集结尾", "last_ending"),
        ("已埋伏笔", "pending_foreshadow"), ("下集引爆", "next_foreshadow"),
        ("情绪轨迹", "emotion_track")
    ]:
        new_val = st.text_input(f"📌 {label}", value=mem.get(key, ""), key=f"mem_edit_{key}")
        st.session_state.memory[key] = new_val

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; padding: 16px 0;">
<span style="color:#a0aec0; font-size:0.75rem;">
🎬 影视化视觉翻译引擎 V3.2 · 基于微短剧3.1系统指令 · 
接入第三方AI · Streamlit Cloud · 模型：{get_active_model()}
</span>
</div>
""", unsafe_allow_html=True)
