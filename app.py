import streamlit as st
import requests
import json

# ==========================================
# 核心函数：AI 调用逻辑
# ==========================================

def call_ai(provider, key, mid, base_url, prompt):
    key = key.strip()
    
    # 模型配置
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "第三方中转 (OpenAI格式)": "gpt-4o"
    }
    target_model = mid if mid else default_models.get(provider, "")

    # URL 逻辑
    if provider == "第三方中转 (OpenAI格式)":
        url = base_url.rstrip('/')
        if not url.endswith('/chat/completions'): url += '/chat/completions'
    else:
        urls = {
            "DeepSeek": "https://api.deepseek.com/chat/completions",
            "ChatGPT": "https://api.openai.com/v1/chat/completions",
            "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "Grok (xAI)": "https://api.x.ai/v1/chat/completions",
            "豆包 (火山引擎)": "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        }
        url = urls.get(provider)

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    
    # 增加指令权重：设置低 Temperature 保证格式
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位资深漫剧分镜导演，擅长将网文逻辑转化为高审美、电影感的视觉脚本。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=180)
        
        if response.status_code != 200:
            return f"API 错误 ({response.status_code}): {response.text}"
            
        res_data = response.json()
        return res_data['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# Streamlit UI 布局
# ==========================================

st.set_page_config(page_title="漫剧大师 v2.4 - 专业分镜工作站", layout="wide")

if 'step1_result' not in st.session_state:
    st.session_state.step1_result = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 1. API 引擎配置")
    provider = st.selectbox("API 供应商", 
                            ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    
    custom_base = ""
    if provider == "第三方中转 (OpenAI格式)":
        custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1")
    
    api_key = st.text_input("输入 API Key", type="password")
    model_id = st.text_input("Model ID", placeholder="如: gpt-4o, deepseek-v3")
    
    st.divider()
    st.header("👤 2. 核心角色文本 (关键)")
    st.info("请严格按照：姓名：(详细描述) 的格式录入")
    char_setup = st.text_area("人物角色描述库", height=400, 
                               placeholder="安妙衣：(清丽绝伦的美人，眉眼柔弱...)")

# --- 主界面 ---
st.title("🎬 漫剧全流程自动化分镜工作站 v2.4")
st.markdown("---")

tab1, tab2 = st.tabs(["第一步：逻辑深度分镜", "第二步：高一致性视觉描述生成"])

# --- Tab 1: 逻辑拆分 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑拆分 (35字/动作导向)")
    st.info("规则：不仅是按句拆，更是按‘画面动作切换’拆分。单条文案不超35字。")
    raw_script = st.text_area("输入原始剧本全文", height=300)
    
    if st.button("执行逻辑分镜拆分"):
        if not api_key: st.error("请填入 Key")
        else:
            prompt_split = f"""
            任务：请根据内容逻辑，将以下剧本拆分为适合漫剧制作的分镜。
            
            拆分原则：
            1. 内容导向：每当角色改变动作、产生心理转折、或对话对象切换时，必须拆分为新分镜。
            2. 时长限制：每段文案严禁超过 35 个汉字（5秒原则）。
            3. 零损耗：不准遗漏、修改、添加原文任何字。
            4. 格式：序号. [完整文案]
            
            原文：
            {raw_script}
            """
            with st.spinner("导演正在深度解析剧本逻辑..."):
                st.session_state.step1_result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
    
    st.session_state.step1_result = st.text_area("分镜拆分预览", value=st.session_state.step1_result, height=450)

# --- Tab 2: 视觉生成 ---
with tab2:
    st.subheader("🖼️ 全量视觉指令生成 (一致性注入)")
    
    if st.button("开始合成视觉脚本"):
        if not st.session_state.step1_result or not char_setup:
            st.error("请确保已完成第一步切分，且侧边栏已录入人物角色描述！")
        else:
            prompt_visual = f"""
            你是一位顶级的漫剧视觉导演。请为以下分镜列表生成高度一致的视觉脚本。
            
            【核心人物设定】：
            {char_setup}
            
            【分镜任务】：
            {st.session_state.step1_result}
            
            【生成规则 - 必须严格执行】：
            1. 每一个分镜输出格式必须固定为：
               序号. [原文案对比]
               画面描述：[场景、景别、视角]，人物名(完整描述词)，人物名(完整描述词)... [静态氛围、光影、画质词]
               视频生成：[具体动态行为描述]，[表情与情绪变化]，[镜头运动语言（如：镜头由远及近、快速推向人物、跟随运镜等）]。
            
            2. 人物注入规则：
               - 只要分镜涉及某个角色，必须在姓名后接括号，把库中的描述全文填入。
               - 格式范例：安妙衣，(清丽绝伦的美人，眉眼柔弱忧郁，肤色苍白，素雅纱衣)
            
            3. 视觉一致性：
               - 必须通过文字固定每一幕的“场景背景”（例如：京城街角、破旧柴房、华丽王府）。
               - 画面描述必须包含【景别】（特写/中景/全景）和【视角】（平视/俯拍/仰视）。
            
            4. 动静分离：
               - “画面描述”只准描述静态构图，供Midjourney生成底图。
               - “视频生成”必须结合文案，描述人物在画面里的动态动作和镜头语言，供即梦制作视频。
            
            请开始生成：
            """
            with st.spinner("正在生成高一致性脚本..."):
                final_output = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                st.write("---")
                st.markdown(final_output)
                st.download_button("导出分镜文件 (.txt)", final_output, file_name="Storyboard_Master.txt")
