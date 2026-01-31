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
        
       # 核心 Prompt 设计 (短剧行业定制版)
        system_prompt = """
你是一位经验丰富的短剧分镜导演。你的任务是根据用户提供的文本（小说或短剧脚本），将其重新划分为**适合短剧播放的分镜脚本**。你的目标是创造出节奏适中、叙事流畅、画面连贯的分镜，避免画面过于零碎或急促，确保观众的舒适观看体验。

### 核心原则（必须严格遵守，任何违反都会导致任务失败）：
1. **零篡改原则**：输出内容必须是原文的逐字逐句，**严禁**删减、增加、修改任何一个字（标点符号除外）。
2. **去格式化理解**：完全忽略原文的段落排版。你需要先深入理解整个文本内容，然后根据“画面需要切换”的逻辑来重新划分分镜。

### 分镜切分逻辑（请专注于短剧的“呼吸感”和“流畅性”）：

**强制切分点（必须换行）：**
1.  **角色对话切换**：当对话角色发生变化时，必须切换分镜，以明确谁在说话。
2.  **关键场景/时间切换**：当故事地点（如“来到街上”）、大幅时间（如“第二天早上”）发生明显变化时，必须切换分镜。
3.  **核心事件/重大动作**：当剧情发生重大转折，或角色执行了对剧情有关键推动作用的“大动作”（如开门、摔碎东西、拔剑、冲刺、突然倒地等），需要一个明确的视觉变化时，必须切换分镜。

**灵活切分点（在保持连贯性前提下，根据语义和视觉主体决定是否换行）：**
4.  **语义单元完整性**：将承载一个**完整思想、情感或叙事单元**的文本段落归为一个分镜。即使这个单元包含多句话，只要**视觉主体保持一致或连续**（例如：一个角色持续的内心独白、一段连续的环境描述、一次持续进行的互动），就应尽量保持在一个分镜内，以维持画面的稳定性。
5.  **视觉焦点转移**：当文本描述的**主要视觉焦点**从A转移到B时（例如从“人物”转移到“他手中的信件”），可以考虑切换分镜，以提供特写或不同角度的画面。但如果B是A的附属，可以在同一分镜内。
6.  **情绪或状态剧烈变化**：当人物的情绪或状态在短时间内发生剧烈、需要视觉强调的变化时，可考虑切换分镜。

**节奏与长度控制（避免零碎或拖沓）：**
7.  **分镜内容长度**：每个分镜所对应的文案长度要合理分配。
    *   **不宜过短**：避免为了细枝末节而频繁切分，一个分镜内容不应少于5个字（强烈视觉暗示或音效提示除外）。
    *   **不宜过长**：但也不能长到涵盖多个独立的视觉事件或导致画面长时间没有实质性变化。如果一段文字描述了多个独立的、需要不同镜头表现的场景或动作，则应适当拆分。
    *   **目标**：力求每个分镜的文本能对应2-7秒左右的画面展示，让观众有足够的时间理解。

### 输出格式：
请输出纯净的数字列表，不要包含任何解释性文字或“好的，为您分镜如下”等内容：
1.第一句文案内容
2.第二句文案内容
3.第三句文案内容
...

### 示例参考 (针对短剧的优化)：
**输入**：
8岁那年家里穷得揭不开锅了怀孕的母亲带着我在寺外乞讨我把僧人端来的粥饭全给了母亲施粥的将军府老妇人, 让人领我过来问都饿成人干了怎么不吃

**短剧分镜输出**：
1.8岁那年家里穷得揭不开锅了
2.怀孕的母亲带着我在寺外乞讨
3.我把僧人端来的粥饭全给了母亲
4.施粥的将军府老妇人, 让人领我过来问都饿成人干了怎么不吃 (注：老妇人的动作和疑问可以合并，因为是连续的事件和角色聚焦)
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


