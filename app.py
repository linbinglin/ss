import streamlit as st
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 导演分镜工作流", layout="wide", page_icon="🎬")

# 初始化 Session State
if 'step1_result' not in st.session_state:
    st.session_state['step1_result'] = ""

# 侧边栏
st.sidebar.title("⚙️ 全局配置")
api_key = st.sidebar.text_input("API Key", type="password")
base_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("选择模型", ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义"])
if model_id == "自定义":
    model_id = st.sidebar.text_input("输入模型 ID")

st.title("🎬 电影解说全流程分镜工具")

# --- 第一阶段：剧情分析与逻辑分镜 ---
st.header("第一阶段：剧情逻辑切分")
st.info("目标：打碎原文段落，按‘动作/镜头/时长’重新构建分镜骨架。")

uploaded_file = st.file_uploader("上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # 清洗文本：去掉多余换行，合并成一段话，强制 AI 无法参考原段落
    processed_text = " ".join(raw_text.split())
    
    st.subheader("📄 原文内容（已清洗）")
    st.text_area("清洗后的文本流", processed_text, height=100)

    if st.button("🚀 执行专业剧情分镜", use_container_width=True):
        if not api_key:
            st.error("请填入 API Key")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 强化分镜师角色的提示词
            STEP1_PROMPT = """你是一个拥有10年经验的电影分镜导演。你的任务是彻底读懂以下剧情，并进行【画面级】拆解。
            
            ### 你的思考逻辑：
            1. **深度读懂**：先理解故事的情绪转折、关键动作和环境切换。
            2. **彻底粉碎**：忽略原文的任何分段，你要根据“视觉画面感”重新切分。
            3. **切分准则**：
               - 当人物开始一个新动作时（如：从坐下到站起），必须切分。
               - 当镜头需要切换视角时（如：从双人对峙到角色特写），必须切分。
               - 当场景或光影发生变化时，必须切分。
               - **时长对齐**：为了适配5秒视频，每行文字严格控制在35-40个汉字以内。如果一句话太长，必须按语义节奏拆分为两行。
            
            ### 输出格式：
            1. 分镜内容
            2. 分镜内容
            ...
            
            严禁遗漏任何原文文字，严禁添加任何额外解说词。
            """
            
            with st.spinner("导演正在深度阅读剧情并规划镜头..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": STEP1_PROMPT},
                        {"role": "user", "content": f"请粉碎并重构这段剧情的视觉分镜：\n\n{processed_text}"}
                    ],
                    temperature=0.3
                )
                st.session_state['step1_result'] = response.choices[0].message.content

# 展示第一阶段结果并允许修改
if st.session_state['step1_result']:
    st.subheader("📋 导演建议分镜（可编辑）")
    st.session_state['step1_result'] = st.text_area("如果分镜太少或太多，请在此微调", st.session_state['step1_result'], height=300)

    st.markdown("---")

    # --- 第二阶段：视觉描述扩充 ---
    st.header("第二阶段：视觉提示词扩充")
    
    char_desc = st.text_area("👤 角色及着装统一描述", 
                             placeholder="例如：林风：25岁，剑眉星目，黑色劲装，腰佩长剑。\n苏晴：20岁，温婉如水，淡紫色罗裙，发簪缀珍珠。",
                             height=100)
    
    if st.button("🎨 生成视觉 & 视频提示词", use_container_width=True):
        if not char_desc:
            st.warning("请填写角色描述，否则画面会产生割裂感。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            STEP2_PROMPT = f"""你是一个顶级的视觉概念艺术家。
            请根据我提供的【分镜文案】和【角色设定】，为每一个分镜补全视觉细节。
            
            角色设定：{char_desc}
            
            ### 输出规则：
            [序号]. [文案]
            画面描述：[描述当前分镜的静态画面。包含：具体的环境、光影氛围、人物的外表、服装细节、镜头视角（特写/全景/俯拍）。禁止动作词。]
            视频生成：[描述当前分镜的动态过程。包含：人物具体的动作（如：缓缓转头、泪水滑落）、镜头运动（如：慢速推近、环绕拍摄）。]
            ---
            """
            
            with st.spinner("正在绘制画面并设计动态镜头..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": STEP2_PROMPT},
                        {"role": "user", "content": st.session_state['step1_result']}
                    ],
                    temperature=0.4
                )
                final_output = response.choices[0].message.content
                st.subheader("🎥 全流程脚本（可直接用于生产）")
                st.write(final_output)
                st.download_button("📥 下载完整脚本", final_output, file_name="电影分镜全脚本.txt")

st.markdown("---")
st.caption("提示：先做好第一阶段的节奏把控，再进行第二阶段的细节填充，效果最佳。")
