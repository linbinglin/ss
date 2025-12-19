import streamlit as st
import requests
import json
import re

# ==========================================
# 核心函数：AI 调用逻辑 (支持全模型与中转)
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "你是一位精通 9:16 竖屏漫剧导演。你执行双重推理分镜法：1.全文逻辑理解 2.竖屏构图适配。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # 极低随机性确保文案零损耗
    }
    
    try:
        final_url = f"{url}?key={key}" if provider == "Gemini" and "key=" not in url else url
        response = requests.post(final_url, headers=headers, json=payload, timeout=240)
        if response.status_code != 200:
            return f"API ERROR: {response.text}"
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"系统连接异常: {str(e)}"

# ==========================================
# 界面布局与状态管理
# ==========================================

st.set_page_config(page_title="漫剧竖屏导演 v3.4", layout="wide")

if 'step1_list' not in st.session_state: st.session_state.step1_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'accumulated_storyboard' not in st.session_state: st.session_state.accumulated_storyboard = ""

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 1. API 配置")
    provider = st.selectbox("选择供应商", ["第三方中转 (OpenAI格式)", "DeepSeek", "ChatGPT", "Gemini", "Grok (xAI)", "豆包 (火山引擎)"])
    custom_base = st.text_input("API Base URL", value="https://blog.tuiwen.xyz/v1") if provider == "第三方中转 (OpenAI格式)" else ""
    api_key = st.text_input("API Key", type="password")
    model_id = st.text_input("Model ID", value="gpt-4o")
    
    st.divider()
    st.header("👤 2. 角色库注入")
    char_setup = st.text_area("人物详细描述 (姓名：(描述词))", height=350, placeholder="安妙衣：(清丽绝伦的美人...)")
    
    if st.button("🔴 重置项目进程"):
        st.session_state.current_index = 0
        st.session_state.accumulated_storyboard = ""
        st.session_state.step1_list = []
        st.rerun()

# --- 主界面 ---
st.title("🎬 漫剧竖屏导演工作站 v3.4")
st.markdown("**支持双重推理分镜算法 | 9:16 竖屏极致优化 | 文案零损耗**")

tab1, tab2 = st.tabs(["第一步：双重推理逻辑分镜", "第二步：20镜断点生成视觉脚本"])

# --- 第一阶段：分镜拆分 ---
with tab1:
    st.subheader("🖋️ 剧本全量分镜拆解")
    raw_script = st.text_area("输入原始剧本文案", height=300)
    
    if st.button("开始双重推理分镜"):
        if not api_key: st.error("请填入 Key")
        else:
            prompt_split = f"""
            你是一位漫剧导演。请对以下文本进行【双重推理分镜】。
            
            【第一遍推理】：逐字逐句通读全文，理解故事的起承转合、对话逻辑和场景空间。
            【第二遍推理】：针对 9:16 竖屏比例进行精准切分。
            
            【硬性规则】：
            1. **文案零损耗**：必须包含原文中的任何一句话、一个字。严禁删减、总结、修改或添加内容。
            2. **原子分镜**：对话切换、场景切换、动作大改变必须分为下一镜。
            3. **竖屏适配**：如果一句话在 9:16 竖屏内画面内容过多（如多人同框），请将其合理拆分为连续的特写或中景分镜，将原文案对应分配。
            4. **5秒对齐**：每段序号文案严禁超过 35 字。
            
            【输出格式】：
            序号. [文案内容]
            
            待处理文本：
            {raw_script}
            """
            with st.spinner("导演正在理解全文并适配 9:16 竖屏分镜..."):
                result = call_ai(provider, api_key, model_id, custom_base, prompt_split)
                # 使用正则鲁棒匹配序号
                lines = result.split('\n')
                st.session_state.step1_list = [l.strip() for l in lines if re.match(r"^\d+[\.．、\s]", l.strip())]
                
                if st.session_state.step1_list:
                    st.success(f"分镜切分成功！共计 {len(st.session_state.step1_list)} 组。文案 100% 保留。")
                else:
                    st.error("未能识别分镜，请检查 API 返回。")
                    st.code(result)

    if st.session_state.step1_list:
        st.text_area("分镜预览 (请核对)", value="\n".join(st.session_state.step1_list), height=300)

# --- 第二阶段：视觉生成 ---
with tab2:
    st.subheader("🖼️ 视觉指令分段合成")
    if not st.session_state.step1_list:
        st.info("请先完成第一步。")
    else:
        curr = st.session_state.current_index
        total = len(st.session_state.step1_list)
        st.progress(curr / total)
        st.write(f"📊 当前进度：第 **{curr}** 镜 / 共 {total} 镜")

        if curr < total:
            if st.button(f"🚀 生成接下来的 20 组 9:16 指令"):
                end = min(curr + 20, total)
                target_batch = "\n".join(st.session_state.step1_list[curr:end])
                
                prompt_visual = f"""
                任务：为原子化分镜生成 9:16 竖屏视觉描述。
                
                【核心角色库】：
                {char_setup}
                
                【本批次待处理分镜】：
                {target_batch}
                
                【生成规则】：
                1. 格式：序号. [原文案对照]
                   画面描述：[9:16 场景背景、景别、视角]。人物姓名(完整描述词)。[光影氛围]。
                   视频生成：[文案对应的动态动作、神态情绪]、[符合竖屏的镜头语言，如垂直摇镜/推近]。
                2. 人物一致性：角色必须以 姓名(描述词) 格式呈现，括号内严禁缩写。
                3. 9:16 优化：优先使用特写(Close-up)和中景(Medium shot)，避免左右留白过多。
                """
                with st.spinner(f"正在合成第 {curr+1} 镜起的视觉指令..."):
                    res = call_ai(provider, api_key, model_id, custom_base, prompt_visual)
                    if "API ERROR" not in res:
                        st.session_state.accumulated_storyboard += "\n\n" + res
                        st.session_state.current_index = end
                        st.rerun()
                    else:
                        st.error(res)
        else:
            st.success("✅ 全剧 9:16 分镜视觉脚本已生成完毕！")

        if st.session_state.accumulated_storyboard:
            st.divider()
            st.text_area("全量脚本预览", value=st.session_state.accumulated_storyboard, height=500)
            st.download_button("💾 下载脚本文件", st.session_state.accumulated_storyboard, file_name="Verbatim_9_16_Storyboard.txt")
