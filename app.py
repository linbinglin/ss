import streamlit as st
import requests

# 页面配置
st.set_page_config(page_title="漫剧导演级分镜系统", layout="wide")

# --- 侧边栏：API 与模型配置 ---
st.sidebar.header("🎬 导演组 API 配置")
api_base = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")

model_list = ["gpt-4o", "deepseek-chat", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-1", "doubao-pro-4k", "自定义"]
selected_model = st.sidebar.selectbox("选择执行导演模型", model_list)
model_id = st.sidebar.text_input("手动输入 Model ID") if selected_model == "自定义" else selected_model

# --- 初始化状态 ---
if 'storyboard_raw' not in st.session_state:
    st.session_state.storyboard_raw = ""

st.title("🎭 漫剧全流程：视觉导演分镜工作台")
st.markdown("---")

tab1, tab2 = st.tabs(["🎥 第一步：视觉导演思维切分", "🖌️ 第二步：分批美术提示词注入"])

# --- 第一阶段：视觉导演切分 ---
with tab1:
    st.subheader("导演思维：剧本视觉化拆解")
    st.markdown("""
    **分镜准则：**
    1. **动作拆解**：理解文案中的视觉动作（如：从‘愤怒’到‘强颜欢笑’是两个镜头）。
    2. **镜头语言**：换人说话必换景，情绪转折必换景，大动作必换景。
    3. **时长约束**：单条分镜文案严格控制在 **35字以内**，确保5秒视频能完全承载配音内容。
    """)
    
    char_profile = st.text_area("1. 设定角色视觉字典 (必填)", height=150, 
                               placeholder="赵尘：冷峻王爷，玄色织金袍，剑眉星目...\n安妙衣：清冷画师，白色辫子绫罗纱衣，银丝蝴蝶簪...")
    
    uploaded_file = st.file_uploader("2. 上传故事文案 (.txt)", type=['txt'])
    raw_input = st.text_area("或者直接粘贴原文", height=300)

    if st.button("🚀 执行导演思维深度分镜", type="primary"):
        source = raw_input if raw_input else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not api_key or not source:
            st.error("请完善配置信息。")
        else:
            with st.spinner("导演正在阅读剧本，分析视觉节奏与动作节点..."):
                # 核心导演 Prompt：赋予 AI 思考能力
                split_prompt = f"""你现在是一名资深的漫剧导演和分镜师。
                任务：将文案转化为具有“视觉节奏感”的分镜稿。
                
                【导演思维逻辑】：
                1. 扫描文案中的“动作点”。如果是复合动作（如：他走过来并抱住她），必须拆分为两个视觉瞬间（1.走来的中景；2.拥抱的特写）。
                2. 扫描文案中的“情绪点”。眼神的变化、神态的微调都应独立成镜，像漫画格一样细腻。
                3. **强制字数规则**：每条分镜的原文内容绝对不能超过 35 个汉字。如果一句话很长，必须按照导演视角切分为多个镜头，确保视频生成的5秒内能读完配音。
                4. **禁止机械切分**：不要只按标点符号切，要按“画面感”切。
                5. 完整性：必须保留原文所有字，不得删减。

                【输出格式】：
                序号.原文内容
                """
                
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": split_prompt},
                            {"role": "user", "content": source}
                        ],
                        "temperature": 0.3
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    st.session_state.storyboard_raw = res.json()['choices'][0]['message']['content']
                    st.session_state.char_data = char_profile
                    st.success("导演分镜稿已生成！")
                except Exception as e:
                    st.error(f"分镜失败: {str(e)}")

    if st.session_state.storyboard_raw:
        st.write("### 🎬 导演分镜稿预览")
        st.session_state.storyboard_raw = st.text_area("在此检查节奏，确认每行文案都具有独立的画面感", 
                                                      value=st.session_state.storyboard_raw, height=400)

# --- 第二阶段：分批视觉描述生成 ---
with tab2:
    st.subheader("美术组：视觉提示词注入")
    
    if not st.session_state.storyboard_raw:
        st.warning("请先在第一步生成导演分镜稿。")
    else:
        # 解析分镜
        lines = [l.strip() for l in st.session_state.storyboard_raw.split('\n') if l.strip()]
        total = len(lines)
        st.write(f"🎞️ 当前剧本共拆解为 **{total}** 个视觉分镜。")
        
        # 分页生成逻辑（每批20组）
        batch_size = 20
        max_batch = (total // batch_size) + (1 if total % batch_size > 0 else 0)
        current_batch = st.number_input("选择处理批次", min_value=1, max_value=max_batch, step=1)
        
        start = (current_batch - 1) * batch_size
        end = min(start + batch_size, total)
        batch_segments = lines[start:end]
        
        st.info(f"当前任务：处理分镜 {start+1} 至 {end}")

        if st.button(f"生成批次 {current_batch} 的全案描述"):
            with st.spinner("正在根据导演分镜稿，为 MJ 和 即梦AI 撰写美术指令..."):
                visual_prompt = f"""你现在是顶级美术指导。
                
                【人物一致性字典】：
                {st.session_state.get('char_data', '')}
                
                【任务】：
                为每一个导演分镜，构思一个完美的静态画面(MJ)和一个动感的视频方案(即梦)。
                
                【输出标准】：
                1. 每个分镜必须包含：序号、原文内容、画面描述、视频生成。
                2. **画面描述(Midjourney 9:16)**：仅描述静态元素。环境、光影、人物的外观、具体的服装细节（调用字典）、构图视角。**严禁出现任何动词。**
                3. **视频生成(即梦AI)**：描述动态过程。人物的动作轨迹、表情的微妙变化、镜头的推拉摇移。必须契合文案的氛围。
                4. **场景衔接**：确保同一场景内的光影和色调在分镜间是连续的。
                
                【格式要求】：
                数字序号.
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
                            {"role": "user", "content": "\n".join(batch_segments)}
                        ],
                        "temperature": 0.4
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    st.session_state.current_res = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"视觉描述生成失败: {str(e)}")

        if 'current_res' in st.session_state:
            st.text_area("生成的全案提示词", value=st.session_state.current_res, height=500)
            st.download_button(f"📥 下载批次 {current_batch} 分镜稿", st.session_state.current_res, 
                             file_name=f"漫剧分镜_批次{current_batch}.txt")
