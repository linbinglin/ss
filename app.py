import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：支持 9:16 深度推理
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
            {"role": "system", "content": "你是一位精通 9:16 竖屏短视频构图的专业漫剧导演。你擅长通过双重推理（全文理解+构图适配）生成完美的分镜脚本。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2 
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

st.set_page_config(page_title="漫剧竖屏导演 v3.1", layout="wide")

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
    char_setup = st.text_area("人物详细设定 (姓名：(描述词))", height=300, placeholder="安妙衣：(清丽绝伦...)")
    
    if st.button("🔴 重置项目"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

st.title("🎬 漫剧竖屏导演工作站 v3.1")
st.markdown("**专为 9:16 比例设计 | 双重推理分镜算法**")

tab1, tab2 = st.tabs(["第一步：双重推理分镜切分", "第二步：9:16 视觉指令生成"])

# --- 第一步：双重推理分镜 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑拆解 (9:16 适配版)")
    st.markdown("""
    **推理流程：**
    1. **初步分镜**：快速梳理剧情脉络与角色对话。
    2. **二次精准分镜**：针对 **9:16 竖屏比例** 优化。若原文动作在竖屏难以呈现（如两人相距甚远并排走），则拆分为两个特写或改为纵向视角分镜。
    3. **时长约束**：单镜文案字数严控在 **35字以内**，确保音频与 5 秒视频完美同步。
    """)
    raw_script = st.text_area("输入原始剧本文案", height=300)
    
    if st.button("开始双重推理分镜"):
        prompt_split = f"""
        你是一位 9:16 竖屏漫剧导演。请对以下剧本进行双重推理分镜处理。
        
        【第一遍推理】：通读全文，理解故事的起承转合、情绪高潮和角色位置。
        【第二遍推理】：针对 9:16（1080x1920）竖屏构图进行精准分镜。
        
        【分镜规则】：
        1. 每一个分镜必须能在一张 9:16 的竖屏画面中完美呈现。
        2. 动作转折、换人说话、场景改变必须拆分。
        3. 字数限制：单镜文案不得超过 35 字。
        4. 零遗漏：包含原文所有字句。
        
        【输出格式】：
        序号. [文案内容]
        
        待处理文本：
        {raw_script}
        """
        with st.spinner("导演正在进行双重推理（理解全文 + 竖屏构图适配）..."):
            result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
            lines = result.split('\n')
            st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
            st.success(f"分镜切分完成！共计 {len(st.session_state.step1_list)} 镜。")

    if st.session_state.step1_list:
        st.text_area("预览分镜文案", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二步：分段描述生成 ---
with tab2:
    st.subheader("🖼️ 9:16 视觉脚本生成")
    
    if not st.session_state.step1_list:
        st.info("请先完成第一步分镜切分。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 制作进度：{curr} / {total} 镜")
        
        batch_size = st.number_input("本批次生成数量", 1, 50, 20)
        
        if curr < total:
            if st.button(f"🚀 生成接下来的 {batch_size} 组 9:16 指令"):
                end = min(curr + batch_size, total)
                target = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                任务：为分镜生成适合 9:16 竖屏的视觉指令。
                
                【核心人物库】：
                {char_setup}
                
                【当前分镜列表】：
                {target}
                
                【输出规范 (严格执行)】：
                1. 每一个分镜输出必须包含：
                   序号. [原文案对照]
                   画面描述：[9:16构图描述，如 Portrait / Full body / Extreme close-up]、[场景锚点]、姓名(完整角色设定词)... [竖向空间布局描述，如人物一前一后]。
                   视频生成：[结合文案的动态动作]、[表情神态变化]、[符合竖屏的镜头语言，如垂直摇镜 Vertical pan 或 快速推近特写 Zoom in]。
                
                2. 人物一致性：角色名后必须紧跟括号内的【完整描述词】，严禁简化。
                3. 9:16 适配：画面描述中必须明确体现竖向构图美感，避免左右过空。
                
                【格式范例】：
                1. [赵尘走过来，狠狠地甩了我一巴掌]
                画面描述：9:16 纵深视角，华丽王府内，(赵尘，俊美霸道男子...)的身影由远及近遮住光线，前方是跌坐在地的(安妙衣，清丽绝伦的美人...)。
                视频生成：赵尘面色阴冷地快速跨步进入画面，右手猛地挥出，安妙衣侧脸受击，发丝飞散，镜头给到手部击打特写。
                """
                with st.spinner(f"正在生成第 {curr+1} 至 {end} 镜的竖屏脚本..."):
                    batch_res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    if "API ERROR" not in batch_res:
                        st.session_state.accumulated_storyboard += "\n\n" + batch_res
                        st.session_state.current_index = end
                        st.rerun()
                    else:
                        st.error(batch_res)
        else:
            st.success("全部 9:16 脚本生成完成！")
        
        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("全量脚本汇总", value=st.session_state.accumulated_storyboard, height=450)
            st.download_button("💾 下载竖屏脚本文件", st.session_state.accumulated_storyboard, file_name="9_16_Storyboard.txt")
