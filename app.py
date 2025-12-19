import streamlit as st
import requests
import json

# ==========================================
# 核心函数定义
# ==========================================

def call_ai(provider, key, mid, base_url, prompt):
    """
    支持原生接口与第三方中转接口的通用调用函数
    """
    key = key.strip()
    
    # 1. 默认模型配置
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "豆包 (火山引擎)": "",
        "第三方中转 (OpenAI格式)": "gpt-4o"
    }
    target_model = mid if mid else default_models.get(provider, "")

    # 2. 供应商 URL 逻辑
    if provider == "第三方中转 (OpenAI格式)":
        # 如果用户提供了中转地址，确保路径正确
        if not base_url:
            return "错误：使用第三方中转必须填写 API Base URL。"
        # 自动补全路径
        url = base_url.rstrip('/')
        if not url.endswith('/chat/completions'):
            url += '/chat/completions'
    else:
        urls = {
            "DeepSeek": "https://api.deepseek.com/chat/completions",
            "ChatGPT": "https://api.openai.com/v1/chat/completions",
            "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "Grok (xAI)": "https://api.x.ai/v1/chat/completions",
            "豆包 (火山引擎)": "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        }
        url = urls.get(provider)

    # 3. 认证 Header (兼容模式)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    # 4. 构建 Payload
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位专业的漫剧分镜导演，擅长精准切分文案并注入丰富的视觉细节。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        # Gemini 特殊处理：有时需要在 URL 挂 Key
        final_url = url
        if provider == "Gemini" and "key=" not in url:
            final_url = f"{url}?key={key}"

        response = requests.post(final_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            return f"API 错误 ({response.status_code}): {response.text}"
            
        res_data = response.json()
        return res_data['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# Streamlit 界面
# ==========================================

st.set_page_config(page_title="漫剧全流程工作站 v2.3", layout="wide")

if 'step1_result' not in st.session_state:
    st.session_state.step1_result = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 第一步：API 配置")
    provider = st.selectbox("选择大模型/供应商", 
                            ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    
    # 针对第三方中转的地址输入
    custom_base = ""
    if provider == "第三方中转 (OpenAI格式)":
        custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1", help="请填入中转站的API根地址")
    
    api_key = st.text_input("输入 API Key", type="password")
    model_id = st.text_input("自定义 Model ID", placeholder="如: gpt-4o, deepseek-v3", help="必填：中转接口支持的模型名称")
    
    st.divider()
    st.header("👤 第二步：人物设定库")
    char_setup = st.text_area("人物角色详细描述", height=300, 
                               placeholder="在此粘贴人物.txt的内容...")

# --- 主界面 ---
st.title("🎬 漫剧自动化分镜与视觉生成工作站")

tab1, tab2 = st.tabs(["第一步：35字精准拆分", "第二步：注入角色并生成视觉脚本"])

# 第一阶段
with tab1:
    st.subheader("1. 精确分镜拆分")
    st.info("AI 将确保每段文案 < 35字，并根据动作/对话切换分镜。")
    raw_script = st.text_area("输入原始剧情文本", height=250)
    
    if st.button("开始拆分"):
        if not api_key: st.warning("请输入 API Key")
        else:
            prompt_split = f"""请将以下文案切分为分镜序号。
            规则：
            1. 每行文案严格控制在 35 字以内。
            2. 对话切换、动作大变、场景转换必须拆分。
            3. 严禁修改或遗漏原文任何字。
            4. 格式：序号. [文案内容]
            
            文案如下：
            {raw_script}"""
            with st.spinner("正在拆分..."):
                st.session_state.step1_result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
    
    st.session_state.step1_result = st.text_area("拆分结果（可微调）", value=st.session_state.step1_result, height=350)

# 第二阶段
with tab2:
    st.subheader("2. 生成视觉指令 (MJ + 即梦)")
    if st.button("生成视觉脚本"):
        if not st.session_state.step1_result or not char_setup:
            st.error("请确保已完成第一步且已填写人物设定！")
        else:
            prompt_visual = f"""
            任务：为分镜生成视觉指令。
            
            【人物设定库】：
            {char_setup}
            
            【分镜列表】：
            {st.session_state.step1_result}
            
            【输出规范】：
            每一组必须包含：
            序号. [原文案对比]
            画面描述：(描述场景、景别。必须完整提取【人物设定库】中的对应角色外貌描述，不得简化)。
            视频生成：(描述5秒内的动态动作、神态、镜头运动)。
            
            *注意：画面描述是静态的，视频生成描述动态。*
            """
            with st.spinner("正在注入人物细节并分析场景..."):
                final_output = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                st.write("---")
                st.markdown(final_output)
                st.download_button("下载完整脚本", final_output, file_name="storyboard.txt")
