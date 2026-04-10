import streamlit as st
from openai import OpenAI
import os

# ==========================================
# 1. 定义极其严格的系统提示词（微短剧3.1核心指令）
# ==========================================
SYSTEM_PROMPT = """
【微短剧生成 3.1 系统指令】
此处由于篇幅限制，此处为你上面提供的**全部文本内容**。
（请在实际代码中，将你问题中提供的从“第零法则：视觉翻译”到“模式开关”的所有系统指令完整粘贴到这三个引号之间）
"""

# 为了代码直接可用，我们将你提供的核心指令缩影加载，实际使用请用你完整的指令覆盖这段字符串
SYSTEM_PROMPT = SYSTEM_PROMPT.strip()

# ==========================================
# 2. 页面与会话状态初始化
# ==========================================
st.set_page_config(page_title="微短剧3.1 剧本生成系统", page_icon="🎬", layout="wide")

if "messages" not in st.session_state:
    # 初始化系统指令
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "novel_content" not in st.session_state:
    st.session_state.novel_content = ""
if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = ""
# ==========================================
# 3. 侧边栏：API配置与记忆面板
# ==========================================
with st.sidebar:
    st.header("⚙️ API 配置中心")
    api_key = st.text_input("输入 API Key", type="password", help="第三方API平台的密钥")
    base_url = st.text_input("接口地址 (Base URL)", value="https://yunwu.ai/v1/")
    
    # ------------------ 修改了这里 ------------------
    st.subheader("🤖 模型选择")
    # 预设几个目前最流行的高级写剧本模型
    model_options = [
        "deepseek-chat",           # DeepSeek V3 (性价比之王)
        "deepseek-reasoner",       # DeepSeek R1 (深度思考模型)
        "gpt-4o",                  # OpenAI 最新全能模型
        "claude-3-5-sonnet-20241022", # Claude 最新模型 (写文科极强)
        "✍️ 自定义 (手动输入其他模型ID)"
    ]
    
    selected_model = st.selectbox("选择常用模型", model_options)
    
    # 如果用户选择自定义，则弹出一个输入框让他自己填中转站的模型名称
    if selected_model == "✍️ 自定义 (手动输入其他模型ID)":
        model_name = st.text_input("请输入中转站对应的真实 模型ID", value="deepseek-chat", help="请参考 yunwu.ai 或你的中转站后台支持的模型名称列表")
    else:
        model_name = selected_model
        
    st.info(f"当前生效模型: **{model_name}**")
    # ------------------------------------------------
    
    st.markdown("---")
    st.header("🧠 全局记忆管理")
    st.caption("以下面板由AI自动更新，如果你发现AI遗忘了，可以在此点击清空重置。")
    if st.button("🗑️ 清空所有对话记忆", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.success("记忆已清空，系统已重置为初始状态。")

# ==========================================
# 4. 核心对话与AI请求逻辑
# ==========================================
def chat_with_ai(prompt):
    if not api_key:
        st.error("请先在左侧边栏填写 API Key！")
        st.stop()
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 开启流式输出
            response = client.chat.completions.create(
                model=model_name,
                messages=st.session_state.messages,
                stream=True,
                temperature=0.7 # 控制一定的创造力，但又不会太乱
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"API 请求失败: {e}")
            st.session_state.messages.pop() # 失败则移除刚才的用户提问
            return
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.last_ai_response = full_response
# ==========================================
# 5. 主工作区：小说输入与工作流
# ==========================================
st.title("🎬 影视化视觉翻译引擎 V3.1")
st.markdown("> **“小说是给耳朵的，剧本是给眼睛的。”** —— 严格按照6层视觉翻译法则执行。")

# 面板1：添加小说章节 (优化交互逻辑)
with st.expander("📝 步骤一：导入小说章节原文 (防文字转文字偷懒机制)", expanded=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("选择本地 TXT 文件", type=["txt"])
    with col2:
        pasted_text = st.text_area("或者在此处直接粘贴章节内容", height=150)
    
    # 获取当前输入框或文件中的文本
    current_input = ""
    if uploaded_file is not None:
        current_input = uploaded_file.getvalue().decode("utf-8")
    elif pasted_text:
        current_input = pasted_text

    # 操作按钮组
    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 4])
    with btn_col1:
        if st.button("📥 录入为当前处理章节 (覆盖旧内容)", type="primary"):
            if current_input:
                st.session_state.novel_content = current_input
                st.success(f"成功录入！当前待处理小说共计 {len(st.session_state.novel_content)} 字。")
            else:
                st.warning("请先上传文件或粘贴文本！")
    with btn_col2:
        if st.button("➕ 追加新章节 (保留之前内容)"):
            if current_input:
                st.session_state.novel_content += "\n\n" + current_input
                st.success(f"追加成功！当前系统内小说总计 {len(st.session_state.novel_content)} 字。")
            else:
                st.warning("请先上传文件或粘贴文本！")
    
    if st.session_state.novel_content:
        st.info(f"💡 系统内存中已有 {len(st.session_state.novel_content)} 字的小说原稿供提取。")

