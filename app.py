import streamlit as st
from openai import OpenAI
import io

# 设置页面配置
st.set_page_config(page_title="AI 文案自动分镜工具", layout="wide")

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 配置选项")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
base_url = st.sidebar.text_input("2. 中转接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("3. 选择模型 (Model ID)", 
                                 ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet-20240620", 
                                  "gemini-1.5-pro", "grok-1", "doubao-pro-128k"])
custom_model = st.sidebar.text_input("或者手动输入其他 Model ID")
final_model = custom_model if custom_model else model_id

st.sidebar.info("""
**分镜逻辑提醒：**
- 严格遵循35个字符/5秒原则。
- 场景、对话、动作切换即分镜。
- 不遗漏任何原文文字。
""")

# --- 主界面 ---
st.title("🎬 电影解说文案自动分镜系统")
st.markdown("上传你的故事文案，AI 将自动为你拆解为适合剪辑的分镜脚本。")

uploaded_file = st.file_uploader("选择本地 TXT 文案文件", type=['txt'])

if uploaded_file is not None:
    # 读取文件内容
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    raw_text = stringio.read()
    
    with st.expander("👀 查看原始文案"):
        st.text_area("原文内容", raw_text, height=200)

    if st.button("🚀 开始自动化分镜分析"):
        if not api_key:
            st.error("请先在侧边栏输入 API Key！")
        else:
            try:
                # 初始化 OpenAI 客户端 (兼容中转地址)
                client = OpenAI(api_url=base_url, api_key=api_key, base_url=base_url)
                
                # 构建 Prompt
                system_prompt = f"""
你是一个优秀的电影解说工作员，现在需要对文本进行分镜处理。

【核心规则】：
1. 逐字逐句理解内容，进行分段。
2. 分镜触发条件：每个角色对话切换、场景切换、动作画面改变，必须设定为下一个分镜。
3. 整理后的内容不可遗漏原文中的任何一句话、一个字，不能改变原文故事结构，禁止添加原文以外任何内容。
4. 严格要求根据场景转换进行段落分行：当故事从一个场景切换到另一个场景时，必须用新的分镜。
5. 每个分镜对应的文案不能太长。因为每个分镜视频停留约5秒，而35个字符接近5秒，所以每个分镜文案严格控制在35个字符左右。
6. 分镜必须连贯流畅，按照剧情划分。
7. 输出格式：每一行代表一个分镜，前面加上数字序号。

示例格式：
1.8岁那年家里穷得揭揭不开锅了
2.怀孕的母亲带着我在寺外乞讨
3.我把僧人端来的粥饭全给了母亲
4.施粥的将军府老妇人, 让人领我过来问
5.都饿成人干了怎么不吃
"""
                
                with st.spinner("AI 正在深度解析剧情并拆解分镜..."):
                    response = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"请对以下文本进行分镜处理：\n\n{raw_text}"}
                        ],
                        temperature=0.3, # 降低随机性，保证严谨
                    )
                    
                    result = response.choices[0].message.content
                    
                    st.success("✅ 分镜处理完成！")
                    st.text_area("🎬 处理后的分镜脚本", result, height=500)
                    
                    # 提供下载
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=result,
                        file_name=f"分镜_{uploaded_file.name}",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"处理失败，错误信息：{str(e)}")

# --- 底部说明 ---
st.markdown("---")
st.caption("基于 Streamlit + 大模型驱动 | 适合短视频解说、剧情拆解")
