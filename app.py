import streamlit as st
import requests
import json
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
# 自定义 CSS（简约风格）
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* 主体背景 */
    .stApp {
        background-color: #0f0f0f;
        color: #e8e8e8;
    }

    /* 隐藏默认 Streamlit 头部菜单 */
    #MainMenu, footer, header {visibility: hidden;}

    /* 标题区域 */
    .main-title {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
    }
    .main-title h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.05em;
        margin-bottom: 0.2rem;
    }
    .main-title p {
        color: #888888;
        font-size: 0.95rem;
        margin-top: 0;
    }

    /* 分隔线 */
    .divider {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 1.5rem 0;
    }

    /* 输入标签 */
    .stTextArea label, .stTextInput label, .stSelectbox label, .stFileUploader label {
        color: #cccccc !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    /* 文本框 */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #e8e8e8 !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #555555 !important;
        box-shadow: none !important;
    }

    /* 文本输入框 */
    .stTextInput input {
        background-color: #1a1a1a !important;
        color: #e8e8e8 !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #555555 !important;
        box-shadow: none !important;
    }

    /* 下拉框 */
    .stSelectbox > div > div {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        color: #e8e8e8 !important;
        border-radius: 8px !important;
    }

    /* 文件上传 */
    .stFileUploader > div {
        background-color: #1a1a1a !important;
        border: 1px dashed #333333 !important;
        border-radius: 8px !important;
    }

    /* 按钮 */
    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: opacity 0.2s ease !important;
    }
    .stButton > button:hover {
        opacity: 0.85 !important;
    }
    .stButton > button:disabled {
        opacity: 0.4 !important;
    }

    /* 信息提示框 */
    .info-box {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-size: 0.88rem;
        color: #aaaaaa;
        line-height: 1.6;
    }

    /* 成功提示框 */
    .success-box {
        background-color: #0d1f0d;
        border: 1px solid #1a4a1a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-size: 0.88rem;
        color: #88cc88;
    }

    /* 错误提示框 */
    .error-box {
        background-color: #1f0d0d;
        border: 1px solid #4a1a1a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-size: 0.88rem;
        color: #cc8888;
    }

    /* 剧本输出区域 */
    .screenplay-output {
        background-color: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 1.5rem 2rem;
        font-family: 'Courier New', monospace;
        font-size: 0.88rem;
        line-height: 1.8;
        color: #ddd;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    /* 章节标签 */
    .section-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #666666;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    /* 字数统计 */
    .word-count {
        font-size: 0.78rem;
        color: #555555;
        text-align: right;
        margin-top: 0.3rem;
    }

    /* Tab 样式 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 0.2rem;
        gap: 0.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #888888 !important;
        border-radius: 6px !important;
        padding: 0.4rem 1rem !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
    }

    /* 进度条颜色 */
    .stProgress > div > div > div {
        background-color: #ffffff !important;
    }

    /* 折叠组件 */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        color: #cccccc !important;
        border-radius: 8px !important;
        border: 1px solid #2a2a2a !important;
    }

    /* 密码输入框眼睛图标 */
    button[data-testid="baseButton-headerNoPadding"] {
        color: #888 !important;
    }

    /* 滚动条 */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 剧本生成系统提示词（完整指令）
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
三、你必须理解的"影视化优化"
====================
影视化优化不是"多写"也不是"少写"，而是"有效转化"：

A. 可拍转化
- 心理描写 -> 动作/表情/停顿/视线/内心OS/手部反应
- 设定信息 -> 场景细节或人物互动中自然带出
- 异能/特殊能力 -> 明确可视效果（出现方式、反应、后果）

B. 互动转化
- 不允许单人独角戏长期霸屏
- 任一关键动作后，要有他人反应或关系变化反馈

C. 推进转化
- 每段内容必须至少完成一个功能：
  - 推剧情
  - 推关系
  - 推人物性格
  - 推悬念
- 纯重复、纯回锅、纯解释同一信息 -> 删

====================
四、"点到为止"的正确执行（重点）
====================
"点到为止"不是缩减台词长度，也不是禁用情绪表达。
定义如下：

1) 同一个情绪点/包袱/信息点，只推进一次，不反复讲解。
2) 台词可以长，但每句都要有新信息或新立场，不得原地打转。
3) 情绪可以强，但不能靠重复同义句堆时长。
4) 包袱抖出后尽快进入后续行动或关系变化，不挂着不走。

====================
五、对白规则（高优先）
====================
1) 对白先服务逻辑，再服务风格。
2) 问与答必须有逻辑对应，允许：
   - 正面回答
   - 回避（但要显示回避意图）
   - 反问（但要推动冲突）
   - 打断（但要带来新方向）
3) 角色"说什么"不能脱离原著信息边界。
4) 角色"怎么说"体现性格差异（语气、节奏、措辞、攻击方式）。
5) 禁止把同一句"模板腔"分配给所有角色。

====================
六、人物存在感规则（防工具人）
====================
1) 关键角色每次出场都要有"可识别行为"或"可识别表达"。
2) 不能说话的角色可用内心OS，但只在必要处使用，作用是补充角色立场，不是解释画面废话。
3) 任何角色连续长时间仅"站着看"且无功能 -> 判定为工具人，必须改写互动。

