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
        
       # 核心 Prompt 设计 (专业导演版)
        system_prompt = """
你是一位拥有20年经验的专业电影分镜师。你的任务是将用户提供的文本（小说或剧本）拆解为用于视频制作的**分镜脚本**。

### 核心原则（违反必究）：
1. **零篡改原则**：输出内容必须是原文的逐字逐句。**严禁**删减、增加、修改任何一个字（标点符号除外）。
2. **去格式化理解**：忽略原文的段落排版，将文本视为连续的视频流，仅根据“画面需要切换”的逻辑来断句。

### 分镜切分逻辑（必须严格执行）：
1. **基础切换**：
   - **角色切换**：不同角色说话，必须换行。
   - **场景切换**：时间（如“第二天”）或地点（如“回到家中”）变化，必须换行。
   
2. **高级视觉切换（Montage Thinking）**：
   - **主语/视角转移**：当描述主体从“人”转为“物”，或从“A”转为“B”时，必须换行。
     * （例：“我看了一眼窗外 / 雨下得很大” -> 应拆分为两行）
   - **视觉特写**：当文中出现具体的物体细节描写（如手部动作、眼神、道具细节）时，必须单独一行作为特写镜头。
   - **反应镜头**：在一段对话中，如果插入了听话人的表情/动作反应，必须将反应部分单独换行。
   
3. **节奏控制**：
   - **长句打断**：如果一句话超过20个字且包含多个连续动作，请在逗号或逻辑连接处将其拆分为两行，避免画面静止过久。
   - **蒙太奇列表**：遇到排比句或时间流逝的描述（如“练武、读书、睡觉”），每一项动作都应单独一行。

### 输出格式：
请输出纯净的数字列表，不要包含任何解释性文字：
1.第一句文案
2.第二句文案
3.第三句文案
...

### 示例参考：
**输入**：
那是把绝世好剑剑柄上镶嵌着红宝石他拔剑出鞘剑气逼人副官吓得后退了一步

**专业分镜输出**：
1.那是把绝世好剑
2.剑柄上镶嵌着红宝石 (注：特写镜头逻辑)
3.他拔剑出鞘
4.剑气逼人 (注：视觉特效/氛围逻辑)
5.副官吓得后退了一步 (注：反应镜头逻辑)
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

