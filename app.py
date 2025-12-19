import streamlit as st
import requests
import re

# 页面配置
st.set_page_config(page_title="漫剧全流程分步分镜工具", layout="wide")

# 初始化 Session State
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'descriptions' not in st.session_state:
    st.session_state.descriptions = {}

# --- 侧边栏配置 ---
st.sidebar.header("⚙️ 系统配置")
api_url = st.sidebar.text_input("API 接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")
model_id = st.sidebar.text_input("模型 ID", value="gpt-4o")

# --- 主界面渲染 ---
st.title("🎬 漫剧全流程分段工作台")

# 步骤进度条
steps = ["1. 导入与文案切分", "2. 校验分镜节奏", "3. 分批生成视觉描述"]
st.progress(st.session_state.step / len(steps))

# --- 第一步：导入与文案切分 ---
if st.session_state.step == 1:
    st.header("第 1 步：文案逻辑切分")
    char_profile = st.text_area("人物角色外观字典 (必填)", height=150, placeholder="赵尘：玄色长袍... \n安妙衣：白色辫子绫罗纱衣...")
    
    uploaded_file = st.file_uploader("上传原文文本 (.txt)", type=['txt'])
    raw_input = st.text_area("或者直接粘贴原文内容", height=300)
    
    if st.button("开始逻辑切分"):
        content = raw_input if raw_input else (uploaded_file.read().decode("utf-8") if uploaded_file else "")
        if not content or not api_key:
            st.error("请提供原文和 API Key")
        else:
            with st.spinner("正在严格按照 35 字及动作切换规则进行切分..."):
                # 专门用于切分的 Prompt
                split_prompt = """你是一个剧本拆解专家。
                任务：将文案拆分为独立分镜。
                规则：
                1. 只要出现【角色对话切换】、【场景切换】、【动作改变】，必须切分为下一个分镜。
                2. 严格对齐5秒视频：每段原文不得超过35个字。超过35字必须强制拆分。
                3. 必须100%保留原文，不许漏字，不许改字。
                4. 只输出分镜后的原文，格式：
                   1. 原文内容
                   2. 原文内容
                """
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": model_id,
                        "messages": [{"role": "system", "content": split_prompt}, {"role": "user", "content": content}],
                        "temperature": 0.1
                    }
                    res = requests.post(api_url, headers=headers, json=payload)
                    res.raise_for_status()
                    segments_raw = res.json()['choices'][0]['message']['content']
                    
                    # 简单解析出分镜列表
                    st.session_state.segments = [s.strip() for s in segments_raw.split('\n') if s.strip()]
                    st.session_state.char_profile = char_profile
                    st.session_state.step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"切分失败: {str(e)}")

# --- 第二步：校验分镜节奏 ---
elif st.session_state.step == 2:
    st.header("第 2 步：核对分镜内容 (配音时长对齐)")
    st.write("请检查切分是否合理（每行建议不超过35字）。你可以手动修改下方文本。")
    
    edited_segments = st.text_area("分镜原文预览", value="\n".join(st.session_state.segments), height=400)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 返回修改原文"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步：开始描述画面 ➡️"):
            st.session_state.segments = [s.strip() for s in edited_segments.split('\n') if s.strip()]
            st.session_state.step = 3
            st.rerun()

# --- 第三步：分批生成描述 ---
elif st.session_state.step == 3:
    st.header("第 3 步：视觉描述生成 (Midjourney + 即梦)")
    
    total = len(st.session_state.segments)
    st.write(f"总计分镜数：{total}")
    
    # 分页设置
    batch_size = 20
    current_batch_idx = st.number_input("批次选择 (每批20组)", min_value=1, 
                                        max_value=(total // batch_size) + 1, step=1)
    
    start_idx = (current_batch_idx - 1) * batch_size
    end_idx = min(start_idx + batch_size, total)
    
    st.info(f"当前准备处理第 {start_idx + 1} 到 {end_idx} 组分镜")

    if st.button(f"生成该批次 ({start_idx+1}-{end_idx}) 描述"):
        batch_to_process = st.session_state.segments[start_idx:end_idx]
        
        desc_prompt = f"""你是一个视觉分镜师。
        任务：为分镜生成画面和视频描述。
        比例：9:16。
        人物描述字典：{st.session_state.char_profile}
        
        要求：
        1. 每一个分镜输出：
           序号.
           原文内容：(保留输入内容)
           画面描述：(MJ提示词。场景+人物外观着装+视角。静态，无动作词)
           视频生成：(即梦提示词。动作+神态变化+镜头运动。5秒时长)
        2. 画面必须严格保持一致性，场景切换要平滑。
        """
        
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": desc_prompt},
                    {"role": "user", "content": "\n".join(batch_to_process)}
                ],
                "temperature": 0.3
            }
            res = requests.post(api_url, headers=headers, json=payload)
            res.raise_for_status()
            batch_result = res.json()['choices'][0]['message']['content']
            
            # 存入结果字典
            st.session_state.descriptions[current_batch_idx] = batch_result
        except Exception as e:
            st.error(f"描述生成失败: {str(e)}")

    # 显示已生成的结果
    if st.session_state.descriptions:
        st.subheader("生成结果预览")
        all_results = "\n\n".join(st.session_state.descriptions.values())
        st.text_area("当前已生成的全部描述", value=all_results, height=400)
        
        st.download_button("💾 下载全部分镜结果", data=all_results, file_name="storyboard_desc_final.txt")

    if st.button("⏪ 重置并回到第一步"):
        st.session_state.step = 1
        st.session_state.segments = []
        st.session_state.descriptions = {}
        st.rerun()
