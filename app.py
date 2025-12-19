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
            {"role": "system", "content": "你是一位专业的漫剧导演，擅长平衡分镜的视觉美感与制作效率。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3 
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

st.set_page_config(page_title="漫剧导演工作站 v3.0", layout="wide")

if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""

with st.sidebar:
    st.header("⚙️ 1. API 引擎配置")
    provider = st.selectbox("选择供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 2. 核心角色库")
    char_setup = st.text_area("粘贴人物详细描述 (姓名：(描述))", height=300, placeholder="姓名：(描述词)...")
    
    if st.button("🔴 重置项目进度"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

st.title("🎬 漫剧全流程分镜工作站 v3.0")

tab1, tab2 = st.tabs(["第一步：视觉节奏分镜", "第二步：分段视觉指令生成"])

# --- 第一步：视觉节奏分镜 ---
with tab1:
    st.subheader("🖋️ 剧本分镜切分")
    st.markdown("""
    **分镜逻辑：**
    1. **视觉完整性**：将一个能在5秒内通过一张底图+动态表达清楚的【意群】合为一个分镜。
    2. **5秒准则**：单镜文案字数严格控制在 **35字以内**。
    3. **换镜信号**：换人说话、场景大跳跃、或发生了无法在同一画面表达的剧烈动作。
    4. **连贯性**：确保分镜之间像电影剪辑一样流畅，不破碎。
    """)
    raw_script = st.text_area("输入原始剧本文案", height=250)
    
    if st.button("执行分镜切分"):
        prompt_split = f"""
        你是一位漫剧导演。请将以下剧本拆分为适合制作的分镜。
        
        【规则】：
        1. 合理分镜：将一个视觉连贯的场景或动作意群合为一个分镜，不要拆得太碎。
        2. 时长对齐：每段文案字数绝对禁止超过 35 个字（对应5秒视频）。
        3. 动作与对话：角色对话切换、或场景大幅度改变时，必须另起分镜。
        4. 零遗漏：包含原文所有字。
        
        【输出格式】：
        序号. [文案内容]
        
        待处理剧本：
        {raw_script}
        """
        with st.spinner("导演正在构思分镜节奏..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            lines = result.split('\n')
            st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
            st.success(f"分镜切分完成！共计 {len(st.session_state.step1_list)} 镜。")

    if st.session_state.step1_list:
        st.text_area("预览分镜文案", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二步：分段描述生成 ---
with tab2:
    st.subheader("🖼️ 视觉描述与视频动态")
    
    if not st.session_state.step1_list:
        st.info("请先完成第一步分镜切分。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 制作进度：{curr} / {total} 镜")
        
        batch_size = st.number_input("本批次生成数量", 1, 50, 20)
        
        if curr < total:
            if st.button(f"🚀 生成接下来的 {batch_size} 组指令"):
                end = min(curr + batch_size, total)
                target = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                任务：为漫剧分镜生成视觉指令。
                
                【核心人物库】：
                {char_setup}
                
                【当前分镜列表】：
                {target}
                
                【输出规范】：
                1. 格式严格如下：
                   序号. [原文案对比]
                   画面描述：[描述所在具体场景、景别、视角]，姓名(完整角色设定词)... [静态构图与光影氛围]。
                   视频生成：[结合文案描述该5秒内的动态变化、角色神态、动作、镜头语言]。
                
                2. 人物一致性：必须在角色名后紧跟括号内的【完整描述词】，严禁简化。
                3. 一镜一画：每一组必须清晰描述该分镜所在的场景背景。
                
                【参考案例】：
                1. [我拉过灵曦的手 转身离开]
                画面描述：京城繁华街角，特写镜头，(赵清月，清冷美人...)正紧紧拉着(赵灵曦，明艳张扬...)的手。
                视频生成：两人转身，白色衣角与黄色裙摆交错，镜头跟随两人移动，路人纷纷退开。
                """
                with st.spinner(f"正在生成第 {curr+1} 至 {end} 镜..."):
                    batch_res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    if "API ERROR" not in batch_res:
                        st.session_state.accumulated_storyboard += "\n\n" + batch_res
                        st.session_state.current_index = end
                        st.rerun() # 确保界面即时刷新
                    else:
                        st.error(batch_res)
        else:
            st.success("全部生成完成！")
        
        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("已生成的视觉脚本汇总", value=st.session_state.accumulated_storyboard, height=450)
            st.download_button("💾 下载脚本文件", st.session_state.accumulated_storyboard, file_name="Manga_Drama_Storyboard.txt")
