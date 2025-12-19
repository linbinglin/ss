import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="电影解说AI分镜 Pro", layout="wide", page_icon="🎬")

# --- 初始化数据状态 ---
if 'all_segments' not in st.session_state:
    st.session_state['all_segments'] = []
if 'batch_result' not in st.session_state:
    st.session_state['batch_result'] = ""

# 2. 侧边栏：配置参数与后缀
st.sidebar.title("⚙️ 全局设置")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 风格后缀")
mj_suffix = st.sidebar.text_input("Midjourney 后缀词", value="--ar 16:9 --v 6.1 --style raw")

st.sidebar.markdown("---")
st.sidebar.subheader("4. 模型设置")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型 (手动输入)"]
selected_option = st.sidebar.selectbox("选择大脑", model_options)

if selected_option == "自定义模型 (手动输入)":
    model_id = st.sidebar.text_input("请输入具体的 Model ID", placeholder="例如：gpt-4-turbo")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("第一步：复用 v5.1 纯净导演逻辑 | 第二步：支持批处理与视觉一致性锚定")

# --- 第一阶段：逻辑分镜（完全还原 v5.1 逻辑） ---
st.header("第一步：逻辑分镜（构建纯净骨架）")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # v5.1 核心预处理：物理抹除换行，合并为纯文字流
    full_story = "".join(raw_text.split())

    if st.button("🚀 生成逻辑分镜脚本", use_container_width=True):
        if not api_key or not model_id:
            st.error("请先填入配置信息！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # v5.1 核心纯净提示词
            STEP1_PROMPT = """你是一个极其严谨的电影分镜师。你的任务是将提供的【纯文字流】拆解为【数字编号的分镜脚本】。

### 核心规则：
1. **严格编号**：每一个分镜必须以“1.” “2.” “3.” 这种数字序号开头，不得遗漏。
2. **拒绝注释**：严禁在分镜中添加任何括号、分析、镜头意图或额外描述。只需输出“数字. 原文”。
3. **视觉单元切分（严禁合并）**：
   - 一个分镜只能包含一个视觉重点或核心动作。
   - 严禁为了省事将两个不同的动作（如：他跑回家、他坐下喝水）合并在一个分镜里。
4. **字数与时长对齐**：
   - 每个分镜目标字数为 25-35 字。
   - 绝对严禁超过 40 字。
5. **原文零改动**：不准改字、删字、加字。
"""
            with st.spinner("正在逐句深度解析并精准分镜..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP1_PROMPT},
                                  {"role": "user", "content": f"请对以下文字流进行等权重的精确分镜，从头到尾保持高精度拆解，必须带数字编号：\n\n{full_story}"}],
                        temperature=0.1
                    )
                    # 将结果保存并解析
                    st.session_state['all_segments'] = [l.strip() for l in response.choices[0].message.content.split('\n') if re.match(r'^\d+', l.strip())]
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

# 展示并检查第一步结果
if st.session_state['all_segments']:
    st.subheader(f"📋 分镜骨架预览 (共 {len(st.session_state['all_segments'])} 组)")
    
    # 字数监测显示
    for line in st.session_state['all_segments'][:10]: # 预览前10条
        text_only = re.sub(r'^\d+[\.、\s]+', '', line)
        length = len(text_only)
        if length > 40: st.error(f"❌ {line} (字数超标: {length})")
        else: st.success(f"✅ {line} (字数: {length})")
    
    st.info("如需微调，请在下方文本框修改后继续。")
    edited_text = st.text_area("分镜文案内容", "\n".join(st.session_state['all_segments']), height=250)
    st.session_state['all_segments'] = [l.strip() for l in edited_text.split('\n') if re.match(r'^\d+', l.strip())]

    st.markdown("---")

    # --- 第二阶段：分镜描述（按批次微调版） ---
    st.header("第二步：视觉化扩充（批处理模式）")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        char_desc = st.text_area("👤 角色形象设定 (调用逻辑：分镜出现即引用)", 
                                 placeholder="例：林凡：(25岁，玄色刺绣长袍，目光如电，黑色马尾)。\n苏晴：(18岁，紫色纱裙，蝴蝶簪)。",
                                 height=200)
    with col2:
        st.info("💡 批处理模式：建议每次生成 20 组，以保证视觉描述的细致度。")
        total_len = len(st.session_state['all_segments'])
        batch_size = 20
        batch_options = [f"第 {i+1} - {min(i+batch_size, total_len)} 组" for i in range(0, total_len, batch_size)]
        selected_batch = st.selectbox("选择要生成的批次", batch_options)
        
        # 解析选中索引
        match = re.findall(r'\d+', selected_batch)
        start_idx = int(match[0]) - 1
        end_idx = int(match[1])

    if st.button(f"🎨 为 {selected_batch} 生成描述词", use_container_width=True):
        if not char_desc:
            st.error("请先填写角色形象设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            current_batch_data = "\n".join(st.session_state['all_segments'][start_idx:end_idx])
            
            # 第二步提示词：增加括号调用与场景强制描述
            STEP2_PROMPT = f"""你是一个视觉导演。为分镜脚本配上视觉指令。

### 核心规则：
1. **视觉锚定**：文案中出现角色时，必须完整调用以下形象，并用括号包裹。
角色设定：{char_desc}
2. **场景强制描述**：每一个分镜必须明确描述场景环境和光影氛围，防止AI随机生成。
3. **格式化输出**：
   - 画面描述（静态）：描述场景、光影、(人物形象描述)、视角。末尾固定加上后缀词：{mj_suffix}
   - 视频生成（动态）：描述人物动作行为、神态、镜头运动。
4. **原文复读**：严禁改动分镜中的文案原文。

### 输出格式：
---
[序号]. [文案原文]
画面描述：[场景细节], [光影], (人物具体形象描写), [构图视角] {mj_suffix}
视频生成：[动作过程], [神态演变], [镜头运动]
---"""

            with st.spinner(f"正在分析 {selected_batch} ..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP2_PROMPT},
                                  {"role": "user", "content": current_batch_data}],
                        temperature=0.4
                    )
                    st.session_state['batch_result'] = response.choices[0].message.content
                    st.success("批次生成成功！")
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

    if st.session_state['batch_result']:
        st.subheader(f"🎥 {selected_batch} 视觉方案")
        st.text_area("结果预览", st.session_state['batch_result'], height=400)
        st.download_button(f"📥 下载{selected_batch}", st.session_state['batch_result'], file_name=f"分镜描述_{selected_batch}.txt")

st.markdown("---")
st.caption("分镜助手 v6.1 | 已复原 v5.1 第一步逻辑 | 优化第二步人物一致性与画风后缀")
