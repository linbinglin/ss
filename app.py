import streamlit as st
import requests
import json

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
        "messages": [{"role": "system", "content": "你是一位漫剧导演，负责将剧本细化为MJ画面描述与即梦视频指令。"}, {"role": "user", "content": prompt}],
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
# 界面布局与 Session 状态管理
# ==========================================

st.set_page_config(page_title="漫剧大师 v2.6 - 断点批处理版", layout="wide")

# 初始化状态
if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""
if 'last_batch_result' not in st.session_state: st.session_state.last_batch_result = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 1. API 引擎")
    provider = st.selectbox("选择供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 2. 人物设定库")
    char_setup = st.text_area("人物角色描述词 (姓名：(描述词))", height=300, 
                               placeholder="安妙衣：(描述内容...)\n赵尘：(描述内容...)")
    
    if st.button("🔴 重置所有进度"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.last_batch_result = ""
        st.rerun()

# --- 主界面 ---
st.title("🎬 漫剧全流程分镜站 (断点式生成)")

tab1, tab2 = st.tabs(["第一步：逻辑切分", "第二步：分段生成视觉指令"])

# --- 第一步：逻辑切分 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑处理 (每条不超35字)")
    raw_script = st.text_area("输入原始剧本", height=250)
    
    if st.button("开始分镜拆分"):
        prompt_split = f"""
        任务：将以下剧本拆分为逻辑连贯的分镜。
        规则：
        1. 逻辑合并：将同一场景、连贯动作的短句合并。
        2. 时长限制：合并后每条文案严禁超过35个字。
        3. 格式：仅输出 序号. [文案内容]
        
        文案：
        {raw_script}
        """
        with st.spinner("正在逻辑切分..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            # 存入列表，过滤掉空行
            st.session_state.step1_list = [line.strip() for line in result.split('\n') if line.strip() and '.' in line]
            st.session_state.current_index = 0 # 重置索引
            st.success(f"切分完成，共 {len(st.session_state.step1_list)} 个逻辑分镜。")
    
    if st.session_state.step1_list:
        st.write(f"当前已加载 {len(st.session_state.step1_list)} 条分镜文案。")
        st.text_area("切分列表预览", value="\n".join(st.session_state.step1_list), height=200)

# --- 第二步：分段生成 ---
with tab2:
    st.subheader("🖼️ 视觉描述生成 (分段控制)")
    
    if not st.session_state.step1_list:
        st.info("请先在‘第一步’完成分镜拆分。")
    else:
        total = len(st.session_state.step1_list)
        current = st.session_state.current_index
        
        # 进度显示
        st.progress(current / total if total > 0 else 0)
        st.write(f"📊 当前进度：第 **{current}** 镜 / 共 {total} 镜")

        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.number_input("每次生成分镜数", min_value=1, max_value=50, value=20)
        
        # 检查是否处理完毕
        if current < total:
            if st.button(f"🚀 生成接下来的 {batch_size} 组描述"):
                end_index = min(current + batch_size, total)
                batch_data = st.session_state.step1_list[current:end_index]
                batch_text = "\n".join(batch_data)
                
                prompt_visual = f"""
                你是一位漫剧视觉导演。请为以下分镜生成对应的 MJ 画面描述 和 即梦视频生成指令。
                
                【核心角色库】：
                {char_setup}
                
                【本次分镜列表】：
                {batch_text}
                
                【输出要求】：
                1. 格式：
                   序号. [原文案对比]
                   画面描述：[场景、景别、视角]，角色名(完整描述词)，角色名(完整描述词)... [静态构图与光影]
                   视频生成：[具体动态行为与表情]，[镜头语言描述]
                
                2. 人物注入：必须在角色名后紧跟括号内的完整描述词。
                3. 每一镜开头必须描述具体的场景背景以保证一致性。
                """
                
                with st.spinner(f"正在生成 {current+1} 到 {end_index} 镜..."):
                    batch_result = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    st.session_state.last_batch_result = batch_result
                    st.session_state.accumulated_storyboard += "\n\n" + batch_result
                    st.session_state.current_index = end_index
                    st.rerun() # 刷新界面显示结果
        else:
            st.success("✅ 全部 600+ 分镜已完成生成！")

        # 展示最近一次生成的结果
        if st.session_state.last_batch_result:
            with st.expander("✨ 查看最近生成的 20 组结果", expanded=True):
                st.markdown(st.session_state.last_batch_result)

        st.divider()
        st.subheader("📝 已生成的全量脚本汇总")
        st.text_area("全量数据 (可直接复制)", value=st.session_state.accumulated_storyboard, height=400)
        
        if st.session_state.accumulated_storyboard:
            st.download_button("💾 下载已生成的部分脚本", 
                               st.session_state.accumulated_storyboard, 
                               file_name=f"Storyboard_Progress_{current}.txt")