====================
七、场景与输出格式（严格）
====================
输出时仅使用以下形式：

【场景：地点｜时间（白天/夜晚）】
正文段落...
正文段落...

【场景：地点｜时间】
正文段落...
正文段落...

规则：
1) 只有"场景变化"时才写新的【场景】头。
2) 同一场景内连续写，不重复场景头。
3) 不要写：片段1/2/3、分镜1/2、镜头1/2、秒数、机位术语。
4) 每个自然段都必须是一个完整"可拍单元"（有动作/对白/结果中的至少两项）。
5) 描述简洁但具体，避免空泛形容词堆砌。

====================
八、强制自检（全部通过后才输出）
====================
逐项判定 Pass/Fail：
1) 是否新增原著没有的关键剧情？（Fail即重写）
2) 是否改变原著因果或角色动机？（Fail即重写）
3) 是否存在"问非所答且无意图"的对白？（Fail即重写）
4) 是否存在工具人角色？（Fail即重写）
5) 是否存在不可拍描述？（Fail即重写）
6) 是否存在同一信息重复解释三次以上？（Fail即重写）
7) 场景切换是否清楚且衔接自然？（Fail即重写）
8) 每段是否具备"动作+反应/对白+结果"的推进结构？（Fail即重写）

====================
九、输出后附加简报
====================
在剧本末尾仅补三行：
- 原著保真：列出未改动的关键事件点
- 影视化优化：列出本次做的3-5个有效优化点
- 逻辑保障：列出3处关键问答或衔接如何成立"""

# ─────────────────────────────────────────────
# 常用模型列表
# ─────────────────────────────────────────────
PRESET_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4.1",
    "gpt-4.1-mini",
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
# 核心生成函数（流式输出）
# ─────────────────────────────────────────────
def generate_screenplay_stream(novel_text: str, api_key: str, api_base: str, model: str):
    """调用 OpenAI 兼容接口，以流式方式返回剧本内容。"""
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"请将以下小说原文改编为短剧剧本：\n\n{novel_text}",
            },
        ],
        "temperature": 0.7,
        "max_tokens": 8000,
    }

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
        if resp.status_code != 200:
            error_detail = resp.text[:300]
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
# 进度阶段描述
# ─────────────────────────────────────────────
PROGRESS_STAGES = [
    (0.05, "正在连接 API..."),
    (0.15, "提取原著骨架：事件链、因果链、关系链..."),
    (0.30, "场景重组：按地点 / 时间切分场景..."),
    (0.50, "影视化落地：心理描写 → 可拍动作..."),
    (0.65, "对白逻辑校正：检查问答对应关系..."),
    (0.80, "节奏校正：删除重复信息，推进包袱..."),
    (0.92, "强制自检：逐项验证八条标准..."),
    (0.98, "生成剧本简报..."),
]

# ─────────────────────────────────────────────
# Session State 初始化
# ─────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = ""
if "generating" not in st.session_state:
    st.session_state.generating = False
if "input_char_count" not in st.session_state:
    st.session_state.input_char_count = 0

# ─────────────────────────────────────────────
# 页面主体
# ─────────────────────────────────────────────

# 标题
st.markdown("""
<div class="main-title">
    <h1>🎬 短剧剧本生成器</h1>
    <p>上传或粘贴小说原文，一键转化为可拍摄的短剧剧本</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 第一区块：API 配置 ──────────────────────────
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
            help="兼容 OpenAI 格式的中转接口地址",
        )

    col_model, col_custom = st.columns([1, 1])
    with col_model:
        model_choice = st.selectbox(
            "Model ID",
            options=PRESET_MODELS,
            index=0,
            help="选择要使用的模型",
        )
    with col_custom:
        if model_choice == "自定义模型...":
            custom_model = st.text_input(
                "输入自定义模型名称",
                placeholder="例如：gpt-4o-2024-11-20",
            )
        else:
            st.text_input(
                "当前选用模型",
                value=model_choice,
                disabled=True,
            )
            custom_model = ""

final_model = custom_model if model_choice == "自定义模型..." else model_choice

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 第二区块：输入小说原文 ───────────────────────
st.markdown('<div class="section-label">小说原文输入</div>', unsafe_allow_html=True)

input_tab1, input_tab2 = st.tabs(["📄  上传文件", "✏️  粘贴文本"])

novel_text = ""

