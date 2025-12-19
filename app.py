import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="电影解说AI工作流 Pro", layout="wide", page_icon="🎬")

# --- 初始化数据状态 ---
if 'all_segments' not in st.session_state:
    st.session_state['all_segments'] = []
if 'batch_result' not in st.session_state:
    st.session_state['batch_result'] = ""

# 2. 侧边栏：全局配置与画风后缀
st.sidebar.title("⚙️ 全局配置")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 风格预设")
mj_suffix = st.sidebar.text_area("Midjourney 后缀词", 
                                value="--ar 16:9 --v 6.0 --style raw", 
                                help="这些词会自动添加到每个画面描述的末尾，用于固定画风、比例等。")

st.sidebar.markdown("---")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("4. 选择大脑", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具 (批处理版)")

# --- 第一阶段：分镜切分 ---
st.header("第一步：逻辑分镜切分")
uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 生成分镜骨架", use_container_width=True):
        client = OpenAI(api_key=api_key, base_url=base_url)
        STEP1_PROMPT = """你是一个极其严谨的电影分镜师。将文字流拆解为数字编号的分镜脚本。
        要求：严格编号（1. 2. 3.）；字数在25-35字之间；零增删改；每个分镜仅一个核心动作。"""
        
        with st.spinner("正在切分分镜..."):
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": STEP1_PROMPT},
                          {"role": "user", "content": clean_stream}],
                temperature=0.1
            )
            result = response.choices[0].message.content
            # 解析成列表保存到状态
            st.session_state['all_segments'] = [l.strip() for l in result.split('\n') if re.match(r'^\d+', l.strip())]

if st.session_state['all_segments']:
    st.subheader(f"📋 分镜骨架已就绪 (共 {len(st.session_state['all_segments'])} 组)")
    # 显示分镜，带字数检测
    with st.expander("点击预览/微调全部分镜"):
        edited_segments = st.text_area("分镜内容", "\n".join(st.session_state['all_segments']), height=300)
        st.session_state['all_segments'] = edited_segments.split('\n')

    st.markdown("---")

    # --- 第二阶段：分镜描述 (分批次处理) ---
    st.header("第二步：分镜视觉描述词生成")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        char_desc = st.text_area("👤 角色形象及着装设定 (必填)", 
                                 placeholder="例：林凡：(25岁，玄色长袍，目光如电，黑色马尾)。\n苏晴：(18岁，紫色纱裙，蝴蝶簪)。",
                                 height=200)
    with col2:
        st.info("💡 批处理模式：为了保证 AI 生成质量，建议每次处理 20 组。")
        total_len = len(st.session_state['all_segments'])
        # 生成批次选项
        batch_size = 20
        batch_options = []
        for i in range(0, total_len, batch_size):
            end = min(i + batch_size, total_len)
            batch_options.append(f"第 {i+1} - {end} 组")
        
        selected_batch = st.selectbox("选择要处理的批次", batch_options)
        # 获取选中的索引范围
        match = re.findall(r'\d+', selected_batch)
        start_idx = int(match[0]) - 1
        end_idx = int(match[1])

    if st.button(f"🎨 生成 {selected_batch} 的描述词", use_container_width=True):
        if not char_desc:
            st.error("请填写角色形象设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            # 获取当前批次文本
            current_batch_text = "\n".join(st.session_state['all_segments'][start_idx:end_idx])
            
            STEP2_PROMPT = f"""你是一个顶级的视觉美术导演。
            请根据提供的【分镜脚本】和【角色设定】，生成精细的视觉指令。

            ### 视觉锚定规则：
            1. **角色调用**：如果文案中出现角色，必须完整调用以下形象，并使用括号包裹。
            角色列表：{char_desc}
            2. **场景锁定**：每个分镜必须描述场景地点和环境氛围。
            3. **静态与动态分离**：
               - 画面描述：描述静态场景、光影、人物外貌、着装。禁止动词。末尾必须加上：{mj_suffix}
               - 视频生成：描述分镜文案对应的核心动作和神态，确保5秒内完成。

            ### 输出格式（严格）：
            ---
            [序号]. [文案原文]
            画面描述：场景位置, 氛围细节, (人物全量描写), 构图视角 {mj_suffix}
            视频生成：动作细节, 神态演变, 镜头运动
            ---
            """
            
            with st.spinner(f"正在生成 {selected_batch} 的视觉细节..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "system", "content": STEP2_PROMPT},
                              {"role": "user", "content": current_batch_text}],
                    temperature=0.4
                )
                st.session_state['batch_result'] = response.choices[0].message.content

    if st.session_state['batch_result']:
        st.subheader(f"✅ {selected_batch} 生成结果")
        st.text_area("当前批次描述词", st.session_state['batch_result'], height=400)
        st.download_button(f"📥 下载{selected_batch}", st.session_state['batch_result'], file_name=f"分镜描述_{selected_batch}.txt")

st.markdown("---")
st.caption("v6.0 精准批处理版 | 核心逻辑：分而治之，人物一致，画风统一")
