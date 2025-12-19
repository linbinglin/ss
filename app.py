import streamlit as st
from openai import OpenAI
import re

# 页面配置
st.set_page_config(page_title="AI 视频工作流助手", layout="wide", page_icon="🎬")

# 初始化 Session State (用于跨步骤存储数据)
if 'segmented_script' not in st.session_state:
    st.session_state['segmented_script'] = ""

# 侧边栏：全局配置
st.sidebar.title("⚙️ 设置")
api_key = st.sidebar.text_input("API Key", type="password")
base_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("选择模型", ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义"])
if model_id == "自定义":
    model_id = st.sidebar.text_input("输入模型 ID")

st.title("🚀 电影解说全流程分镜工具")

# --- 步骤一：文案逻辑分镜 ---
st.header("第一步：逻辑分镜（构建骨架）")
with st.expander("点击展开第一步说明", expanded=True):
    st.info("此步骤将原文按逻辑、场景、动作以及'5秒40字'原则进行拆分，确保视频节奏。")

raw_txt = st.file_uploader("1. 上传原文 TXT", type=['txt'])
if raw_txt:
    text_content = raw_txt.getvalue().decode("utf-8", errors="ignore")
    
    if st.button("开始逻辑分镜", use_container_width=True):
        client = OpenAI(api_key=api_key, base_url=base_url)
        # 第一步专用提示词
        PROMPT_STEP1 = """你是一个专业的视频剪辑导演。请将以下文案进行精确分镜。
        规则：
        1. 严禁修改、遗漏原文任何字。
        2. 逻辑拆分：根据动作切换、对话切换、场景转换分行。
        3. 长度硬指标：每行（分镜）文案严禁超过40个汉字（对应5秒配音）。
        4. 如果原句过长，请按语感拆分为连续的多个分镜。
        5. 格式：序号. 文案内容
        """
        with st.spinner("正在优化文案节奏..."):
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": PROMPT_STEP1},
                          {"role": "user", "content": text_content}],
                temperature=0.2
            )
            st.session_state['segmented_script'] = response.choices[0].message.content

# 如果已经生成了第一步内容，显示出来并允许编辑
if st.session_state['segmented_script']:
    st.subheader("📋 逻辑分镜结果（您可以直接在下方修改）")
    edited_script = st.text_area("分镜文案内容", st.session_state['segmented_script'], height=300)
    st.session_state['segmented_script'] = edited_script

    st.markdown("---")

    # --- 步骤二：视觉描述生成 ---
    st.header("第二步：视觉化扩充（填补血肉）")
    st.warning("注：只有在您对第一步的分镜感到满意时，再执行这一步。")
    
    char_info = st.text_area("👤 输入核心角色及着装描述", 
                           placeholder="例：赵清月：20岁，清冷美人，白衣刺绣。/ 赵灵曦：18岁，杏眼，黄裙。", height=100)
    
    if st.button("为以上分镜生成 AI 提示词", use_container_width=True):
        if not char_info:
            st.error("请先填写角色描述，确保视觉统一。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            # 第二步专用提示词
            PROMPT_STEP2 = f"""你是一个视觉设计师。基于我提供的【分镜文案】和【角色描述】，为每个分镜输出对应的提示词。
            
            角色设定参考：{char_info}
            
            格式要求（严格执行）：
            [序号]. [分镜文案]
            画面描述（MJ生成图片用）：[静态描述：环境、光影、人物外貌、服装、发饰、构图视角。禁止动作描写]
            视频生成（即梦AI用）：[动态描述：人物动作、神态变化、镜头语言控制]
            ---
            """
            with st.spinner("正在为每个分镜设计画面..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "system", "content": PROMPT_STEP2},
                              {"role": "user", "content": st.session_state['segmented_script']}],
                    temperature=0.4
                )
                final_result = response.choices[0].message.content
                st.subheader("🎥 最终全流程脚本（含提示词）")
                st.write(final_result)
                st.download_button("📥 下载完整分镜脚本", final_result, file_name="完整制作脚本.txt")

st.markdown("---")
st.caption("设计理念：简单化、步骤化。先稳住文案节奏，再刻画视觉细节。")
