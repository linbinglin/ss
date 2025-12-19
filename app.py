import streamlit as st
import google.generativeai as genai
import io

st.set_page_config(page_title="漫剧自动分镜工具", layout="centered")

st.title("🎬 漫剧分镜自动处理系统")
st.caption("输入原始剧本文本，自动按照对话、动作、场景切换生成标准分镜")

# 侧边栏配置
with st.sidebar:
    st.header("1. 密钥配置")
    api_key = st.text_input("输入 Gemini API Key:", type="password")
    # 使用更准确的模型 ID
    model_choice = st.selectbox("选择模型", [
        "gemini-1.5-flash-latest", 
        "gemini-1.5-pro-latest",
        "gemini-2.0-flash-exp" # 备选最新实验版
    ])
    st.markdown("---")
    st.info("💡 如果 1.5 系列报错，请尝试在 ID 后加上 '-latest' 或选择其他版本。")

# 文件上传
uploaded_file = st.file_uploader("2. 上传剧本文件 (TXT)", type=["txt"])

if uploaded_file and api_key:
    # 自动读取内容
    content = uploaded_file.read().decode("utf-8")
    
    if st.button("开始自动分镜处理"):
        try:
            genai.configure(api_key=api_key)
            
            # 这里的模型名有时需要处理，如果 404，尝试加上后缀
            target_model = model_choice
            model = genai.GenerativeModel(target_model)
            
            prompt = f"""
            你是一个资深的漫剧分镜师。任务：将以下剧本进行物理分镜处理。
            
            严格规范：
            1. 必须保留原文的所有文字，禁止遗漏、修改或自行扩写。
            2. 遇到以下情况必须切换至下一行并编号：
               - 不同的角色开始说话
               - 发生了新的动作或身体接触
               - 环境或背景发生了转移
            3. 格式要求：数字序号 + 实心句号 + 原文内容（例如：1.我是名满京城的神秘画师）。
            4. 节奏要求：保持短促、高频的切换感。

            剧本原文如下：
            {content}
            """
            
            with st.spinner("AI 正在分析并生成分镜..."):
                response = model.generate_content(prompt)
                
                if response.text:
                    st.success("分镜处理完成！")
                    st.text_area("处理结果预览", value=response.text, height=400)
                    
                    st.download_button(
                        label="📥 下载处理后的分镜文件",
                        data=response.text,
                        file_name=f"processed_{uploaded_file.name}",
                        mime="text/plain"
                    )
                else:
                    st.error("AI 未返回内容，请检查 API Key 是否有效。")

        except Exception as e:
            # 自动报错引导
            error_msg = str(e)
            if "not found" in error_msg:
                st.error(f"模型找不到: {model_choice}。请尝试在侧边栏选择其他模型或联系管理员。")
            else:
                st.error(f"处理失败: {error_msg}")

elif not api_key:
    st.info("💡 请在左侧输入你的 Gemini API Key 以激活系统。")

