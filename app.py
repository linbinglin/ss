import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="AI分镜导演 v6.6", layout="wide", page_icon="🎬")

# 数据持久化
if 'all_segments' not in st.session_state:
    st.session_state['all_segments'] = []
if 'batch_result' not in st.session_state:
    st.session_state['batch_result'] = ""

# 2. 侧边栏：配置中心
st.sidebar.title("⚙️ 系统配置")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. Midjourney 画风后缀")
mj_suffix = st.sidebar.text_input("后缀词 (如: --ar 16:9 --v 6.1)", value="--ar 16:9 --v 6.1 --style raw")

st.sidebar.markdown("---")
st.sidebar.subheader("4. 模型设置")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("选择模型", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("手动输入 Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("第一步：还原 V5.1 物理切分逻辑 | 第二步：视觉锚定+文案对照+批处理")

# --- 第一阶段：还原 V5.1 物理切分 ---
st.header("第一步：逻辑分镜（还原 V5.1 纯净骨架）")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # V5.1 核心逻辑：抹除格式
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 生成物理分镜脚本", use_container_width=True):
        if not api_key or not model_id:
            st.error("请配置 API 信息")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # V5.1 核心提示词：纯净分镜，不改字
            STEP1_PROMPT = """你是一个极其严谨的电影分镜师。你的任务是将提供的【纯文字流】拆解为【数字编号的分镜脚本】。

### 核心规则：
1. **严格编号**：每一个分镜必须以“1.” “2.” “3.” 这种数字序号开头，不得遗漏。
2. **拒绝注释**：严禁在分镜中添加任何括号、分析、镜头意图或额外描述。只需输出“数字. 原文”。
3. **视觉单元切分（严禁合并）**：
   - 一个分镜只能包含一个视觉重点或核心动作。
   - 严禁为了省事将两个不同的动作合并在一个分镜里。
4. **字数与时长对齐**：
   - 每个分镜目标字数为 25-35 字。
   - 绝对严禁超过 40 字。
5. **原文零改动**：不准改字、删字、加字。
"""
            with st.spinner("正在以 V5.1 机械逻辑切分分镜..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP1_PROMPT},
                                  {"role": "user", "content": f"请对以下文字流进行等权重的精确分镜，必须带数字编号：\n\n{clean_stream}"}],
                        temperature=0.1
                    )
                    st.session_state['all_segments'] = [l.strip() for l in response.choices[0].message.content.split('\n') if re.match(r'^\d+', l.strip())]
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

# 第一步结果预览与统计
if st.session_state['all_segments']:
    st.subheader(f"📋 分镜骨架预览 (共 {len(st.session_state['all_segments'])} 组)")
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        for line in st.session_state['all_segments'][:10]: 
            text_only = re.sub(r'^\d+[\.、\s]+', '', line)
            count = len(text_only)
            if count > 40: st.error(f"❌ {line} ({count}字)")
            else: st.success(f"✅ {line} ({count}字)")
    
    with col_b:
        edited_text = st.text_area("✍️ 物理分镜编辑区", "\n".join(st.session_state['all_segments']), height=300)
        st.session_state['all_segments'] = [l.strip() for l in edited_text.split('\n') if re.match(r'^\d+', l.strip())]

    st.markdown("---")

    # --- 第二阶段：分镜描述 (对照版) ---
    st.header("第二步：分镜视觉描述（带文案对照）")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        char_desc = st.text_area("👤 角色形象及着装设定 (必填)", 
                                 placeholder="例：林凡：(25岁，玄色刺绣长袍，目光如电，黑色马尾)。\n苏晴：(18岁，紫色纱裙，蝴蝶簪)。",
                                 height=200)
    with c2:
        total = len(st.session_state['all_segments'])
        batch_size = 20
        batch_options = [f"第 {i+1} - {min(i+batch_size, total)} 组" for i in range(0, total, batch_size)]
        selected_batch = st.selectbox("选择当前处理批次 (每次20组)", batch_options)
        
        # 索引提取
        nums = re.findall(r'\d+', selected_batch)
        start_idx, end_idx = int(nums[0]) - 1, int(nums[1])

    if st.button(f"🎨 为 {selected_batch} 生成描述词", use_container_width=True):
        if not char_desc:
            st.error("请填写角色设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            current_batch_txt = "\n".join(st.session_state['all_segments'][start_idx:end_idx])
            
            # 【重要微调】在输出格式中强制要求复读文案
            STEP2_PROMPT = f"""你是一个视觉美术导演。为分镜脚本配上视觉指令。

### 核心规则：
1. **文案复读（铁律）**：输出的每一组必须以脚本中的【序号和文案原文】开头，严禁遗漏文案。
2. **视觉锚定**：当文案中出现角色时，必须完整调用以下形象，并使用括号包裹。
角色列表：{char_desc}
3. **场景锁定**：每个分镜必须描述场景地点和环境氛围，防止跳戏。
4. **格式化输出要求**：
   - 画面描述：[场景位置], [光影细节], (人物完整形象描写), [视角构图] {mj_suffix}
   - 视频生成：[人物具体动作], [神态演变], [镜头运动]。确保5秒内完成。

### 输出格式范例：
1. 8岁那年家里穷得揭不开锅了
画面描述：破败的农舍背景, 阴暗的光线, (林凡，8岁模样，衣衫褴褛，面黄肌瘦), 远景视角 {mj_suffix}
视频生成：林凡绝望地看着空碗，眼眶湿润，镜头缓缓拉近。
---
"""
            with st.spinner(f"正在生成 {selected_batch} 的图文对照方案..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP2_PROMPT},
                                  {"role": "user", "content": current_batch_txt}],
                        temperature=0.4
                    )
                    st.session_state['batch_result'] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

    if st.session_state['batch_result']:
        st.subheader(f"🎥 {selected_batch} 视觉方案（文案对照预览）")
        st.text_area("结果预览（含文案原文）", st.session_state['batch_result'], height=500)
        st.download_button(f"📥 下载 {selected_batch}", st.session_state['batch_result'], file_name=f"分镜对照描述_{selected_batch}.txt")

st.markdown("---")
st.caption("v6.6 | 保持 V5.1 分镜骨架 | 增强 Step2 文案对照 | 角色括号锚定 | 画风后缀自动拼接")
