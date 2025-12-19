import streamlit as st
import requests

# --- 页面配置 ---
st.set_page_config(page_title="漫剧导演分镜大师 v10.0", layout="wide", page_icon="🎬")

# --- 侧边栏：API 与自定义模型配置 ---
with st.sidebar:
    st.header("⚙️ 导演工作室配置")
    base_url = st.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "grok-beta", "✨ 自定义 Model ID"]
    selected_model = st.selectbox("选择逻辑驱动模型", options=model_options)
    
    if selected_model == "✨ 自定义 Model ID":
        final_model_id = st.text_input("请输入具体的 Model ID")
    else:
        final_model_id = selected_model

st.title("🎬 漫剧导演级分镜大师 v10.0")
st.error("🚨 警告：AI 将彻底打碎原文段落，按 35 字限时和视觉画面重新排版，严禁丢字！")

# --- 第一阶段：无视段落的精准分镜 ---
st.subheader("第一阶段：视觉化精细分镜（打破段落，重新建模）")

col_script, col_board = st.columns(2)

with col_script:
    raw_script = st.text_area("1. 粘贴剧本原文", height=400, placeholder="请粘贴文案...")
    
    if st.button("🚀 执行视觉重构分镜"):
        if not api_key or not final_model_id:
            st.error("请完善配置。")
        elif not raw_script:
            st.warning("内容为空。")
        else:
            with st.spinner("正在粉碎原文结构，进行视觉化重组..."):
                # v10.0 针对性指令：打破段落依赖
                step1_prompt = """
你是一个顶级的漫剧分镜导演。
【你的死命令】：
1. **彻底忽略原文段落**：不要看原文是怎么分行的。将全文看作一个连续的字符流。
2. **重新定义分镜点**：
   - 每当说话人切换（如：赵尘说、安妙衣说），必须切分。
   - 每当动作发生质变（如：推门、倒地、流泪），必须切分。
   - **物理硬限**：单个分镜字数绝对禁止超过 35 个汉字。如果一句话长达 40 字，必须从中间拆开！
3. **严禁丢字**：100%还原原文所有文字，一个标点符号都不能少。
4. **分镜密度要求**：不要给太少的分镜！要保证画面感。如果连续 30 字都在描述一个复杂的场景，请根据视觉重心拆分成 2-3 个画面。

【两遍处理流程】：
- 第一步：把原文所有换行符删掉，合成一段话。
- 第二步：根据视觉逻辑（动作、对话、时长）重新进行编号分镜。

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
                    "temperature": 0.0
                }
                try:
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=200)
                    st.session_state['step1_res'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"分镜失败：{str(e)}")

with col_board:
    final_script_v1 = st.text_area("2. 重组后的分镜预览（可手动微调）", 
                                  value=st.session_state.get('step1_res', ''), 
                                  height=400)
    st.caption("检查建议：确保每一行都不长（读完约4秒），且每一行只有一个核心动作或一句对话。")

st.markdown("---")

# --- 第二阶段：双重提示词生成 ---
st.subheader("第二阶段：视觉指令集生成 (Midjourney + 即梦)")

use_char = st.checkbox("开启角色一致性参考词", value=True)
char_detail = ""
if use_char:
    char_detail = st.text_area("输入核心人物外貌描述（发型、着装、长相）", height=150)

if st.button("🎨 生成视觉提示词全案"):
    if not final_script_v1:
        st.error("请先完成第一阶段。")
    else:
        with st.spinner("正在翻译视觉信号..."):
            step2_prompt = f"""
你是一名漫剧视觉导演。请为每个分镜生成画面描述（MJ）和动态指令（即梦AI）。

【角色设定参考】：
{char_detail}

【视觉生成规范】：
1. **画面描述 (MJ)**：
   - 适配 9:16 比例。
   - 描述：具体的场景名、角色核心词（引用参考）、景别（特写/中景）、视角、氛围。
   - **禁止出现动词**，必须是静态的瞬间。
2. **视频生成 (即梦 AI)**：
   - 基于 MJ 画面的动态描述。
   - 动作必须在 5 秒内可完成（如：眼神闪烁、嘴角上扬、镜头平移）。

输出格式：
[序号]. [文案]
画面描述：场景内容，[角色设定词]，[景别视角]，氛围描述词，--ar 9:16
视频生成：具体动态动作，镜头移动指令，情绪变化
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
                res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=300)
                st.session_state['step2_res'] = res.json()['choices'][0]['message']['content']
            except Exception as e:
                st.error(f"生成失败：{str(e)}")

if 'step2_res' in st.session_state:
    st.text_area("📋 最终导演分镜表", st.session_state['step2_res'], height=600)
    st.download_button("📥 下载完整导演稿", st.session_state['step2_res'], file_name="漫剧分镜导演稿.txt")
