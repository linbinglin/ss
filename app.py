import streamlit as st
import requests
import json

# ==========================================
# 核心函数定义
# ==========================================

def call_ai(provider, key, mid, prompt):
    """
    针对不同供应商进行差异化认证和调用
    """
    key = key.strip()  # 去除可能存在的空格
    
    # 1. 设置默认模型名
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "豆包 (火山引擎)": ""
    }
    target_model = mid if mid else default_models.get(provider, "")

    # 2. 根据供应商构建请求
    headers = {"Content-Type": "application/json"}
    
    if provider == "Gemini":
        # Gemini OpenAI 兼容路径要求把 key 放在 URL 参数中
        url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={key}"
        # Gemini 不需要 Authorization Header，或者使用 api-key header
    elif provider == "豆包 (火山引擎)":
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers["Authorization"] = f"Bearer {key}"
        if not mid: return "错误：使用豆包必须输入 Endpoint ID。"
    else:
        # DeepSeek, ChatGPT, Grok 使用标准 Bearer Token
        urls = {
            "DeepSeek": "https://api.deepseek.com/chat/completions",
            "ChatGPT": "https://api.openai.com/v1/chat/completions",
            "Grok (xAI)": "https://api.x.ai/v1/chat/completions"
        }
        url = urls.get(provider)
        headers["Authorization"] = f"Bearer {key}"

    # 3. 构建 Payload
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位专业的漫剧导演。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        # 调试信息 (如果出错可以查看打印)
        if response.status_code != 200:
            return f"API 错误 ({response.status_code}): {response.text}"
            
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# Streamlit 界面
# ==========================================

st.set_page_config(page_title="漫剧全流程工作站 v2.1", layout="wide")

if 'step1_result' not in st.session_state:
    st.session_state.step1_result = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ API 配置")
    provider = st.selectbox("选择供应商", ["DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    api_key = st.text_input("输入 API Key", type="password")
    model_id = st.text_input("Model ID / Endpoint ID", help="Gemini 默认 gemini-1.5-pro，豆包必填")
    
    st.divider()
    st.header("👤 人物设定库")
    char_setup = st.text_area("粘贴角色外貌描述", height=350, placeholder="安妙衣（女主）：（清丽绝伦...）\n赵尘（男主）：（深邃冷峻...）")

# --- 主界面 ---
st.title("🎬 漫剧全流程自动化分镜工作站")

tab1, tab2 = st.tabs(["第一步：精确拆分分镜", "第二步：生成视觉指令"])

# 第一步：拆分
with tab1:
    st.subheader("1. 文案长度与场景拆分")
    raw_script = st.text_area("粘贴原始剧本", height=300)
    
    if st.button("开始拆分"):
        if not api_key: st.error("请填入 Key")
        else:
            prompt_split = f"请将以下剧本拆分为分镜。规则：每段文案严禁超过35字，角色切换或动作改变必须另起分镜。格式：序号. [文案内容]。全文内容：\n{raw_script}"
            res = call_ai(provider, api_key, model_id, prompt_split)
            st.session_state.step1_result = res
    
    st.session_state.step1_result = st.text_area("拆分结果预览（可修改）", value=st.session_state.step1_result, height=400)

# 第二步：描述
with tab2:
    st.subheader("2. 注入人物设定并生成指令")
    if st.button("生成视觉脚本"):
        if not st.session_state.step1_result or not char_setup:
            st.error("请检查分镜结果和人物设定是否已填写")
        else:
            prompt_visual = f"""
            任务：为以下分镜生成视觉指令。
            
            【人物设定库】：
            {char_setup}
            
            【分镜列表】：
            {st.session_state.step1_result}
            
            【格式要求】：
            每一个分镜必须包含：
            序号. [原文案对照]
            画面描述：(描述场景、景别、静态。必须完整提取【人物设定库】中的外貌着装描述，不得简化)。
            视频生成：(描述5秒内的动态动作、神态变化、镜头运动语言)。
            
            注意：画面描述只准写静态，动作描述必须写在视频生成里。
            """
            final_output = call_ai(provider, api_key, model_id, prompt_visual)
            st.markdown(final_output)
            st.download_button("导出最终脚本", final_output)
