import streamlit as st
import requests
import json

# ==========================================
# 核心函数定义（必须放在最上方，防止 NameError）
# ==========================================

def call_ai(provider, key, mid, prompt):
    """
    通用 AI 调用接口，适配多种大模型 API
    """
    # 1. 适配不同供应商的 Base URL
    urls = {
        "DeepSeek": "https://api.deepseek.com/chat/completions",
        "ChatGPT": "https://api.openai.com/v1/chat/completions",
        "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "Grok (xAI)": "https://api.x.ai/v1/chat/completions",
        "豆包 (火山引擎)": "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    }
    
    # 2. 适配默认模型名称
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "豆包 (火山引擎)": ""  # 豆包必须由用户输入 Endpoint ID
    }

    # 如果用户没填 Model ID，使用默认值
    target_model = mid if mid else default_models.get(provider, "")
    
    if provider == "豆包 (火山引擎)" and not mid:
        return "错误：使用豆包 API 必须在侧边栏输入 Endpoint ID (推理接入点)。"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位专业的漫剧导演和视觉美术专家，擅长将文字精准转化为视频分镜脚本。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3  # 较低随机性确保精准
    }
    
    try:
        response = requests.post(urls[provider], headers=headers, json=payload, timeout=120)
        response_json = response.json()
        
        if response.status_code != 200:
            return f"API 错误 ({response.status_code}): {response.text}"
            
        return response_json['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# Streamlit 界面配置
# ==========================================

st.set_page_config(page_title="漫剧全流程分镜工作站 v2.0", layout="wide")

# 初始化 Session State（存储第一步的结果，供第二步使用）
if 'step1_result' not in st.session_state:
    st.session_state.step1_result = ""

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.header("⚙️ 1. 模型与 API 配置")
    provider = st.selectbox("选择 AI 供应商", ["DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    api_key = st.text_input("输入 API Key", type="password")
    model_id = st.text_input("Model ID / Endpoint ID (可选)", help="Gemini 或 豆包建议手动填写具体的模型 ID")
    
    st.divider()
    st.header("👤 2. 人物设定库 (关键)")
    st.markdown("请将人物的详细外貌描述粘贴在此，系统将自动完整提取并注入分镜。")
    char_setup = st.text_area("人物角色描述文本", height=350, placeholder="安妙衣（女主）：（描述词...）\n赵尘（男主）：（描述词...）")

# --- 主界面 ---
st.title("🎬 漫剧全流程自动化分镜工作站")

tab1, tab2 = st.tabs(["第一步：35字精准分镜切分", "第二步：视觉指令(MJ+视频)生成"])

# --- 第一步逻辑 ---
with tab1:
    st.subheader("第一阶段：文案拆解")
    st.info("规则：按‘35字原则’切分音频时长，并根据‘动作/对话切换’拆分镜头。")
    
    raw_script = st.text_area("在此处输入剧本原文案", height=300, placeholder="粘贴需要转换的剧本全文...")
    
    if st.button("开始精准拆分文案"):
        if not api_key:
            st.warning("请先在左侧侧边栏填入 API Key。")
        else:
            prompt_split = f"""
            任务：请将以下剧本文案进行分镜切分。
            
            强制规则：
            1. 每一个分镜文案严格禁止超过 35 个字符（以匹配5秒音频）。
            2. 只要【角色说话切换】、【场景变化】、【动作改变】，必须另起一行作为新的序号分镜。
            3. 严禁修改原文、遗漏字句或添加任何旁白。
            4. 格式：序号. [文案内容]
            
            待处理文案：
            {raw_script}
            """
            with st.spinner("AI 正在计算字数并拆分分镜..."):
                result = call_ai(provider, api_key, model_id, prompt_split)
                st.session_state.step1_result = result
                st.success("拆分完成！请在下方核对结果。")

    # 显示结果区域，用户可以手动微调
    st.session_state.step1_result = st.text_area("分镜拆分预览 (你可以手动修改)：", 
                                               value=st.session_state.step1_result, height=400)

# --- 第二步逻辑 ---
with tab2:
    st.subheader("第二阶段：视觉指令合成")
    st.info("系统将自动把左侧的人物描述完整注入到每一组分镜中。")
    
    if st.button("生成 MJ 画面描述 + 视频动态描述"):
        if not st.session_state.step1_result:
            st.error("请先在‘第一步’中完成分镜拆分！")
        elif not char_setup:
            st.error("请先在左侧输入‘人物设定’！")
        else:
            prompt_visual = f"""
            任务：根据拆分好的分镜，结合人物设定，生成对应的画面描述词和视频生成指令。
            
            【已知人物设定库】：
            {char_setup}
            
            【分镜列表】：
            {st.session_state.step1_result}
            
            【输出要求 (严格遵守)】：
            1. 每一个分镜必须包含三部分，格式如下：
               序号. [原文案对比]
               画面描述：描述场景、景别、人物静态。必须完整提取【人物设定库】中对应的角色外貌描述词，禁止简化。
               视频生成：描述动作、神态变化、镜头运动（如：镜头向人物面部快速推进、人物眼球颤动）。
               
            2. 画面描述规范：描述静止帧，包含场景、灯光、人物详细外表（引用库中原话）。
            3. 视频生成规范：描述动态过程，结合文案描述该5秒视频内的具体动作。
            4. 每一个分镜必须有对应的 [原文案对比]，严禁遗漏。
            
            请开始生成：
            """
            with st.spinner("AI 正在绘制视觉蓝图并注入人物细节..."):
                final_output = call_ai(provider, api_key, model_id, prompt_visual)
                st.write("---")
                st.markdown(final_output)
                st.download_button("下载完整分镜脚本", final_output, file_name="storyboard_final.txt")
