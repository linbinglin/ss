import streamlit as st
from openai import OpenAI
import os

# --- 核心提示词模版 (根据你提供的 6秒分镜模版) ---
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

# --- 页面配置 ---
st.set_page_config(
    page_title="AI 6秒分镜脚本生成器",
    page_icon="🎬",
    layout="wide"
)

# --- 侧边栏：设置 ---
with st.sidebar:
    st.header("⚙️ 模型设置")
    
    # API Key 输入
    api_key = st.text_input("API Key", type="password", help="请输入你的 API 密钥")
    
    # Base URL 输入 (默认你提供的地址)
    base_url = st.text_input("Base URL (中转地址)", value="https://yunwu.ai/v1/")
    
    # 模型名称输入 (允许用户自定义)
    model_name = st.text_input(
        "模型名称 (Model ID)", 
        value="gpt-4o", 
        placeholder="例如: deepseek-chat, gpt-4o, claude-3-5-sonnet-20240620"
    )
    
    st.markdown("---")
    st.markdown("### 支持模型参考")
    st.markdown("- `gpt-4o`\n- `deepseek-chat`\n- `claude-3-5-sonnet`\n- `gemini-pro`")

# --- 主页面 ---
st.title("🎬 6秒黄金时间轴 - 分镜生成器")
st.markdown("专为 AI 视频生成 (Runway/Pika/Sora) 打造。自动将文案重组为 **3.5s-6.5s** 的标准分镜单元。")

# 1. 文件上传
uploaded_file = st.file_uploader("📂 选择本地文件 (TXT 或 SRT)", type=['txt', 'srt'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        st.error("文件编码错误，请上传 UTF-8 编码的文本文件。")
        st.stop()

    # 显示原始内容预览
    with st.expander("查看原始文案", expanded=False):
        st.text_area("原始内容", content, height=150)

    # 生成按钮
    if st.button("🚀 开始生成分镜", type="primary"):
        if not api_key:
            st.error("请先在左侧侧边栏输入 API Key！")
        elif not base_url:
            st.error("请输入 Base URL！")
        elif not model_name:
            st.error("请输入模型名称！")
        else:
            # --- API 调用逻辑 ---
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            st.divider()
            st.subheader("📝 生成结果")
            
            # 使用流式输出 (Streaming) 以获得更好的体验
            result_container = st.empty()
            full_response = ""
            
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"请处理以下文案：\n\n{content}"}
                    ],
                    stream=True
                )
                
                # 实时显示生成内容
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content_chunk = chunk.choices[0].delta.content
                        full_response += content_chunk
                        result_container.markdown(full_response)
                
                # 生成完毕后提供下载
                st.download_button(
                    label="📥 下载分镜脚本 (.txt)",
                    data=full_response,
                    file_name="storyboard_output.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"发生错误: {e}")
                st.info("请检查 API Key、Base URL 和 模型名称是否正确。")

# --- 页脚 ---
st.markdown("---")
st.caption("Powered by Streamlit & OpenAI Compatible API")
