import streamlit as st
from openai import OpenAI
import io

# 设置页面配置
st.set_page_config(page_title="AI 文案自动分镜工具", layout="wide")

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 配置选项")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
# 默认地址改为基础 API 地址，不包含 /chat/completion
base_url = st.sidebar.text_input("2. 中转接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("3. 选择模型 (Model ID)", 
                                 ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet", 
                                  "gemini-1.5-pro", "grok-1", "doubao-pro-128k"])
custom_model = st.sidebar.text_input("或者手动输入其他 Model ID")
final_model = custom_model if custom_model else model_id

# --- 主界面 ---
st.title("🎬 电影解说文案自动分镜系统")

uploaded_file = st.file_uploader("选择本地 TXT 文案文件", type=['txt'])

if uploaded_file is not None:
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    raw_text = stringio.read()
    
    with st.expander("👀 查看原始文案"):
        st.text_area("原文内容", raw_text, height=200)

    if st.button("🚀 开始自动化分镜分析"):
        if not api_key:
            st.error("请先在侧边栏输入 API Key！")
        else:
            try:
                # 核心修正：只保留 base_url 和 api_key
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                system_prompt = """
你是一个优秀的电影解说工作员，现在需要对文本进行分镜处理。
【核心规则】：
1. 逐字逐句理解内容，进行分段。
2. 分镜触发条件：每个角色对话切换、场景切换、动作画面改变，必须设定为下一个分镜。
3. 整理后的内容不可遗漏原文中的任何一句话、一个字，不能改变原文故事结构，禁止添加原文以外任何内容。
4. 严格要求根据场景转换进行段落分行：当故事从一个场景切换到另一个场景时，必须用新的分镜。
5. 每个分镜文案严格控制在35个字符左右（约5秒音频时长）。
6. 输出格式：每一行代表一个分镜，前面加上数字序号。
"""
                
                with st.spinner("AI 正在深度解析剧情并拆解分镜..."):
                    response = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"请对以下文本进行分镜处理：\n\n{raw_text}"}
                        ],
                        temperature=0.3,
                    )
                    
                    result = response.choices[0].message.content
                    st.success("✅ 分镜处理完成！")
                    st.text_area("🎬 处理后的分镜脚本", result, height=500)
                    
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=result,
                        file_name=f"分镜_{uploaded_file.name}",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"处理失败，错误信息：{str(e)}")
