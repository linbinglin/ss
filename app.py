import streamlit as st
import requests
import json

# --- 页面配置 ---
st.set_page_config(page_title="漫剧导演大师 Pro", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stTextArea textarea { font-size: 15px !important; line-height: 1.6 !important; }
    .status-text { color: #2e7bcf; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 漫剧导演级分镜系统")
st.caption("深度逻辑：全局视觉推理 ➡️ 35字精准切割 ➡️ MJ+即梦双驱描述词")

# --- 侧边栏：API 与模型配置 ---
with st.sidebar:
    st.header("⚙️ 配置中心")
    base_url = st.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    st.subheader("🤖 模型驱动")
    model_options = [
        "gpt-4o", 
        "claude-3-5-sonnet-20240620", 
        "deepseek-chat", 
        "grok-beta",
        "✨ 自定义 Model ID"
    ]
    selected_model = st.selectbox("选择模型", options=model_options)
    
    if selected_model == "✨ 自定义 Model ID":
        final_model_id = st.text_input("手动输入准确的 Model ID")
    else:
        final_model_id = selected_model

    st.markdown("---")
    st.info("💡 核心规则：\n1. 9:16 竖屏构图\n2. 单镜限长 35 字\n3. 视觉合并，拒绝零碎")

# --- 阶段一：精细化视觉分镜 ---
st.subheader("第一阶段：视觉化精细分镜（双重推理逻辑）")

col_in, col_out = st.columns(2)

with col_in:
    raw_script = st.text_area("1. 粘贴剧本原文", height=400, placeholder="在此粘贴您的原始故事文本...")
    
    if st.button("🚀 执行导演级精准分镜"):
        if not api_key or not final_model_id:
            st.error("请先完善 API 地址、Key 和模型选择。")
        elif not raw_script:
            st.warning("内容为空。")
        else:
            with st.spinner("导演正在进行深度思考：全局扫描 ➡️ 视觉聚合 ➡️ 时长校验..."):
                # 核心 Prompt：引入分镜师思维
                step1_prompt = """
你是一个资深的短视频漫剧导演，擅长 9:16 竖屏视觉呈现。
任务：对以下文案进行【二次精准分镜】。

【第一遍推理：全局视觉规划】
- 阅读全文，识别故事的场景（Scene）和动作流（Action Flow）。
- 【视觉合并原则】：如果连续几句话发生在同一场景、同一人物身上，且动作是连贯的（如：他走过来，拉住她的手，低头耳语），在总字数不超过35字的前提下，必须合并为一个分镜。严禁将连贯动作拆得细碎。

【第二遍推理：物理时长限制】
- 【35字硬限】：合并后的单个分镜文案绝对不能超过 35 个汉字（为了对齐 5 秒音频）。
- 若合并后超过35字，必须在语气转折或动作断点处精准切分为两个分镜。
- 【9:16 构思】：确保每个分镜的文案能在竖屏画面中产生强烈的视觉冲击力。

【底线要求】：
- 严禁遗漏原文任何一个字，不改字，不删字。
- 严禁添加任何描述语。只输出分镜序号和文案。

输出格式示例：
1.第一段合并或拆分后的文案内容
2.第二段内容
"""
                payload = {
                    "model": final_model_id,
                    "messages": [
                        {"role": "system", "content": step1_prompt},
                        {"role": "user", "content": raw_script}
                    ],
                    "temperature": 0.2
                }
                try:
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=180)
                    st.session_state['s1_res'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"调用失败：{str(e)}")

with col_out:
    step1_final = st.text_area("2. 分镜检查结果（可手动微调合并）", 
                                value=st.session_state.get('s1_res', ''), 
                                height=400)
    st.caption("提示：请检查是否有单行文案过长，或动作太碎可以合并的情况。")

st.markdown("---")

# --- 阶段二：视觉提示词生成 ---
st.subheader("第二阶段：9:16 分镜图 (MJ) 与视频 (即梦) 描述生成")

use_char_ref = st.checkbox("开启角色一致性锁定（推荐）", value=True)
char_ref = ""
if use_char_ref:
    char_ref = st.text_area("输入角色外貌细节（如：赵尘，玄色锦袍，冷傲神态...）", height=150)

if st.button("🎨 生成 MJ + 即梦全套指令"):
    if not step1_final:
        st.error("请先完成第一阶段分镜。")
    else:
        with st.spinner("正在根据 9:16 比例设计视觉方案..."):
            # 视觉生成 Prompt
            step2_prompt = f"""
你是一个漫剧原画指导。请为每个分镜生成画面描述（给Midjourney）和动态指令（给即梦AI）。

【角色核心参考】：
{char_ref}

【制作规范】：
1. 【画面描述 (MJ)】：描述 9:16 比例的静态艺术。
   - 包含：环境场景、角色（严格引用参考词）、景别（多用特写、中景以适配竖屏）、视角（仰拍、俯拍、平视）、光影。
   - 严禁动词，只描述静态瞬间。
2. 【视频生成 (即梦)】：描述 5 秒内的动态演变。
   - 包含：基于原图的动作（如：发丝飘动、眼眶湿润、缓慢转头）、镜头语言（如：镜头匀速拉近、平移跟拍）。
   - 动作必须在 5 秒音频时间内可完成。

【格式要求】：
[序号]. [文案]
画面描述：场景内容，[角色设定]，[景别视角]，氛围说明，--ar 9:16
视频生成：动态动作描述，镜头语言轨迹，情绪节奏
"""
            payload = {
                "model": final_model_id,
                "messages": [
                    {"role": "system", "content": step2_prompt},
                    {"role": "user", "content": step1_final}
                ],
                "temperature": 0.3
            }
            try:
                res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=200)
                st.session_state['s2_res'] = res.json()['choices'][0]['message']['content']
            except Exception as e:
                st.error(f"生成失败：{str(e)}")

if 's2_res' in st.session_state:
    st.text_area("🎥 最终漫剧导演脚本", st.session_state['s2_res'], height=600)
    st.download_button("📥 导出分镜稿.txt", st.session_state['s2_res'], file_name="漫剧脚本_导演版.txt")
