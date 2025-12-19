import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(page_title="AI 文案分镜自动处理工具", layout="wide")

st.title("🎬 AI 文案分镜自动处理工具")
st.caption("按照角色切换、场景转换、动作改变自动切分，100%还原原文，不丢字。")

# 侧边栏配置
st.sidebar.header("⚙️ API 配置")
api_url = st.sidebar.text_input("API 中转地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password", help="输入您的 API 密钥")

model_options = [
    "deepseek-chat", 
    "gpt-4o", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro", 
    "grok-1",
    "自定义"
]
selected_model = st.sidebar.selectbox("选择 AI 模型", model_options)

if selected_model == "自定义":
    model_id = st.sidebar.text_input("请输入自定义 Model ID")
else:
    model_id = selected_model

# 主界面布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 输入原文")
    uploaded_file = st.file_uploader("从本地选择 .txt 文件", type=['txt'])
    
    input_text = ""
    if uploaded_file is not None:
        input_text = uploaded_file.read().decode("utf-8")
    
    raw_text = st.text_area("或者在此处直接粘贴文案", value=input_text, height=400)

with col2:
    st.subheader("2. 分镜结果")
    output_area = st.empty()
    result_text = st.text_area("等待生成...", height=400, key="output_res")

# 处理逻辑
if st.button("🚀 开始分析生成分镜"):
    if not api_key:
        st.error("请在左侧侧边栏配置 API Key")
    elif not raw_text:
        st.error("请先上传或输入文案内容")
    else:
        with st.spinner("AI 正在深度分析剧情并切分分镜，请稍候..."):
            try:
                # 系统提示词 (Prompt)
                system_prompt = """你是一个专业短剧和小说分镜师。
                任务：将用户提供的文本进行分镜整理。
                分镜规则：
                1. 每个【角色对话切换】、每个【场景切换】、每个【关键动作改变】，都必须设定为下一个分镜序号。
                2. 严禁遗漏原文中的任何内容、句子或一个字。必须100%保留原文。
                3. 严禁改变原文故事结构。
                4. 严禁添加任何原文以外的描述性内容或个人评论。
                5. 输出格式必须严格按照数字序号排列，例如：
                1.内容...
                2.内容...
                3.内容..."""

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": raw_text}
                    ],
                    "temperature": 0.1  # 极低随机性，确保不删减内容
                }

                response = requests.post(api_url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                
                res_data = response.json()
                final_content = res_data['choices'][0]['message']['content']
                
                # 更新结果显示区
                st.session_state.result_text = final_content
                st.success("生成成功！")
                st.rerun()

            except Exception as e:
                st.error(f"处理出错：{str(e)}")

# 复制按钮功能（Streamlit原生支持受限，通常直接手动复制文本框内容）
if 'result_text' in st.session_state:
    st.download_button("📥 下载分镜文件 (.txt)", st.session_state.result_text, file_name="分镜结果.txt")
