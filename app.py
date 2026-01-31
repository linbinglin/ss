import streamlit as st
from openai import OpenAI

# --- 页面基础设置 ---
st.set_page_config(
    page_title="AI 6秒分镜大师",
    page_icon="🎬",
    layout="wide"
)

# --- 核心提示词模版 (V3.0 - 针对图2效果优化) ---
SYSTEM_PROMPT = """
# Role: 资深短视频分镜师 (6s-Video Specialist)

## Goal
将用户输入的剧本/小说文本，拆解为适合 AI 视频生成的**分镜列表**。
**核心标准**：每一行对应的视频时长必须严格控制在 **3.5秒 ~ 6.5秒**。

## 核心执行准则 (必须严格遵守)

### 1. 时长控制 (字数锚定法)
AI生成的视频通常为 4s 或 6s。
*   **最佳长度**：每行文案长度控制在 **12 ~ 22 个中文字符**（含标点）。
*   **过长拆分**：如果一句话超过 25 字，**必须**在逗号或逻辑转折处拆分为两行。
    *   *错误*: 8岁那年家里穷得揭不开锅了，怀孕的母亲带着我在寺外乞讨。(24字 -> 危险，读完需7-8秒)
    *   *正确*: 
        1. 8岁那年家里穷得揭不开锅了，
        2. 怀孕的母亲带着我在寺外乞讨。
*   **过短合并**：如果一句话少于 8 字，尝试与下一句合并（除非是极短的强情绪对白）。

### 2. 格式与符号 (复刻图2风格)
*   **对话保护**：人物的对话（带引号 `“...”` 的内容）尽量**单独成行**，或者是“动作+对话”的形式。
*   **标点保留**：必须保留原文的标点符号，特别是引号。
*   **序号列表**：每一行必须以数字序号开头（1. 2. 3. ...）。

### 3. 内容完整性
*   **零删减**：严禁删除原文任何一个字。
*   **零修改**：严禁修改原文措辞。

## 思考与处理示例

**输入文本**:
我娘还怀着弟弟，我怕她吃不好，弟弟也跟着挨饿。她俯下身又问我，你怎么知道你娘怀的就是个弟弟呢。我爹说生不出儿子就要我娘一直生，她身子已弱极了，我怕她。

**处理逻辑**:
1. "我娘还怀着弟弟...挨饿" -> 字数适中，但分两段更有节奏。
2. "她俯下身又问我" + 对话 -> 动作引出对话，完美。
3. "我爹说...一直生" -> 这一句很长，包含因果，建议保留完整逻辑但注意时长，或者拆分。

**标准输出**:
1. “我娘还怀着弟弟，我怕她吃不好，弟弟也跟着挨饿。”
2. 她俯下身又问我：“你怎么知道你娘怀的就是个弟弟呢？”
3. “我爹说生不出儿子，就要我娘一直生。”
4. “她身子已弱极了，我……我怕她……”

## 初始化指令
读取用户输入，直接进行分镜拆解。**只输出分镜结果，不要输出任何分析过程或前言后语。**
"""

# --- 侧边栏：配置区域 ---
with st.sidebar:
    st.header("⚙️ 模型配置")
    
    # 1. API Base URL
    base_url = st.text_input(
        "API Base URL", 
        value="https://yunwu.ai/v1",
        help="例如: https://yunwu.ai/v1"
    )
    
    # 2. API Key
    api_key = st.text_input(
        "API Key", 
        type="password", 
        placeholder="sk-..."
    )
    
    st.markdown("---")
    
    # 3. 模型选择 (含自定义功能)
    st.subheader("🤖 模型选择")
    
    # 常用模型列表
    default_models = [
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20240620",
        "gemini-pro",
        "doubao-pro-32k"
    ]
    model_options = default_models + ["✨ 自定义 (Custom)"]
    
    selected_option = st.selectbox("选择模型", options=model_options, index=0)
    
    # 如果选择自定义，显示输入框
    if selected_option == "✨ 自定义 (Custom)":
        final_model_id = st.text_input("输入模型ID", placeholder="例如: deepseek-v3")
    else:
        final_model_id = selected_option
        
    if final_model_id:
        st.caption(f"当前模型: `{final_model_id}`")

# --- 主界面 ---
st.title("🎬 6秒黄金时间轴 - 智能分镜助手")
st.markdown("上传剧本 TXT，AI 将自动按 **[对话保留 + 15字节奏]** 进行拆解，还原小说阅读感。")

# 1. 文件上传
uploaded_file = st.file_uploader("📂 选择本地 TXT 文件", type=["txt"])

if "generated_content" not in st.session_state:
    st.session_state.generated_content = ""

# 2. 执行逻辑
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    
    with st.expander("📄 查看原始内容", expanded=False):
        st.text_area("Original Text", file_content, height=150)

    if st.button("🚀 开始分镜处理", type="primary"):
        if not api_key:
            st.error("❌ 请先配置 API Key")
        elif not final_model_id:
            st.error("❌ 请选择或输入模型 ID")
        else:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                result_area = st.empty()
                full_response = ""
                
                # 调用 API
                stream = client.chat.completions.create(
                    model=final_model_id,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"请处理以下剧本内容：\n\n{file_content}"}
                    ],
                    stream=True,
                    temperature=0.3 # 降低随机性，让格式更稳定
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        result_area.markdown(full_response)
                
                st.session_state.generated_content = full_response
                
            except Exception as e:
                st.error(f"❌ 发生错误: {str(e)}")

# 3. 结果下载
if st.session_state.generated_content:
    st.markdown("---")
    final_text = st.session_state.generated_content
    # 清洗 markdown 标记，确保下载的是纯文本
    clean_text = final_text.replace("```txt", "").replace("```", "").strip()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.download_button(
            label="📥 下载分镜文件 (.txt)",
            data=clean_text,
            file_name="storyboard_split.txt",
            mime="text/plain"
        )
    with col2:
        st.success("✅ 处理完成")
