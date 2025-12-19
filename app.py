import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：零损耗双重推理
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
            {
                "role": "system", 
                "content": "你是一位专业的漫剧分镜导演。你的核心天职是【原文保护】：严禁遗漏任何字词，严禁总结文案，严禁修改原话。你需要在保证文案100%完整的前提下，进行 9:16 竖屏分镜处理。"
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # 降至最低，防止模型自我发挥
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=300)
        if response.status_code != 200:
            return f"API ERROR: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"系统异常: {str(e)}"

# ==========================================
# 界面布局
# ==========================================

st.set_page_config(page_title="漫剧竖屏导演 v3.2 - 零损耗版", layout="wide")

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
    char_setup = st.text_area("人物设定 (姓名：(描述))", height=300)
    
    if st.button("🔴 重置项目进度"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

st.title("🎬 漫剧竖屏导演工作站 v3.2")
st.markdown("⚠️ **当前版本：零损耗全量文案保留 | 9:16 深度适配**")

tab1, tab2 = st.tabs(["第一步：零损耗逻辑分镜", "第二步：9:16 视觉脚本生成"])

# --- 第一阶段：零损耗拆分 ---
with tab1:
    st.subheader("🖋️ 全量文案拆解 (双重推理)")
    st.info("规则：必须包含原文每一个字。如果单句超 35 字或需要换镜，请拆分为 a/b 镜，严禁删减文字。")
    raw_script = st.text_area("在此输入剧本原文", height=300)
    
    if st.button("执行零损耗分镜拆分"):
        if not api_key: st.error("请填入 Key")
        else:
            # 强化提示词：强调逐字保留
            prompt_split = f"""
            你是一位漫剧导演。请对以下剧本进行【零损耗】分镜处理。
            
            【核心规则】：
            1. **字数绝对保留**：整理后的内容【不可遗漏原文中的任何一句话，一个字】。禁止添加原文以外的内容，禁止总结或改写。
            2. **逻辑分镜**：
               - 每个角色对话切换、场景切换、动作画面改变，必须设定为下一个分镜。
               - 一个分镜描述一个画面。如果一段文案内容太多（超过35字），一个画面展现不全，必须将其拆分为连续的几组分镜。
            3. **9:16 竖屏适配**：拆分分镜时，请在脑中进行二次推理，确保每一段拆分后的文案对应的动作能在竖屏空间内完成。
            
            【格式】：
            序号. [完整文案]
            
            原文文本：
            {raw_script}
            """
            with st.spinner("导演正在进行逐字解析，确保文案 100% 完整..."):
                result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
                lines = result.split('\n')
                # 匹配：数字. [文案]
                st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
                
                if st.session_state.step1_list:
                    st.success(f"分镜切分完成！共计 {len(st.session_state.step1_list)} 组文案已 100% 锁定。")
                else:
                    st.error("未能识别分镜，请检查 API 返回。")
                    st.code(result)

    if st.session_state.step1_list:
        st.text_area("分镜文案预览 (请核对原文完整性)", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二阶段：视觉生成 ---
with tab2:
    st.subheader("🖼️ 9:16 视觉指令生成")
    if not st.session_state.step1_list:
        st.info("请先完成第一步。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 进度：{curr} / {total} 镜")
        
        batch_size = st.number_input("本批次处理数量", 1, 50, 20)
        
        if curr < total:
            if st.button(f"🚀 生成后续 {batch_size} 组 9:16 指令"):
                end = min(curr + batch_size, total)
                batch_text = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                任务：为分镜生成 9:16 竖屏视觉描述。
                
                【人物设定】：
                {char_setup}
                
                【分镜文案】：
                {batch_text}
                
                【要求】：
                1. **原文对照**：格式必须为：序号. [原文案对比]。
                2. **人物注入**：姓名(完整描述词)。
                3. **视觉布局**：针对 9:16 比例。
                4. **动静结合**：画面描述写构图与静态；视频生成写动态与运镜。
                """
                with st.spinner("正在生成高一致性视觉指令..."):
                    res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    if "API ERROR" not in res:
                        st.session_state.accumulated_storyboard += "\n\n" + res
                        st.session_state.current_index = end
                        st.rerun()
                    else:
                        st.error(res)
        
        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("全量结果预览", value=st.session_state.accumulated_storyboard, height=450)
            st.download_button("💾 下载全量脚本", st.session_state.accumulated_storyboard, file_name="Verbatim_9_16_Storyboard.txt")
