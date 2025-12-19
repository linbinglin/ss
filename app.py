import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：支持全模型与第三方
# ==========================================

def call_ai(provider, key, mid, base_url, prompt):
    key = key.strip()
    default_models = {
        "DeepSeek": "deepseek-chat",
        "ChatGPT": "gpt-4o",
        "Gemini": "gemini-1.5-pro",
        "Grok (xAI)": "grok-beta",
        "第三方中转 (OpenAI格式)": "gpt-4o"
    }
    target_model = mid if mid else default_models.get(provider, "")

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
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位分镜剪辑大师，追求一镜一画的极致视觉表达。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # 极低随机性确保严格执行拆分规则
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=240)
        if response.status_code != 200:
            return f"API ERROR: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"系统异常: {str(e)}"

# ==========================================
# 界面布局
# ==========================================

st.set_page_config(page_title="漫剧原子分镜站 v2.9", layout="wide")

if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""

with st.sidebar:
    st.header("⚙️ 引擎配置")
    provider = st.selectbox("API 供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 人物角色库")
    char_setup = st.text_area("角色详细描述词", height=300, placeholder="姓名：(描述词)...")
    
    if st.button("🔴 重置进度"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

st.title("🎬 漫剧原子分镜工作站 - 一镜一画版")

tab1, tab2 = st.tabs(["第一步：原子化分镜拆解", "第二步：高一致性视觉指令"])

# --- 第一步：极致拆分 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑原子拆分")
    st.markdown("""
    **拆分金律：**
    1. **一镜一画**：每一个分镜只描述一个核心动作或画面。
    2. **动作必拆**：即便文案短，只要包含连续动作（如：走过去、坐下），必须拆为两个分镜。
    3. **对话必拆**：角色对话切换时，必须换镜。
    4. **画面过载必拆**：如果一句话描述了太多视觉内容，必须拆分成多组。
    5. **5秒原则**：单镜文案绝对禁止超过 35 字。
    """)
    raw_script = st.text_area("输入原始文本", height=250)
    
    if st.button("执行原子化拆分"):
        prompt_split = f"""
        你是一位顶级分镜导演。请将以下剧本进行【原子化拆分】。
        
        【规则】：
        1. 一个分镜对应一个独立的画面。
        2. 遇到以下情况必须拆分为下一镜：
           - 场景切换
           - 角色对话切换
           - 人物动作改变（即便在同一句文案里）
           - 镜头焦点从人物A转移到人物B
        3. 如果一段文案内容太多，一个静态画面展现不全，请根据逻辑将其重新拆分为两组或多组分镜，并将文案合理分配。
        4. 严禁遗漏原文任何一个字，严禁添加内容。
        5. 每一组文案不得超过35个字。
        
        【输出格式】：
        序号. [原文案]
        
        待处理剧本：
        {raw_script}
        """
        with st.spinner("导演正在进行原子化解析..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            lines = result.split('\n')
            st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
            st.success(f"拆分完成！已生成 {len(st.session_state.step1_list)} 个原子分镜。")

    if st.session_state.step1_list:
        st.text_area("原子分镜预览", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二步：精准生成 ---
with tab2:
    st.subheader("🖼️ 视觉描述与视频生成")
    
    if not st.session_state.step1_list:
        st.info("请先在第一步完成拆分。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 进度：{curr} / {total}")
        
        batch_size = st.number_input("每次生成数量", 1, 50, 20)
        
        if curr < total:
            if st.button(f"🚀 生成下 {batch_size} 组视觉描述"):
                end = min(curr + batch_size, total)
                target = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                任务：为原子化分镜生成视觉描述。
                
                【人物库】：
                {char_setup}
                
                【分镜列表】：
                {target}
                
                【输出要求】：
                1. 格式严格如下：
                   序号. [原文案]
                   画面描述：描述所在场景、景别、视角。人物必须以“姓名(完整描述)”格式呈现。
                   视频生成：根据原文案描述角色的动态动作、神态情绪、镜头语言。
                
                2. 人物注入：每个角色必须带括号()完整描述。
                3. 场景固定：每一组都要明确描述当前场景。
                """
                with st.spinner("生成中..."):
                    batch_res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    st.session_state.accumulated_storyboard += "\n\n" + batch_res
                    st.session_state.current_index = end
                    st.rerun()
        
        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("全量结果", value=st.session_state.accumulated_storyboard, height=400)
            st.download_button("下载结果", st.session_state.accumulated_storyboard, file_name="Storyboard.txt")
