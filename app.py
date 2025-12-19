import streamlit as st
import requests
import json

# --- 页面配置 ---
st.set_page_config(page_title="漫剧导演全流程系统 Pro", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextArea textarea { font-size: 14px !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .step-box { padding: 15px; border-radius: 10px; background-color: #ffffff; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 漫剧导演级全流程分镜系统")
st.caption("分步式创作：精准文本分镜 ➡️ 视觉提示词生成")

# --- 侧边栏：API 与模型配置 ---
with st.sidebar:
    st.header("⚙️ 接口配置")
    base_url = st.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    st.subheader("🤖 模型选择")
    model_options = [
        "gpt-4o", 
        "claude-3-5-sonnet-20240620", 
        "deepseek-chat", 
        "grok-beta",
        "✨ 自定义 Model ID"
    ]
    selected_model = st.selectbox("选择驱动模型", options=model_options)
    
    # 核心：处理自定义 Model ID 逻辑
    if selected_model == "✨ 自定义 Model ID":
        final_model_id = st.text_input("请输入具体的 Model ID", placeholder="例如: gpt-4-turbo")
    else:
        final_model_id = selected_model

    st.markdown("---")
    st.error("⚠️ 核心约束：单镜头文案 ≤ 35字（约5秒音频）。")

# --- 第一阶段：文本精细分镜 ---
st.markdown('<div class="step-box">', unsafe_allow_html=True)
st.subheader("第一阶段：文本精细分镜（双重推理 + 35字硬限）")

col_s1_in, col_s1_out = st.columns(2)

with col_s1_in:
    raw_script = st.text_area("1. 粘贴剧本原文", height=300, placeholder="在此输入原始文案...")
    
    if st.button("🚀 执行第一步：精准分镜"):
        if not api_key or not final_model_id:
            st.error("请先完善左侧 API 配置和模型选择。")
        elif not raw_script:
            st.warning("请先输入文案。")
        else:
            with st.spinner("导演正在进行双重推理：构思全局 -> 暴力切割..."):
                # 第一阶段 Prompt
                step1_prompt = """
你是一个拥有极强时间感的漫剧导演。
任务：将提供的文案进行【二次精准分镜】。

硬性准则：
1. 【35字生死线】：每个分镜文案绝对不能超过 35 个汉字。这是为了配合 5 秒的视频生成和音频时长。
   - 若原句超过35字，必须无条件在逻辑断句处拆分为两个分镜。
2. 【双重推理】：
   - 第一遍：阅读全文，识别剧情转场、情绪爆发点和视觉连贯性。
   - 第二遍：在保证不碎的前提下，将意境连贯且总长在35字内的内容合并；将超长的内容拆分。
3. 【忠于原文】：严禁遗漏、修改、添加原文任何一个字。必须100%还原结构。
4. 【分镜点】：对话切换、物理场景改变必须拆分。

输出格式：
1.内容...
2.内容...
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
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=180)
                    st.session_state['step1_res'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"分镜失败：{str(e)}")

with col_s1_out:
    # 允许用户手动修改第一步结果
    final_script_v1 = st.text_area("2. 检查并微调分镜结果", 
                                  value=st.session_state.get('step1_res', ''), 
                                  height=300)
    st.caption("提示：请确认每一行文案都足够短（<35字），如有需要请手动拆分。")
st.markdown('</div>', unsafe_allow_html=True)

# --- 第二阶段：描述词生成 ---
st.markdown('<div class="step-box">', unsafe_allow_html=True)
st.subheader("第二阶段：分镜图 (MJ) 与视频 (即梦) 描述生成")

use_char_ref = st.checkbox("启用【核心角色/着装描述】一致性参考", value=True)
char_ref_text = ""
if use_char_ref:
    char_ref_text = st.text_area("输入角色描述（如：赵尘，黑发束冠，玄色锦袍...）", height=150)

if st.button("🎨 执行第二步：生成全套提示词"):
    if not final_script_v1:
        st.error("请先完成第一阶段分镜。")
    else:
        with st.spinner("正在生成视觉方案..."):
            step2_prompt = f"""
你是一个漫剧视觉导演。请根据分镜内容生成 Midjourney 提示词和即梦 AI 视频动态指令。

核心角色参考资料：
{char_ref_text}

规则：
1. 【画面描述 (MJ)】：描述 9:16 比例下的静态画面。必须包含：场景名称、角色特征（严格引用参考资料）、景别视角（特写/中景/俯仰拍）、光影氛围。严禁描述动作。
2. 【视频生成 (即梦)】：在静态图基础上描述 5 秒内的动态。包括：人物动作（如缓慢转头、挥手）、情绪变化、镜头运动（推拉、平移）。
3. 【一致性】：每个分镜都要写明场景和人物特征词，防止 AI 跑题。
4. 【文案对齐】：视频动态必须在 5 秒内能完成。

输出格式：
[序号]. [文案内容]
画面描述：场景描述，[角色特征词]，[景别视角]，氛围说明，--ar 9:16
视频生成：动态动作描述，镜头语言，情绪节奏
"""
            payload = {
                "model": final_model_id,
                "messages": [
                    {"role": "system", "content": step2_prompt},
                    {"role": "user", "content": final_script_v1}
                ],
                "temperature": 0.4
            }
            try:
                res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=200)
                st.session_state['step2_res'] = res.json()['choices'][0]['message']['content']
            except Exception as e:
                st.error(f"描述生成失败：{str(e)}")

if 'step2_res' in st.session_state:
    st.subheader("🎥 最终导演分镜稿")
    st.text_area("结果预览", st.session_state['step2_res'], height=500)
    st.download_button("📥 下载完整分镜脚本", st.session_state['step2_res'], file_name="漫剧导演分镜表.txt")
st.markdown('</div>', unsafe_allow_html=True)
