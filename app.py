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
    st.markdown("**⏱️ 6秒黄金时间轴逻辑：**")
    st.info("目标：将文案重组为适合 AI 生成的 6秒视频单元。")
    st.caption("1. **合并短句**：<3.5秒 (约10字内) 必须合并。")
    st.caption("2. **切分长句**：>6.5秒 (约20字以上) 必须切分。")
    st.caption("3. **严禁改词**：保持原文绝对一致。")

# 主界面
st.title("⏱️ 6秒 AI 漫剧分镜工具")
st.markdown("专为 Runway/Kling/Luma 等 AI 视频模型设计，自动将文案重组为 **3.5s - 6.5s** 的黄金节奏。")

uploaded_file = st.file_uploader("选择本地 TXT 文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        string_data = uploaded_file.read().decode("utf-8")
        # 去掉原文的所有换行符，变成一整段
        clean_text = string_data.replace("\n", "").replace("\r", "").strip()
        
        st.subheader("📄 原文预览 (已去除格式)")
        st.text_area("原文内容", clean_text, height=150, disabled=True)
        
        # 核心 Prompt 设计 - 6秒黄金时间轴版
        system_prompt = """
# Role: 资深AI漫剧分镜导演 (6s-Video Specialist)

## Profile
- **身份**: 专精于**6秒短视频节奏**的分镜导演。你擅长将松散的台词压缩为高密度的“6秒视觉胶囊”。
- **任务**: 读取用户提供的文本，将其重组为一系列**“6秒标准视频单元”**。
- **核心目标**: 确保每一行文案对应的阅读/表演时长严格落在 **[3.5秒 - 6.5秒]** 区间内。完美适配Runway/Pika/Sora等模型的6秒生成模式。

## 核心算法与绝对约束 (Crucial Algorithms)

### 1. 黄金时间轴锁定 (The 6s Golden Lock)
*   **字数辅助估算**: 假设正常语速下，**4-5个汉字 ≈ 1秒**。
    *   **目标区间**: 每行文案长度最好控制在 **12字 - 25字** 之间。
*   **时长限制**:
    *   **< 3.5秒 (约10字以内)**: **禁止单独输出**。必须向下合并下一句（除非是极短的强情绪爆发，如“滚！”）。
    *   **> 6.5秒 (约30字以上)**: **强制预警**。必须寻找最近的语义停顿点（逗号）进行切分，否则视频生成会由快变慢或画面冻结。

### 2. 视觉密度整合法则 (Visual Consolidation)
在6秒的时长里，画面必须饱满但不能杂乱。
*   **合并原则 (Merge)**:
    *   **动作+结果**: “我拿起杯子” (短) + “喝了一口水” (短) = **合并输出**。
    *   **环境+主体**: “雨很大” (短) + “淋湿了我的头发” (短) = **合并输出**。
*   **切分原则 (Split)**:
    *   如果两句话合并后过长（超过30字），必须在中间的逗号或逻辑转折处切开。

### 3. 语义原子性 (Semantic Atomicity)
*   **关联词保护**: 严禁在“因为/所以/但是/虽然”之后立刻断句。
*   **主谓不离**: 严禁出现“我是(换行)一个好人”这种低级错误。

### 4. 原文零容忍协议 (Zero Tolerance)
*   **严禁改词**: 绝对不允许修改、增加、删除原文的任何文字（汉字）。
*   **格式**: 请输出纯净的文本，每一行是一句完整的分镜。

## 思考路径修正示例

**[反面案例 - 节奏崩坏]**:
1. 天亮了。(太短，浪费生成次数)
2. 阳光照在我的脸上，我觉得非常温暖，仿佛回到了童年。(太长，画面会不够用)

**[正面案例 - 6秒黄金节奏]**:
1. 天亮了，阳光照在我的脸上。 (环境+状态，约4秒，完美)
2. 我觉得非常温暖，仿佛回到了童年。 (情绪+想象，约5秒，完美)

## 输出格式
1.请直接输出序号列表。
2.不要包含任何分析过程或废话。
3.每一行的末尾必须保留原文标点。

"""

        user_prompt = f"请对以下文本进行【6秒黄金分镜】处理：\n\n{clean_text}"

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
                        temperature=0.1, # 极低温度，确保严格遵循合并规则，不乱发挥
                    )

                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            output_placeholder.markdown(full_response)
                    
                    st.success("分镜处理完成！符合 3.5s - 6.5s 节奏。")
                    
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
