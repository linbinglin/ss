import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：电影导演思维分镜与视觉生成
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
            {"role": "system", "content": "你是一位拥有顶级导演思维的漫剧分镜师。你擅长逐字理解文案逻辑，并将文案转化为极具故事感、电影感的画面脚本。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3 # 稍微提高一点创造力以增强故事感，但保持格式稳定
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=240)
        if response.status_code != 200:
            return f"API 出错: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"系统连接异常: {str(e)}"

# ==========================================
# 界面布局与状态管理
# ==========================================

st.set_page_config(page_title="漫剧导演工作站 v2.8", layout="wide")

# 初始化 Session 状态，防止刷新丢失数据
if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 引擎配置")
    provider = st.selectbox("API 供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 核心角色描述库")
    char_setup = st.text_area("人物设定 (格式：姓名：(描述词))", height=350, placeholder="安妙衣：(清丽绝伦...)\n赵尘：(深邃冷峻...)")
    
    if st.button("🔴 重置所有流程"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

# --- 主界面 ---
st.title("🎬 漫剧全流程分镜站 - 导演思维版")

tab1, tab2 = st.tabs(["第一步：电影导演分镜切分", "第二步：视觉描述指令生成"])

# --- 第一步：逻辑切分逻辑 ---
with tab1:
    st.subheader("🖋️ 剧本逻辑深度拆解")
    raw_script = st.text_area("在此输入剧本原文", height=300)
    
    if st.button("执行导演分镜"):
        if not api_key: st.error("请先填入 API Key")
        else:
            prompt_split = f"""
            你是一个优秀的电影解说导演，请对以下文本进行分镜。
            
            【导演任务】：
            1. 逐字逐句理解文本中的内容，然后对文本进行分段处理。
            2. 逻辑原则：每个角色对话切换、场景切换、动作画面改变，都需要设定为下一个分镜。
            3. 禁止修改原文：不可遗漏、改变原文故事结构，严禁添加原文以外内容。
            4. 连贯流畅：不要一句话一个分镜，而是根据剧情来划分，让分镜连贯流畅。
            5. 时长控制：由于文案要配音，单镜头限制在5秒内（约35个汉字）。如果剧情连贯但字数超过35字，必须在逻辑转折点切分。
            
            【格式要求】：
            仅输出序号列表，格式为：序号. [文案内容]
            
            待处理文案：
            {raw_script}
            """
            with st.spinner("导演正在逐句研读剧本并划分分镜..."):
                result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
                
                # 增强的正则表达式提取逻辑
                lines = result.split('\n')
                st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
                
                if not st.session_state.step1_list:
                    st.error("未能识别分镜，请检查 AI 返回结果。")
                    st.code(result)
                else:
                    st.success(f"分镜划分成功！共计 {len(st.session_state.step1_list)} 组。")
                    st.session_state.current_index = 0

    if st.session_state.step1_list:
        st.text_area("分镜预览 (可手动修改文案)", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二步：视觉生成逻辑 ---
with tab2:
    st.subheader("🖼️ 画面描述与视频生成 (逐镜注入)")
    
    if not st.session_state.step1_list:
        st.info("请先完成第一步分镜拆分。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 进度：{curr} / {total}")

        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.number_input("每次生成分镜数", 1, 50, 20)
        
        if curr < total:
            if st.button(f"🚀 生成下 {batch_size} 组视觉脚本"):
                end = min(curr + batch_size, total)
                target_data = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                你是一位漫剧视觉导演。请为以下分镜生成对应的 Midjourney 画面描述 和 即梦视频生成指令。
                
                【核心人物设定】：
                {char_setup}
                
                【待处理分镜】：
                {target_data}
                
                【生成规则 (严格执行)】：
                1. 每一个分镜必须包含且仅包含以下三部分：
                   序号. [原文案对照]
                   画面描述：描述所在场景、景别(特写/全景)、视角。如果出现人物，必须使用(姓名+完整设定)的形式，例如：(安妙衣，清丽绝伦的美人...)。
                   视频生成：根据文案描述画面中角色的动态动作、神态变化、镜头语言。
                2. 人物描述：必须用括号()扩上角色设定词。当分镜出现多个角色时，每个角色都要独立带括号描述。
                3. 一致性：每个分镜必须描述所在场景，确保视觉连贯。
                
                【案例参考】：
                1. [我拉过灵曦的手 转身离开]
                画面描述：京城街角，(赵清月，清冷美人，眉眼极精致...)拉着(赵灵曦，明艳张扬，杏眼桃腮...)的手。
                视频生成：白衣女人牵着黄衣女人的手转向一边，镜头跟随两人移动，路人虚化。
                """
                
                with st.spinner(f"正在生成第 {curr+1} 到 {end} 镜..."):
                    batch_res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    if "API 出错" not in batch_res:
                        st.session_state.accumulated_storyboard += "\n\n" + batch_res
                        st.session_state.current_index = end
                        st.rerun() # 强制刷新以显示最新结果
                    else:
                        st.error(batch_res)
        else:
            st.success("✅ 全剧分镜视觉描述已全部出炉！")

        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("全量视觉脚本汇总", value=st.session_state.accumulated_storyboard, height=500)
            st.download_button("💾 下载脚本文件", st.session_state.accumulated_storyboard, file_name="Storyboard_Production.txt")
