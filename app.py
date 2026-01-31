import streamlit as st
from openai import OpenAI
import os

# --- 核心提示词模版 (根据你的文件内容植入) ---
SYSTEM_PROMPT_TEMPLATE = """
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
3. **划分语句**：为文本添加合适标点。
4. **输出**: 直接输出重组后的 `txt` 代码块。
"""

# --- 页面配置 ---
st.set_page_config(
    page_title="AI视频分镜大师 (6秒法则)",
    page_icon="🎬",
    layout="wide"
)

# --- 侧边栏：API 配置 ---
st.sidebar.header("🔌 API 设置")
st.sidebar.markdown("配置云雾API或其他中转服务")

api_base = st.sidebar.text_input("API Base URL", value="https://yunwu.ai/v1/")
api_key = st.sidebar.text_input("API Key", type="password", help="请输入您的API Key")

# 模型预设列表 (包含你要求的模型)
model_options = {
    "DeepSeek V3": "deepseek-chat",
    "DeepSeek R1": "deepseek-reasoner",
    "GPT-4o": "gpt-4o",
    "Claude 3.5 Sonnet": "claude-3-5-sonnet-20240620",
    "Gemini Pro": "gemini-1.5-pro",
    "Grok Beta": "grok-beta",
    "豆包 (Doubao)": "doubao-pro-32k", # 注意：具体ID需根据中转商实际支持填写
    "自定义模型": "custom"
}

selected_model_label = st.sidebar.selectbox("选择大模型", list(model_options.keys()))

if selected_model_label == "自定义模型":
    model_name = st.sidebar.text_input("请输入自定义模型ID")
else:
    model_name = model_options[selected_model_label]

st.sidebar.info(f"当前使用模型 ID: `{model_name}`")

# --- 主界面 ---
st.title("🎬 AI 6秒分镜生成器")
st.markdown("**功能**：上传剧本/字幕，自动按「6秒黄金法则」拆解分镜。")

# 1. 文件上传
uploaded_file = st.file_uploader("📂 选择本地文件 (TXT/SRT)", type=['txt', 'srt', 'md'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        content = uploaded_file.read().decode("utf-8")
        st.subheader("📄 原文预览")
        with st.expander("查看原文内容", expanded=False):
            st.text_area("Original Text", content, height=150, label_visibility="collapsed")
    except Exception as e:
        st.error(f"文件读取失败，请确保文件是 UTF-8 编码。错误: {e}")
        content = None

    # 2. 执行按钮
    if content and api_key:
        if st.button("🚀 开始生成分镜 (AI Process)", type="primary"):
            
            result_placeholder = st.empty()
            result_placeholder.info("正在连接 AI 模型进行深度思考与分镜拆解，请稍候...")

            try:
                # 初始化 OpenAI 客户端 (兼容云雾API)
                client = OpenAI(
                    api_key=api_key,
                    base_url=api_base
                )

                # 调用 API
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                        {"role": "user", "content": f"请处理以下文本：\n\n{content}"}
                    ],
                    stream=True, # 开启流式输出
                    temperature=0.7
                )

                # 流式接收结果
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        result_placeholder.markdown(full_response + "▌")
                
                # 显示最终结果
                result_placeholder.markdown(full_response)
                
                st.success("✅ 分镜生成完成！")

                # 3. 下载功能
                st.download_button(
                    label="📥 下载分镜脚本 (.txt)",
                    data=full_response,
                    file_name="storyboard_output.txt",
                    mime="text/plain"
                )

            except Exception as e:
                result_placeholder.empty()
                st.error(f"❌ API 请求出错: {str(e)}")
                st.warning("建议检查：1. API Key 是否正确。 2. 模型 ID 是否有效。 3. 账户余额。")
    
    elif content and not api_key:
        st.warning("⚠️ 请在左侧边栏输入 API Key 才能开始处理。")

# --- 底部版权 ---
st.divider()
st.caption("Powered by Streamlit | 6秒黄金时间轴V2.0算法")
