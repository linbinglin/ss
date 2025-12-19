import streamlit as st
from openai import OpenAI
import os

# 1. 页面配置
st.set_page_config(page_title="漫剧导演级分镜系统", layout="wide")

# --- 侧边栏：API 与模型配置 ---
st.sidebar.header("🎬 导演组 API 配置")
api_key = st.sidebar.text_input("请输入 API Key", type="password")
base_url = st.sidebar.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox(
    "选择执行导演模型",
    ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-beta", "自定义"]
)
if model_id == "自定义":
    model_id = st.sidebar.text_input("手动输入 Model ID")

# --- 初始化 Session State ---
if 'storyboard_result' not in st.session_state:
    st.session_state.storyboard_result = ""
if 'visual_prompts' not in st.session_state:
    st.session_state.visual_prompts = ""

st.title("🎭 漫剧全流程：视觉导演分镜工作台")

tab1, tab2 = st.tabs(["🎥 第一步：视觉导演切分", "🖌️ 第二步：美术提示词注入"])

# --- 第一阶段：视觉导演切分 ---
with tab1:
    st.subheader("导演思维：剧本视觉化拆解")
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        char_profile = st.text_area("1. 设定角色视觉字典 (可选)", height=150, 
                                   placeholder="例如：赵尘：冷峻王爷，玄色织金袍...\n安妙衣：清冷画师，白色纱衣...")
        uploaded_file = st.file_uploader("2. 上传故事文案 (.txt)", type=['txt'])
        raw_input = st.text_area("或者直接粘贴原文", height=200)

    with col_b:
        st.info("""
        **分镜准则：**
        1. **动作拆解**：换人说话必换景，情绪转折必换景。
        2. **时长约束**：单条分镜严格控制在 **35字以内** (约5秒配音)。
        3. **绝对忠实**：不遗漏、不修改原文任何一个字。
        """)
        
        if st.button("🚀 执行导演思维深度分镜", type="primary"):
            source_text = ""
            if raw_input:
                source_text = raw_input
            elif uploaded_file:
                source_text = uploaded_file.read().decode("utf-8")

            if not api_key or not source_text:
                st.error("请完善 API Key 和 文案内容")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)
                split_prompt = f"""你是一个优秀的电影解说工作员和资深导演。
                任务：对文本进行逐字理解并进行分镜处理。
                
                核心要求：
                1. 每个角色对话切换、场景切换、动作改变都必须设定为下一个分镜。
                2. **严禁遗漏或改变原文任何一个字**，禁止添加原文以外的内容。
                3. **严格字数控制**：每个分镜文案不能超过35个字。如果原句过长，请在不改变文字的前提下拆分为多行分镜。
                4. 输出格式：
                1.第一行内容
                2.第二行内容...
                """
                
                try:
                    with st.spinner("导演正在拆解分镜..."):
                        response = client.chat.completions.create(
                            model=model_id,
                            messages=[
                                {"role": "system", "content": split_prompt},
                                {"role": "user", "content": source_text}
                            ],
                            temperature=0.2
                        )
                        st.session_state.storyboard_result = response.choices[0].message.content
                        st.success("分镜稿生成成功！")
                except Exception as e:
                    st.error(f"失败: {str(e)}")

    if st.session_state.storyboard_result:
        st.divider()
        st.session_state.storyboard_result = st.text_area("🎬 导演分镜稿（可在此微调）", 
                                                        value=st.session_state.storyboard_result, height=400)

# --- 第二阶段：美术提示词生成 ---
with tab2:
    st.subheader("美术组：视觉提示词生成")
    
    if not st.session_state.storyboard_result:
        st.warning("请先在第一步生成分镜稿。")
    else:
        # 分批处理逻辑
        lines = [l.strip() for l in st.session_state.storyboard_result.split('\n') if l.strip()]
        st.write(f"共检测到 {len(lines)} 条分镜。")
        
        if st.button("🖌️ 为当前分镜生成 AI 绘图/视频指令"):
            client = OpenAI(api_key=api_key, base_url=base_url)
            visual_prompt_sys = f"""你现在是顶级美术指导。
            角色设定：{char_profile}
            
            任务：为每条分镜生成美术描述。
            格式要求：
            数字序号.
            原文内容：...
            画面描述(MJ)：(描述环境、构图、光影、人物特征，9:16比例)
            视频动作(即梦)：(描述人物动态、镜头推拉摇移)
            ---
            """
            
            try:
                with st.spinner("正在生成美术指令..."):
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": visual_prompt_sys},
                            {"role": "user", "content": st.session_state.storyboard_result}
                        ]
                    )
                    st.session_state.visual_prompts = response.choices[0].message.content
            except Exception as e:
                st.error(f"生成失败: {str(e)}")

        if st.session_state.visual_prompts:
            st.text_area("生成的全案提示词", value=st.session_state.visual_prompts, height=500)
            st.download_button("📥 下载完整分镜美术案", st.session_state.visual_prompts, file_name="storyboard_full.txt")
