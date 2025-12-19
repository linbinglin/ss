import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(page_title="漫剧全流程分镜工作站", layout="wide")

# --- 侧边栏：API 接入与人物设定 ---
with st.sidebar:
    st.header("⚙️ 1. API 配置")
    model_provider = st.selectbox("选择大模型", ["DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    api_key = st.text_input("API Key", type="password")
    
    # 豆包或特定模型需要的 Endpoint/Model ID
    model_id = ""
    if model_provider in ["豆包 (火山引擎)", "Gemini", "Grok (xAI)"]:
        model_id = st.text_input("Model ID / Endpoint ID")

    st.divider()
    st.header("👤 2. 人物设定库")
    st.info("请在此输入人物的详细外貌描述，生成时将自动注入分镜。")
    char_config = st.text_area("人物设定文本 (如：安妙衣：描述...)", height=300, 
                               placeholder="安妙衣（女主）：（描述内容...）\n赵尘（男主）：（描述内容...）")

# --- 主界面 ---
st.title("🎬 漫剧全流程分镜工作站")

tab1, tab2 = st.tabs(["第一步：精确分镜切分", "第二步：视觉指令生成"])

# 全局状态管理
if 'segmented_text' not in st.session_state:
    st.session_state.segmented_text = ""

# --- 第一步：精确分镜切分 ---
with tab1:
    st.header("步骤 1：文案时长与动作切分")
    st.markdown("""
    **切分规则：**
    1. 每段文案严禁超过 **35个字**（对齐5秒音频）。
    2. 遇到**人物对话切换**、**场景转换**、**动作改变**必须强制拆分。
    3. 严禁修改、遗漏原文，按序号排列。
    """)
    
    raw_text = st.text_area("请输入原始剧本文本", height=300)
    
    if st.button("开始精确切分"):
        if not api_key:
            st.error("请先配置 API Key")
        else:
            with st.spinner("正在进行 35字/动作 深度切分..."):
                # 构造 Prompt
                prompt_step1 = f"""
                你是一个漫剧脚本专家。请将以下文本进行精确分镜切分。
                规则：
                1. 每一行文案不能超过35个字。如果原句太长，请拆分成a/b两部分。
                2. 角色说话切换、场景改变、或动作发生变化，必须拆分为新的分镜。
                3. 必须包含原文所有字，不得遗漏或添加。
                4. 格式：序号. [文案内容]
                
                文本内容：
                {raw_text}
                """
                
                # 调用 API (封装函数见下方)
                result = call_ai(model_provider, api_key, model_id, prompt_step1)
                st.session_state.segmented_text = result
                st.success("切分完成！请在下方核对，如有误可手动修改后再进入第二步。")

    st.text_area("分镜切分结果（可手动微调）", value=st.session_state.segmented_text, height=400, key="edit_area")

# --- 第二步：视觉指令生成 ---
with tab2:
    st.header("步骤 2：画面描述与动态指令生成")
    st.info("系统将根据第一步的分镜，自动注入左侧的人物描述，生成 MJ 画面描述词 和 即梦视频描述词。")
    
    if st.button("生成视觉描述指令"):
        if not st.session_state.edit_area:
            st.error("请先完成第一步切分")
        else:
            with st.spinner("正在分析角色动作、神态与场景视角..."):
                prompt_step2 = f"""
                你是一个资深漫剧导演。请根据分镜文案生成视觉指令。
                
                【已知角色设定库】：
                {char_config}
                
                【分镜任务列表】：
                {st.session_state.edit_area}
                
                【生成要求】：
                1. 每一个分镜必须严格包含三个部分：原文案、画面描述、视频生成。
                2. 画面描述：描述场景、景别（特写/全景/俯拍）、人物静态细节。
                   - 必须完整提取角色设定库中的外貌着装描述，注入其中。
                   - 严禁描述动作。
                3. 视频生成：描述人物的动作、神态变化及镜头运动语言。
                4. 确保分镜之间的人物和场景具有一致性。
                
                格式参考：
                序号. [文案内容]
                画面描述：场景描述，（角色完整描述）...
                视频生成：动作描述，镜头语言描述...
                """
                
                final_result = call_ai(model_provider, api_key, model_id, prompt_step2)
                st.write("---")
                st.markdown(final_result)
                st.download_button("导出最终分镜脚本", final_result)

# --- AI 调用通用函数 ---
def call_ai(provider, key, mid, prompt):
    # 根据 provider 设置 base_url
    urls = {
        "DeepSeek": "https://api.deepseek.com/v1/chat/completions",
        "ChatGPT": "https://api.openai.com/v1/chat/completions",
        "Gemini": f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "Grok (xAI)": "https://api.x.ai/v1/chat/completions",
        "豆包 (火山引擎)": "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    }
    
    # 根据 provider 设置模型名
    models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": mid if mid else "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "豆包 (火山引擎)": mid
    }

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": models[provider],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(urls[provider], headers=headers, json=payload, timeout=120)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"调用失败: {str(e)}"
