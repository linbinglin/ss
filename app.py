import streamlit as st
import requests
import json

# 页面基础配置
st.set_page_config(page_title="漫剧导演分镜工作台", layout="wide")

# --- 侧边栏：API 与模型配置 ---
st.sidebar.header("⚙️ 核心 API 与模型配置")
api_base = st.sidebar.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")

model_list = [
    "gpt-4o", 
    "deepseek-chat", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro", 
    "grok-1", 
    "doubao-pro-4k", 
    "自定义"
]
selected_model = st.sidebar.selectbox("选择执行大模型", model_list)
model_id = st.sidebar.text_input("手动输入 Model ID") if selected_model == "自定义" else selected_model

# --- 主界面 ---
st.title("🎬 漫剧原子级视觉导演分镜系统")
st.markdown("---")

# 初始化 Session State
if 'split_text' not in st.session_state:
    st.session_state.split_text = ""
if 'char_dict' not in st.session_state:
    st.session_state.char_dict = ""

tab_split, tab_visual = st.tabs(["📌 第一步：视觉导演切分 (逻辑颗粒度)", "🎨 第二步：美术提示词生成 (每批20组)"])

# --- 第一阶段：视觉导演切分 ---
with tab_split:
    st.subheader("导演视角：原子级视觉瞬间拆解")
    st.info("💡 逻辑：像画漫画一样，每一个动作、每一句对话、每一处字数超标都是一个新格。")
    
    char_desc = st.text_area("1. 录入角色外观字典 (用于后续视觉对齐)", height=150, 
                             placeholder="安妙衣：清冷美人，银丝蝴蝶簪，白色绫罗纱衣...")
    
    uploaded_file = st.file_uploader("2. 上传故事文案 (.txt)", type=['txt'])
    input_text = st.text_area("或者直接在此粘贴文案内容", height=300)

    if st.button("🚀 执行导演级视觉拆解 (暴力切分)", type="primary"):
        source_content = input_text if input_text else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not api_key or not source_content:
            st.error("请确认 API Key 和文案已填写。")
        else:
            with st.spinner("导演正在构思每一格漫画的切分点..."):
                # 视觉导演指令：强制打破段落思维
                split_prompt = """你现在是一名顶级的漫剧导演和漫画家。
                你的任务是将用户提供的长文案进行【原子级视觉切分】。
                
                【切分准则 - 严禁妥协】：
                1. 忘记段落：不要按照原文的段落来分。要按照“视觉瞬间”来分。
                2. 视觉瞬间定义：
                   - 任何一个独立的动作（如：推门、回眸、倒地、冷笑）。
                   - 任何一处对话切换（换人说话必须换景）。
                   - 任何一处场景/焦点变化。
                3. 长度强制红线：每个分镜文案绝对严禁超过 35 个汉字。因为每张图只能生成5秒视频，文案太长音频会超长。
                   - 如果一句话很长（如40字），你必须根据逻辑停顿（逗号/转折）将其强行物理切割为 2-3 个分镜。
                4. 完整保留：不许遗漏原文中的任何一个字！
                
                【输出格式】：
                序号.原文内容
                
                【示例】：
                原文：他推门进来，看着满地碎片，冷笑着说你终于肯低头了。
                拆解结果：
                1.他推门进来
                2.看着满地碎片
                3.冷笑着说
                4.“你终于肯低头了。”
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
                    st.session_state.split_text = res.json()['choices'][0]['message']['content']
                    st.session_state.char_dict = char_desc
                    st.success("切分完成！请根据下方结果进行核对，确保每一行都很短且有视觉感。")
                except Exception as e:
                    st.error(f"切分请求失败: {str(e)}")

    if st.session_state.split_text:
        st.write("### 导演分镜稿预览 (请在此微调切分点)")
        st.session_state.split_text = st.text_area("微调区域 (确认无误后进入下一步)", 
                                                 value=st.session_state.split_text, height=450)

# --- 第二阶段：视觉提示词生成 ---
with tab_visual:
    st.subheader("美术设定：MJ图片 + 即梦视频描述词")
    
    if not st.session_state.split_text:
        st.warning("请先在第一步完成文案切分。")
    else:
        # 解析切分好的分镜列表
        lines = [line.strip() for line in st.session_state.split_text.split('\n') if line.strip()]
        total = len(lines)
        st.write(f"🎞️ 总分镜数：{total}")
        
        # 批次处理逻辑
        batch_size = 20
        max_batch = (total // batch_size) + (1 if total % batch_size > 0 else 0)
        current_batch = st.number_input("批次选择 (分批生成防止模型遗忘及断连)", min_value=1, max_value=max_batch, step=1)
        
        start = (current_batch - 1) * batch_size
        end = min(start + batch_size, total)
        current_lines = lines[start:end]
        
        st.info(f"当前批次：第 {start+1} 至 {end} 个分镜")

        if st.button(f"生成批次 {current_batch} 的视觉提示词"):
            with st.spinner("正在调用角色字典，构思电影感画面..."):
                visual_prompt = f"""你现在是 AI 绘画(Midjourney) 和 AI 视频(即梦/Runway) 的顶级专家。
                
                【一致性人物字典 - 每一张画都必须严格遵守】：
                {st.session_state.char_dict}
                
                【生成任务】：
                请根据以下分镜文案，生成高度契合故事且一致性强的视觉描述。
                1. 每一个分镜包含三项：原文内容、画面描述、视频生成。
                2. 【画面描述】：用于 MJ 生成 9:16 底图。描述：环境场景、光影材质、人物具体着装细节、视角(特写/中景等)。**注意：禁止描述动作(如哭、跑、打架)，必须是静态瞬间。**
                3. 【视频生成】：用于即梦AI使图片动起来。描述：人物的动作幅度、神态细节变化、镜头语言（推拉摇移、升降镜头）。必须展现文案中表达的情绪。
                
                【格式要求】：
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
                            {"role": "user", "content": "\n".join(current_lines)}
                        ],
                        "temperature": 0.4
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    st.session_state.visual_output = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"视觉生成失败: {str(e)}")

        if 'visual_output' in st.session_state:
            st.text_area("生成的全流程提示词 (MJ+即梦)", value=st.session_state.visual_output, height=500)
            st.download_button(f"📥 下载批次 {current_batch} 结果", st.session_state.visual_output, 
                             file_name=f"分镜描述_批次{current_batch}.txt")
