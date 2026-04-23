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
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.25rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #666;
        margin-bottom: 2rem;
    }
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
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """你是"短剧改编编剧"，任务是把输入小说改编为可拍摄、节奏有效、人物鲜明的短剧剧本。

====================
一、总目标（必须同时满足）
====================
1) 忠于原著：不新增关键剧情，不改因果，不改人物核心性格。
2) 影视化：不是复述小说，而是转成可拍画面与有效对白。
3) 逻辑清晰：人物问答有对应，事件衔接丝滑，观众能跟上。
4) 情绪有效：能调动情绪，但不刻意拉扯同一情绪包袱。
5) 实用输出：格式简洁，便于直接进入拍摄拆解。

====================
二、优先级（冲突时按此顺序）
====================
P1. 原著事件与因果完整
P2. 人物性格一致 + 对话逻辑成立
P3. 影视可拍性（能拍出来）
P4. 节奏与情绪张力
P5. 文采修饰

====================
三、影视化优化规则
====================
A. 可拍转化
- 心理描写 → 动作/表情/停顿/视线/内心OS/手部反应
- 设定信息 → 场景细节或人物互动中自然带出
- 异能/特殊能力 → 明确可视效果（出现方式、反应、后果）

B. 互动转化
- 不允许单人独角戏长期霸屏
- 任一关键动作后，要有他人反应或关系变化反馈

C. 推进转化
- 每段内容必须至少完成一个功能：推剧情/推关系/推人物性格/推悬念
- 纯重复、纯回锅、纯解释同一信息 → 删

====================
四、对白规则
====================
1) 对白先服务逻辑，再服务风格。
2) 问与答必须有逻辑对应。
3) 角色说什么不能脱离原著信息边界。
4) 角色怎么说体现性格差异。
5) 禁止把同一句模板腔分配给所有角色。

====================
五、人物存在感规则
====================
1) 关键角色每次出场都要有可识别行为或可识别表达。
2) 不能说话的角色可用内心OS补充角色立场。
3) 任何角色连续长时间仅站着看且无功能 → 必须改写互动。

====================
六、输出格式（严格执行）
====================
【场景：地点｜时间（白天/夜晚）】
正文段落...

规则：
1) 只有场景变化时才写新的场景头。
2) 每个自然段都必须是一个完整可拍单元（有动作/对白/结果中的至少两项）。
3) 描述简洁但具体，避免空泛形容词堆砌。
4) 不使用像……宛如……等比喻词。

====================
七、结尾必须附加简报
====================
- 原著保真：列出未改动的关键事件点
- 影视化优化：列出本次做的3-5个有效优化点
- 逻辑保障：列出3处关键问答或衔接如何成立

====================
参考示例（必须参考此格式）
====================

【场景：拍卖会场｜夜晚】
拍卖师掀开红布。展台上的寒玉在射灯下泛着青白色。
林初雪站在后排第三列，手里攥着一张支票，指节发白。她看清寒玉后身体往前倾，嘴唇动了一下没出声。
拍卖师敲槌："千年寒玉，起拍一百万。"
前排男人举牌："一百五十万。"
左侧女宾客跟着举牌："两百万。"
林初雪把支票翻过来看背面数字，又翻回去，咬住下唇。

【场景：拍卖会场二楼包厢｜夜晚】
黑袍男人坐在栏后的椅子上，手指敲了两下扶手。
侍从俯身听令，转身推开纱帘，朝楼下喊："一千万。"

【场景：拍卖会场｜夜晚】
叫价声停住。
前排举牌的男人把号牌放下，转头看向二楼。
拍卖师握槌的手停在半空。
林初雪抬头盯着二楼纱帘，呼吸加快。
拍卖师回过神，举槌："一千万一次——"
林初雪冲到台前，手按在展台边缘："等等！"
拍卖师收回木槌，皱眉看她。台下有人站起来看热闹。
林初雪深吸一口气："这块玉是我母亲的遗物。"
拍卖师脸色一冷："小姐，拍卖会讲证据。你拿什么证明？"
林初雪把支票拍在台面上："我先不加价，我先证明它认我。"

【场景：拍卖会场二楼栏边｜夜晚】
包厢门打开，黑袍男人走到栏杆边，双手撑在栏杆上俯视她："可以。你证明。"

【场景：拍卖会场展台｜夜晚】
林初雪双手按在展台玻璃上，闭眼，肩膀绷紧。
她的呼吸放慢，手掌下的玻璃表面开始起雾。
雾气蔓延到展台四角，边缘凝出白霜。
寒玉内部亮起淡蓝光，一层层增强。
前排宾客往后退，椅子拖动声响成一片。
拍卖师手一松，木槌掉在地上。
林初雪睁眼，脸色发白，额头全是汗。她手撑着台面才站稳，抬头看向二楼："够不够？"

【场景：拍卖会场二楼栏边｜夜晚】
黑袍男人盯着寒玉看了三秒，直起身："认主现象成立。"
他转向林初雪："但拍卖流程已启动，规则不变。一千万，你继续出价。"

【场景：拍卖会场展台｜夜晚】
林初雪把支票推到拍卖师面前。
拍卖师低头看一眼，抬起头："五十万。"
台下有人笑出声，有人摇头。
林初雪抬头盯住二楼黑袍男人，声音发紧："你到底想要什么？"
黑袍男人转身往包厢里走，停在门口侧过头："明晚子时，城北废宅。你一个人来，寒玉的事继续谈。迟到作废。"
包厢门合上。
林初雪把支票收回袖子里，转身离开展台。

-----------------------------
【剧本简报】
原著保真：拍卖会见到母亲遗物寒玉、无力竞拍、神秘男人出天价压场、被迫当场证明认主、灵力觉醒引发异象、对方以规则压制并抛出约见条件。
影视化优化：心理描写改为手部动作；灵力觉醒具象化为起雾→结霜→发光递进视觉链；群体反应拆解为个体可拍动作；删除所有重复心理独白。
逻辑保障："你有证据"→"我先证明"形成挑战-应战；"够不够"→"认主成立"给出判定；"五十万被读出"→台下笑声形成群体反馈。

现在请按照以上规则和示例，将用户提供的小说原文改编为短剧剧本。
"""

