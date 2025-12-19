import streamlit as st
import requests
import json

# --- 页面设置 ---
st.set_page_config(page_title="智能文案分镜助手 Pro", layout="wide", page_icon="🎬")

# 自定义样式
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 智能文案分镜自动处理应用")
st.caption("适配自定义中转接口，精准控制 Model ID，实现零损剧情拆解。")

# --- 侧边栏：API 与模型配置 ---
with st.sidebar:
    st.header("⚙️ 接口与模型配置")
    
    # 1. 中转接口地址
    base_url = st.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    
    # 2. API Key
    api_key = st.text_input("输入 API Key", type="password", help="从中转站获取的令牌 (SK-...)")

    st.markdown("---")
    
    # 3. 模型选择逻辑
    st.subheader("🤖 模型设置")
    use_custom_model = st.checkbox("手动输入 Model ID", value=True, help="如果下拉菜单的模型报错503，请勾选此项并输入正确的 ID")
    
    if use_custom_model:
        model_id = st.text_input("请输入准确的 Model ID", value="", placeholder="例如: grok-beta 或 gpt-4o")
        st.warning("⚠️ 请确保此 ID 与中转站后台『可用模型』列表中的名称一致。")
    else:
        model_id = st.selectbox(
            "选择预设模型",
            ["gpt-4o", "deepseek-chat", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-beta"]
        )
    
    st.markdown("---")
    st.info("💡 提示：对话切换、场景改变、动作变化将自动划分为下一分镜。")

# --- 主界面：操作区 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 导入文案内容")
    uploaded_file = st.file_uploader("上传本地文本文件 (.txt)", type=["txt"])
    
    original_text = ""
    if uploaded_file:
        try:
            original_text = uploaded_file.read().decode("utf-8")
        except:
            original_text = uploaded_file.read().decode("gbk") # 兼容部分中文编码
        st.text_area("原文预览 (不可修改)", original_text, height=450)

with col2:
    st.subheader("2. 自动分镜生成")
    
    if st.button("🚀 执行 AI 深度分镜分析"):
        if not api_key:
            st.error("错误：请在侧边栏配置 API Key")
        elif not model_id:
            st.error("错误：请在侧边栏输入或选择 Model ID")
        elif not original_text:
            st.warning("请先上传需要分析的文案")
        else:
            with st.spinner(f"正在请求模型 [{model_id}]，请稍候..."):
                
                # --- 严格的分镜 Prompt ---
                system_prompt = """你是一个极其严谨的分镜师。
你的任务是将提供的文案处理为带编号的分镜脚本。
必须严格遵守以下准则：
1. 【拆分规则】：角色对话切换、物理场景切换、人物动作显著改变，必须另起一行作为一个新分镜。
2. 【内容忠实】：严禁遗漏原文任何一个字，严禁修改错别字，严禁改变原文结构。
3. 【禁止创作】：严禁添加任何原文中没有的画面描述、旁白、内心独白或解释说明。
4. 【格式要求】：每一行必须以"数字."开头，例如：1.内容\n2.内容。
5. 【纯净输出】：不要输出任何开场白（如"好的"）或结束语。直接开始编号。"""

                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请对以下文案进行分镜处理，保持全文完整无遗漏：\n\n{original_text}"}
                    ],
                    "temperature": 0.0, # 设为0以获得最稳定的输出，不乱改字
                    "presence_penalty": 0.0,
                    "stream": False
                }

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                try:
                    response = requests.post(base_url, headers=headers, json=payload, timeout=180)
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        if 'choices' in res_json:
                            result = res_json['choices'][0]['message']['content']
                            st.success(f"处理完成！模型：{model_id}")
                            st.text_area("分镜结果内容", result, height=450)
                            
                            st.download_button(
                                label="📥 点击下载分镜结果",
                                data=result,
                                file_name=f"分镜_{model_id}.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error(f"响应内容异常: {res_json}")
                    else:
                        # 详细的错误处理
                        error_detail = response.text
                        st.error(f"接口返回错误 (状态码 {response.status_code})")
                        st.code(error_detail, language="json")
                        st.info("💡 提示：如果报 503 或 model_not_found，请在中转站后台确认你的令牌是否启用了该模型 ID。")
                
                except requests.exceptions.Timeout:
                    st.error("请求超时，文案可能过长，请尝试缩短文案或更换响应更快的模型。")
                except Exception as e:
                    st.error(f"程序运行异常: {str(e)}")

# --- 底部版权/提示 ---
st.markdown("---")
st.caption("注：本应用通过 API 实时调用大模型。由于长文本分镜对 AI 逻辑能力要求极高，推荐优先使用 GPT-4o 或 Claude-3.5-Sonnet 获得最佳效果。")import streamlit as st
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

