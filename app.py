import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="AI分镜导演 v6.7", layout="wide", page_icon="🎬")

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
st.caption("第一步：回归 v5.1 黄金平衡切分 | 第二步：视觉锚定+文案对照+分批生成")

# --- 第一阶段：逻辑分镜（找回 v5.1 平衡感） ---
st.header("第一步：逻辑分镜（物理级精准切分）")
st.info("💡 **分镜金律**：每个分镜 **25-35字**。严禁合并不同动作。目标是确保 5秒 视频能完美承载内容。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # 核心逻辑：抹除所有格式，强迫 AI 重新测量文字长度
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 生成黄金平衡分镜", use_container_width=True):
        if not api_key or not model_id:
            st.error("请配置 API 信息")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 【回归 v5.1 核心】物理切割指令，强化“严禁合并”和“字数区间”
            STEP1_PROMPT = """你是一个极其严谨的电影分镜师。你的任务是将提供的【纯文字流】拆解为【数字编号的分镜脚本】。

### 必须严格遵守的物理切分规则：
1. **严格编号**：每一个分镜必须以“1.” “2.” “3.” 这种数字序号开头。
2. **拒绝注释**：严禁添加任何括号、意图分析或描述，只需输出“数字. 原文”。
3. **视觉单元切分（核心）**：
   - 一个分镜只能包含一个核心动作或视觉画面。
   - 【严禁合并】：即使两句话逻辑相关，只要字数总和超过 35 字，或者包含两个不同动作（如：他跑回家、他坐下），必须强制分为两个分镜。
4. **黄金字数区间**：
   - 每个分镜目标字数为 **25-35 字**。
   - 绝对严禁单行超过 40 字（配音 5 秒上限）。
   - 如果一句话太短（小于15字），可与下文合并，但合并后严禁超过 35 字。
5. **原文零改动**：不准改字、删字、加字。
"""
            with st.spinner("正在找回黄金节奏，进行物理切分..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP1_PROMPT},
                                  {"role": "user", "content": f"请对以下文字流进行精准的等权重分镜，必须带数字编号：\n\n{clean_stream}"}],
                        temperature=0.1
                    )
                    st.session_state['all_segments'] = [l.strip() for l in response.choices[0].message.content.split('\n') if re.match(r'^\d+', l.strip())]
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

# 第一步结果预览与统计
if st.session_state['all_segments']:
    st.subheader(f"📋 分镜预览 (共 {len(st.session_state['all_segments'])} 组)")
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        # 显示前10条的字数检测，方便用户判断节奏
        for line in st.session_state['all_segments'][:10]: 
            text_only = re.sub(r'^\d+[\.、\s]+', '', line)
            count = len(text_only)
            if count > 40: st.error(f"❌ {line} ({count}字)")
            elif count < 20: st.warning(f"🟡 {line} ({count}字)")
            else: st.success(f"✅ {line} ({count}字)")
    
    with col_b:
        edited_text = st.text_area("✍️ 分镜编辑区（可手动微调）", "\n".join(st.session_state['all_segments']), height=300)
        st.session_state['all_segments'] = [l.strip() for l in edited_text.split('\n') if re.match(r'^\d+', l.strip())]

    st.markdown("---")

    # --- 第二阶段：分镜描述 (保持文案对照) ---
    st.header("第二步：分镜视觉描述（图文对照版）")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        char_desc = st.text_area("👤 核心角色及着装设定 (必填)", 
                                 placeholder="角色名：(外观、衣服、发型细节描写)",
                                 height=200)
    with c2:
        total = len(st.session_state['all_segments'])
        batch_size = 20
        batch_options = [f"第 {i+1} - {min(i+batch_size, total)} 组" for i in range(0, total, batch_size)]
        selected_batch = st.selectbox("选择处理批次 (每20组一推)", batch_options)
        
        # 索引计算
        nums = re.findall(r'\d+', selected_batch)
        start_idx, end_idx = int(nums[0]) - 1, int(nums[1])

    if st.button(f"🎨 生成 {selected_batch} 的图文对照描述", use_container_width=True):
        if not char_desc:
            st.error("请填写角色设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            current_batch_txt = "\n".join(st.session_state['all_segments'][start_idx:end_idx])
            
            STEP2_PROMPT = f"""你是一个视觉美术导演。为分镜脚本配上视觉指令。

### 核心规则：
1. **对照复读**：必须以【序号. 文案原文】开头，严禁遗漏文案。
2. **形象注入**：文案中出现角色名，必须完整复述以下形象并用括号包裹。
角色设定：{char_desc}
3. **场景锁定**：每个分镜必须描述具体地点和环境细节，防止割裂。
4. **格式规范**：
   - 画面描述：[环境描写], [光影], (人物具体形象描述), [视角] {mj_suffix}
   - 视频生成：[动作过程], [神态变化], [镜头运动]。
"""
            with st.spinner(f"正在生成 {selected_batch} ..."):
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
        st.subheader(f"🎥 {selected_batch} 视觉制作全案")
        st.text_area("提示词结果", st.session_state['batch_result'], height=500)
        st.download_button(f"📥 下载该批次", st.session_state['batch_result'], file_name=f"分镜描述_{selected_batch}.txt")

st.markdown("---")
st.caption("v6.7 | 回归黄金平衡切分逻辑 | 保持图文对照输出")
