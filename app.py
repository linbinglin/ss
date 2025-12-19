import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：AI 调用逻辑
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
        "messages": [{"role": "system", "content": "你是一位漫剧导演，请严格按照格式输出。不要说任何废话。"}, {"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            return f"API 错误: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# 界面布局与状态管理
# ==========================================

st.set_page_config(page_title="漫剧大师 v2.7 - 鲁棒性修复版", layout="wide")

if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 1. API 引擎")
    provider = st.selectbox("选择供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 2. 人物设定库")
    char_setup = st.text_area("人物设定 (姓名：(描述))", height=300)
    
    if st.button("🔴 重置进度"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

# --- 主界面 ---
st.title("🎬 漫剧大师 v2.7")

tab1, tab2 = st.tabs(["第一步：逻辑分镜拆分", "第二步：分段生成视觉脚本"])

# --- 第一步：逻辑切分修复版 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑拆分")
    raw_script = st.text_area("输入原始剧本", height=250)
    
    if st.button("开始分镜拆分"):
        prompt_split = f"""
        任务：将剧本拆分为适合漫剧的分镜。
        
        要求：
        1. 每一个分镜文案严格禁止超过 35 个汉字。
        2. 同场景、连贯动作请合并。
        3. 对话切换、大动作必须拆分。
        4. 禁止遗漏原文任何字。
        5. 格式要求：序号. [文案内容]
           例如：
           1. [我是名满京城的神秘画师，一笔一划皆能勾动男子情欲。]
           2. [世间女子骂我伤风败俗，可男人们却视若珍宝。]
        
        待处理剧本：
        {raw_script}
        """
        with st.spinner("AI 正在思考逻辑分镜..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            
            # 优化解析逻辑：使用正则表达式匹配 "数字. [内容]" 或 "数字、[内容]"
            lines = result.split('\n')
            new_list = []
            for line in lines:
                line = line.strip()
                if re.match(r"^\d+[\.．、\s]", line): # 匹配数字开头后接标点或空格
                    new_list.append(line)
            
            if not new_list:
                st.error("解析失败！AI 返回的内容格式不正确。请查看下方 AI 的原始回复并尝试重新生成。")
                with st.expander("查看 AI 原始回复"):
                    st.code(result)
            else:
                st.session_state.step1_list = new_list
                st.session_state.current_index = 0
                st.success(f"成功拆分出 {len(new_list)} 个分镜！")

    if st.session_state.step1_list:
        st.text_area("当前分镜预览", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二步：分段生成视觉指令 ---
with tab2:
    st.subheader("🖼️ 视觉指令生成 (断点控制)")
    
    if not st.session_state.step1_list:
        st.info("请先在‘第一步’完成拆分。")
    else:
        current = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(current / total)
        st.write(f"📊 进度：{current} / {total}")

        batch_size = st.number_input("每次生成数量", 1, 50, 20)
        
        if current < total:
            if st.button(f"🚀 生成接下来的 {batch_size} 组"):
                end = min(current + batch_size, total)
                batch_data = "\n".join(st.session_state.step1_list[current:end])
                
                prompt_visual = f"""
                任务：为以下分镜生成视觉脚本。
                
                【人物设定】：
                {char_setup}
                
                【本批次分镜】：
                {batch_data}
                
                【输出格式】：
                序号. [原文案对比]
                画面描述：[场景、景别、视角]，姓名(完整描述)，姓名(完整描述)... [静态构图与光影]
                视频生成：[动态动作与表情变化]，[镜头运动语言]
                
                注意：人物描述词必须用()扩起来。每一组必须包含原文案对照。
                """
                
                with st.spinner("正在生成描述词..."):
                    batch_res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    st.session_state.accumulated_storyboard += "\n\n" + batch_res