with input_tab1:
    uploaded_file = st.file_uploader(
        "选择 .txt 文件",
        type=["txt"],
        help="仅支持 UTF-8 或 GBK 编码的纯文本文件",
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
            # 预览前 200 字
            with st.expander("预览文件内容（前 200 字）"):
                st.text(novel_text[:200] + ("..." if len(novel_text) > 200 else ""))
        except Exception as e:
            st.markdown(
                f'<div class="error-box">✗ 文件读取失败：{str(e)}</div>',
                unsafe_allow_html=True,
            )

with input_tab2:
    pasted_text = st.text_area(
        "在此粘贴小说原文",
        height=280,
        placeholder="将小说文本粘贴至此处...\n\n支持任意长度，建议单次输入 500～5000 字以获得最佳效果。",
        label_visibility="collapsed",
    )
    if pasted_text.strip():
        novel_text = pasted_text
        st.markdown(
            f'<div class="word-count">{len(pasted_text):,} 字符</div>',
            unsafe_allow_html=True,
        )

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 第三区块：生成按钮 ───────────────────────────
can_generate = bool(api_key.strip()) and bool(novel_text.strip()) and bool(final_model.strip())

if not api_key.strip():
    st.markdown(
        '<div class="info-box">💡 请在上方填写 API Key 以启用生成功能</div>',
        unsafe_allow_html=True,
    )
elif not novel_text.strip():
    st.markdown(
        '<div class="info-box">💡 请上传文件或粘贴小说原文</div>',
        unsafe_allow_html=True,
    )
elif not final_model.strip():
    st.markdown(
        '<div class="info-box">💡 请输入自定义模型名称</div>',
        unsafe_allow_html=True,
    )

generate_btn = st.button(
    "🎬  开始生成剧本",
    disabled=not can_generate or st.session_state.generating,
    use_container_width=True,
)

# ── 第四区块：生成流程 ───────────────────────────
if generate_btn and can_generate:
    st.session_state.generating = True
    st.session_state.result = ""

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">生成进度</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0)
    status_text = st.empty()

    # 模拟前置阶段进度
    for prog, label in PROGRESS_STAGES[:3]:
        progress_bar.progress(prog)
        status_text.markdown(
            f'<div class="info-box">⏳ {label}</div>', unsafe_allow_html=True
        )
        time.sleep(0.6)

    # 开始实际流式调用
    progress_bar.progress(0.35)
    status_text.markdown(
        '<div class="info-box">⏳ 正在生成剧本内容（流式输出）...</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">剧本输出</div>', unsafe_allow_html=True)

    output_placeholder = st.empty()
    full_result = ""
    error_occurred = False

    try:
        char_count = 0
        stage_idx = 3  # 从第 4 个阶段开始推进

        for chunk in generate_screenplay_stream(
            novel_text=novel_text,
            api_key=api_key.strip(),
            api_base=api_base.strip(),
            model=final_model.strip(),
        ):
            full_result += chunk
            char_count += len(chunk)

            # 根据字符数推进进度条（粗略估计）
            estimated_progress = min(0.35 + char_count / max(len(novel_text) * 3, 3000) * 0.55, 0.95)
            if stage_idx < len(PROGRESS_STAGES) and estimated_progress >= PROGRESS_STAGES[stage_idx][0]:
                status_text.markdown(
                    f'<div class="info-box">⏳ {PROGRESS_STAGES[stage_idx][1]}</div>',
                    unsafe_allow_html=True,
                )
                stage_idx += 1

            progress_bar.progress(estimated_progress)

            # 实时渲染输出
            output_placeholder.markdown(
                f'<div class="screenplay-output">{full_result}</div>',
                unsafe_allow_html=True,
            )

    except RuntimeError as e:
        error_occurred = True
        st.markdown(
            f'<div class="error-box">✗ 生成失败：{str(e)}</div>',
            unsafe_allow_html=True,
        )
    except requests.exceptions.ConnectionError:
        error_occurred = True
        st.markdown(
            '<div class="error-box">✗ 网络连接失败，请检查接口地址是否可访问</div>',
            unsafe_allow_html=True,
        )
    except requests.exceptions.Timeout:
        error_occurred = True
        st.markdown(
            '<div class="error-box">✗ 请求超时（120秒），请尝试缩短输入文本或更换模型</div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        error_occurred = True
        st.markdown(
            f'<div class="error-box">✗ 发生未知错误：{str(e)}</div>',
            unsafe_allow_html=True,
        )

    if not error_occurred and full_result:
        progress_bar.progress(1.0)
        status_text.markdown(
            '<div class="success-box">✓ 剧本生成完成！</div>', unsafe_allow_html=True
        )
        st.session_state.result = full_result

        # 下载按钮
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.download_button(
            label="⬇️  下载剧本（.txt）",
            data=full_result.encode("utf-8"),
            file_name="screenplay_output.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.session_state.generating = False

# ── 第五区块：历史结果展示（刷新后保留）────────────
elif st.session_state.result and not st.session_state.generating:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">上次生成结果</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="screenplay-output">{st.session_state.result}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.download_button(
        label="⬇️  下载剧本（.txt）",
        data=st.session_state.result.encode("utf-8"),
        file_name="screenplay_output.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ─────────────────────────────────────────────
# 底部说明
# ─────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<div class="info-box" style="text-align:center; font-size:0.8rem;">
    API Key 仅用于本次请求，不会被记录或存储。&nbsp;&nbsp;|&nbsp;&nbsp;
    推荐输入长度：500 ~ 5000 字 / 次。&nbsp;&nbsp;|&nbsp;&nbsp;
    接口地址默认适配 yunwu.ai 中转站，可替换为任意 OpenAI 兼容地址。
</div>
""", unsafe_allow_html=True)
