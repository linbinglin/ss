import streamlit as st
import requests
import json
import time

# ==========================================
# 核心函数：AI 调用与批处理逻辑
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
        "messages": [{"role": "system", "content": "你是一位资深漫剧导演，严谨执行视觉脚本分步任务。"}, {"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=200)
        if response.status_code != 200:
            return f"API ERROR: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"ERROR: {str(e)}"

# ==========================================
# Streamlit 界面
# ==========================================

st.set_page_config(page_title="漫剧大师 v2.5 - 全量批处理版", layout="wide")

# 初始化数据
if 'final_storyboard' not in st.session_state: st.session_state.final_storyboard = ""
if 'step1_list' not in st.session_state: st.session_state.step1_list = []

with st.sidebar:
    st.header("⚙️ 1. 引擎配置")
    provider = st.selectbox("API 供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    batch_size = st.slider("每批次处理分镜数", 5, 20, 10, help="如果模型经常断开，请调小此数值")

    st.divider()
    st.header("👤 2. 核心角色库")
    char_setup = st.text_area("人物设定 (姓名：(描述))", height=300, 
                               placeholder="安妙衣：(描述...)\n赵尘：(描述...)")

st.title("🎬 漫剧全量自动化分镜工作站 v2.5")

tab1, tab2 = st.tabs(["第一步：逻辑分镜合并与切分", "第二步：视觉脚本批处理生成"])

# --- Tab 1: 逻辑切分 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑处理")
    st.markdown("将零散文案合并为一个个【视觉分镜】。要求：逻辑连贯、不超35字。")
    raw_script = st.text_area("输入原始剧本", height=300)
    
    if st.button("开始逻辑切分"):
        prompt_split = f"""
        任务：请对以下剧本进行【视觉分镜逻辑合并】。
        
        规则：
        1. 逻辑合并：不要机械地一句话一分镜。将发生在【同一场景、同一动作序列】下的短句合并为一条分镜文案。
        2. 时长限制：合并后的单条分镜文案严禁超过 35 个字（为了匹配5秒视频）。
        3. 动作切换：如果文案中发生了明显的动作转折（如从“坐着”变成“站起来”），即使字数很少也要拆分。
        4. 零遗漏：包含原文所有字，严禁修改。
        5. 格式：仅输出 序号. [文案内容]
        
        待处理原文：
        {raw_script}
        """
        with st.spinner("正在优化分镜逻辑..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            # 解析成列表方便后续批处理
            st.session_state.step1_list = [line.strip() for line in result.split('\n') if line.strip()]
            st.success(f"逻辑切分完成，共计 {len(st.session_state.step1_list)} 镜。")
    
    st.write(st.session_state.step1_list)

# --- Tab 2: 全量批处理 ---
with tab2:
    st.subheader("🖼️ 视觉指令全量批处理生成")
    st.warning("由于长剧本字数极多，系统将自动分批次调用 AI。请勿关闭页面。")
    
    if st.button("🚀 开始全量自动生成 (支持600+镜)"):
        if not st.session_state.step1_list or not char_setup:
            st.error("请先完成第一步，并填入角色设定。")
        else:
            total_list = st.session_state.step1_list
            st.session_state.final_storyboard = "" # 重置结果
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 分批次循环
            for i in range(0, len(total_list), batch_size):
                chunk = total_list[i : i + batch_size]
                current_batch_str = "\n".join(chunk)
                
                status_text.text(f"正在处理第 {i+1} 至 {min(i+batch_size, len(total_list))} 镜...")
                
                prompt_visual = f"""
                你是一位漫剧导演。请为以下分镜生成对应的 Midjourney 画面描述 和 即梦视频生成指令。
                
                【核心人物设定库】：
                {char_setup}
                
                【本次待处理分镜列表】：
                {current_batch_str}
                
                【生成规则】：
                1. 严格格式：
                   序号. [原文案对照]
                   画面描述：[场景、景别、视角]，角色名(描述词)，角色名(描述词)... [静态构图与光影]
                   视频生成：[动态动作与表情变化]，[镜头运动描述]
                
                2. 人物描述注入：必须在角色名后紧跟括号内的完整描述词，例如：安妙衣(清丽绝伦的美人...)。
                3. 一致性：每一镜开头必须描述场景背景（如：破旧柴房内）。
                4. 严禁断更：必须处理完我给你的【所有】分镜，不准只出一部分。
                """
                
                chunk_result = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                
                st.session_state.final_storyboard += chunk_result + "\n\n"
                
                # 更新进度
                progress = min((i + batch_size) / len(total_list), 1.0)
                progress_bar.progress(progress)
                
                # 预留 1 秒防止请求过快触发限制
                time.sleep(1)
            
            status_text.text("✅ 全量生成完成！")
            st.success("全部 600+ 分镜已处理完毕。")

    if st.session_state.final_storyboard:
        st.markdown(st.session_state.final_storyboard)
        st.download_button("💾 下载全量分镜脚本", st.session_state.final_storyboard, file_name="Full_Storyboard.txt")
