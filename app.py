import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="AI分镜导演 v6.5", layout="wide", page_icon="🎬")

# 数据持久化
if 'all_segments' not in st.session_state:
    st.session_state['all_segments'] = []
if 'batch_result' not in st.session_state:
    st.session_state['batch_result'] = ""

# 2. 侧边栏：全局配置
st.sidebar.title("⚙️ 系统配置")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. Midjourney 画风后缀")
mj_suffix = st.sidebar.text_input("后缀词 (仅在第二步生效)", value="--ar 16:9 --v 6.1 --style raw")

st.sidebar.markdown("---")
st.sidebar.subheader("4. 模型设置")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("选择模型", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("手动输入 Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("第一步：100% 还原 V5.1 物理切分逻辑 | 第二步：视觉锚定与批处理")

# --- 第一阶段：还原 V5.1 物理切分 ---
st.header("第一步：逻辑分镜（还原 V5.1 纯净骨架）")
st.info("💡 逻辑：此步骤执行‘物理切割’。目标：每个分镜 25-35 字，包含一个核心视觉单元。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # V5.1 灵魂逻辑：彻底粉碎原文格式，合并为纯文字流
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 生成物理分镜脚本", use_container_width=True):
        if not api_key or not model_id:
            st.error("请配置 API 信息")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 【核心】这里完全复原 V5.1 的提示词，不改动任何字
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
        for line in st.session_state['all_segments'][:15]: # 预览前15条
            text_only = re.sub(r'^\d+[\.、\s]+', '', line)
            count = len(text_only)
            if count > 40: st.error(f"❌ {line} ({count}字)")
            else: st.success(f"✅ {line} ({count}字)")
    
    with col_b:
        edited_text = st.text_area("✍️ 物理分镜编辑区", "\n".join(st.session_state['all_segments']), height=400)
        st.session_state['all_segments'] = [l.strip() for l in edited_text.split('\n') if re.match(r'^\d+', l.strip())]

    st.markdown("---")

    # --- 第二阶段：分镜描述 (用户微调版) ---
    st.header("第二步：分镜视觉描述（分批执行）")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        char_desc = st.text_area("👤 角色形象及着装设定", 
                                 placeholder="角色A：(形象描写)\n角色B：(形象描写)",
                                 height=200)
    with c2:
        total = len(st.session_state['all_segments'])
        batch_size = 20
        batch_options = [f"第 {i+1} - {min(i+batch_size, total)} 组" for i in range(0, total, batch_size)]
        selected_batch = st.selectbox("选择当前要生成的批次 (每次20组)", batch_options)
        
        # 索引提取
        nums = re.findall(r'\d+', selected_batch)
        start_idx, end_idx = int(nums[0]) - 1, int(nums[1])

    if st.button(f"🎨 为 {selected_batch} 生成视觉描述词", use_container_width=True):
        if not char_desc:
            st.error("请填写角色设定！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            current_batch_txt = "\n".join(st.session_state['all_segments'][start_idx:end_idx])
            
            # 第二步提示词：增加角色括号调用、场景锁定、后缀添加
            STEP2_PROMPT = f"""你是一个视觉美术导演。为分镜脚本配上视觉指令。

### 核心规则：
1. **视觉锚定**：当文案中出现角色时，必须完整调用以下形象，并使用括号包裹。
角色列表：{char_desc}
2. **场景锁定**：每个分镜必须描述场景地点和环境氛围，严禁随机生成。
3. **格式化输出**：
   - 画面描述：[场景位置], [光影细节], (人物完整形象描写), [视角构图] {mj_suffix}
   - 视频生成：[人物具体动作], [神态演变], [镜头运动]。确保5秒内完成。
4. **原文复读**：严禁改动分镜中的文案原文。
"""
            with st.spinner(f"正在分析 {selected_batch} 的画面..."):
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
        st.subheader(f"🎥 {selected_batch} 视觉方案结果")
        st.text_area("提示词预览", st.session_state['batch_result'], height=400)
        st.download_button(f"📥 下载 {selected_batch}", st.session_state['batch_result'], file_name=f"分镜描述_{selected_batch}.txt")

st.markdown("---")
st.caption("v6.5 完美回归版 | 锁定 V5.1 分镜逻辑 | 支持批处理与画风后缀词")
