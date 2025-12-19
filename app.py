import streamlit as st
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="电影解说AI导演 v4.0", layout="wide", page_icon="🎬")

if 'step1_result' not in st.session_state:
    st.session_state['step1_result'] = ""

# 2. 侧边栏
st.sidebar.title("⚙️ 系统配置")
api_key = st.sidebar.text_input("API Key", type="password")
base_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("选择模型", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具 (精准控时版)")
st.markdown("---")

# --- 第一阶段：精准控时分镜 ---
st.header("第一步：精准控时分镜（5秒法则）")
st.info("💡 **分镜金律**：每个分镜目标字数为 **25-35字**。严禁一个分镜出现多个复杂动作，确保 5 秒视频能从容展现画面。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    clean_stream = "".join(raw_text.split()) # 抹除所有格式

    if st.button("🚀 执行精准节奏分镜", use_container_width=True):
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 核心提示词：引入数学级的限制
        STEP1_PROMPT = """你是一个极其严谨的电影解说分镜导演。
你的任务是将文字流拆分为【5秒内可完成】的视觉分镜。

### 必须严格执行的数学级准则：
1. **字数硬指标（黄金区间）**：
   - 每个分镜的文字量必须在 **25 到 35 个汉字** 之间。
   - 绝对严禁超过 40 字（因为 5 秒内读不完，视频也放不下）。
   - 如果原文一句话只有 10 个字，请观察下一句，若下一句也是短句且逻辑连贯，请合并，使总字数达到 25-35 字。
   - 如果原文一句话有 60 个字，必须在中间语义停顿处强行切分为两个分镜。

2. **动作容量限制**：
   - 一个分镜只能包含【一个核心动作】（如：推门、回头、流泪、奔跑）。
   - 禁止在一个分镜（5秒）内塞入多个复杂动作。

3. **零增删改**：
   - 严禁改动原文任何字词。
   - 输出格式：[序号]. [文案]

### 逻辑示例：
原文：他失魂落魄地走在街上，天空突然下起了大雨，他抬头看天，任由雨水冲刷。
分镜结果：
1.他失魂落魄地走在街上，天空突然下起了大雨。（23字，一个环境改变）
2.他抬头看天，任由雨水冲刷。（12字，为了保证画面感，此处虽短但为重点动作，可独立）
"""

        with st.spinner("正在计算字数并规划叙事节奏..."):
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": STEP1_PROMPT},
                          {"role": "user", "content": clean_stream}],
                temperature=0.1
            )
            st.session_state['step1_result'] = response.choices[0].message.content

# 展示并增加字数统计
if st.session_state['step1_result']:
    st.subheader("📋 导演分镜草案（附字数检查）")
    
    # 解析分镜并实时计算字数
    lines = st.session_state['step1_result'].split('\n')
    for line in lines:
        if line.strip():
            # 提取文字内容（去掉序号）
            text_only = re.sub(r'^\d+[\.、\s]+', '', line)
            count = len(text_only)
            if count > 40:
                st.error(f"⚠️ 分镜过长 ({count}字)：{line}")
            elif count < 15:
                st.warning(f"⚠️ 分镜过短 ({count}字)：{line}")
            else:
                st.success(f"✅ 节奏完美 ({count}字)：{line}")

    st.session_state['step1_result'] = st.text_area("在此手动微调分镜", st.session_state['step1_result'], height=300)

    st.markdown("---")

    # --- 第二阶段：视觉描述 ---
    st.header("第二步：视觉扩充（MJ + 即梦）")
    char_desc = st.text_area("👤 角色及着装核心设定", placeholder="例：林凡：25岁，玄色长袍，目光如电。")

    if st.button("🎨 生成全套视觉描述词", use_container_width=True):
        client = OpenAI(api_key=api_key, base_url=base_url)
        STEP2_PROMPT = f"""你是一个电影视觉导演。请为分镜文案配上视觉描述。
        角色设定：{char_info if 'char_info' in locals() else char_desc}
        
        要求：
        1. 画面描述：静态、环境、光影。
        2. 视频生成：描述分镜内唯一的那个动作，确保5秒内能做完。
        3. 格式：[序号]. [原文]\n画面描述：...\n视频生成：...\n---"""
        
        with st.spinner("正在生成提示词..."):
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": STEP2_PROMPT},
                          {"role": "user", "content": st.session_state['step1_result']}],
                temperature=0.4
            )
            st.write(response.choices[0].message.content)
