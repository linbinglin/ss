import streamlit as st
from openai import OpenAI
import os

# --- 页面配置 ---
st.set_page_config(page_title="AI 6秒分镜助手", layout="wide")

# --- 侧边栏：API 配置 ---
st.sidebar.title("⚙️ 设置")

st.sidebar.markdown("### 1. API 接入")
# 默认使用云雾API地址
base_url = "https://yunwu.ai/v1/" 
st.sidebar.info(f"中转接口: {base_url}")

# API Key 输入
api_key = st.sidebar.text_input("请输入 API Key", type="password", help="在此输入云雾API的Key (sk-...)")

st.sidebar.markdown("---")

# --- 核心功能：模型选择 (满足用户自定义填写需求) ---
st.sidebar.markdown("### 2. 模型选择")

# 预设一些常用模型，最后加一个"自定义"选项
model_mode = st.sidebar.radio(
    "选择方式:",
    ("选择常用模型", "自定义填写模型ID")
)

if model_mode == "选择常用模型":
    # 这里的列表你可以根据云雾支持的模型随时补充
    model_name = st.sidebar.selectbox(
        "请选择模型:",
        ["gpt-4o", "claude-3-5-sonnet-20240620", "gpt-4-turbo", "gpt-3.5-turbo"]
    )
else:
    # 这里满足用户“自己填写”的需求
    model_name = st.sidebar.text_input(
        "请输入模型ID:", 
        value="", 
        placeholder="例如: deepseek-chat, gemini-pro...",
        help="请准确输入模型在API中的ID名称"
    )

st.sidebar.info(f"当前使用的模型: **{model_name}**")

st.sidebar.markdown("---")
st.sidebar.markdown("### 关于")
st.sidebar.markdown("此工具用于将长文案按**6秒黄金时间轴**进行智能切分，适配Runway/Sora等生成式AI。")

# --- 主页面 ---
st.title("🎬 AI 6秒漫剧分镜生成器")
st.markdown("上传文案TXT文件，AI将自动按照 **[3.5s - 6.5s]** 的节奏重组分镜。")

# --- 核心 Prompt 模版 ---
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
3. **划分语句**，为文本添加合适语句
4. **输出**: 直接输出重组后的 `txt` 代码块。
"""

# --- 文件上传 ---
uploaded_file = st.file_uploader("📂 请选择本地TXT文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        content = uploaded_file.read().decode("utf-8")
        st.subheader("原始文案预览:")
        st.text_area("Original Text", content, height=150)
        
        # 处理按钮
        if st.button("🚀 开始分镜处理", type="primary"):
            # 校验输入
            if not api_key:
                st.error("❌ 错误：请先在左侧侧边栏输入 API Key！")
            elif not model_name:
                st.error("❌ 错误：模型名称不能为空！请在侧边栏选择或填写模型ID。")
            else:
                with st.spinner(f'AI导演正在使用 {model_name} 思考分镜节奏...'):
                    try:
                        # 初始化 OpenAI 客户端
                        client = OpenAI(
                            api_key=api_key,
                            base_url=base_url
                        )

                        # 调用 API
                        response = client.chat.completions.create(
                            model=model_name, # 使用用户选择或填写的模型名称
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": content}
                            ],
                            temperature=0.7
                        )
                        
                        # 获取结果
                        result_text = response.choices[0].message.content
                        
                        # 展示结果
                        st.success("✅ 处理完成！")
                        st.subheader("📋 分镜结果")
                        st.markdown(result_text)
                        
                        # 提供下载按钮
                        st.download_button(
                            label="📥 下载分镜结果 (.txt)",
                            data=result_text,
                            file_name="split_storyboard.txt",
                            mime="text/plain"
                        )

                    except Exception as e:
                        st.error(f"发生错误: {str(e)}")
                        st.info("💡 提示：请检查API Key是否正确，或确认该模型ID是否存在于云雾AI中。")
                        
    except UnicodeDecodeError:
        st.error("文件编码错误，请确保上传的是 UTF-8 编码的 TXT 文件。")
