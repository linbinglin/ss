import streamlit as st
import requests
import json

# --- 页面配置 ---
st.set_page_config(page_title="漫剧专业导演分镜系统", layout="wide", page_icon="🎬")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 导演配置中心")
    base_url = st.text_input("接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    model_list = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "✨ 自定义 Model ID"]
    selected_option = st.selectbox("选择模型", options=model_list)
    final_model_id = st.text_input("输入 Model ID", value="") if selected_option == "✨ 自定义 Model ID" else selected_option
    
    st.markdown("---")
    st.info("""
    **分镜逻辑优化：**
    1. **杜绝零碎**：不再机械地按行分镜。
    2. **两遍推理**：先构思全局画面感，再进行物理切割。
    3. **9:16 适配**：分镜内容必须能在竖屏内承载。
    """)

st.title("🎬 漫剧专业导演分镜系统")

# --- 第一阶段：导演级精细分镜 ---
st.subheader("第一步：双重推理精细分镜（确定节奏与时长）")

col_script, col_result = st.columns(2)

with col_script:
    raw_script = st.text_area("请粘贴原始剧本文案", height=400, placeholder="在此输入原始文案...")
    
    if st.button("🚀 执行导演级分镜规划"):
        if not api_key or not raw_script:
            st.error("请完善配置并输入文案。")
        else:
            with st.spinner("正在进行双重推理：全局构思 + 精准切割..."):
                # 强化版第一阶段 Prompt
                step1_prompt = """
你是一个拥有10年经验的漫剧导演，专门负责 9:16 竖屏短剧的分镜规划。
任务：将用户文案处理成最适合【漫剧出图】和【5秒视频生成】的分镜脚本。

【执行流程：双重推理】
第一遍（全局构思）：阅读全文，分析故事的起承转合。确定哪些动作是连贯的（可以合并为一个画面），哪些是情绪转折（必须拆分）。
第二遍（精准切割）：在保证视觉连贯的基础上，严格执行“35字/5秒”物理限制。

【分镜准则 - 严禁零碎】：
1. 严禁按行分割。如果连续三行文案都在描述同一个细微动作且总字数 < 35字，必须合并为一个分镜，以保证出图的稳定。
2. 严禁添加、遗漏、修改原文任何一个字。必须100%还原原文。
3. 9:16 竖屏逻辑：考虑竖屏构图。如果文案涉及多人大场面，请在分镜时构思好如何通过局部或特写来呈现。
4. 拆分触发点：只有当“角色切换”、“物理场景变动”、“时间大幅跳跃”或“单镜文案超过35字”时才允许拆分。

【输出要求】：
仅输出分镜编号和文案内容，格式如下：
1.分镜内容...
2.分镜内容...
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
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
                    st.session_state['step1_output'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"分镜失败: {str(e)}")

with col_result:
    step1_final = st.text_area("导演分镜建议（可在此手动微调合并/拆分）", 
                                value=st.session_state.get('step1_output', ''), 
                                height=400)
    st.caption("检查建议：确认每个分镜是否能在一张 9:16 的图中表达，且读完文案在 5 秒内。")

st.markdown("---")

# --- 第二阶段：双重描述生成 ---
st.subheader("第二步：画面 (MJ) 与视频 (即梦) 描述生成")

use_char = st.checkbox("启用【核心角色一致性】设定", value=True)
char_detail = ""
if use_char:
    char_detail = st.text_area("输入角色外貌/着装细节", 
                               placeholder="赵尘：冷酷男人，黑发束冠，玄色刺绣锦袍...\n安妙衣：肤白如雪，步摇发饰，白色绫罗裙...",
                               height=150)

if st.button("🎨 生成 MJ 提示词 + 视频动态指令"):
    if not step1_final:
        st.error("请先完成第一步分镜。")
    else:
        with st.spinner("正在根据 9:16 构思画面与动态..."):
            step2_prompt = f"""
你是一个漫剧原画师和视觉特效师。请根据分镜内容生成 Midjourney 绘画提示词和即梦 AI 视频动态指令。

【角色一致性参考】：
{char_detail}

【视觉生成规范】：
1. 【画面描述 (MJ)】：
   - 适配 9:16。必须描述：景别（特写/中景）、视角（平视/俯视）、具体的场景环境、光影氛围。
   - 角色描述：必须严格引用提供的【角色参考】，确保长相和衣服在每一镜中固定。
   - 静态化：只描述样子，不描述动作。
2. 【视频生成 (即梦)】：
   - 必须基于“画面描述”的静态内容。
   - 描述动态：如“人物眼眶发红，缓慢转过头”、“镜头从脚部向上平移”、“长发随风飘动”。
   - 时间感知：所有动作必须在 5 秒内完成。

【输出格式】：
[序号]. [文案内容]
画面描述：场景描述，人物外表着装，景别视角，氛围，--ar 9:16
视频生成：动作行为描述，镜头运动指令，情绪流向
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
                st.error(f"描述生成失败: {str(e)}")

if 'step2_output' in st.session_state:
    st.text_area("最终分镜表结果", st.session_state['step2_output'], height=500)
    st.download_button("📥 导出分镜文案", st.session_state['step2_output'], file_name="漫剧脚本_最终版.txt")
