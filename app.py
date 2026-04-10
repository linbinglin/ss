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

# ==========================================
# 3. 侧边栏：API配置与记忆面板
# ==========================================
with st.sidebar:
    st.header("⚙️ API 配置中心")
    api_key = st.text_input("输入 API Key", type="password", help="第三方API平台的密钥")
    base_url = st.text_input("接口地址 (Base URL)", value="https://yunwu.ai/v1/")
    
    # 模型选择
    model_options = [
        "deepseek-chat", 
        "deepseek-coder",
        "gpt-4-turbo", 
        "gpt-4o",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "moonshot-v1-128k"
    ]
    model_name = st.selectbox("选择模型 ID", model_options)
    
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

# ==========================================
# 5. 主工作区：小说输入与工作流
# ==========================================
st.title("🎬 影视化视觉翻译引擎 V3.1")
st.markdown("> **“小说是给耳朵的，剧本是给眼睛的。”** —— 严格按照6层视觉翻译法则执行。")

# 面板1：添加小说章节
with st.expander("📝 步骤一：导入小说章节原文 (防文字转文字偷懒机制)", expanded=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("选择本地 TXT 文件", type=["txt"])
    with col2:
        pasted_text = st.text_area("或者在此处直接粘贴章节内容", height=150)
    
    # 合并文本内容
    current_text = ""
    if uploaded_file is not None:
        current_text = uploaded_file.getvalue().decode("utf-8")
    if pasted_text:
        current_text = pasted_text
        
    if current_text:
        st.success(f"已成功加载小说内容，共计 {len(current_text)} 字。")
        st.session_state.novel_content = current_text

# 面板2：系统工作流控制台
st.markdown("### ⚙️ 编剧工作流控制台")
control_cols = st.columns(4)

with control_cols[0]:
    if st.button("🚀 第1轮：全局提炼", use_container_width=True):
        if not st.session_state.novel_content:
            st.warning("请先在上方导入小说内容！")
        else:
            prompt = f"【微短剧3.1启动】\n以下为小说最新内容，请执行【第1轮：全局提炼】。\n\n小说内容如下：\n{st.session_state.novel_content}"
            chat_with_ai(prompt)

with control_cols[1]:
    if st.button("🎬 第2轮：设计开场", use_container_width=True):
        chat_with_ai("已确认角色驱动卡。请执行【第2轮：开场手法设计】。")

with control_cols[2]:
    episode_num = st.number_input("集数设置", min_value=1, max_value=100, value=1, label_visibility="collapsed")
    if st.button(f"🎥 第3轮：生成第 {episode_num} 集", use_container_width=True):
        chat_with_ai(f"开始生成剧本 第{episode_num}集。请严格执行【第3轮：剧本生成】的前置A、B、C、D并输出10-15个分镜。")

with control_cols[3]:
    if st.button("🔍 第4轮：原著对比自检", use_container_width=True):
        check_prompt = """
        请严格执行【第4轮：自检与优化】。
        对比刚刚生成的剧本与小说原文，针对每一个剧本分镜进行详细的检查。
        1. 调用敌对视角攻击（普通观众、竞品编剧、原著粉）。
        2. 进行量化打分。
        3. 7分以下的项目必须立即给出修改版！
        """
        chat_with_ai(check_prompt)

st.divider()

# ==========================================
# 6. 对话历史展示区
# ==========================================
st.subheader("💬 创作记录面板")
# 过滤掉系统提示词，只展示用户和AI的对话
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 允许用户自由输入修改指令（如：只改第X集/优化台词等）
if user_input := st.chat_input("自由模式：输入如'只优化台词'、'修改第3个分镜，让他更冷血一点'..."):
    chat_with_ai(user_input)
