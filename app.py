import streamlit as st
import requests
import json
import time

st.set_page_config(
    page_title="短剧剧本生成器",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.output-box {
    background: #f8f8f8;
    border-left: 3px solid #333;
    padding: 1.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.88rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
}
.stButton > button {
    background-color: #1a1a1a;
    color: white;
    border: none;
    padding: 0.6rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 4px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """你是"短剧改编编剧"，任务是把输入小说改编为可拍摄、节奏有效、人物鲜明的短剧剧本。

一、总目标
1) 忠于原著：不新增关键剧情，不改因果，不改人物核心性格。
2) 影视化：转成可拍画面与有效对白。
3) 逻辑清晰：人物问答有对应，事件衔接丝滑。
4) 情绪有效：能调动情绪，不刻意拉扯同一情绪包袱。
5) 实用输出：格式简洁，便于直接进入拍摄拆解。

二、优先级
P1. 原著事件与因果完整
P2. 人物性格一致 + 对话逻辑成立
P3. 影视可拍性
P4. 节奏与情绪张力
P5. 文采修饰

三、影视化规则
- 心理描写转为动作/表情/停顿/视线/手部反应
- 设定信息在场景细节或人物互动中自然带出
- 异能转为明确可视效果
- 不允许单人独角戏长期霸屏
- 每段内容必须推剧情/推关系/推人物/推悬念中的至少一个

四、对白规则
- 对白先服务逻辑，再服务风格
- 问与答必须有逻辑对应
- 角色怎么说体现性格差异
- 禁止模板腔

五、输出格式
【场景：地点|时间】
正文段落...

六、结尾附加简报
- 原著保真：关键事件点
- 影视化优化：3-5个优化点
- 逻辑保障：3处衔接说明

现在请将用户提供的小说原文改编为短剧剧本。
"""

PRESET_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "deepseek-chat",
    "deepseek-reasoner",
    "qwen-plus",
    "qwen-turbo",
    "custom",
]


def call_api(api_key, base_url, model, user_content):
    api_key = str(api_key).strip()
    base_url = str(base_url).strip()
    model = str(model).strip()
    user_content = str(user_content).strip()

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "请将以下小说原文改编为短剧剧本：\n\n" + user_content},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 8192,
    }

    base_url = base_url.rstrip("/") + "/"
    url = base_url + "chat/completions"

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                decoded = decoded[6:]
            if decoded.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(decoded)
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    yield delta["content"]
            except Exception:
                continue


with st.sidebar:
    st.markdown("## API Config")
    st.markdown("---")

    api_key_input = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-xxx",
    )

    base_url_input = st.text_input(
        "Base URL",
        value="https://yunwu.ai/v1/",
    )

    model_choice = st.selectbox(
        "Model",
        options=PRESET_MODELS,
        index=0,
    )

    if model_choice == "custom":
        custom_input = st.text_input(
            "Custom Model ID",
            value="",
            placeholder="e.g. claude-opus-4-7",
        )
        if custom_input and custom_input.strip():
            final_model = custom_input.strip()
        else:
            final_model = ""
            st.warning("Please enter a Model ID")
    else:
        final_model = model_choice

    st.caption("Model: " + final_model)
    st.markdown("---")


st.markdown("## 短剧剧本生成器")
st.markdown("将小说原文一键转化为可拍摄的短剧剧本")

input_method = st.radio(
    "input",
    options=["粘贴文本", "上传文件"],
    horizontal=True,
    label_visibility="collapsed",
)

novel_text = ""

if input_method == "粘贴文本":
    raw = st.text_area(
        "text",
        height=280,
        placeholder="请粘贴小说原文...",
        label_visibility="collapsed",
    )
    novel_text = str(raw).strip() if raw else ""

else:
    uploaded_file = st.file_uploader(
        "file",
        type=["txt"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        try:
            novel_text = uploaded_file.read().decode("utf-8")
            st.success("读取成功，共 " + str(len(novel_text)) + " 字")
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                novel_text = uploaded_file.read().decode("gbk")
                st.success("读取成功(GBK)，共 " + str(len(novel_text)) + " 字")
            except Exception as e:
                st.error("解码失败: " + str(e))
                novel_text = ""

if novel_text:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("字数", str(len(novel_text)) + " 字")
    with col2:
        st.metric("预计场景", "~" + str(max(1, len(novel_text) // 300)) + " 场")
    with col3:
        st.metric("模型", final_model if final_model else "未选择")

st.markdown("---")
generate_btn = st.button("开始生成剧本", use_container_width=True)

if generate_btn:
    safe_key = str(api_key_input).strip() if api_key_input else ""
    safe_url = str(base_url_input).strip() if base_url_input else "https://yunwu.ai/v1/"
    safe_model = str(final_model).strip() if final_model else ""
    safe_text = str(novel_text).strip() if novel_text else ""

    if not safe_key:
        st.error("请填写 API Key")
        st.stop()
    if not safe_model:
        st.error("请选择或输入 Model ID")
        st.stop()
    if not safe_text:
        st.error("请输入或上传原文")
        st.stop()

    progress_bar = st.progress(0, text="connecting...")
    status_box = st.empty()
    output_box = st.empty()

    full_output = ""
    start_time = time.time()

    try:
        progress_bar.progress(15, text="analyzing...")
        time.sleep(0.3)
        progress_bar.progress(30, text="generating...")

        token_count = 0
        for piece in call_api(safe_key, safe_url, safe_model, safe_text):
            full_output = full_output + piece
            token_count = token_count + len(piece)
            p = min(30 + int(token_count / 50), 90)
            progress_bar.progress(p, text="writing...")
            output_box.markdown(
                '<div class="output-box">' + full_output + "</div>",
                unsafe_allow_html=True,
            )

        elapsed = round(time.time() - start_time, 1)
        progress_bar.progress(100, text="done")
        status_box.success("完成，共 " + str(len(full_output)) + " 字，用时 " + str(elapsed) + " 秒")

        st.download_button(
            label="下载剧本 TXT",
            data=full_output.encode("utf-8"),
            file_name="script.txt",
            mime="text/plain",
            use_container_width=True,
        )

    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        st.error("连接失败，请检查 Base URL")
    except requests.exceptions.HTTPError as e:
        progress_bar.empty()
        code = e.response.status_code if e.response else 0
        if code == 401:
            st.error("API Key 无效")
        elif code == 429:
            st.error("请求频率超限")
        elif code == 404:
            st.error("模型不存在，请检查 Model ID")
        else:
            st.error("HTTP 错误 " + str(code))
    except requests.exceptions.Timeout:
        progress_bar.empty()
        st.error("请求超时，请缩短原文后重试")
    except Exception as e:
        progress_bar.empty()
        st.error("错误: " + str(e))