PRESET_MODELS = [
    "gpt-5.3-codex-low",
    "claude-opus-4-7",
    "gemini-3.1-pro-preview",
    "deepseek-chat",
    "qwen3.6-27b",
    "自定义输入",
]


def call_api(api_key, base_url, model, user_content):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请将以下小说原文改编为短剧剧本：\n\n{user_content}"},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 8192,
    }
    url = base_url.rstrip("/") + "/chat/completions"
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
            except (json.JSONDecodeError, KeyError, IndexError):
                continue


# 侧边栏
with st.sidebar:
    st.markdown("## ⚙️ API 配置")
    st.markdown("---")

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxxxxx",
        help="输入您的 API 密钥"
    )

    base_url = st.text_input(
        "接口地址（Base URL）",
        value="https://yunwu.ai/v1/",
        help="默认使用云雾中转站，可替换为其他兼容接口"
    )

    st.markdown("##### Model ID")

    model_choice = st.selectbox(
        "选择模型",
        options=PRESET_MODELS,
        index=0,
        label_visibility="collapsed"
    )

    if model_choice == "自定义输入":
        custom_model = st.text_input(
            "自定义 Model ID",
            placeholder="例如：gpt-4o-2024-11-20",
        )
        model_id = custom_model.strip() if custom_model else ""
        if model_id:
            st.caption(f"当前模型：`{model_id}`")
        else:
            st.warning("请输入自定义 Model ID")
    else:
        model_id = model_choice
        st.caption(f"当前模型：`{model_id}`")

    st.markdown("---")
    st.markdown("##### 关于本工具")
    st.caption("本工具将小说原文按照专业短剧编剧规则自动转化为可拍摄剧本，适配任何 OpenAI 兼容接口。")


# 主界面
st.markdown('<div class="main-title">🎬 短剧剧本生成器</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">将小说原文一键转化为可拍摄的短剧剧本</div>', unsafe_allow_html=True)

input_method = st.radio(
    "选择输入方式",
    options=["📋 粘贴文本", "📁 上传文件"],
    horizontal=True,
    label_visibility="collapsed"
)

novel_text = ""

