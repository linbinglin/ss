import streamlit as st
from openai import OpenAI
import os

# --- 页面基础设置 ---
st.set_page_config(
    page_title="AI 6秒分镜大师",
    page_icon="🎬",
    layout="wide"
)

# --- 核心提示词模版 (基于提供的V2.0模版) ---
SYSTEM_PROMPT = """
# Role: 资深AI漫剧分镜导演 (6s-Video Specialist)
## Profile
- **身份**: 专精于**6秒短视频节奏**的分镜导演。你擅长将松散的台词压缩为高密度的“6秒视觉胶囊”。
- **任务**: 读取用户提供的字幕（SRT或文本），将其重组为一系列**“6秒标准视频单元”**。
- **核心目标**: 确保每一行文案对应的阅读/表演时长严格落在 **[3.5秒 - 6.5秒]** 区间内。完美适配Runway/Pika/Sora等模型的6秒生成模式。

## 核心算法与绝对约束 (Crucial Algorithms)

### 1. 黄金时间轴锁定 (The 6s Golden Lock)
*   **目标时长**: **6秒** (AI生成视频的标准时长)。
*   **文案时长限制**: 单行文案的阅读时长必须控制在 **3.5秒 - 6.5秒**。
    *   **< 3.5秒**: **禁止输出**。必须向下合并下一句（除非是极短的强情绪词，如“滚！”）。
    *   **> 6.5秒**: **强制预警**。必须寻找最近的语义点进行切分，否则视频生成会由快变慢或画面冻结。

### 2. 视觉密度整合法则 (Visual Consolidation)
在6秒的时长里，画面必须饱满但不能杂乱。
*   **合并原则**:
    *   **动作+结果**: “我拿起杯子” (2s) + “喝了一口水” (2s) = **4s (完美合并)**。-> *输出: 我拿起杯子喝了一口水。*
    *   **环境+主体**: “雨很大” (2s) + “淋湿了我的头发” (3s) = **5s (完美合并)**。-> *输出: 雨很大，淋湿了我的头发。*
*   **切分原则**:
    *   如果两句话合并后超过7秒（约30个字），必须在中间的逗号或逻辑转折处切开，确保每一段都在6秒内。

### 3. 语义原子性 (Semantic Atomicity)
*   **关联词保护**: 严禁在“因为/所以/但是/虽然”之后立刻断句。
*   **主谓不离**: 严禁出现“我是(换行)一个好人”这种低级错误。

### 4. 原文零容忍协议 (Zero Tolerance)
*   **严禁改词**: 绝对不允许修改、增加、删除原字幕的任何文字（汉字）。
*   **清洗格式**: 必须去除SRT原本的序号（1,2...）和时间码（00:00:xx...）。

## 输出格式 (Strict Output Format)
- **纯文本**模式。
- 每一行对应一个**6秒**的分镜。
- **严禁**输出时间码、序号、解析或废话。
- 每一行的末尾必须是标点符号。
- 每一行的前方必须加上序号。
- 最终结果必须放在 `txt` 代码块中。

## 初始化指令
请读取用户提供的字幕内容。
1. **计算**: 按正常语速预估时长。
2. **重组**: 严格执行[3.5s - 6.5s]的区间合并与切分。
3. **输出**: 直接输出重组后的 `txt` 代码块。
"""

# --- 侧边栏：配置区域 ---
with st.sidebar:
    st.header("⚙️ 模型配置")
    
    # 1. API Base URL 配置
    base_url = st.text_input(
        "API Base URL (中转接口)", 
        value="https://yunwu.ai/v1",
        help="请输入OpenAI兼容接口地址，末尾通常包含/v1"
    )
    
    # 2. API Key 配置
    api_key = st.text_input(
        "API Key", 
        type="password", 
        placeholder="sk-..."
    )
    
    # 3. 模型选择 (包含DeepSeek, GPT-4o, Claude等)
    # 这里预设了一些常用模型ID，用户也可以手动输入
    model_options = [
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20240620",
        "gemini-pro",
        "grok-beta",
        "doubao-pro-32k"
    ]
    selected_model = st.selectbox(
        "选择模型 (Model ID)", 
        options=model_options,
        index=0, # 默认选择第一个
        help="选择第三方接口支持的模型名称"
    )
    
    st.markdown("---")
    st.info("💡 提示：请确保你的API Key有对应模型的访问权限。")

# --- 主界面 ---
st.title("🎬 6秒黄金时间轴 - 智能分镜助手")
st.markdown("上传剧本TXT，AI将自动按照 **[3.5s - 6.5s]** 的节奏进行分镜拆解，完美适配 Runway/Sora/Pika 生成。")

# 1. 文件上传
uploaded_file = st.file_uploader("📂 选择本地 TXT 剧本文件", type=["txt"])

# 初始化 Session State 用于存储结果
if "generated_content" not in st.session_state:
    st.session_state.generated_content = ""

# 2. 执行按钮与逻辑
if uploaded_file is not None:
    # 读取文件内容
    file_content = uploaded_file.read().decode("utf-8")
    
    # 显示原始内容预览
    with st.expander("查看原始文案", expanded=False):
        st.text_area("Original Text", file_content, height=150)

    if st.button("🚀 开始AI分镜处理", type="primary"):
        if not api_key:
            st.error("❌ 请先在左侧侧边栏输入 API Key")
        else:
            try:
                # 初始化 OpenAI 客户端
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                # 创建显示区域
                result_area = st.empty()
                full_response = ""
                
                st.subheader("🤖 AI 处理结果")
                
                # 调用 API (流式输出)
                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"请处理以下文案：\n\n{file_content}"}
                    ],
                    stream=True,
                    temperature=0.7 # 稍微降低随机性以保证格式稳定
                )
                
                # 实时渲染流式响应
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        result_area.markdown(full_response)
                
                # 存储结果到 session state
                st.session_state.generated_content = full_response
                
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 3. 结果下载与展示
if st.session_state.generated_content:
    st.markdown("---")
    # 提取代码块中的内容 (如果AI输出了markdown代码块)
    final_text = st.session_state.generated_content
    # 简单的清洗逻辑，尝试去掉 ```txt 和 ``` 标记，只保留纯文本供下载
    clean_text = final_text.replace("```txt", "").replace("```", "").strip()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.download_button(
            label="📥 下载分镜脚本 (.txt)",
            data=clean_text,
            file_name="split_script_6s.txt",
            mime="text/plain"
        )
    with col2:
        st.success("✅ 处理完成！可以直接复制或下载。")
