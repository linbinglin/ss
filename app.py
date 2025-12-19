import streamlit as st
import requests
import json

# --- 页面设置 ---
st.set_page_config(page_title="智能文案分镜助手 Pro", layout="wide", page_icon="🎬")

# 自定义 CSS 样式
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; font-weight: bold; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 智能文案分镜自动处理应用")
st.caption("基于大语言模型，自动按对话、场景、动作拆分分镜，严禁删改原文。")

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.header("⚙️ 设置中心")
    
    # 1. API 接口地址
    base_url = st.text_input("接口地址 (Base URL)", value="https://blog.tuiwen.xyz/v1/chat/completions")
    
    # 2. API Key
    api_key = st.text_input("API Key (令牌)", type="password")

    st.markdown("---")
    
    # 3. 模型选择逻辑（整合自定义选项）
    st.subheader("🤖 模型选择")
    model_list = [
        "gpt-4o", 
        "claude-3-5-sonnet-20240620", 
        "deepseek-chat", 
        "gemini-1.5-pro", 
        "grok-beta", 
        "doubao-pro-128k",
        "✨ 自定义 Model ID"
    ]
    
    selected_option = st.selectbox("选择或手动输入模型", options=model_list)
    
    # 如果选择了自定义，则显示输入框
    if selected_option == "✨ 自定义 Model ID":
        final_model_id = st.text_input("请输入准确的 Model ID", value="", placeholder="例如: gpt-4-turbo")
        st.info("💡 请从中转站后台复制准确的模型名称")
    else:
        final_model_id = selected_option

    st.markdown("---")
    st.caption("分镜规则：角色对话切换、物理场景切换、人物动作改变时自动分段。")

# --- 主界面：内容区 ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📝 导入原文内容")
    uploaded_file = st.file_uploader("上传 .txt 文案文件", type=["txt"])
    
    raw_text = ""
    if uploaded_file:
        content = uploaded_file.read()
        # 尝试常用编码进行解码
        for encoding in ['utf-8', 'gbk', 'gb2312']:
            try:
                raw_text = content.decode(encoding)
                break
            except:
                continue
        st.text_area("内容预览", raw_text, height=450)

with col_right:
    st.subheader("🎥 自动分镜结果")
    
    if st.button("🚀 开始生成分镜"):
        if not api_key:
            st.error("请先输入 API Key")
        elif not final_model_id:
            st.error("请选择或输入 Model ID")
        elif not raw_text:
            st.warning("请上传文案内容")
        else:
            with st.spinner(f"正在调用 {final_model_id} 分析中..."):
                
                # --- 严格的分镜指令 ---
                system_instruction = """你是一个极其严谨的文案分镜助手。
任务：将用户提供的文案进行分段编号（分镜处理）。
分段准则：
1. 对话切换：不同角色的对话必须分开。
2. 场景切换：地点、环境发生改变时必须分开。
3. 动作改变：人物有显著的新动作或画面重心偏移时必须分开。

输出要求：
1. 必须保留原文中的【每一个字】，严禁精简、严禁修改错别字、严禁润色。
2. 每一个分镜必须以数字序号+点开头（例如: 1.内容）。
3. 严禁添加任何原文以外的描述性文字（如画面说明、旁白、内心戏等）。
4. 严禁有任何开场白或结束语，直接输出带序号的全文内容。"""

                payload = {
                    "model": final_model_id,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"请对以下全文进行分镜处理，不得遗漏任何字：\n\n{raw_text}"}
                    ],
                    "temperature": 0,  # 确保稳定性，不乱改
                    "stream": False
                }

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    response = requests.post(base_url, headers=headers, json=payload, timeout=200)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'choices' in data:
                            final_result = data['choices'][0]['message']['content']
                            st.success("分析完成！")
                            st.text_area("分镜脚本", final_result, height=450)
                            
                            st.download_button(
                                label="📥 下载分镜脚本",
                                data=final_result,
                                file_name=f"分镜_{final_model_id}.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error(f"解析失败：{data}")
                    elif response.status_code == 503:
                        st.error("Error 503: 模型未就绪或 ID 错误")
                        st.code(response.text, language="json")
                        st.info("💡 请确认『Model ID』是否与中转站后台一致。")
                    else:
                        st.error(f"接口返回错误 (Code: {response.status_code})")
                        st.code(response.text, language="json")

                except Exception as e:
                    st.error(f"运行出错: {str(e)}")

# --- 底部 ---
st.markdown("---")
st.center = st.caption("提示：长文案建议使用 GPT-4o 或 Claude 3.5 以获得最精准的逻辑切分。")
