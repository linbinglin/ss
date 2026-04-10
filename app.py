# ==========================================
# 3. 侧边栏：API配置与记忆面板
# ==========================================
with st.sidebar:
    st.header("⚙️ API 配置中心")
    api_key = st.text_input("输入 API Key", type="password", help="第三方API平台的密钥")
    base_url = st.text_input("接口地址 (Base URL)", value="https://yunwu.ai/v1/")
    
    # ------------------ 修改了这里 ------------------
    st.subheader("🤖 模型选择")
    # 预设几个目前最流行的高级写剧本模型
    model_options = [
        "deepseek-chat",           # DeepSeek V3 (性价比之王)
        "deepseek-reasoner",       # DeepSeek R1 (深度思考模型)
        "gpt-4o",                  # OpenAI 最新全能模型
        "claude-3-5-sonnet-20241022", # Claude 最新模型 (写文科极强)
        "✍️ 自定义 (手动输入其他模型ID)"
    ]
    
    selected_model = st.selectbox("选择常用模型", model_options)
    
    # 如果用户选择自定义，则弹出一个输入框让他自己填中转站的模型名称
    if selected_model == "✍️ 自定义 (手动输入其他模型ID)":
        model_name = st.text_input("请输入中转站对应的真实 模型ID", value="deepseek-chat", help="请参考 yunwu.ai 或你的中转站后台支持的模型名称列表")
    else:
        model_name = selected_model
        
    st.info(f"当前生效模型: **{model_name}**")
    # ------------------------------------------------
    
    st.markdown("---")
    st.header("🧠 全局记忆管理")
    st.caption("以下面板由AI自动更新，如果你发现AI遗忘了，可以在此点击清空重置。")
    if st.button("🗑️ 清空所有对话记忆", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.success("记忆已清空，系统已重置为初始状态。")
