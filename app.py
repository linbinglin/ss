import streamlit as st
import requests
import json

# 页面基础配置
st.set_page_config(page_title="漫剧全流程分镜工具V3", layout="wide")

# --- 侧边栏：API 与模型配置 ---
st.sidebar.header("🚀 核心 API 配置")
api_base = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")

model_list = ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-1", "doubao-pro-4k", "自定义"]
selected_model = st.sidebar.selectbox("选择模型", model_list)
model_id = st.sidebar.text_input("手动输入 Model ID") if selected_model == "自定义" else selected_model

# --- 主界面 ---
st.title("🎬 漫剧全流程分镜处理系统")
st.markdown("---")

# 初始化 Session State
if 'split_result' not in st.session_state:
    st.session_state.split_result = ""
if 'visual_results' not in st.session_state:
    st.session_state.visual_results = []

# 定义 Tab
tab1, tab2 = st.tabs(["📝 第一步：文案逻辑切分", "🎨 第二步：分批视觉描述词生成"])

# --- Tab 1: 文案切分逻辑 ---
with tab1:
    st.subheader("文案自动切分 (35字/动作/对话原则)")
    st.info("AI 将严格按照人物切换、动作改变及字数限制（35字内/5秒视频）进行切分，不漏一个字。")
    
    col_char, col_text = st.columns([1, 2])
    with col_char:
        char_desc = st.text_area("角色外观字典 (必填)", height=150, help="描述角色外观着装，用于第二步注入", 
                                placeholder="赵尘：玄色长袍，腰间佩玉...\n安妙衣：白色辫子绫罗纱衣，银丝蝴蝶簪...")
    with col_text:
        uploaded_file = st.file_uploader("上传原文文本 (.txt)", type=['txt'])
        input_raw = st.text_area("或者直接粘贴原文内容", height=250, placeholder="在此粘贴需要处理的故事原文...")

    if st.button("开始自动化切分分镜", type="primary"):
        source_content = input_raw if input_raw else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not api_key or not source_content:
            st.error("请确保填写了 API Key 和文案内容")
        else:
            with st.spinner("AI 正在执行深度切分逻辑（严格执行35字原则）..."):
                split_prompt = """你是一个顶级漫剧编剧。
                任务：将文案严格拆分为独立分镜。
                
                严格准则：
                1. 对话切换必分：不同人说话必须是独立分镜。
                2. 动作改变必分：如从“坐着”到“起身”，必须切分。
                3. 场景转换必分。
                4. 字数强制限制：文案每段字数控制在30-35字以内（对应5秒配音）。若原文一段话过长，必须从语义停顿处强制拆分为多个分镜。
                5. 原文完整：严禁遗漏任何一个字，严禁修改任何原文词语，严禁添加描述词。
                
                输出格式范例：
                1.原文内容...
                2.原文内容...
                """
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {
                        "model": model_id,
                        "messages": [{"role": "system", "content": split_prompt}, {"role": "user", "content": source_content}],
                        "temperature": 0.1
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    st.session_state.split_result = res.json()['choices'][0]['message']['content']
                    st.session_state.char_desc_stored = char_desc
                    st.success("切分完成！请在下方核对并微调。")
                except Exception as e:
                    st.error(f"切分失败: {e}")

    # 显示并允许手动编辑切分结果
    if st.session_state.split_result:
        st.write("### 逻辑分镜预览 (可在此微调序号和内容)")
        st.session_state.split_result = st.text_area("编辑分镜预览", value=st.session_state.split_result, height=400)

# --- Tab 2: 分批视觉描述生成 ---
with tab2:
    st.subheader("视觉提示词分批生成 (MJ图片 + 即梦视频)")
    
    if not st.session_state.split_result:
        st.warning("请先在第一个标签页完成‘文案切分’。")
    else:
        # 解析分镜列表
        segments = [s.strip() for s in st.session_state.split_result.split('\n') if s.strip()]
        total_count = len(segments)
        st.write(f"检测到共 **{total_count}** 个分镜。")
        
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            batch_size = 20
            max_batch = (total_count // batch_size) + (1 if total_count % batch_size > 0 else 0)
            current_batch = st.number_input("选择处理批次 (每批20个分镜)", min_value=1, max_value=max_batch, step=1)
        
        start_idx = (current_batch - 1) * batch_size
        end_idx = min(start_idx + batch_size, total_count)
        
        st.info(f"当前准备处理第 {start_idx + 1} 到 {end_idx} 组分镜。")

        if st.button(f"开始生成视觉描述词 (批次 {current_batch})"):
            batch_data = segments[start_idx:end_idx]
            with st.spinner("注入角色外观字典，正在生成动静分离提示词..."):
                visual_prompt = f"""你是一个视觉分镜专家。
                任务：为给出的分镜文案生成 Midjourney(9:16) 画面和 即梦AI 视频描述。
                
                角色外观一致性字典：
                {st.session_state.get('char_desc_stored', '')}
                
                规则：
                1. 严禁漏掉原文中的任何字。
                2. 【画面描述】：Midjourney专用。描述静态场景、光影、构图、人物外观细节、服装材质。**绝对不能包含任何动作动作词语（如跑、跳、哭）**。视角采用漫剧常用视角（如：中景、特写）。
                3. 【视频生成】：即梦AI专用。基于画面描述，增加动态：动作起伏、神态变化、镜头推拉摇移。描述需体现故事感。
                
                输出格式示例：
                [序号]
                原文内容：...
                画面描述：...
                视频生成：...
                ---
                """
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": visual_prompt},
                            {"role": "user", "content": "\n".join(batch_data)}
                        ],
                        "temperature": 0.3
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    batch_res = res.json()['choices'][0]['message']['content']
                    st.session_state.current_visual_batch = batch_res
                except Exception as e:
                    st.error(f"描述生成失败: {e}")

        # 显示批次生成结果
        if 'current_visual_batch' in st.session_state:
            st.write("---")
            st.write(f"### 第 {current_batch} 批次处理结果")
            st.text_area("生成的视觉提示词结果", value=st.session_state.current_visual_batch, height=500)
            st.download_button(f"下载第 {current_batch} 批次分镜", 
                             st.session_state.current_visual_batch, 
                             file_name=f"分镜描述_批次{current_batch}.txt")
