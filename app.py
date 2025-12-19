import streamlit as st
from openai import OpenAI
import os

# 页面配置
st.set_page_config(page_title="AI文案自动分镜工具", layout="wide")

st.title("🎬 AI文案自动分镜工具")
st.caption("输入解说文案，自动进行分镜处理，适配短视频节奏")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ API 设置")
    api_key = st.text_input("请输入 API Key", type="password")
    base_url = st.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1")
    model_id = st.selectbox(
        "选择模型 (Model ID)",
        ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-beta"]
    )
    st.info("提示：请确保中转接口支持所选模型 ID")

# 系统提示词 (核心逻辑)
SYSTEM_PROMPT = """你是一个优秀的电影解说工作员，你的任务是对文案进行精准的分镜处理。

1. 要求先逐字逐句理解文本中的内容，然后对文本进行分段处理。
2. 分镜要求：每个角色对话切换，场景切换，动作画面改变，都需要将其设定为下一个分镜，并将分段后的原文内容进行整理输出。
3. 整理后的内容不可遗漏原文中的任何一句话，一个字，不能改变原文故事结构，禁止添加原文以外任何内容。
4. 分镜逻辑：严格要求根据场景转换进行段落分行：当故事从一个场景切换到另一个场景时，请另起一行，用新的分镜来表示。
5. 节奏控制：每一段分镜所对应的文案不能太长。因为一个分镜只能停留约5秒，而35个字符接近5秒。因此，请务必保证每行分镜的文字长度在35个字符以内。如果一句话很长，请在不改变原意和文字的前提下，合理拆分成多个分镜。
6. 严格保持逻辑：不是用上传的原文段落来分镜，而是根据剧情来划分分镜，让分镜连贯流畅。
7. 输出格式要求：
1.第一行内容
2.第二行内容
3.第三行内容
以此类推。"""

# 主界面布局
col1, col2 = st.columns(2)

uploaded_file = st.file_uploader("选择本地 TXT 文案文件", type=['txt'])

if uploaded_file is not None:
    # 读取文本内容
    raw_text = uploaded_file.read().decode("utf-8")
    st.text_area("原文预览", raw_text, height=200)

    if st.button("🚀 开始自动化分镜处理"):
        if not api_key:
            st.error("请先在侧边栏配置 API Key")
        else:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                with st.spinner('AI 正在深度解析剧情并分镜...'):
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"请对以下文案进行分镜处理：\n\n{raw_text}"}
                        ],
                        temperature=0.3, # 降低随机性，保证严格遵循原文
                    )
                    
                    result = response.choices[0].message.content
                    
                    st.success("分镜处理完成！")
                    st.text_area("处理后的分镜文案", result, height=500)
                    
                    # 提供下载按钮
                    st.download_button(
                        label="下载分镜结果",
                        data=result,
                        file_name="分镜结果.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"处理失败: {str(e)}")

# 使用说明
with st.expander("📌 使用说明"):
    st.write("""
    1. 在侧边栏输入你的 API Key 和中转地址。
    2. 选择你要使用的模型。
    3. 上传本地 .txt 格式的文案文件。
    4. 点击开始处理，AI 会严格按照每行约35字、场景切换、角色切换的原则生成分镜。
    5. 生成的结果可以直接复制或下载。
    """)
