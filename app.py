import streamlit as st
from openai import OpenAI
import textwrap

# 页面配置
st.set_page_config(
    page_title="6秒黄金分镜助手",
    page_icon="⏱️",
    layout="wide"
)

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 设置")
    
    api_key = st.text_input("请输入 API Key", type="password", help="请填写云雾或其他中转平台的 API Key")
    base_url = st.text_input("API Base URL", value="https://yunwu.ai/v1/", help="第三方中转接口地址")
    
    st.markdown("### 🤖 模型选择")
    # 预设模型列表
    model_options = [
        "deepseek-chat",
        "gpt-4o",
        "claude-3-5-sonnet-20240620",
        "deepseek-reasoner",
        "自定义 (Custom)"
    ]
    
    selected_model_option = st.selectbox(
        "选择模型",
        options=model_options,
        index=0,
        help="建议使用 deepseek-chat 或 gpt-4o，逻辑理解最强"
    )

    if selected_model_option == "自定义 (Custom)":
        raw_model_id = st.text_input("👉 请手动输入模型 ID", value="", placeholder="例如: deepseek-v3")
        model_id = raw_model_id.strip() 
    else:
        model_id = selected_model_option
    
    if model_id:
        st.caption(f"当前使用模型: `{model_id}`")

    st.markdown("---")
    st.info("已加载：6秒分镜模版 - 黄金时间轴V2.0")

# 主界面
st.title("⏱️ 6秒 AI 漫剧分镜工具")
st.markdown("专为 Runway/Kling/Luma 等 AI 视频模型设计，严格执行 **3.5s - 6.5s** 黄金节奏。")

uploaded_file = st.file_uploader("选择本地 TXT 文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        string_data = uploaded_file.read().decode("utf-8")
        # 去掉原文的所有换行符，变成一整段，防止AI偷懒
        clean_text = string_data.replace("\n", "").replace("\r", "").strip()
        
        st.subheader("📄 原文预览 (已去除格式)")
        st.text_area("原文内容", clean_text, height=150, disabled=True)
        
        # ---------------------------------------------------------
        # 核心 Prompt 设计 - 原封不动植入你的指令
        # ---------------------------------------------------------
        system_prompt = """
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

## 思考路径修正示例 (Corrective Thinking)

**[反面案例 - 节奏崩坏]**:
1. 天亮了。(1.5s) -> *错误：太短，浪费一次生成机会*
2. 阳光照在我的脸上，我觉得非常温暖，仿佛回到了童年。(9.0s) -> *错误：太长，6秒视频跑不完这段话，画面会嘴型对不上*

**[正面案例 - 6秒黄金节奏]**:
*(处理逻辑: 1太短，合并入2；合并后总长10.5s太长，寻找中间切分点)*
1. 天亮了，阳光照在我的脸上。(4.0s) -> *完美：环境+状态*
2. 我觉得非常温暖，仿佛回到了童年。(5.0s) -> *完美：情绪+想象*

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

**执行**
深度思考后，直接开始执行。
"""

        user_prompt = f"请对以下文本进行处理：\n\n{clean_text}"

        generate_btn = st.button("🚀 生成 6秒黄金分镜", type="primary")

        if generate_btn:
            if not api_key:
                st.error("请先在左侧侧边栏设置 API Key！")
            elif not model_id:
                st.error("请选择或输入有效的模型 ID！")
            else:
                st.divider()
                st.subheader("🎞️ 6秒节奏分镜结果")
                output_placeholder = st.empty()
                full_response = ""
                
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )

                    stream = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        stream=True,
                        temperature=0.1, # 保持低温，确保严格执行指令
                    )

                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            output_placeholder.markdown(full_response)
                    
                    st.success("分镜处理完成！")
                    
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=full_response,
                        file_name="6s_storyboard_script.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
                    st.info("提示：请检查 API Key 是否正确，或尝试更换模型 ID。")

    except UnicodeDecodeError:
        st.error("文件编码错误，请确保上传的是 UTF-8 编码的 TXT 文件。")
