<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>漫剧AI智能分镜系统</title>
    <style>
        body { font-family: sans-serif; background: #f4f7f6; padding: 20px; color: #333; }
        .container { max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .config-section, .input-section { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #28a745; color: white; border: none; padding: 12px 25px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #218838; }
        #output { white-space: pre-wrap; background: #272822; color: #f8f8f2; padding: 20px; border-radius: 4px; margin-top: 20px; min-height: 200px; }
        .loading { color: #007bff; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎬 漫剧AI智能分镜系统</h2>
        
        <!-- 配置项 -->
        <div class="config-section">
            <label>API 接口地址</label>
            <input type="text" id="apiUrl" value="https://blog.tuiwen.xyz/v1/chat/completions">
            
            <label>API Key</label>
            <input type="password" id="apiKey" placeholder="输入你的 API Key">
            
            <label>选择模型名称 (Model ID)</label>
            <select id="modelId">
                <option value="deepseek-chat">DeepSeek-V3</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="claude-3-5-sonnet-20240620">Claude-3.5-Sonnet</option>
                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                <option value="doubao-pro-128k">豆包 Pro</option>
            </select>
        </div>

        <!-- 输入项 -->
        <div class="input-section">
            <label>1. 上传文案文本 (.txt)</label>
            <input type="file" id="fileInput" accept=".txt">
            
            <label>2. 人物设定 (描述角色外观、着装)</label>
            <textarea id="characterInfo" rows="4" placeholder="例如：赵清月：清冷美人，银丝蝴蝶簪，白色绫罗纱衣..."></textarea>
            
            <button onclick="processScript()">开始分析生成分镜</button>
            <span id="loadingMsg" class="loading">正在处理中，请稍候...</span>
        </div>

        <!-- 输出展示 -->
        <label>生成结果</label>
        <div id="output">解析后的分镜将显示在这里...</div>
    </div>

    <script>
        let uploadedText = "";

        // 读取文件内容
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                uploadedText = e.target.result;
            };
            reader.readAsText(file);
        });

        async function processScript() {
            const apiUrl = document.getElementById('apiUrl').value;
            const apiKey = document.getElementById('apiKey').value;
            const modelId = document.getElementById('modelId').value;
            const charInfo = document.getElementById('characterInfo').value;
            const outputDiv = document.getElementById('output');
            const loadingMsg = document.getElementById('loadingMsg');

            if (!uploadedText || !apiKey) {
                alert("请先上传文件并输入API Key");
                return;
            }

            loadingMsg.style.display = "inline";
            outputDiv.innerText = "AI 正在深度推理文案并生成提示词...";

            // 系统提示词逻辑 (将在第二部分详细说明)
            const systemPrompt = `你是一个专业的漫剧导演和Midjourney提示词专家。
任务：将用户上传的文案进行二次分镜。
严格要求：
1. 字符限制：每个分镜的文案不能超过35个字。如果超过，必须拆分为多个分镜。
2. 结构一致：严禁修改原文文字。
3. 画面描述：描述场景、环境、人物外观（严格调用用户提供的人物设定）、灯光、视角（特写/中景/全景）。
4. 视频生成：描述画面中的动态行为、镜头推拉摇移、神态变化。
5. 比例：9:16。`;

            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: modelId,
                        messages: [
                            { role: "system", content: systemPrompt },
                            { role: "user", content: `人物设定：\n${charInfo}\n\n待处理文案：\n${uploadedText}` }
                        ],
                        temperature: 0.7
                    })
                });

                const data = await response.json();
                outputDiv.innerText = data.choices[0].message.content;
            } catch (error) {
                outputDiv.innerText = "发生错误: " + error.message;
            } finally {
                loadingMsg.style.display = "none";
            }
        }
    </script>
</body>
</html>