# 面板2：系统工作流控制台
st.markdown("### ⚙️ 编剧工作流控制台")
control_cols = st.columns(4)
if "global_setting" not in st.session_state:
    st.session_state.global_setting = "暂无全局设定，请先执行第1轮提炼，然后把觉得好的设定复制到这里备用。"

with st.expander("🧠 全局驱动卡与设定库 (允许人工修改)", expanded=False):
    st.session_state.global_setting = st.text_area(
        "在此修改或粘贴AI提炼的角色人设，后续生成将严格以此为准：", 
        value=st.session_state.global_setting, 
        height=200
    )

control_cols = st.columns(4)

with control_cols[0]:
    if st.button("🚀 第1轮：全局提炼", use_container_width=True):
        # ... (原代码不变)

with control_cols[1]:
    if st.button("🎬 第2轮：设计开场", use_container_width=True):
        # ... (原代码不变)

with control_cols[2]:
    episode_num = st.number_input("集数", min_value=1, value=1, label_visibility="collapsed")
    # 新增：剧情范围锚定
    plot_focus = st.text_input("本集剧情范围(防流水账):", placeholder="例：只写前30%女主被刁难的情节")
    
    if st.button(f"🎥 第3轮：生成第 {episode_num} 集", use_container_width=True):
        prompt = f"""
        开始生成剧本 第{episode_num}集。
        
        【剧情进度锚定】：本集只允许推进以下剧情：{plot_focus if plot_focus else '根据原文合理推进单集容量'}。绝对禁止剧情快进或流水账！
        
        【核心人设依据】：
        {st.session_state.global_setting}
        
        请严格执行【第3轮：剧本生成】的前置A、B、C、D并输出10-15个分镜。
        小说原文参考（请结合范围提取细节）：\n{st.session_state.novel_content}
        """
        chat_with_ai(prompt)
with control_cols[3]:
    if st.button("🔍 第4轮：自检并输出最终剧本", use_container_width=True):
        check_prompt = f"""
        请严格执行【第4轮：自检与优化】。
        对比刚刚生成的剧本与我上传的小说原文，针对每一个剧本分镜进行详细的检查。
        
        第一步：简要展示敌对视角攻击和量化打分。
        第二步（🚨核心要求）：结合打分和修改建议，**请务必将优化后的【完整剧本】重新输出一遍！**
        
        输出最终剧本时，必须严格遵守以下格式，绝对不准用一两句话概括（禁止偷懒）：
        【分镜X】
        场景：...
        画面+台词：(必须包含3个连续动作、详细的视觉描写、环境音效等，严格遵循视觉翻译法则)
        衔接点：...
        
        小说原文参考：
        {st.session_state.novel_content}
        """
        chat_with_ai(check_prompt)

st.divider()

# ==========================================
# 6. 对话历史展示区
# ==========================================
col_title, col_download = st.columns([3, 1])
with col_title:
    st.subheader("💬 创作记录面板")
with col_download:
    # 如果系统有最新生成的回复，展示下载按钮
    if st.session_state.last_ai_response:
        st.download_button(
            label="💾 将最新结果下载为 TXT",
            data=st.session_state.last_ai_response,
            file_name="微短剧生成_或_自检结果.txt",
            mime="text/plain",
            use_container_width=True
        )

# 过滤掉系统提示词，只展示用户和AI的对话
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 允许用户自由输入修改指令（如：只改第X集/优化台词等）
if user_input := st.chat_input("自由模式：输入如'只优化台词'、'修改第3个分镜，让他更冷血一点'..."):
    chat_with_ai(user_input)