if input_method == "📋 粘贴文本":
    novel_text = st.text_area(
        "粘贴小说原文",
        height=280,
        placeholder="请在此处粘贴小说原文内容……\n\n支持任意长度，建议单次处理 500～3000 字以获得最佳效果。",
        label_visibility="collapsed"
    )
else:
    uploaded_file = st.file_uploader(
        "上传 TXT 文件",
        type=["txt"],
        label_visibility="collapsed",
        help="仅支持 .txt 格式"
    )
    if uploaded_file is not None:
        try:
            novel_text = uploaded_file.read().decode("utf-8")
            st.success(f"✅ 文件读取成功，共 {len(novel_text)} 字")
            with st.expander("预览文件内容（前 300 字）"):
                st.text(novel_text[:300] + ("……" if len(novel_text) > 300 else ""))
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                novel_text = uploaded_file.read().decode("gbk")
                st.success(f"✅ 文件读取成功（GBK 编码），共 {len(novel_text)} 字")
            except Exception as e:
                st.error(f"文件解码失败：{e}")

if novel_text:
    char_count = len(novel_text.strip())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("原文字数", f"{char_count:,} 字")
    with col2:
        st.metric("预计场景数", f"~{max(1, char_count // 300)} 场")
    with col3:
        st.metric("当前模型", model_id if model_id else "未选择")

st.markdown("---")

generate_btn = st.button("🚀 开始生成剧本", use_container_width=True)

if generate_btn:
    if not api_key.strip():
        st.error("⚠️ 请在左侧侧边栏填写 API Key。")
        st.stop()

    if not model_id:
        st.error("⚠️ 请选择或输入 Model ID。")
        st.stop()

    if not novel_text or not novel_text.strip():
        st.error("⚠️ 请先输入或上传小说原文内容。")
        st.stop()

    progress_bar = st.progress(0, text="正在连接 API……")
    status_placeholder = st.empty()
    output_placeholder = st.empty()

    full_output = ""
    start_time = time.time()

    try:
        progress_bar.progress(10, text="已连接，正在分析原著结构……")
        time.sleep(0.3)
        progress_bar.progress(20, text="正在提取事件链与人物性格锚点……")
        time.sleep(0.3)
        progress_bar.progress(35, text="正在进行场景重组与影视化转化……")

        token_count = 0
        for chunk_text in call_api(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            model=model_id.strip(),
            user_content=novel_text.strip(),
        ):
            full_output += chunk_text
            token_count += len(chunk_text)

            estimated_progress = min(35 + int(token_count / 50), 90)
            stage = "正在生成对白与场景描述……"
            if token_count > 1000:
                stage = "正在完善人物互动与动作细节……"
            if token_count > 2500:
                stage = "正在生成剧本简报……"
            progress_bar.progress(estimated_progress, text=stage)

            output_placeholder.markdown(
                f'<div class="output-box">{full_output}</div>',
                unsafe_allow_html=True
            )

        elapsed = round(time.time() - start_time, 1)
        progress_bar.progress(100, text=f"✅ 生成完成！用时 {elapsed} 秒")
        status_placeholder.success(f"剧本生成完毕，共输出 {len(full_output):,} 字，用时 {elapsed} 秒。")

        st.download_button(
            label="⬇️ 下载剧本（TXT）",
            data=full_output.encode("utf-8"),
            file_name="短剧剧本.txt",
            mime="text/plain",
            use_container_width=True,
        )

    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        st.error("❌ 无法连接到接口地址，请检查 Base URL 是否正确。")
    except requests.exceptions.HTTPError as e:
        progress_bar.empty()
        status_code = e.response.status_code if e.response else "未知"
        if status_code == 401:
            st.error("❌ API Key 无效或已过期。")
        elif status_code == 429:
            st.error("❌ 请求频率超限，请稍后重试。")
        elif status_code == 404:
            st.error(f"❌ 模型 `{model_id}` 不存在，请确认 Model ID 拼写正确。")
        else:
            st.error(f"❌ 接口返回错误 {status_code}：{e}")
    except requests.exceptions.Timeout:
        progress_bar.empty()
        st.error("❌ 请求超时（120秒），建议缩短原文长度后重试。")
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ 发生未知错误：{e}")
