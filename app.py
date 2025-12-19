import streamlit as st
import requests

# --- 页面配置 ---
st.set_page_config(page_title="漫剧专业导演系统 Pro", layout="wide", page_icon="🎬")

# --- 侧边栏：API 与自定义模型配置 ---
with st.sidebar:
    st.header("⚙️ 导演工作室配置")
    base_url = st.text_input("中转接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "✨ 自定义 Model ID"]
    selected_model = st.selectbox("选择逻辑驱动模型", options=model_options)
    
    if selected_model == "✨ 自定义 Model ID":
        final_model_id = st.text_input("请输入准确的 Model ID (如: grok-beta)")
    else:
        final_model_id = selected_model

st.title("🎬 漫剧专业导演级分镜系统")
st.info("💡 核心准则：文案长度是分镜的生命线。1秒≈7字，5秒≈35字。超过35字必须拆分，情绪质变必须拆分。")

# --- 第一阶段：节奏感知型分镜 ---
st.subheader("第一阶段：精准节奏分镜（双重推理 + 时长对齐）")

col_script, col_board = st.columns(2)

with col_script:
    raw_script = st.text_area("1. 粘贴剧本原文", height=400, placeholder="请输入完整文案内容...")
    
    if st.button("🚀 执行节奏感分镜规划"):
        if not api_key or not final_model_id:
            st.error("请完善左侧 API 配置。")
        elif not raw_script:
            st.warning("内容为空。")
        else:
            with st.spinner("导演正在进行全篇建模与节奏切割..."):
                # 强化版第一步 Prompt：核心是“呼吸感”和“物理限时”
                step1_prompt = """
你是一名顶级漫剧导演，专门创作 9:16 比例的视觉作品。你的任务是对文案进行【二次精准分镜】。

【你的核心认知】：
1. **5秒底线**：视频生成工具（即梦AI）单次只能生成5秒动态。
2. **35字准则**：人类配音平均语速下，35个字刚好对应约5秒。**绝对禁止单镜文案超过35字**，否则音画会严重脱节，这是分镜失败的底线！
3. **分镜的度**：
   - 如果一段话有60字，即使内容连贯，你也必须从逻辑或情感断句处拆分为两个（例如 30+30）。
   - 如果内容包含“猛然回头”、“流下眼泪”等强情绪点，哪怕文案只有3字，也应独立成镜，给观众视觉冲击。
   - 严禁直接按原文段落分镜，要理解每一句的画面感。

【执行流程】：
- **Pass 1 (全局推理)**：分析全文的剧情起伏，确定哪里是高潮，哪里是铺垫。
- **Pass 2 (精准切割)**：
  - 遇到长句（>35字）：暴力拆分。
  - 遇到情绪转折：拆分。
  - 遇到连贯短句（总和<35字）：合并。

【输出要求】：
- 严禁遗漏原文任何一个字，严禁改变原文结构，严禁添加额外解释。
- 仅输出：序号.文案
"""
                payload = {
                    "model": final_model_id,
                    "messages": [
                        {"role": "system", "content": step1_prompt},
                        {"role": "user", "content": raw_script}
                    ],
                    "temperature": 0.2 # 降低随机性，提高逻辑严谨度
                }
                try:
                    res = requests.post(base_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=200)
                    st.session_state['step1_res'] = res.json()['choices'][0]['message']['content']
                except Exception as e:
                    st.error(f"分镜失败：{str(e)}")

with col_board:
    final_script_v1 = st.text_area("2. 导演精修分镜（请核对字数）", 
                                  value=st.session_state.get('step1_res', ''), 
                                  height=400)
    st.caption("💡 导演提示：请扫视右侧结果。如果某一行看起来超过两行半，说明字数可能超标，请手动敲回车切开并重新编号。")

st.markdown("---")

# --- 第二阶段：视觉指令集生成 ---
st.subheader("第二阶段：9:16 视觉语言转化（MJ + 即梦）")

use_char = st.checkbox("固定角色/着装参考（确保不跳戏）", value=True)
char_detail = ""
if use_char:
    char_detail = st.text_area("输入核心人物外貌特征（必填）", 
                               placeholder="例如：\n赵尘：冷酷男人，黑发束冠，玄色刺绣锦袍，剑眉星目。\n安妙衣：肤白如雪，银丝蝴蝶簪，白色绫罗裙，眼神空洞。", 
                               height=150)

if st.button("🎨 生成视觉全案"):
    if not final_script_v1:
        st.error("请先完成第一阶段分镜。")
    else:
        with st.spinner("正在根据竖屏构图设计画面..."):
            # 第二步 Prompt：强调 9:16 适配和 5秒动作逻辑
            step2_prompt = f"""
你是一名漫剧视觉总监。请为以下分镜生成 MJ 提示词和视频动态指令。

【核心设定】：
{char_detail}

【视觉逻辑要求】：
1. **画面描述 (MJ)**：
   - 适配 9:16。描述静态画面（环境、角色长相、着装、神态、光影）。
   - **景别控制**：竖屏比例下，多用“中景”和“特写”。除非是大背景介绍，否则少用远景。
   - **静止原则**：只写状态，不写动词。
2. **视频生成 (即梦 AI)**：
   - 描述基于该画面的动态。
   - 动作必须能在 **5秒内** 顺畅完成（如：人物低头、转过脸看镜头、眼眶变红）。
   - 加入镜头运动（如：推近、摇拍）。

输出格式：
[序号]. [文案]
画面描述：场景内容，[角色设定词]，[景别视角]，氛围描述词，--ar 9:16
视频生成：动态动作描述，镜头移动指令，情绪节奏
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
                st.error(f"指令生成失败：{str(e)}")

if 'step2_res' in st.session_state:
    st.text_area("📋 最终漫剧导演稿", st.session_state['step2_res'], height=600)
    st.download_button("📥 导出最终分镜表", st.session_state['step2_res'], file_name="漫剧分镜全案.txt")
