import streamlit as st
from openai import OpenAI
import textwrap

# 页面配置
st.set_page_config(
    page_title="智能文案分镜助手",
    page_icon="🎬",
    layout="wide"
)

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 设置")
    
    api_key = st.text_input("请输入 API Key", type="password", help="请填写云雾或其他中转平台的 API Key")
    base_url = st.text_input("API Base URL", value="https://yunwu.ai/v1/", help="第三方中转接口地址")
    
    st.markdown("### 🤖 模型选择")
    # 预设模型列表，最后添加一个自定义选项
    model_options = [
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4o",
        "claude-3-5-sonnet-20240620",
        "gemini-1.5-pro",
        "grok-beta",
        "自定义 (Custom)"  # <--- 添加自定义选项
    ]
    
    selected_model_option = st.selectbox(
        "选择模型",
        options=model_options,
        index=0,
        help="选择预设模型，或者选择'自定义'手动输入模型ID"
    )

    # 逻辑判断：如果选择了自定义，则显示输入框；否则直接使用选择的值
    if selected_model_option == "自定义 (Custom)":
        model_id = st.text_input("👉 请手动输入模型 ID", value="", placeholder="例如: deepseek-v3")
    else:
        model_id = selected_model_option
    
    # 显示当前使用的模型ID以供确认
    if model_id:
        st.caption(f"当前使用模型: `{model_id}`")

    st.markdown("---")
    st.markdown("**分镜逻辑说明：**")
    st.caption("1. 忽略原文段落，重新理解语义")
    st.caption("2. 遇场景/对话/动作切换则分行")
    st.caption("3. 严格原文输出，不改一字")

# 主界面
st.title("🎬 AI 智能文案分镜工具")
st.markdown("上传 TXT 文本，AI 将自动分析剧情，进行专业的逐字逐句分镜处理。")

uploaded_file = st.file_uploader("选择本地 TXT 文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件内容
    try:
        string_data = uploaded_file.read().decode("utf-8")
        # 去掉原文的所有换行符，变成一整段，防止AI偷懒直接用原文分段
        clean_text = string_data.replace("\n", "").replace("\r", "").strip()
        
        st.subheader("📄 原文预览 (已去除格式)")
        st.text_area("原文内容", clean_text, height=150, disabled=True)
        
       # 核心 Prompt 设计 (爆款短剧导演版 - 节奏平衡)
        system_prompt = """
你是一位专业的爆款微短剧导演和剪辑师。你的任务是将用户输入的文本，拆解为符合观众视听习惯的视频分镜脚本。
微短剧的核心痛点是：镜头不能切得太碎（导致观众眼花缭乱），也不能太长（导致视觉疲劳）。

### 核心铁律：
1. **零篡改原则**：输出内容必须是原文的逐字逐句，严禁修改、增减任何字词（只重构分行）。
2. **忘掉原文排版**：无视原文的换行，重新根据画面节奏断句。

### 黄金分镜节奏逻辑（核心要求）：
一个舒适的短剧镜头大约停留 3-6 秒，对应文案大约 **10 到 30 个字**。请以此为锚点进行切分。

#### ⛔ 防碎剪机制（何时必须合并，不能切）：
1. **连贯动作一镜到底**：同一主体连续的几个小动作（如：“他拿起茶杯，吹了吹热气，轻轻抿了一口”），请合并为同一个分镜，不要切开。
2. **说话人神态+台词**：说话者的动作神态与他的台词（如：“将军怒吼道：你给我滚出去！”），必须合并在同一分镜。
3. **字数过少强行合并**：如果某句分镜少于8个字，请寻找上下文逻辑，将其并入上一句或下一句，避免画面一闪而过。

#### ✅ 必切分机制（何时必须切开）：
1. **角色切换**：从 A 说话切换到 B 说话或 B 做动作时，必须换行。
2. **场景/时间跳跃**：时间（“三年后”）或空间（“回到公司”）发生转变，必须换行。
3. **超长句打断**：如果一段文案超过 40 个字，或者包含多个复杂的主体变化，请在自然的语意停顿处（逗号或句号）将其切分为两行。

### 输出格式：
只输出纯净的数字列表，不要包含任何解释性文字：
1.第一句文案内容
2.第二句文案内容
3.第三句文案内容

### 正确节奏示例：
**输入**：
林萧冷笑一声把合同狠狠砸在桌上吓得周围高管大气都不敢喘他转过身看着窗外这只是个开始

**专业短剧分镜输出**：
1.林萧冷笑一声把合同狠狠砸在桌上 (动作+情绪，约3秒)
2.吓得周围高管大气都不敢喘 (主体转移，反应镜头，约2.5秒)
3.他转过身看着窗外这只是个开始 (情绪转折+内心独白，约4秒)
"""

        user_prompt = f"请对以下文本进行分镜处理：\n\n{clean_text}"

        generate_btn = st.button("🚀 开始生成分镜", type="primary")

        if generate_btn:
            if not api_key:
                st.error("请先在左侧侧边栏设置 API Key！")
            elif not model_id:
                st.error("请选择或输入有效的模型 ID！")
            else:
                st.divider()
                st.subheader("🎞️ 分镜结果")
                output_placeholder = st.empty()
                full_response = ""
                
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )

                    # 使用流式输出 (Stream=True)
                    stream = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        stream=True,
                        temperature=0.3, # 降低随机性，保证忠实原文
                    )

                    # 实时显示结果
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            output_placeholder.markdown(full_response)
                    
                    st.success("分镜处理完成！")
                    
                    # 提供下载按钮
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=full_response,
                        file_name="storyboard_script.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
                    st.info("提示：请检查 API Key 是否正确，或尝试更换模型 ID。")

    except UnicodeDecodeError:
        st.error("文件编码错误，请确保上传的是 UTF-8 编码的 TXT 文件。")



