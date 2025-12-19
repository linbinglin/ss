import streamlit as st
import requests
import json

# --- 页面设置 ---
st.set_page_config(page_title="智能文案分镜助手V2", layout="wide", page_icon="🎬")

# 自定义样式
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 智能文案分镜自动处理应用")
st.info("通过 AI 自动分析剧情，根据对话切换、场景切换、动作改变进行分镜拆解。")

# --- 侧边栏：API 与模型配置 ---
with st.sidebar:
    st.header("⚙️ 接口配置")
    
    # 1. 中转接口地址
    base_url = st.text_input("中转接口地址 (Base URL)", value="https://blog.tuiwen.xyz/v1/chat/completions")
    
    # 2. 模型选择
    model_option = st.selectbox(
        "选择 AI 模型",
        [
            "gpt-4o", 
            "deepseek-chat", 
            "claude-3-5-sonnet-20240620", 
            "gemini-1.5-pro", 
            "grok-beta", 
            "doubao-pro-128k"
        ]
    )
    
    # 3. API Key
    api_key = st.text_input("输入 API Key", type="password")
    
    st.markdown("---")
    st.caption("提示：请确保中转接口已开通所选模型的权限。")

# --- 主界面：操作区 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 上传文案")
    uploaded_file = st.file_uploader("选择本地文本文件 (.txt)", type=["txt"])
    
    original_text = ""
    if uploaded_file:
        original_text = uploaded_file.read().decode("utf-8")
        st.text_area("原文预览", original_text, height=400)

with col2:
    st.subheader("2. 分镜处理结果")
    
    # 运行逻辑
    if st.button("开始自动分镜分析"):
        if not api_key:
            st.warning("请在侧边栏输入 API Key")
        elif not original_text:
            st.warning("请先上传文案文件")
        else:
            with st.spinner(f"正在调用 {model_option} 进行深度分析..."):
                
                # --- 构建严格的 Prompt ---
                system_prompt = """你是一个专业的分镜脚本分析师。
你的任务是将用户提供的文案拆解为分镜列表。
分镜拆分规则：
1. 每当角色对话切换、场景切换、或者人物动作发生改变时，必须另起一行作为一个新的分镜。
2. 每个分镜以数字序号开头（例如 1. 2. 3.）。
3. 严禁遗漏原文中的任何一个字。
4. 严禁改变原文的顺序或结构。
5. 严禁添加原文以外的任何解释性文字、旁白或画面描述。
6. 严禁修改原文中的任何错别字或标点符号。
你的输出必须【仅包含】带序号的分镜内容，不准有任何开场白或结束语。"""

                payload = {
                    "model": model_option,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请对以下文案进行分镜处理，保持全文完整：\n\n{original_text}"}
                    ],
                    "temperature": 0.1,  # 低随机性确保忠实原文
                    "stream": False
                }

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    # 发起请求
                    response = requests.post(base_url, headers=headers, json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        result = res_json['choices'][0]['message']['content']
                        
                        st.text_area("分镜结果", result, height=400)
                        
                        st.download_button(
                            label="📥 下载分镜结果 (.txt)",
                            data=result,
                            file_name=f"分镜结果_{model_option}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(f"接口调用失败 (Error {response.status_code}): {response.text}")
                
                except Exception as e:
                    st.error(f"发生程序错误: {str(e)}")

# --- 底部说明 ---
st.markdown("---")
st.caption("分镜规则说明：本工具强制要求 AI 遵循原文，每个对话/动作/场景切换均独立成行。如果结果不理想，建议尝试更换 GPT-4o 或 Claude-3.5 模型。")
