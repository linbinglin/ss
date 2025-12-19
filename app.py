import streamlit as st
from openai import OpenAI
import io

# 设置页面配置
st.set_page_config(page_title="AI 文案自动分镜工具", layout="wide")

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 配置选项")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
# 注意：中转地址通常到 /v1 结束
base_url = st.sidebar.text_input("2. 中转接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("3. 选择模型 (Model ID)", 
                                 ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet", 
                                  "gemini-1.5-pro", "grok-1", "doubao-pro-128k"])
custom_model = st.sidebar.text_input("或者手动输入其他 Model ID")
final_model = custom_model if custom_model else model_id

# --- 主界面 ---
st.title("🎬 电影解说文案自动分镜系统")
st.info("💡 提示：请确保 GitHub 仓库根目录下有 requirements.txt 文件，内容包含 streamlit 和 openai")

uploaded_file = st.file_uploader("选择本地 TXT 文案文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件
    content = uploaded_file.getvalue().decode("utf-8")
    
    with st.expander("👀 查看原始文案"):
        st.text_area("原文内容", content, height=200)

    if st.button("🚀 开始自动化分镜分析"):
        if not api_key:
            st.error("请先在侧边栏输入 API Key！")
        else:
            try:
                # 初始化客户端 (修正了参数名，只使用 base_url)
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                system_prompt = """
你是一个优秀的电影解说工作员，接下来我会提供给你一个文本，
1.要求先逐字逐句理解文本中的内容，然后对文本进行分段处理。
2.分镜要求：每个角色对话切换，场景切换，动作画面改变，都需要将其设定为下一个分镜，并将分段后的原文内容进行整理输出。
3.整理后的内容不可遗漏原文中的任何一句话，一个字，不能改变原文故事结构，禁止添加原文以外任何内容。
5.分镜逻辑：严格要求根据场景转换进行段落分行：当故事从一个场景切换到另一个场景时，请另起一行，用新的分镜来表示。
6.每一个分段都要符合分段逻辑，每一段分镜所对应的文案不能太长。
7.请记住：不是用上传的原文段落来分镜，而是根据剧情来划分分镜，让分镜连贯流畅。
8.文案配成音频，一个分镜只能停留五秒钟的时间，而35个字符就接近五秒钟的时间，因此在分镜时还要考虑文案时间能否和视频对齐，不能让文案音频时间长于分镜视频。
9. 每一行开头请加上数字序号。
"""
                
                with st.spinner("AI 正在解析并分镜..."):
                    response = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"请对以下文本进行分镜：\n\n{content}"}
                        ],
                        temperature=0.3,
                    )
                    
                    result = response.choices[0].message.content
                    st.success("✅ 分镜处理完成！")
                    st.text_area("🎬 分镜结果", result, height=500)
                    
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=result,
                        file_name=f"split_{uploaded_file.name}",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"发生错误：{str(e)}")
