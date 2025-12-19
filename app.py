import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="AI 电影导演 Pro v6.2", layout="wide", page_icon="🎬")

# --- 数据持久化 ---
if 'all_segments' not in st.session_state:
    st.session_state['all_segments'] = []
if 'batch_result' not in st.session_state:
    st.session_state['batch_result'] = ""

# 2. 侧边栏
st.sidebar.title("⚙️ 配置中心")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 风格后缀词")
mj_suffix = st.sidebar.text_input("MJ 后缀 (固定画风)", value="--ar 16:9 --v 6.1 --style raw")

st.sidebar.markdown("---")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("4. 选择大脑", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("请输入具体的 Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("精准还原 v5.1 叙事分镜逻辑 | 视觉锚定批处理")

# --- 第一阶段：还原 v5.1 纯净分镜逻辑 ---
st.header("第一步：叙事逻辑分镜（还原 v5.1 核心节奏）")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # v5.1 核心预处理：物理抹除换行，切断一切原格式参考
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 生成叙事感分镜脚本", use_container_width=True):
        if not api_key:
            st.error("请先配置 API Key")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 精准还原 v5.1 提示词逻辑：强调“视觉连贯性”下的切分
            STEP1_PROMPT = """你是一个极其严谨的电影分镜师。你的任务是将提供的【纯文字流】拆解为【叙事感极强的分镜脚本】。

### 核心分镜逻辑（还原 v5.1 精髓）：
1. **严格编号**：必须以“1.” “2.”这种数字序号开头。
2. **拒绝注释**：严禁输出任何分析、括号、注释，只需输出“数字. 原文”。
3. **分镜切分点（寻找视觉节拍）**：
   - 必须在人物动作大转折、场景切换、或说话人变化时切分。
   - **不要碎片化**：如果连续的微小动作（如：他进门、转头、看到桌子）逻辑连贯且总字数在 25-35 字内，请【合并】在一个分镜里，不要强行拆散。
4. **物理硬指标**：
   - 每个分镜目标字数为 25-35 字。
   - 严禁超过 40 字（对应5秒配音极限）。
5. **原文零改动**：绝对不准多、少、改任何一个字。
"""
            with st.spinner("正在还原 v5.1 叙事节奏进行分镜..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP1_PROMPT},
                                  {"role": "user", "content": f"请对以下文字流进行叙事逻辑切分，必须带数字编号：\n\n{clean_stream}"}],
                        temperature=0.1
                    )
                    st.session_state['all_segments'] = [l.strip() for l in response.choices[0].message.content.split('\n') if re.match(r'^\d+', l.strip())]
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

# 结果预览与实时反馈
if st.session_state['all_segments']:
    st.subheader(f"📋 分镜骨架预览 (共 {len(st.session_state['all_segments'])} 组)")
    
    # 渲染前 10 条检测字数
    for line in st.session_state['all_segments'][:10]:
        text_only = re.sub(r'^\d+[\.、\s]+', '', line)
        length = len(text_only)
        if length > 40: st.error(f"❌ {line} (字数超标: {length})")
        else: st.success(f"✅ {line} (字数: {length})")
    
    st.info("如分镜切分点不符合预期，请在下方文本框手动微调。")
    edited_text = st.text_area("分镜文案内容编辑区", "\n".join(st.session_state['all_segments']), height=250)
    st.session_state['all_segments'] = [l.strip() for l in edited_text.split('\n') if re.match(r'^\d+', l.strip())]

    st.markdown("---")

    # --- 第二阶段：批处理视觉描述 ---
    st.header("第二步：视觉化描述扩充（分批处理）")
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        char_desc = st.text_area("👤 角色形象设定", 
                                 placeholder="例：林凡：(25岁，玄色长袍，目光如电)。\n苏晴：(18岁，紫色纱裙，蝴蝶簪)。",
                                 height=200)
    with col_r:
        st.info("💡 批处理模式：为了生成质量，建议每 20 组为一个批次生成。")
        total = len(st.session_state['all_segments'])
        batch_size = 20
        batch_options = [f"第 {i+1} - {min(i+batch_size, total)} 组" for i in range(0, total, batch_size)]
        selected_batch = st.selectbox("选择当前处理批次", batch_options)
        
        # 索引计算
        indices = re.findall(r'\d+', selected_batch)
        start, end = int(indices[0]) - 1, int(indices[1])

    if st.button(f"🎨 为 {selected_batch} 生成视觉细节", use_container_width=True):
        if not char_info if 'char_info' in locals() else char_desc:
            st.error("请填写角色设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            batch_data = "\n".join(st.session_state['all_segments'][start:end])
            
            STEP2_PROMPT = f"""你是一个视觉导演。为分镜配上视觉指令。

### 核心执行逻辑：
1. **视觉锚定**：文案中出现角色名，必须完整调用以下形象，并用括号包裹。
角色设定：{char_desc}
2. **场景强制**：每个分镜必须描述具体场景地点和光影氛围，严禁跳戏。
3. **格式化输出**：
   - 画面描述：[场景描述], [光影], (人物具体形象), [视角构图] {mj_suffix}
   - 视频生成：[动作行为], [神态演变], [镜头控制]。确保5秒内完成。
4. **原文复读**：严禁改动脚本原文。
"""
            with st.spinner(f"正在分析 {selected_batch} 的视觉细节..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP2_PROMPT},
                                  {"role": "user", "content": batch_data}],
                        temperature=0.4
                    )
                    st.session_state['batch_result'] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

    if st.session_state['batch_result']:
        st.subheader(f"🎥 {selected_batch} 制作全案")
        st.text_area("结果预览", st.session_state['batch_result'], height=400)
        st.download_button(f"📥 下载{selected_batch}", st.session_state['batch_result'], file_name=f"分镜描述_{selected_batch}.txt")

st.markdown("---")
st.caption("v6.2 还原优化版 | 核心：叙事感重回 v5.1 逻辑")
