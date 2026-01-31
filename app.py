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
        
        # 核心 Prompt 设计
        system_prompt = """
你是一位专业的影视分镜导演。你的任务是将用户提供的文本重新划分为分镜脚本。
请严格遵守以下规则，任何违反都会导致任务失败：

1. **绝对忠实原文**：输出的内容必须是原文的逐字逐句，**严禁**修改、删除、增加任何一个字。不要进行总结，不要进行改写。
2. **重构分段逻辑**：请完全忽略原文的段落格式。你需要先理解整段文本，然后根据画面感进行切分。
3. **切分标准**：
   - 当**说话角色**发生变化时，必须切换分镜。
   - 当**场景**（地点/时间）发生变化时，必须切换分镜。
   - 当**视觉动作**发生显著变化时，必须切换分镜。
4. **长度控制**：分镜文案不宜过长（造成视觉疲劳），也不宜过短（过于细碎）。请根据自然语流和画面节奏合理断句。
5. **输出格式**：
   - 请使用数字列表格式输出，例如：
     1.第一句文案内容
     2.第二句文案内容
   - 纯粹输出分镜内容，不要包含"好的"、"分析如下"等任何废话。

**示例输入**：
8岁那年家里穷得揭不开锅了怀孕的母亲带着我在寺外乞讨我把僧人端来的粥饭全给了母亲施粥的将军府老妇人, 让人领我过来问都饿成人干了怎么不吃

**示例输出**：
1.8岁那年家里穷得揭不开锅了
2.怀孕的母亲带着我在寺外乞讨
3.我把僧人端来的粥饭全给了母亲
4.施粥的将军府老妇人, 让人领我过来问
5.都饿成人干了怎么不吃
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
