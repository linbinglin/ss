import streamlit as st
import requests
import json
import time
import os
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
# 自定义样式
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2d3436;
        border-bottom: 2px solid #e74c3c;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .chapter-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .review-pass {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        color: #155724;
    }
    .review-fail {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        color: #721c24;
    }
    .review-warn {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        color: #856404;
    }
    .memory-box {
        background: #eef2ff;
        border: 1px solid #c3d4ff;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.9rem;
    }
    .stButton > button {
        border-radius: 6px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State 初始化
# ============================================================
defaults = {
    "api_key": "",
    "api_base": "https://yunwu.ai/v1/",
    "model_id": "deepseek-chat",
    "chapters": {},          # {章节名: 内容}
    "chapter_order": [],     # 章节顺序
    "global_extraction": "", # 全局提炼结果
    "character_cards": "",   # 角色驱动卡
    "opening_designs": "",   # 开场设计
    "selected_opening": "",  # 选中的开场
    "episodes": {},          # {集数: 剧本内容}
    "reviews": {},           # {集数: 审查结果}
    "memory": {              # 全局记忆
        "主线": "",
        "核心人物": "",
        "当前进度": "未开始",
        "上集结尾": "",
        "已埋伏笔": "",
        "下集伏笔": "",
        "情绪轨迹": ""
    },
    "chat_history": [],      # 完整对话历史
    "current_step": "upload", # upload / extract / opening / generate / review
    "generation_mode": "完整模式",
    "episode_chapter_map": {},  # {集数: [对应章节]}
    "custom_models": [],
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, (dict, list)) else type(v)(v)


# ============================================================
# 系统指令（完整版）
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
因此在给核心角色编写每一句台词的时候都要参考【角色驱动卡】

这是一条凌驾于所有其他规则之上的法则。

---

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

第二步——台词的适配：画面呈现张力，台词赋予情感！

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集分镜数量自由抉择 | 无第三人称旁白 | 集集强钩子。

═══════════════════════════════════════
第一层：五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切"想、觉得、心痛、暗爽"必须转化为可拍摄的具体画面。允许角色用【第一人称内心OS】展现性格，严禁第三人称旁白。
③【伏笔】每一个重大转折前，必须存在至少一个1-5秒的视觉/听觉微伏笔。
④【潜台词】角色嘴上说的话与真实意图之间必须存在缝隙。台词传递表面意思，身体泄露真相。
⑤【钩子铁律】前15秒必须制造具体的疑问或情绪冲击。每集结尾必须制造"不看下一集不行"的未完成悬念。

═══════════════════════════════════════
第二层：角色驱动卡系统
═══════════════════════════════════════
必须为每个主要角色建立驱动卡：核心人格、说话DNA、行为DNA、红线、关系动态。

═══════════════════════════════════════
第五层：分镜格式与密度标准
═══════════════════════════════════════
【分镜XX】
场景：地点·时间·天气·光线
内容：画面+台词(内心OS)+音效
衔接点：[本镜最后一帧→下一镜接入方式]

每个分镜控制在10-14秒，必须包含：≥3个连续动作事件、≥1个环境/声音细节、≥1个角色微表情或身体细节。

═══════════════════════════════════════
时长感知校准
═══════════════════════════════════════
【2秒】快速表情+短动作+1-3字台词+音效
【5秒】完整肢体动作+5-12字短台词+表情反应
【10秒】对话交锋+复杂连续动作+环境氛围+微型情绪转折
【14秒】2-3句对话+铺垫→触发→爆发的完整微型事件
"""

REVIEW_SYSTEM_PROMPT = """你是一个专业的微短剧剧本审查官。你的任务是对照小说原文，对生成的剧本分镜进行严格审查。

审查维度（每项1-10分）：
1. 角色一致性（台词+行为是否符合角色驱动卡）
2. 画面具象度（每个分镜是否有具体的不寻常细节）
3. 台词活人感（台词是否像真人说的话，而非念小说）
4. 因果链完整度（情节是否逻辑自洽）
5. 情绪过山车强度（情绪变化是否足够）
6. 开场15秒留人率预估
7. 上下镜衔接流畅度
8. 无旁白叙事清晰度
9. 时长准确度（标注时长与内容实算时长偏差≤±2秒）
10. 分镜密度（每个10-14秒分镜是否≥3个动作事件）
11. 视觉翻译完成度（是否有台词替代画面叙事的情况）

五个敌对视角攻击：
- 普通观众视角：有没有跳戏？台词像不像人话？
- 竞品编剧视角：哪场戏是老套路？哪个转折可预测？
- 原著粉视角：哪个角色OOC了？哪句台词不对味？
- 剪辑师视角：分镜衔接是否流畅？
- 导演视角：台词是否突兀？声音轨道是否完整？

对每一条分镜逐一检查，指出具体问题，给出修改建议。
7分以下的项目必须标红并给出具体修改方案。

最后给出总评和总分。
"""


# ============================================================
# API 调用函数
# ============================================================
def call_api(messages, system_prompt=None, stream=True):
    """调用 AI API"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = st.session_state.model_id

    if not api_key:
        st.error("❌ 请先在侧边栏设置 API Key")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload = {
        "model": model,
        "messages": full_messages,
        "stream": stream,
        "temperature": 0.7,
        "max_tokens": 16000
    }

    try:
        if stream:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            return response
        else:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API 调用失败: {str(e)}")
        return None


def stream_response(response, placeholder):
    """流式输出响应"""
    full_text = ""
    try:
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_text += content
                            placeholder.markdown(full_text)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        st.error(f"流式读取错误: {e}")
    return full_text


# ============================================================
# 侧边栏：API 配置
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ API 配置中心")

    st.session_state.api_key = st.text_input(
        "🔑 API Key",
        value=st.session_state.api_key,
        type="password",
        help="输入您的 API Key"
    )

    st.session_state.api_base = st.text_input(
        "🌐 接口地址 (Base URL)",
        value=st.session_state.api_base,
        help="第三方中转地址"
    )

    st.markdown("---")
    st.markdown("### 🤖 模型选择")

    # 预设模型列表
    preset_models = [
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "gemini-2.5-pro-preview",
        "gemini-2.0-flash",
        "gemini-1.5-pro-preview",
        "qwen-max",
        "qwen-plus",
        "glm-4",
    ]

    all_models = preset_models + st.session_state.custom_models

    model_choice = st.selectbox(
        "选择模型",
        options=all_models + ["➕ 自定义模型ID..."],
        index=all_models.index(st.session_state.model_id) if st.session_state.model_id in all_models else 0
    )

    if model_choice == "➕ 自定义模型ID...":
        custom_model = st.text_input("输入自定义模型ID", placeholder="例如: my-model-v1")
        if custom_model and st.button("添加模型"):
            if custom_model not in st.session_state.custom_models:
                st.session_state.custom_models.append(custom_model)
            st.session_state.model_id = custom_model
            st.rerun()
    else:
        st.session_state.model_id = model_choice

    st.markdown(f"**当前模型:** `{st.session_state.model_id}`")

    # 连接测试
    if st.button("🔗 测试连接"):
        if st.session_state.api_key:
            with st.spinner("测试中..."):
                result = call_api(
                    [{"role": "user", "content": "请回复'连接成功'四个字。"}],
                    stream=False
                )
                if result:
                    st.success(f"✅ 连接成功！\n回复: {result[:50]}")
                else:
                    st.error("❌ 连接失败")
        else:
            st.warning("请先输入 API Key")

    st.markdown("---")
    st.markdown("### 🎬 模式选择")
    st.session_state.generation_mode = st.radio(
        "生成模式",
        ["完整模式", "快速模式"],
        help="完整模式按四轮流程执行；快速模式可跳过部分步骤"
    )

    # 全局记忆显示
    st.markdown("---")
    st.markdown("### 📌 全局记忆追踪")
    memory = st.session_state.memory
    if any(v for v in memory.values()):
        st.markdown(f"""
<div class="memory-box">
📌 <b>一句话主线：</b>{memory.get('主线', '待提炼')}<br>
📌 <b>核心人物：</b>{memory.get('核心人物', '待提炼')}<br>
📌 <b>当前进度：</b>{memory.get('当前进度', '未开始')}<br>
📌 <b>上集结尾：</b>{memory.get('上集结尾', '无')}<br>
📌 <b>已埋伏笔：</b>{memory.get('已埋伏笔', '无')}<br>
📌 <b>下集伏笔：</b>{memory.get('下集伏笔', '无')}<br>
📌 <b>情绪轨迹：</b>{memory.get('情绪轨迹', '无')}
</div>
""", unsafe_allow_html=True)
    else:
        st.info("上传小说并完成全局提炼后，记忆将在此显示")

    # 管理已保存记忆
    if st.button("🗑️ 清除所有记忆与数据"):
        for k, v in defaults.items():
            if k not in ["api_key", "api_base", "model_id", "custom_models"]:
                st.session_state[k] = type(v)(v) if isinstance(v, (dict, list)) else v
        st.rerun()

    # 快捷导出
    st.markdown("---")
    st.markdown("### 📥 快捷导出")
    if st.session_state.episodes:
        all_scripts = ""
        for ep_num in sorted(st.session_state.episodes.keys()):
            all_scripts += f"\n{'='*60}\n第{ep_num}集\n{'='*60}\n"
            all_scripts += st.session_state.episodes[ep_num]
            if ep_num in st.session_state.reviews:
                all_scripts += f"\n\n--- 审查报告 ---\n{st.session_state.reviews[ep_num]}"
        st.download_button(
            "📄 下载全部剧本 (TXT)",
            data=all_scripts,
            file_name=f"微短剧剧本_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )


# ============================================================
# 主界面
# ============================================================
st.markdown('<div class="main-header">🎬 影视化视觉翻译引擎 V3.2</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">小说影视化改编系统，严格遵循视觉翻译法则，杜绝文字到文字的低级转换</div>', unsafe_allow_html=True)

# ============================================================
# 步骤一：小说章节管理
# ============================================================
st.markdown('<div class="step-header">📖 步骤一：导入小说章节原文</div>', unsafe_allow_html=True)

col_upload, col_preview = st.columns([1, 1])

with col_upload:
    st.markdown("##### 添加章节")

    input_method = st.radio(
        "输入方式",
        ["📋 粘贴文本", "📁 上传文件"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if input_method == "📋 粘贴文本":
        chapter_name = st.text_input("章节名称", placeholder="例如: 第1章 末日降临")
        chapter_content = st.text_area(
            "章节内容",
            height=250,
            placeholder="在此粘贴小说章节内容..."
        )
        if st.button("➕ 添加此章节", type="primary", use_container_width=True):
            if chapter_name and chapter_content:
                st.session_state.chapters[chapter_name] = chapter_content
                if chapter_name not in st.session_state.chapter_order:
                    st.session_state.chapter_order.append(chapter_name)
                st.success(f"✅ 已添加: {chapter_name}")
                st.rerun()
            else:
                st.warning("请填写章节名称和内容")

    else:  # 上传文件
        uploaded_files = st.file_uploader(
            "选择文件（支持 .txt .md）",
            type=["txt", "md"],
            accept_multiple_files=True,
            help="可以同时上传多个文件，每个文件作为一个章节"
        )
        if uploaded_files:
            for uf in uploaded_files:
                content = uf.read().decode("utf-8", errors="ignore")
                name = os.path.splitext(uf.name)[0]
                st.session_state.chapters[name] = content
                if name not in st.session_state.chapter_order:
                    st.session_state.chapter_order.append(name)
            st.success(f"✅ 已导入 {len(uploaded_files)} 个章节")
            st.rerun()

    # 批量导入提示
    st.markdown("---")
    st.info("💡 **提示：** 系统会将所有章节作为原文参考，确保AI在生成剧本时严格对照小说内容，防止偷懒式转换。")

with col_preview:
    st.markdown("##### 已导入章节管理面板")
    if st.session_state.chapter_order:
        for i, ch_name in enumerate(st.session_state.chapter_order):
            with st.expander(f"📄 {ch_name} ({len(st.session_state.chapters[ch_name])}字)", expanded=False):
                st.text_area(
                    "内容预览",
                    value=st.session_state.chapters[ch_name][:2000] + ("..." if len(st.session_state.chapters[ch_name]) > 2000 else ""),
                    height=150,
                    key=f"preview_{i}",
                    disabled=True
                )
                col_del, col_edit = st.columns(2)
                with col_del:
                    if st.button(f"🗑️ 删除", key=f"del_{i}"):
                        del st.session_state.chapters[ch_name]
                        st.session_state.chapter_order.remove(ch_name)
                        st.rerun()
                with col_edit:
                    st.markdown(f"**字数:** {len(st.session_state.chapters[ch_name])}")
        st.markdown(f"**共 {len(st.session_state.chapter_order)} 章，总计 {sum(len(v) for v in st.session_state.chapters.values())} 字**")
    else:
        st.info("暂无章节，请从左侧添加")

st.markdown("---")

# ============================================================
# 步骤二：章节拆解与取舍决策
# ============================================================
st.markdown('<div class="step-header">🔍 步骤二：章节拆解与取舍决策 (新增关键步骤)</div>', unsafe_allow_html=True)

st.markdown("在生成剧本前，AI会先对小说原文进行深度分析，识别可拍摄内容，杜绝文字到文字的低级转换。")

col_extract_left, col_extract_right = st.columns([1, 1])

with col_extract_left:
    st.markdown("##### 章节对标映射（AI分析后自动生成，也可手工调整）")
    if st.session_state.chapter_order:
        # 让用户选择哪些章节用于当前全局提炼
        selected_chapters = st.multiselect(
            "选择参与本次分析的章节",
            options=st.session_state.chapter_order,
            default=st.session_state.chapter_order
        )

        if st.button("🚀 启动全局提炼（需联网调用AI）", type="primary", use_container_width=True):
            if not selected_chapters:
                st.warning("请至少选择一个章节")
            else:
                # 构建小说内容
                novel_text = ""
                for ch in selected_chapters:
                    novel_text += f"\n\n===== {ch} =====\n{st.session_state.chapters[ch]}"

                # 构建提炼请求
                extract_prompt = f"""【微短剧3.1启动】

以下是小说原文内容：
{novel_text}

请严格按照系统指令【第1轮：全局提炼】执行，输出以下内容（不输出任何剧本）：

1. 一句话故事核心
2. 每个主要角色的【驱动卡】（按角色驱动卡格式，必须从原著中提取原句作为说话DNA示范）
3. 故事大纲（分阶段）+ 各阶段核心情绪类型
4. 必须保留的核心情节节点（10-20个）
5. 需要补充的逻辑链节点（列出+补全方式）
6. 全剧环境/氛围基调 + 天气光影变化建议
7. 视觉强场景与短剧记忆点（最有冲击力的5-8个瞬间，每个用3-5句话描述具体画面，不是概括）

同时输出：
8. 章节→集数映射建议（哪些章节内容对应哪一集）
9. 每个章节中需要【视觉翻译】的关键段落标记"""

                messages = [{"role": "user", "content": extract_prompt}]

                with st.spinner("🧠 AI 正在深度分析小说原文..."):
                    placeholder = st.empty()
                    response = call_api(messages, system_prompt=SYSTEM_PROMPT, stream=True)
                    if response:
                        result = stream_response(response, placeholder)
                        st.session_state.global_extraction = result
                        st.session_state.current_step = "extract"
                        # 更新记忆
                        st.session_state.memory["当前进度"] = "全局提炼完成"
    else:
        st.info("请先在步骤一中导入小说章节")

with col_extract_right:
    st.markdown("##### 视觉翻译分析结果")
    if st.session_state.global_extraction:
        st.markdown(st.session_state.global_extraction)

        # 允许用户编辑提炼结果
        if st.checkbox("✏️ 手动编辑提炼结果"):
            edited = st.text_area(
                "编辑全局提炼",
                value=st.session_state.global_extraction,
                height=400
            )
            if st.button("💾 保存修改"):
                st.session_state.global_extraction = edited
                st.success("✅ 已保存修改")
    else:
        st.info("点击左侧「启动全局提炼」后，结果将显示在此")

st.markdown("---")

# ============================================================
# 步骤三：编剧工作流控制台
# ============================================================
st.markdown('<div class="step-header">⚙️ 步骤三：编剧工作流控制台</div>', unsafe_allow_html=True)

# 工作流按钮行
col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)

with col_b1:
    do_opening = st.button("🎬 设计开场", use_container_width=True)
with col_b2:
    do_generate = st.button("📝 生成剧本", type="primary", use_container_width=True)
with col_b3:
    do_review = st.button("🔍 审查剧本", use_container_width=True)
with col_b4:
    do_optimize = st.button("✨ 优化修改", use_container_width=True)
with col_b5:
    do_batch = st.button("📦 批量生成", use_container_width=True)

# --- 集数与章节映射 ---
st.markdown("---")

col_gen_left, col_gen_right = st.columns([1, 1.5])

with col_gen_left:
    st.markdown("##### 生成参数配置")

    episode_num = st.number_input("集数编号", min_value=1, value=1, step=1)

    # 选择对应章节
    ep_chapters = st.multiselect(
        f"第{episode_num}集 对应的小说章节",
        options=st.session_state.chapter_order,
        default=st.session_state.episode_chapter_map.get(episode_num, []),
        help="选择本集剧本对应的小说原文章节，AI将严格对照这些内容生成"
    )
    st.session_state.episode_chapter_map[episode_num] = ep_chapters

    # 自定义指令
    custom_instruction = st.text_area(
        "补充指令（可选）",
        placeholder="例如：这集重点展现男主的内心挣扎，节奏偏慢，多用沉默和环境音...",
        height=80
    )

    # 批量生成设置
    if do_batch:
        batch_start = st.number_input("起始集", min_value=1, value=1)
        batch_end = st.number_input("结束集", min_value=1, value=3)

with col_gen_right:
    st.markdown("##### 工作台输出区")

    # ========== 设计开场 ==========
    if do_opening:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        else:
            opening_prompt = f"""基于以下全局提炼结果：

{st.session_state.global_extraction}

请严格按照系统指令【第2轮：开场手法设计】执行：

输出6条完全不同的第1集开场方案，每条必须包含：
- 开场类型标签
- 前30秒的逐秒画面描述（具体到：第1-3秒观众看到什么、听到什么；第4-10秒发生什么；第11-20秒情绪转向什么；第21-30秒钩子落在哪里）
- 30秒后如何衔接到主线

请选择开场手法（编号）。"""

            messages = [
                {"role": "assistant", "content": st.session_state.global_extraction},
                {"role": "user", "content": opening_prompt}
            ]

            with st.spinner("🎬 设计开场方案中..."):
                placeholder = st.empty()
                response = call_api(messages, system_prompt=SYSTEM_PROMPT, stream=True)
                if response:
                    result = stream_response(response, placeholder)
                    st.session_state.opening_designs = result

    # ========== 生成剧本 ==========
    if do_generate:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        elif not ep_chapters:
            st.warning("⚠️ 请选择本集对应的小说章节")
        else:
            # 构建本集的小说原文
            novel_ref = ""
            for ch in ep_chapters:
                novel_ref += f"\n\n===== {ch} =====\n{st.session_state.chapters[ch]}"

            # 构建上集记忆
            prev_context = ""
            if episode_num > 1 and (episode_num - 1) in st.session_state.episodes:
                prev_context = f"\n\n上一集（第{episode_num-1}集）剧本内容：\n{st.session_state.episodes[episode_num-1][-2000:]}"

            generate_prompt = f"""开始生成剧本 第{episode_num}集

【全局记忆】
📌 一句话主线：{st.session_state.memory.get('主线', '见全局提炼')}
📌 当前进度：已生成到第{episode_num-1}集
📌 上集结尾画面+悬念：{st.session_state.memory.get('上集结尾', '无（第1集）')}
📌 已埋未引爆的伏笔：{st.session_state.memory.get('已埋伏笔', '无')}

【全局提炼参考】
{st.session_state.global_extraction[:3000]}

【本集对应的小说原文（必须严格对照）】
{novel_ref}
{prev_context}

{f"【用户补充指令】{custom_instruction}" if custom_instruction else ""}

请严格按照系统指令【第3轮：剧本生成】执行：

前置A——编剧内心独白（必须输出）
前置B——本集结构速写
前置C——角色驱动卡调用声明
前置D——影视化排雷扫描

然后输出完整分镜剧本。

⚠️ 关键要求：
1. 每一条分镜必须严格对照小说原文进行【视觉翻译】，不允许偷懒式的文字到文字转换
2. 叙述→动作流，心理→身体反应+内心OS，设定→环境展示
3. 每个分镜10-14秒，≥3个连续动作事件
4. 台词必须符合角色驱动卡的说话DNA
5. 禁止第三人称旁白"""

            messages = [{"role": "user", "content": generate_prompt}]

            with st.spinner(f"📝 正在生成第{episode_num}集剧本..."):
                placeholder = st.empty()
                response = call_api(messages, system_prompt=SYSTEM_PROMPT, stream=True)
                if response:
                    result = stream_response(response, placeholder)
                    st.session_state.episodes[episode_num] = result
                    st.session_state.memory["当前进度"] = f"已生成到第{episode_num}集"
                    st.success(f"✅ 第{episode_num}集剧本生成完成！")

    # ========== 审查剧本 ==========
    if do_review:
        if episode_num not in st.session_state.episodes:
            st.warning(f"⚠️ 第{episode_num}集剧本尚未生成")
        else:
            # 获取对应的小说原文
            novel_ref = ""
            mapped_chapters = st.session_state.episode_chapter_map.get(episode_num, [])
            for ch in mapped_chapters:
                if ch in st.session_state.chapters:
                    novel_ref += f"\n\n===== {ch} =====\n{st.session_state.chapters[ch]}"

            script_content = st.session_state.episodes[episode_num]

            review_prompt = f"""请对以下第{episode_num}集剧本进行严格审查。

【小说原文参考】
{novel_ref if novel_ref else "（未指定对应章节，请基于剧本本身审查）"}

【角色驱动卡参考】
{st.session_state.global_extraction[:2000] if st.session_state.global_extraction else "（未提供）"}

【待审查的剧本内容】
{script_content}

请严格按照审查系统执行：

1. **逐条分镜审查**：对每一条分镜逐一检查，对照小说原文，指出：
   - 是否存在"偷懒式文字转文字"（直接把小说叙述塞进台词）
   - 是否完成了视觉翻译（叙述→动作流？心理→身体反应？设定→环境展示？）
   - 分镜密度是否达标（≥3个连续动作事件？有具体环境/声音细节？）
   - 台词是否符合角色说话DNA
   - 时长标注是否准确

2. **五个敌对视角攻击**（普通观众/竞品编剧/原著粉/剪辑师/导演）

3. **11项量化评分**（每项1-10分）

4. **具体修改建议**：对7分以下的项目，给出逐条修改方案

5. **原文对照标记**：标出剧本中哪些地方偏离了原著，以及是合理改编还是不当删改"""

            messages = [{"role": "user", "content": review_prompt}]

            with st.spinner(f"🔍 正在审查第{episode_num}集..."):
                placeholder = st.empty()
                response = call_api(messages, system_prompt=REVIEW_SYSTEM_PROMPT, stream=True)
                if response:
                    result = stream_response(response, placeholder)
                    st.session_state.reviews[episode_num] = result
                    st.success(f"✅ 第{episode_num}集审查完成！")

    # ========== 优化修改 ==========
    if do_optimize:
        if episode_num not in st.session_state.episodes:
            st.warning(f"⚠️ 第{episode_num}集剧本尚未生成")
        elif episode_num not in st.session_state.reviews:
            st.warning(f"⚠️ 第{episode_num}集尚未审查，请先审查")
        else:
            optimize_target = st.selectbox(
                "优化方向",
                ["全面优化", "只优化台词", "只优化画面", "只优化情绪", "自定义修改"]
            )

            user_feedback = ""
            if optimize_target == "自定义修改":
                user_feedback = st.text_area("请输入您的修改意见", height=100)

            if st.button("🚀 执行优化", type="primary"):
                novel_ref = ""
                mapped_chapters = st.session_state.episode_chapter_map.get(episode_num, [])
                for ch in mapped_chapters:
                    if ch in st.session_state.chapters:
                        novel_ref += f"\n\n===== {ch} =====\n{st.session_state.chapters[ch]}"

                optimize_prompt = f"""请根据审查报告优化第{episode_num}集剧本。

【优化方向】{optimize_target}
{f"【用户修改意见】{user_feedback}" if user_feedback else ""}

【小说原文参考】
{novel_ref[:3000]}

【审查报告】
{st.session_state.reviews[episode_num]}

【原剧本】
{st.session_state.episodes[episode_num]}

请输出优化后的完整剧本（不是只输出修改部分，而是输出完整的优化版）。
重点修复审查报告中7分以下的项目。
必须严格对照小说原文，确保视觉翻译到位。"""

                messages = [{"role": "user", "content": optimize_prompt}]

                with st.spinner(f"✨ 优化第{episode_num}集中..."):
                    placeholder_opt = st.empty()
                    response = call_api(messages, system_prompt=SYSTEM_PROMPT, stream=True)
                    if response:
                        result = stream_response(response, placeholder_opt)
                        st.session_state.episodes[episode_num] = result
                        st.success(f"✅ 第{episode_num}集优化完成！")

    # ========== 批量生成 ==========
    if do_batch:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成全局提炼")
        else:
            if st.button("🚀 开始批量生成", type="primary"):
                for ep in range(int(batch_start), int(batch_end) + 1):
                    st.markdown(f"---\n### 正在生成第{ep}集...")
                    mapped_chs = st.session_state.episode_chapter_map.get(ep, [])
                    novel_ref = ""
                    for ch in mapped_chs:
                        if ch in st.session_state.chapters:
                            novel_ref += f"\n===== {ch} =====\n{st.session_state.chapters[ch]}"

                    prev_ctx = ""
                    if ep > 1 and (ep - 1) in st.session_state.episodes:
                        prev_ctx = f"\n上一集结尾：\n{st.session_state.episodes[ep-1][-1500:]}"

                    batch_prompt = f"""开始生成剧本 第{ep}集

【全局提炼】{st.session_state.global_extraction[:2000]}
【对应原文】{novel_ref[:3000] if novel_ref else "（请根据全局提炼自行分配）"}
{prev_ctx}

请按第3轮流程完整执行（前置A/B/C/D + 完整分镜剧本）。"""

                    messages = [{"role": "user", "content": batch_prompt}]
                    placeholder_batch = st.empty()
                    response = call_api(messages, system_prompt=SYSTEM_PROMPT, stream=True)
                    if response:
                        result = stream_response(response, placeholder_batch)
                        st.session_state.episodes[ep] = result
                        st.session_state.memory["当前进度"] = f"已生成到第{ep}集"

                st.success(f"✅ 批量生成完成：第{int(batch_start)}集 ~ 第{int(batch_end)}集")

# ============================================================
# 步骤四：剧本展示与审查对照
# ============================================================
if st.session_state.episodes:
    st.markdown("---")
    st.markdown('<div class="step-header">📋 步骤四：剧本成果与审查报告</div>', unsafe_allow_html=True)

    episode_tabs = st.tabs([f"第{ep}集" for ep in sorted(st.session_state.episodes.keys())])

    for tab, ep_num in zip(episode_tabs, sorted(st.session_state.episodes.keys())):
        with tab:
            col_script, col_review = st.columns([1, 1])

            with col_script:
                st.markdown(f"##### 📝 第{ep_num}集 剧本")
                st.markdown(st.session_state.episodes[ep_num])

                # 下载单集
                st.download_button(
                    f"📥 下载第{ep_num}集",
                    data=st.session_state.episodes[ep_num],
                    file_name=f"第{ep_num}集_剧本.txt",
                    mime="text/plain",
                    key=f"dl_{ep_num}"
                )

            with col_review:
                st.markdown(f"##### 🔍 第{ep_num}集 审查报告")
                if ep_num in st.session_state.reviews:
                    st.markdown(st.session_state.reviews[ep_num])
                else:
                    st.info("尚未审查，请在工作台中点击「审查剧本」")

                # 对应原文快速查看
                mapped = st.session_state.episode_chapter_map.get(ep_num, [])
                if mapped:
                    with st.expander("📖 查看对应小说原文"):
                        for ch in mapped:
                            if ch in st.session_state.chapters:
                                st.markdown(f"**{ch}**")
                                st.text(st.session_state.chapters[ch][:1500] + "...")

# ============================================================
# 开场设计结果展示
# ============================================================
if st.session_state.opening_designs:
    st.markdown("---")
    st.markdown('<div class="step-header">🎬 开场方案设计</div>', unsafe_allow_html=True)
    st.markdown(st.session_state.opening_designs)

    selected = st.text_input("选择开场方案编号（1-6）", placeholder="输入编号")
    if selected:
        st.session_state.selected_opening = selected
        st.success(f"✅ 已选择方案 {selected}")

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85rem; padding: 1rem;">
    🎬 影视化视觉翻译引擎 V3.2 | 基于微短剧3.1系统指令 | 
    严格遵循视觉翻译法则，杜绝文字到文字的低级转换<br>
    提示：输入 API Key 后开始使用 → 导入章节 → 全局提炼 → 设计开场 → 生成剧本 → 审查优化
</div>
""", unsafe_allow_html=True)
