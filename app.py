import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(page_title="漫剧自动化分镜助手", layout="wide")

st.title("🎬 漫剧剧情自动化分镜整理工具")
st.markdown("上传剧情文本，利用大模型自动完成分镜切分。")

# --- 侧边栏：API 配置 ---
with st.sidebar:
    st.header("API 设置")
    model_provider = st.selectbox("选择模型供应商", ["DeepSeek", "ChatGPT (OpenAI)", "Gemini", "Groq", "豆包 (火山引擎)"])
    api_key = st.text_input("输入 API Key", type="password")
    
    if model_provider == "DeepSeek":
        base_url = "https://api.deepseek.com/v1/chat/completions"
        model_name = "deepseek-chat"
    elif model_provider == "ChatGPT (OpenAI)":
        base_url = "https://api.openai.com/v1/chat/completions"
        model_name = "gpt-4o"
    elif model_provider == "Gemini":
        # Gemini 通常有专门的 SDK，此处展示通用的 OpenAI 兼容格式
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        model_name = "gemini-1.5-pro"
    elif model_provider == "Groq":
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model_name = "llama-3.1-70b-versatile"
    elif model_provider == "豆包 (火山引擎)":
        base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        model_name = st.text_input("输入 Endpoint ID (豆包需要)", value="")

# --- 主界面：文件处理 ---
uploaded_file = st.file_uploader("选择本地文本文件 (.txt)", type=["txt"])

if uploaded_file is not None:
    # 读取文本内容
    content = uploaded_file.read().decode("utf-8")
    
    with st.expander("查看原始文本"):
        st.text(content)

    if st.button("开始分镜处理"):
        if not api_key:
            st.error("请先在左侧输入 API Key！")
        else:
            with st.spinner("AI 正在深度分析并进行分镜切分，请稍后..."):
                try:
                    # 构造系统 Prompt
                    system_prompt = """你是一位专业的漫剧分镜师。你的任务是将用户提供的原始文本拆分成适合漫剧制作的短分镜。
                    核心规则：
                    1. 分镜原则：每当角色说话切换、场景变换、或画面中动作发生改变时，必须另起一个序号。
                    2. 零遗漏：必须包含原文的所有内容，不漏一个字。
                    3. 零添加：严禁添加原文以外的描述词。
                    4. 格式：数字序号+点（如 1. 2. ）。
                    5. 顺序：严格保持原著顺序。"""

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"请对以下内容进行分镜处理：\n\n{content}"}
                        ],
                        "temperature": 0.1 # 设置低随机性，保证严格遵循原文
                    }

                    response = requests.post(base_url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()['choices'][0]['message']['content']

                    st.success("分镜处理完成！")
                    st.text_area("分镜结果输出", value=result, height=600)
                    
                    # 下载按钮
                    st.download_button(
                        label="下载分镜文件",
                        data=result,
                        file_name="分镜整理_output.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"处理出错: {str(e)}")
