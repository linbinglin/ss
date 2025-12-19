import streamlit as st
import requests
import json

# 页面基础设置
st.set_page_config(page_title="漫剧全流程分镜应用", layout="wide")

# 初始化 session 状态
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'raw_segments' not in st.session_state:
    st.session_state.raw_segments = []
if 'char_desc' not in st.session_state:
    st.session_state.char_desc = ""

# --- 1. 侧边栏：API 与模型配置 (严格满足请求2, 3) ---
st.sidebar.header("🚀 AI 模型配置")
api_base = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")

model_options = [
    "deepseek-chat", 
    "gpt-4o", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro", 
    "grok-1", 
    "doubao-pro-4k", 
    "自定义"
]
selected_model = st.sidebar.selectbox("选择大模型 (Model ID)", model_options)
if selected_model == "自定义":
    model_name = st.sidebar.text_input("手动输入模型名称")
else:
    model_name = selected_model

# --- 主界面 ---
st.title("🎬 漫剧全流程分镜分步工作台")

# --- 第一步：文案逻辑切分 ---
if st.session_state.step == 1:
    st.header("第一阶段：文案逻辑分镜 (切分)")
    st.info("规则：对话切换、动作改变、场景转换或超过35字，即切分为下一个分镜。")
    
    char_input = st.text_area("1. 请输入/粘贴【角色外观及着装描述】(用于后续一致性注入)", height=150, 
                             placeholder="例如：安妙衣：清冷美人，银丝蝴蝶簪，白色绫罗纱衣...")
    
    uploaded_file = st.file_uploader("2. 上传故事原文 (.txt)", type=['txt'])
    text_input = st.text_area("或者直接粘贴文案内容", height=300)

    if st.button("开始逻辑切分"):
        final_text = text_input if text_input else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not api_key or not final_text:
            st.error("请确保填写了 API Key 和文案内容")
        else:
            with st.spinner("正在进行严格逻辑切分，确保不漏一个字并遵循35字原则..."):
                split_prompt = """你是一个专业剧本切分师。
                任务：将文案切分为独立分镜。
                切分规则（优先级排序）：
                1. 每个【角色对话切换】、每个【场景切换】、每个【关键动作改变】，都必须设定为下一个分镜。
                2. 严格对齐时间：由于视频只能生成5秒（约35个字符），若一段内容超过35字，必须强制拆分为多个分镜。
                3. 100%保留原文：严禁遗漏任何内容或一个字，禁止改变故事结构，禁止添加额外内容。
                格式要求：
                仅输出带序号的纯文案列表，例如：
                1.文案...
                2.文案...
                """
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {
                        "model": model_name,
                        "messages": [{"role": "system", "content": split_prompt}, {"role": "user", "content": final_text}],
                        "temperature": 0.1
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    segments = res.json()['choices'][0]['message']['content']
                    st.session_state.raw_segments = segments
                    st.session_state.char_desc = char_input
                    st.session_state.step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"切分请求失败: {e}")

# --- 第二步：预览并确认分镜 ---
elif st.session_state.step == 2:
    st.header("第二阶段：校验分镜内容")
    st.warning("请检查切分是否满足 35字/5秒 规则，可在此手动微调。")
    edited_segments = st.text_area("逻辑分镜预览 (每行代表一个分镜)", value=st.session_state.raw_segments, height=500)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 返回重做"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步：生成视觉描述 ➡️"):
            st.session_state.raw_segments = edited_segments
            st.session_state.step = 3
            st.rerun()

# --- 第三步：分批生成视觉描述 ---
elif st.session_state.step == 3:
    st.header("第三阶段：生成 MJ 画面与即梦视频描述")
    st.info("为节省算力和确保质量，请选择批次生成（每批20个）。")
    
    segments_list = [s for s in st.session_state.raw_segments.split('\n') if s.strip()]
    total = len(segments_list)
    
    # 分页逻辑
    batch_size = 20
    batch_count = (total // batch_size) + (1 if total % batch_size > 0 else 0)
    current_batch = st.number_input(f"当前总计 {total} 个分镜，请选择处理批次 (每批 {batch_size} 组)", 
                                  min_value=1, max_value=batch_count, step=1)
    
    start_idx = (current_batch - 1) * batch_size
    end_idx = min(start_idx + batch_size, total)
    current_batch_list = segments_list[start_idx:end_idx]

    if st.button(f"执行生成：第 {start_idx+1} - {end_idx} 组"):
        with st.spinner("正在注入角色字典并生成 MJ 与即梦描述词..."):
            desc_prompt = f"""你是一个顶级的漫剧导演。
            任务：为以下分镜文案构思画面。比例：9:16。
            
            角色描述字典（必须完整调用，不可缺失细节）：
            {st.session_state.char_desc}
            
            输出规则：
            1. 每一组分镜必须包含：[原文内容]、[画面描述]、[视频生成]。
            2. 【画面描述】：用于 Midjourney。描述场景、光影、人物外观、着装、景别。必须是静态描述，**严禁出现动作行为词**。
            3. 【视频生成】：用于即梦AI。基于画面描述，增加动作描述、神态变化、镜头语言。必须结合文案体现故事感。
            4. 必须保持场景连续性，确保相邻分镜不割裂。
            
            格式示例：
            数字序号.
            原文内容：...
            画面描述：...
            视频生成：...
            ---
            """
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                data = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": desc_prompt},
                        {"role": "user", "content": "\n".join(current_batch_list)}
                    ],
                    "temperature": 0.3
                }
                res = requests.post(api_base, headers=headers, json=data)
                res.raise_for_status()
                st.session_state.final_output = res.json()['choices'][0]['message']['content']
            except Exception as e:
                st.error(f"生成描述失败: {e}")

    if 'final_output' in st.session_state:
        st.subheader("🖼️ 生成结果预览")
        st.text_area("当前批次描述词", value=st.session_state.final_output, height=500)
        st.download_button("📥 下载当前结果", st.session_state.final_output, file_name=f"分镜描述_批次{current_batch}.txt")

    if st.button("🔄 重置工作台"):
        st.session_state.step = 1
        st.rerun()
