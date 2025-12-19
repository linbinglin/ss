import streamlit as st
import requests
import json

# 页面基础设置
st.set_page_config(page_title="漫剧原子级分镜系统", layout="wide")

# --- 侧边栏配置 ---
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
selected_model = st.sidebar.selectbox("选择大模型", model_list)
model_id = st.sidebar.text_input("手动输入 Model ID") if selected_model == "自定义" else selected_model

# --- 主界面 ---
st.title("🎬 漫剧原子级分镜处理台")
st.markdown("---")

# 初始化状态
if 'split_text' not in st.session_state:
    st.session_state.split_text = ""
if 'char_dict' not in st.session_state:
    st.session_state.char_dict = ""

# 布局：分为“逻辑切分”和“批量描述”两个独立板块
tab_split, tab_visual = st.tabs(["📌 第一步：原子级文案切分", "🎨 第二步：分批视觉提示词生成"])

# --- 第一阶段：文案切分 ---
with tab_split:
    st.subheader("原子级文案切分")
    st.warning("逻辑：AI 会分析动作行为、对话角色。字数超过 35 字必须强制物理切断。")
    
    char_desc = st.text_area("1. 输入角色外观字典 (必填，供后续生成描述使用)", height=150, 
                             placeholder="安妙衣：清冷美人，银丝蝴蝶簪，白色绫罗纱衣...")
    
    uploaded_file = st.file_uploader("2. 上传原文文本 (.txt)", type=['txt'])
    input_text = st.text_area("或者直接在此粘贴原文内容", height=300)

    if st.button("🔥 执行原子级暴力拆解分镜", type="primary"):
        source_content = input_text if input_text else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not api_key or not source_content:
            st.error("请填写 API Key 并输入文案")
        else:
            with st.spinner("正在进行‘外科手术式’分镜切分..."):
                # 原子级切分指令
                split_prompt = """你是一个专业的漫剧分镜剪辑师。
                你的任务是将长文案拆解为适合 9:16 短视频的“原子级”分镜。
                
                【核心准则 - 严禁妥协】：
                1. 颗粒度：不要直接搬运段落！要寻找句子中的动作变化。
                2. 动作切分：只要角色有动作起伏（如：推门、回头、冷哼、坐下）、对话交替、场景切换，必须切分为下一个序号。
                3. 长度对齐（硬性指标）：每个分镜对应的文案严禁超过 35 个字（为了对齐5秒视频）。如果一句话太长，必须从逗号或逻辑断句处暴力拆开。
                4. 完整性：不许漏掉原文任何一个字！不许自行添加描述词！
                
                【思考模式】：
                - 扫描文本 -> 识别动作/对话 -> 检查字数 -> 执行切分。
                
                【输出格式】：
                数字序号.原文内容
                数字序号.原文内容
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
                    st.success("切分完成！请核对并手动微调。")
                except Exception as e:
                    st.error(f"切分失败: {str(e)}")

    if st.session_state.split_text:
        st.write("### 切分结果预览 (请确保每行文案简短且符合动作逻辑)")
        st.session_state.split_text = st.text_area("手动微调区域 (确认无误后进入下一步)", 
                                                 value=st.session_state.split_text, height=400)

# --- 第二阶段：视觉生成 ---
with tab_visual:
    st.subheader("视觉生成 (每批 20 组)")
    
    if not st.session_state.split_text:
        st.info("请先在第一步完成文案切分。")
    else:
        # 解析已经切分好的列表
        lines = [line.strip() for line in st.session_state.split_text.split('\n') if line.strip()]
        total = len(lines)
        
        st.write(f"总分镜数：{total}")
        
        batch_size = 20
        max_batch = (total // batch_size) + (1 if total % batch_size > 0 else 0)
        current_batch = st.number_input("批次选择", min_value=1, max_value=max_batch, step=1)
        
        start = (current_batch - 1) * batch_size
        end = min(start + batch_size, total)
        current_lines = lines[start:end]
        
        st.info(f"当前处理：第 {start+1} 至 {end} 组分镜")

        if st.button(f"生成批次 {current_batch} 的视觉描述词"):
            with st.spinner("正在注入角色字典，构思 MJ 与 即梦 描述..."):
                visual_prompt = f"""你是一个电影分镜师和 AI 提示词专家。
                
                【角色外观一致性字典】：
                {st.session_state.char_dict}
                
                【任务】：
                为分镜文案生成视觉描述。
                1. 每一个序号分镜输出：原文、画面描述、视频生成。
                2. 【画面描述】：Midjourney(9:16)专用。描述静态：场景、光影、人物外观着装细节。**禁止动作词**（禁止写跑、走、哭等）。
                3. 【视频生成】：即梦AI专用。基于画面，加入动态：神态变化、肢体动作、镜头语言（推拉摇移）。
                
                【格式要求】：
                序号.
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
                        "temperature": 0.3
                    }
                    res = requests.post(api_base, headers=headers, json=data)
                    res.raise_for_status()
                    st.session_state.visual_output = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"描述生成失败: {str(e)}")

        if 'visual_output' in st.session_state:
            st.text_area("生成的提示词结果", value=st.session_state.visual_output, height=500)
            st.download_button("📥 下载当前结果", st.session_state.visual_output, 
                             file_name=f"分镜描述_批次{current_batch}.txt")
