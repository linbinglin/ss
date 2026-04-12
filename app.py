import streamlit as st
import requests
import json
import os
from datetime import datetime

# ============================================================
# 页面配置（必须在最前面）
# ============================================================
st.set_page_config(
    page_title="影视化视觉翻译引擎 V3.2",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Session State 初始化（安全方式）
# ============================================================
def init_state():
    defaults = {
        "api_key": "",
        "api_base": "https://yunwu.ai/v1/",
        "model_id": "deepseek-chat",
        "chapters": {},
        "chapter_order": [],
        "global_extraction": "",
        "character_cards": "",
        "opening_designs": "",
        "selected_opening": "",
        "episodes": {},
        "reviews": {},
        "memory_main": "",
        "memory_characters": "",
        "memory_progress": "未开始",
        "memory_last_end": "",
        "memory_foreshadow": "",
        "memory_next_foreshadow": "",
        "memory_emotion": "",
        "chat_history": [],
        "current_step": "upload",
        "generation_mode": "完整模式",
        "episode_chapter_map": {},
        "custom_models": [],
        "batch_start": 1,
        "batch_end": 3,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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
    .memory-box {
        background: #eef2ff;
        border: 1px solid #c3d4ff;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 系统指令
# ============================================================
SYSTEM_PROMPT = """【微短剧生成 3.1 系统指令】

═══════════════════════════════════════
第零法则：视觉翻译（一切规则之上的规则）
═══════════════════════════════════════

小说是给眼睛的——读者靠文字在脑中自己生成画面。
剧本是给画面的——观众只能看到或听到你拍给他看的东西。

你的工作是把小说用文字"告诉"读者的一切，全部翻译成摄像机能拍到的画面,并用人物的台词（声音）来增加代入感！

禁止对角色OOC，人物的台词、行为、举止都必须符合小说里的人设。

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

═══════════════════════════════════════
灵魂锚定
═══════════════════════════════════════
你不是在"把小说改成剧本"。你是在替这些角色活一遍。
产品规格：每集分镜数量自由抉择 | 无第三人称旁白 | 集集强钩子。

═══════════════════════════════════════
五条创作铁律
═══════════════════════════════════════
①【人设即法律】角色性格、说话方式、行为逻辑必须95%忠于原著。
②【外化】一切内心活动必须转化为可拍摄的具体画面。允许【第一人称内心OS】，严禁第三人称旁白。
③【伏笔】每一个重大转折前，必须存在至少一个视觉/听觉微伏笔。
④【潜台词】角色嘴上说的话与真实意图之间必须存在缝隙。
⑤【钩子铁律】前15秒必须制造疑问或情绪冲击。每集结尾必须制造悬念。

═══════════════════════════════════════
角色驱动卡系统
═══════════════════════════════════════
必须为每个主要角色建立驱动卡：核心人格、说话DNA、行为DNA、红线、关系动态。

═══════════════════════════════════════
分镜格式与密度标准
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
1. 角色一致性  2. 画面具象度  3. 台词活人感  4. 因果链完整度
5. 情绪过山车强度  6. 开场15秒留人率  7. 上下镜衔接流畅度
8. 无旁白叙事清晰度  9. 时长准确度  10. 分镜密度  11. 视觉翻译完成度

五个敌对视角：普通观众/竞品编剧/原著粉/剪辑师/导演
逐条分镜检查，7分以下必须标红并给出修改方案。
"""

# ============================================================
# API 调用函数
# ============================================================
def call_api_stream(messages, system_prompt=None):
    """流式调用 AI API，返回 response 对象"""
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
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 16000
    }

    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        resp.raise_for_status()
        return resp
    except Exception as e:
        st.error(f"❌ API 调用失败: {str(e)}")
        return None


def call_api_no_stream(messages, system_prompt=None):
    """非流式调用"""
    api_key = st.session_state.api_key
    api_base = st.session_state.api_base.rstrip("/")
    model = st.session_state.model_id

    if not api_key:
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
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return None


def stream_and_collect(response, container):
    """流式输出到容器，返回完整文本"""
    full_text = ""
    placeholder = container.empty()
    try:
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8", errors="ignore")
            if not line_str.startswith("data: "):
                continue
            data_str = line_str[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_text += content
                        placeholder.markdown(full_text)
            except json.JSONDecodeError:
                continue
    except Exception as e:
        st.error(f"读取流错误: {e}")
    return full_text


# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ API 配置中心")

    st.session_state.api_key = st.text_input(
        "🔑 API Key",
        value=st.session_state.api_key,
        type="password"
    )

    st.session_state.api_base = st.text_input(
        "🌐 接口地址",
        value=st.session_state.api_base
    )

    st.markdown("---")
    st.markdown("### 🤖 模型选择")

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

    all_models = preset_models + list(st.session_state.custom_models)

    # 确保当前model_id在列表中
    current_idx = 0
    if st.session_state.model_id in all_models:
        current_idx = all_models.index(st.session_state.model_id)

    model_choice = st.selectbox(
        "选择模型",
        options=all_models,
        index=current_idx
    )
    st.session_state.model_id = model_choice

    # 自定义模型
    custom_input = st.text_input("或输入自定义模型ID", placeholder="my-model-v1")
    if custom_input:
        if st.button("➕ 添加模型"):
            if custom_input not in st.session_state.custom_models:
                st.session_state.custom_models.append(custom_input)
            st.session_state.model_id = custom_input
            st.rerun()

    st.markdown(f"**当前模型:** `{st.session_state.model_id}`")

    if st.button("🔗 测试连接"):
        if st.session_state.api_key:
            with st.spinner("测试中..."):
                result = call_api_no_stream(
                    [{"role": "user", "content": "请回复'连接成功'四个字。"}]
                )
                if result:
                    st.success(f"✅ {result[:50]}")
                else:
                    st.error("❌ 连接失败")
        else:
            st.warning("请先输入 API Key")

    st.markdown("---")
    st.markdown("### 🎬 模式")
    st.session_state.generation_mode = st.radio(
        "生成模式",
        ["完整模式", "快速模式"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📌 全局记忆")
    mem_main = st.session_state.memory_main
    mem_prog = st.session_state.memory_progress
    if mem_main or mem_prog != "未开始":
        st.markdown(f"""
<div class="memory-box">
📌 <b>主线：</b>{st.session_state.memory_main or '待提炼'}<br>
📌 <b>人物：</b>{st.session_state.memory_characters or '待提炼'}<br>
📌 <b>进度：</b>{st.session_state.memory_progress}<br>
📌 <b>上集结尾：</b>{st.session_state.memory_last_end or '无'}<br>
📌 <b>已埋伏笔：</b>{st.session_state.memory_foreshadow or '无'}<br>
📌 <b>情绪轨迹：</b>{st.session_state.memory_emotion or '无'}
</div>
""", unsafe_allow_html=True)
    else:
        st.info("完成全局提炼后显示")

    st.markdown("---")
    if st.button("🗑️ 清除所有数据"):
        for k in list(st.session_state.keys()):
            if k not in ["api_key", "api_base", "model_id", "custom_models"]:
                del st.session_state[k]
        st.rerun()

    # 导出
    st.markdown("---")
    st.markdown("### 📥 导出")
    if st.session_state.episodes:
        all_scripts = ""
        for ep_num in sorted(st.session_state.episodes.keys()):
            all_scripts += f"\n{'='*50}\n第{ep_num}集\n{'='*50}\n"
            all_scripts += st.session_state.episodes[ep_num]
            if ep_num in st.session_state.reviews:
                all_scripts += f"\n\n--- 审查报告 ---\n{st.session_state.reviews[ep_num]}"

        st.download_button(
            "📄 下载全部剧本",
            data=all_scripts,
            file_name=f"剧本_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# ============================================================
# 主界面
# ============================================================
st.markdown('<div class="main-header">🎬 影视化视觉翻译引擎 V3.2</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">小说影视化改编系统 · 严格遵循视觉翻译法则 · 杜绝文字到文字的低级转换</div>', unsafe_allow_html=True)

# ============================================================
# 步骤一：小说章节管理
# ============================================================
st.markdown('<div class="step-header">📖 步骤一：导入小说章节原文</div>', unsafe_allow_html=True)

col_up, col_prev = st.columns([1, 1])

with col_up:
    st.markdown("##### 添加章节")

    tab_paste, tab_file = st.tabs(["📋 粘贴文本", "📁 上传文件"])

    with tab_paste:
        ch_name = st.text_input("章节名称", placeholder="例如: 第1章 末日降临", key="ch_name_input")
        ch_content = st.text_area("章节内容", height=200, placeholder="在此粘贴小说章节内容...", key="ch_content_input")
        if st.button("➕ 添加此章节", type="primary"):
            if ch_name and ch_content:
                st.session_state.chapters[ch_name] = ch_content
                if ch_name not in st.session_state.chapter_order:
                    st.session_state.chapter_order.append(ch_name)
                st.success(f"✅ 已添加: {ch_name}")
                st.rerun()
            else:
                st.warning("请填写章节名称和内容")

    with tab_file:
        uploaded_files = st.file_uploader(
            "选择文件",
            type=["txt", "md"],
            accept_multiple_files=True,
            key="file_uploader"
        )
        if uploaded_files:
            if st.button("📥 导入所选文件"):
                count = 0
                for uf in uploaded_files:
                    try:
                        content = uf.read().decode("utf-8", errors="ignore")
                        name = os.path.splitext(uf.name)[0]
                        st.session_state.chapters[name] = content
                        if name not in st.session_state.chapter_order:
                            st.session_state.chapter_order.append(name)
                        count += 1
                    except Exception as e:
                        st.error(f"读取 {uf.name} 失败: {e}")
                if count > 0:
                    st.success(f"✅ 已导入 {count} 个章节")
                    st.rerun()

with col_prev:
    st.markdown("##### 已导入章节")
    if st.session_state.chapter_order:
        for i, cname in enumerate(list(st.session_state.chapter_order)):
            if cname not in st.session_state.chapters:
                continue
            content = st.session_state.chapters[cname]
            char_count = len(content)
            with st.expander(f"📄 {cname} ({char_count}字)"):
                st.text(content[:1500] + ("..." if char_count > 1500 else ""))
                if st.button(f"🗑️ 删除此章节", key=f"del_ch_{i}"):
                    del st.session_state.chapters[cname]
                    st.session_state.chapter_order.remove(cname)
                    st.rerun()

        total_chars = sum(len(v) for v in st.session_state.chapters.values())
        st.info(f"共 {len(st.session_state.chapter_order)} 章，总计 {total_chars} 字")
    else:
        st.info("暂无章节，请从左侧添加")

st.markdown("---")

# ============================================================
# 步骤二：全局提炼
# ============================================================
st.markdown('<div class="step-header">🔍 步骤二：章节拆解与取舍决策 (全局提炼)</div>', unsafe_allow_html=True)

col_ext_l, col_ext_r = st.columns([1, 1])

with col_ext_l:
    st.markdown("##### 选择参与分析的章节")
    if st.session_state.chapter_order:
        sel_chapters = st.multiselect(
            "选择章节",
            options=st.session_state.chapter_order,
            default=st.session_state.chapter_order,
            key="sel_extract_chapters"
        )

        if st.button("🚀 启动全局提炼", type="primary", use_container_width=True):
            if not sel_chapters:
                st.warning("请至少选择一个章节")
            elif not st.session_state.api_key:
                st.error("请先设置 API Key")
            else:
                novel_text = ""
                for ch in sel_chapters:
                    novel_text += f"\n\n===== {ch} =====\n{st.session_state.chapters[ch]}"

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
7. 视觉强场景与短剧记忆点（最有冲击力的5-8个瞬间，每个用3-5句话描述具体画面）
8. 章节→集数映射建议
9. 每个章节中需要【视觉翻译】的关键段落标记

输出完毕后写："全局提炼完成。请确认角色驱动卡是否准确。" """

                messages = [{"role": "user", "content": extract_prompt}]

                with st.spinner("🧠 AI 正在深度分析小说原文..."):
                    response = call_api_stream(messages, system_prompt=SYSTEM_PROMPT)
                    if response:
                        result = stream_and_collect(response, st)
                        st.session_state.global_extraction = result
                        st.session_state.memory_progress = "全局提炼完成"
                        st.success("✅ 全局提炼完成！")
    else:
        st.info("请先在步骤一中导入小说章节")

with col_ext_r:
    st.markdown("##### 提炼结果")
    if st.session_state.global_extraction:
        st.markdown(st.session_state.global_extraction)

        if st.checkbox("✏️ 编辑提炼结果", key="edit_extract"):
            edited = st.text_area(
                "编辑",
                value=st.session_state.global_extraction,
                height=400,
                key="edit_extract_area"
            )
            if st.button("💾 保存", key="save_extract"):
                st.session_state.global_extraction = edited
                st.success("✅ 已保存")
    else:
        st.info("点击左侧「启动全局提炼」后显示结果")

st.markdown("---")

# ============================================================
# 步骤三：编剧工作台
# ============================================================
st.markdown('<div class="step-header">⚙️ 步骤三：编剧工作流控制台</div>', unsafe_allow_html=True)

# 参数配置
col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])

with col_cfg1:
    episode_num = st.number_input("集数编号", min_value=1, value=1, step=1, key="ep_num")

with col_cfg2:
    ep_chapters = st.multiselect(
        f"第{episode_num}集 对应章节",
        options=st.session_state.chapter_order,
        default=st.session_state.episode_chapter_map.get(episode_num, []),
        key=f"ep_ch_map_{episode_num}"
    )
    st.session_state.episode_chapter_map[episode_num] = ep_chapters

with col_cfg3:
    custom_instruction = st.text_input("补充指令（可选）", placeholder="例如：节奏偏快，多动作戏...", key="custom_inst")

st.markdown("")

# 操作按钮
col_a, col_b, col_c, col_d, col_e = st.columns(5)

with col_a:
    btn_opening = st.button("🎬 设计开场", use_container_width=True, key="btn_opening")
with col_b:
    btn_generate = st.button("📝 生成剧本", type="primary", use_container_width=True, key="btn_generate")
with col_c:
    btn_review = st.button("🔍 审查剧本", use_container_width=True, key="btn_review")
with col_d:
    btn_optimize = st.button("✨ 优化修改", use_container_width=True, key="btn_optimize")
with col_e:
    btn_batch = st.button("📦 批量生成", use_container_width=True, key="btn_batch")

st.markdown("---")

# 输出区
output_area = st.container()

# --- 设计开场 ---
if btn_opening:
    with output_area:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        else:
            opening_prompt = f"""基于以下全局提炼结果：

{st.session_state.global_extraction[:4000]}

请执行【第2轮：开场手法设计】：
输出6条完全不同的第1集开场方案，每条包含：
- 开场类型标签
- 前30秒逐秒画面描述
- 30秒后如何衔接主线"""

            messages = [{"role": "user", "content": opening_prompt}]

            with st.spinner("🎬 设计开场方案中..."):
                response = call_api_stream(messages, system_prompt=SYSTEM_PROMPT)
                if response:
                    result = stream_and_collect(response, st)
                    st.session_state.opening_designs = result

# --- 生成剧本 ---
if btn_generate:
    with output_area:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成步骤二的全局提炼")
        elif not ep_chapters:
            st.warning("⚠️ 请选择本集对应的小说章节")
        else:
            novel_ref = ""
            for ch in ep_chapters:
                if ch in st.session_state.chapters:
                    novel_ref += f"\n===== {ch} =====\n{st.session_state.chapters[ch]}"

            prev_context = ""
            if episode_num > 1 and (episode_num - 1) in st.session_state.episodes:
                prev_ep = st.session_state.episodes[episode_num - 1]
                prev_context = f"\n上一集（第{episode_num-1}集）结尾：\n{prev_ep[-2000:]}"

            gen_prompt = f"""开始生成剧本 第{episode_num}集

【全局记忆】
📌 主线：{st.session_state.memory_main or '见全局提炼'}
📌 进度：已生成到第{episode_num-1}集
📌 上集结尾：{st.session_state.memory_last_end or '无（第1集）'}
📌 已埋伏笔：{st.session_state.memory_foreshadow or '无'}

【全局提炼】
{st.session_state.global_extraction[:3000]}

【本集对应小说原文（必须严格对照）】
{novel_ref}
{prev_context}

{f"【补充指令】{custom_instruction}" if custom_instruction else ""}

请严格执行【第3轮：剧本生成】：
前置A——编剧内心独白
前置B——本集结构速写
前置C——角色驱动卡调用声明
前置D——影视化排雷扫描
然后输出完整分镜剧本。

⚠️ 关键要求：
1. 逐条分镜严格对照小说原文进行【视觉翻译】
2. 叙述→动作流，心理→身体反应+内心OS，设定→环境展示
3. 每个分镜10-14秒，≥3个连续动作事件
4. 台词符合角色驱动卡说话DNA
5. 禁止第三人称旁白"""

            messages = [{"role": "user", "content": gen_prompt}]

            with st.spinner(f"📝 正在生成第{episode_num}集剧本..."):
                response = call_api_stream(messages, system_prompt=SYSTEM_PROMPT)
                if response:
                    result = stream_and_collect(response, st)
                    st.session_state.episodes[episode_num] = result
                    st.session_state.memory_progress = f"已生成到第{episode_num}集"
                    st.success(f"✅ 第{episode_num}集生成完成！")

# --- 审查剧本 ---
if btn_review:
    with output_area:
        if episode_num not in st.session_state.episodes:
            st.warning(f"⚠️ 第{episode_num}集尚未生成")
        else:
            novel_ref = ""
            mapped = st.session_state.episode_chapter_map.get(episode_num, [])
            for ch in mapped:
                if ch in st.session_state.chapters:
                    novel_ref += f"\n===== {ch} =====\n{st.session_state.chapters[ch]}"

            script = st.session_state.episodes[episode_num]

            review_prompt = f"""请严格审查第{episode_num}集剧本。

【小说原文】
{novel_ref if novel_ref else "（未指定对应章节）"}

【角色驱动卡】
{st.session_state.global_extraction[:2000] if st.session_state.global_extraction else "（未提供）"}

【待审查剧本】
{script}

请执行：
1. **逐条分镜审查**：对照原文检查视觉翻译、分镜密度、台词DNA、时长
2. **五个敌对视角攻击**
3. **11项量化评分**（每项1-10分）
4. **具体修改建议**（7分以下必须给修改方案）
5. **原文对照标记**"""

            messages = [{"role": "user", "content": review_prompt}]

            with st.spinner(f"🔍 审查第{episode_num}集中..."):
                response = call_api_stream(messages, system_prompt=REVIEW_SYSTEM_PROMPT)
                if response:
                    result = stream_and_collect(response, st)
                    st.session_state.reviews[episode_num] = result
                    st.success(f"✅ 第{episode_num}集审查完成！")

# --- 优化修改 ---
if btn_optimize:
    with output_area:
        if episode_num not in st.session_state.episodes:
            st.warning(f"⚠️ 第{episode_num}集尚未生成")
        elif episode_num not in st.session_state.reviews:
            st.warning(f"⚠️ 请先审查第{episode_num}集")
        else:
            opt_type = st.selectbox(
                "优化方向",
                ["全面优化", "只优化台词", "只优化画面", "只优化情绪", "自定义"],
                key="opt_type"
            )

            user_fb = ""
            if opt_type == "自定义":
                user_fb = st.text_area("修改意见", height=100, key="opt_fb")

            if st.button("🚀 执行优化", type="primary", key="do_opt"):
                novel_ref = ""
                mapped = st.session_state.episode_chapter_map.get(episode_num, [])
                for ch in mapped:
                    if ch in st.session_state.chapters:
                        novel_ref += f"\n===== {ch} =====\n{st.session_state.chapters[ch]}"

                opt_prompt = f"""优化第{episode_num}集剧本。

【方向】{opt_type}
{f"【用户意见】{user_fb}" if user_fb else ""}

【原文参考】
{novel_ref[:3000]}

【审查报告】
{st.session_state.reviews[episode_num]}

【原剧本】
{st.session_state.episodes[episode_num]}

请输出完整优化版剧本，重点修复7分以下项目。"""

                messages = [{"role": "user", "content": opt_prompt}]

                with st.spinner("✨ 优化中..."):
                    response = call_api_stream(messages, system_prompt=SYSTEM_PROMPT)
                    if response:
                        result = stream_and_collect(response, st)
                        st.session_state.episodes[episode_num] = result
                        st.success(f"✅ 第{episode_num}集优化完成！")

# --- 批量生成 ---
if btn_batch:
    with output_area:
        if not st.session_state.global_extraction:
            st.warning("⚠️ 请先完成全局提炼")
        else:
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                b_start = st.number_input("起始集", min_value=1, value=1, key="b_start")
            with b_col2:
                b_end = st.number_input("结束集", min_value=1, value=3, key="b_end")

            if st.button("🚀 开始批量生成", type="primary", key="do_batch"):
                for ep in range(int(b_start), int(b_end) + 1):
                    st.markdown(f"### 正在生成第{ep}集...")
                    mapped_chs = st.session_state.episode_chapter_map.get(ep, [])
                    novel_ref = ""
                    for ch in mapped_chs:
                        if ch in st.session_state.chapters:
                            novel_ref += f"\n===== {ch} =====\n{st.session_state.chapters[ch]}"

                    prev_ctx = ""
                    if ep > 1 and (ep - 1) in st.session_state.episodes:
                        prev_ctx = f"\n上集结尾：\n{st.session_state.episodes[ep-1][-1500:]}"

                    bp = f"""开始生成剧本 第{ep}集
【全局提炼】{st.session_state.global_extraction[:2000]}
【对应原文】{novel_ref[:3000] if novel_ref else "（根据全局提炼分配）"}
{prev_ctx}
请按第3轮流程完整执行。"""

                    messages = [{"role": "user", "content": bp}]
                    response = call_api_stream(messages, system_prompt=SYSTEM_PROMPT)
                    if response:
                        result = stream_and_collect(response, st)
                        st.session_state.episodes[ep] = result
                        st.session_state.memory_progress = f"已生成到第{ep}集"

                st.success(f"✅ 批量完成：第{int(b_start)}~{int(b_end)}集")

# ============================================================
# 步骤四：剧本展示与审查
# ============================================================
if st.session_state.episodes:
    st.markdown("---")
    st.markdown('<div class="step-header">📋 步骤四：剧本成果与审查报告</div>', unsafe_allow_html=True)

    sorted_eps = sorted(st.session_state.episodes.keys())
    tab_labels = [f"第{ep}集" for ep in sorted_eps]
    tabs = st.tabs(tab_labels)

    for tab, ep_n in zip(tabs, sorted_eps):
        with tab:
            c_script, c_review = st.columns([1, 1])

            with c_script:
                st.markdown(f"##### 📝 第{ep_n}集 剧本")
                st.markdown(st.session_state.episodes[ep_n])
                st.download_button(
                    f"📥 下载第{ep_n}集",
                    data=st.session_state.episodes[ep_n],
                    file_name=f"第{ep_n}集_剧本.txt",
                    mime="text/plain",
                    key=f"dl_ep_{ep_n}"
                )

            with c_review:
                st.markdown(f"##### 🔍 第{ep_n}集 审查报告")
                if ep_n in st.session_state.reviews:
                    st.markdown(st.session_state.reviews[ep_n])
                else:
                    st.info("尚未审查")

                mapped = st.session_state.episode_chapter_map.get(ep_n, [])
                if mapped:
                    with st.expander("📖 对应原文"):
                        for ch in mapped:
                            if ch in st.session_state.chapters:
                                st.markdown(f"**{ch}**")
                                txt = st.session_state.chapters[ch]
                                st.text(txt[:1500] + ("..." if len(txt) > 1500 else ""))

# 开场设计展示
if st.session_state.opening_designs:
    st.markdown("---")
    st.markdown('<div class="step-header">🎬 开场方案</div>', unsafe_allow_html=True)
    st.markdown(st.session_state.opening_designs)
    sel_op = st.text_input("选择方案编号（1-6）", key="sel_opening")
    if sel_op:
        st.session_state.selected_opening = sel_op
        st.success(f"✅ 已选方案 {sel_op}")

# 页脚
st.markdown("---")
st.caption("🎬 影视化视觉翻译引擎 V3.2 | 基于微短剧3.1系统指令 | 流程：导入章节 → 全局提炼 → 设计开场 → 生成剧本 → 审查优化")
