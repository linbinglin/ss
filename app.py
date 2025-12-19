import streamlit as st
import requests
import json

# --- 页面配置 ---
st.set_page_config(page_title="漫剧全流程分镜大师", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .stTextArea textarea { font-size: 14px !important; font-family: 'Courier New', Courier, monospace; }
    .step-header { padding: 10px; background-color: #2e7bcf; color: white; border-radius: 5px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 漫剧全流程分镜大师")

# --- 侧边栏：API 与模型配置 ---
with st.sidebar:
    st.header("⚙️ 全局配置")
    base_url = st.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    
    model_list = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "grok-beta", "✨ 自定义 Model ID"]
    selected_option = st.selectbox("选择模型", options=model_list)
    final_model_id = st.text_input("输入 Model ID", value="") if selected_option == "✨ 自定义 Model ID" else selected_option

# --- 步骤一：精细文本分镜 ---
st.markdown('<div class="step-header">步骤一：文本精细分镜（2次推理/35字限制）</div>', unsafe_allow_html=True)

col_s1_left, col_s1_right = st.columns([1, 1])

with col_s1_left:
    st.subheader("1. 导入原始文案")
    raw_script = st.text_area("请粘贴剧本文案", height=300, placeholder="在此输入原始文案内容...")
    
    if st.button("🚀 开始第一阶段：精细分镜"):
        if not api_key or not raw_script:
            st.error("请填入 API Key 和文案内容。")
        else:
            with st.spinner("导演正在进行两次推理分析，请稍候..."):
                # 步骤一的 Prompt：专注于文本拆分
                step1_prompt = """
你是一个专业漫剧剪辑导演。
任务：对以下文案进行【二次精准分镜】。

规则：
1. 【两遍推理】：第一遍阅读全文理解剧情逻辑；第二遍结合音频时长（35字=5秒）进行精细分镜。
2. 【35字准则】：每个分镜的文案内容严格控制在 35 个字符以内。如果原句太长，必须在逻辑断句处拆分为两个分镜。
3. 【完整性】：严禁遗漏原文任何一个字，严禁添加任何原文以外的内容，严禁修改结构。
4. 【拆分点】：对话切换、动作改变、场景改变必须拆分。
5. 【合并点】：如果连续几句极短且意境一致，可适当合并，但合并后总字数不得超过35字。

输出格式：
1.分镜内容...
2.分镜内容...
"""
                payload = {
                    "model": final_model_id,
                    "messages": [
                        {"role": "system", "content": step1_prompt},
                        {"role": "user", "content": raw_script}
                    ],
                    "temperature": 0.1
                }
                try:
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
                    st.session_state['step1_output'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"第一阶段失败: {str(e)}")

with col_s1_right:
    st.subheader("2. 分镜检查与微调")
    # 允许用户在进入第二阶段前手动修改分镜文本
    step1_final = st.text_area("分镜拆分结果（可手动修改）", 
                                value=st.session_state.get('step1_output', ''), 
                                height=300)

st.markdown("---")

# --- 步骤二：描述词生成 ---
st.markdown('<div class="step-header">步骤二：分镜图 (MJ) 与视频 (即梦) 描述词生成</div>', unsafe_allow_html=True)

use_char_ref = st.checkbox("是否加入【核心角色/着装描述】？", value=False)
char_description = ""
if use_char_ref:
    char_description = st.text_area("请输入角色设定（例如：赵尘，玄色锦袍，冷酷神态...）", height=150)

if st.button("🎨 开始第二阶段：生成描述词"):
    if not api_key or not step1_final:
        st.error("请先完成第一步分镜。")
    else:
        with st.spinner("正在为每个分镜生成 MJ 提示词和视频动态指令..."):
            # 步骤二的 Prompt：专注于画面
            step2_prompt = f"""
你是一个专业漫剧原画师。请根据提供的【分镜文本】和【角色设定】，为每个分镜生成【画面描述】和【视频生成】描述。

角色设定（如有）：
{char_description}

执行规则：
1. 【画面描述 (MJ)】：描述静态视觉。包括：9:16比例、具体场景（需保持前后一致）、景别（特写/中景等）、视角、光影、人物固定外表与着装、表情神态。注意：严禁描述动作。
2. 【视频生成 (即梦)】：描述动态演变。基于画面描述，增加人物动作（如：转头、走向一边、挥手）、镜头语言（如：推拉镜头、平移跟拍）、情绪变化。
3. 【一致性】：每个分镜都要重复描述场景和角色核心特征，防止AI生成跳戏。
4. 【5秒逻辑】：确保视频生成描述的动作在5秒内可以完成。

输出格式：
序号. [文案内容]
画面描述：场景[XXX]，角色[XXX]，[景别视角]，[氛围光影]
视频生成：[动作描述]，[镜头语言]，[动态流向]
"""
            payload = {
                "model": final_model_id,
                "messages": [
                    {"role": "system", "content": step2_prompt},
                    {"role": "user", "content": step1_final}
                ],
                "temperature": 0.4
            }
            try:
                res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
                st.session_state['step2_output'] = res.json()['choices'][0]['message']['content']
            except Exception as e:
                st.error(f"第二阶段失败: {str(e)}")

if 'step2_output' in st.session_state:
    st.subheader("🎬 最终导演分镜表")
    st.text_area("最终结果", st.session_state['step2_output'], height=600)
    st.download_button("📥 下载完整分镜稿", st.session_state['step2_output'], file_name="导演分镜稿.txt")
