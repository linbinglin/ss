import streamlit as st
import requests
import json

# ==========================================
# 核心函数定义 - 放在最上方确保调用安全
# ==========================================

def call_ai(provider, key, mid, prompt):
    """
    全机型通用 AI 调用函数，修复了 Gemini 的认证 Header 问题
    """
    key = key.strip()
    
    # 1. 默认模型配置
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "豆包 (火山引擎)": ""
    }
    target_model = mid if mid else default_models.get(provider, "")

    # 2. 供应商 URL 配置
    urls = {
        "DeepSeek": "https://api.deepseek.com/chat/completions",
        "ChatGPT": "https://api.openai.com/v1/chat/completions",
        "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "Grok (xAI)": "https://api.x.ai/v1/chat/completions",
        "豆包 (火山引擎)": "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    }
    url = urls.get(provider)

    # 3. 认证 Header 修复 (关键修复点)
    # 无论哪个供应商，统一加上 Authorization Bearer，Gemini 现在也支持并可能强制要求这个
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    # 4. 构建 Payload
    payload = {
        "model": target_model,
        "messages": [
            {
                "role": "system", 
                "content": "你是一位拥有10年经验的漫剧导演，擅长将文字转化为极其精确的视觉分镜，并能完美控制文案时长以适配视频。"
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2 # 降低随机性以保证指令执行
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            return f"API 错误 ({response.status_code}): {response.text}"
            
        res_data = response.json()
        return res_data['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# Streamlit 界面布局
# ==========================================

st.set_page_config(page_title="漫剧自动化分镜工作站 v2.2", layout="wide")

# 初始化 Session State
if 'step1_result' not in st.session_state:
    st.session_state.step1_result = ""

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.header("⚙️ 第一步：API 配置")
    provider = st.selectbox("选择大模型", ["DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    api_key = st.text_input("输入 API Key", type="password")
    model_id = st.text_input("自定义 Model ID / Endpoint ID", help="Gemini 留空默认 1.5-pro，豆包必填")
    
    st.divider()
    st.header("👤 第二步：人物设定库")
    st.markdown("在此录入所有角色的详细外貌、着装。系统将自动完整提取。")
    char_setup = st.text_area("人物角色详细描述", height=350, 
                               placeholder="安妙衣（女主）：清丽绝伦的美人，眉眼柔弱...素雅纱衣\n赵尘（男主）：俊美霸道男子，五官深邃...")

# --- 主界面 ---
st.title("🎬 漫剧全流程自动化分镜工作站")

tab1, tab2 = st.tabs(["第一步：35字精准拆分文案", "第二步：视觉指令生成"])

# --- 第一阶段逻辑 ---
with tab1:
    st.subheader("1. 剧本文案精确分镜处理")
    st.markdown("""
    **处理目标：**
    1. 确保每一段文案在 **35字以内**（对齐5秒音频）。
    2. 只要有 **动作改变**、**角色切换**、**场景改变**，必须拆分为独立分镜。
    """)
    
    raw_script = st.text_area("输入原始剧本/文案", height=300, placeholder="粘贴需要转换的全文...")
    
    if st.button("开始拆分分镜"):
        if not api_key:
            st.warning("请在侧边栏填入 API Key")
        else:
            prompt_split = f"""
            你是一个分镜剪辑师。请处理以下文案。
            规则：
            1. 每一行文案必须在 35 个字以内。如果原句长，拆分为 a/b 序号。
            2. 只要涉及对话切换、人物动作切换、场景切换，必须拆为新的序号。
            3. 不得遗漏、添加或修改原文中的任何一个字。
            4. 输出格式：序号. [文案内容]
            
            待处理文案：
            {raw_script}
            """
            with st.spinner("正在进行 35字/动作 深度拆分..."):
                result = call_ai(provider, api_key, model_id, prompt_split)
                st.session_state.step1_result = result
                st.success("拆分完成！")

    st.session_state.step1_result = st.text_area("分镜拆分预览（请在此核对文案顺序和字数）：", 
                                               value=st.session_state.step1_result, height=400)

# --- 第二阶段逻辑 ---
with tab2:
    st.subheader("2. 自动注入人物描述并合成指令")
    
    if st.button("生成 MJ + 即梦 AI 指令"):
        if not st.session_state.step1_result or not char_setup:
            st.error("请确保‘第一步’已有结果，且侧边栏已填写‘人物设定’！")
        else:
            prompt_visual = f"""
            你是一位漫剧导演。请为以下分镜列表生成视觉指令。
            
            【人物设定库】：
            {char_setup}
            
            【待处理分镜列表】：
            {st.session_state.step1_result}
            
            【输出规范】：
            1. 每一个分镜必须包含以下三部分：
               序号. [原文案对比]
               画面描述：(描述当前场景、景别。必须从【人物设定库】中提取对应人物的【完整外貌和着装描述】，不得简化，必须包含所有细节，如发饰、衣服颜色、质感等)。
               视频生成：(描述该5秒内的动态动作、神态变化、镜头运动语言。例如：镜头特写，某某某神色惊恐，眼角流泪)。
            2. 逻辑：画面描述写“静止时的样子”，视频生成写“动起来的样子”。
            3. 确保所有描述紧贴【原文案对比】的内容。
            
            请开始生成全部分镜的指令：
            """
            with st.spinner("正在注入人物一致性细节并分析动态场景..."):
                final_output = call_ai(provider, api_key, model_id, prompt_visual)
                st.write("---")
                st.markdown(final_output)
                st.download_button("下载完整分镜脚本", final_output, file_name="storyboard_final.txt")
