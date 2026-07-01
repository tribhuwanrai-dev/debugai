import os
import requests
from dotenv import load_dotenv
from groq import Groq
from flask import Flask, request, jsonify, render_template_string
import re 

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DebugAI</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }
        .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 24px; display: flex; align-items: center; gap: 10px; }
        .header h1 { font-size: 20px; color: #58a6ff; }
        .container { max-width: 860px; margin: 32px auto; padding: 0 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
        label { font-size: 13px; color: #8b949e; display: block; margin-bottom: 6px; }
        input, textarea { width: 100%; background: #0d1117; color: #e6edf3; border: 1px solid #30363d; padding: 10px 12px; border-radius: 6px; font-size: 14px; margin-bottom: 14px; outline: none; }
        input:focus, textarea:focus { border-color: #58a6ff; }
        textarea { height: 120px; resize: vertical; }
        .note { font-size: 11px; color: #6e7681; margin-top: -10px; margin-bottom: 14px; }
        button { background: #238636; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 500; width: 100%; }
        button:hover { background: #2ea043; }
        button:disabled { background: #21262d; color: #8b949e; cursor: not-allowed; }
        .loading { text-align: center; color: #58a6ff; padding: 20px; display: none; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid #30363d; border-top-color: #58a6ff; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
        @keyframes spin { to { transform: rotate(360deg); } }
        #results { margin-top: 20px; }
        .result-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 12px; }
        .result-card h2 { font-size: 15px; color: #e6edf3; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #30363d; }
        .result-card p { font-size: 14px; line-height: 1.6; color: #c9d1d9; margin-bottom: 8px; }
        .result-card code { background: #0d1117; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #79c0ff; }
        .result-card pre { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin: 8px 0; overflow-x: auto; }
        .result-card pre code { background: none; padding: 0; color: #e6edf3; }
        .result-card strong { color: #e6edf3; }
        .result-card ul, .result-card ol { padding-left: 20px; margin: 8px 0; }
        .result-card li { margin-bottom: 4px; color: #c9d1d9; font-size: 14px; line-height: 1.6; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-left: 8px; }
        .badge-high { background: #3d1a1a; color: #f85149; }
        .badge-medium { background: #2d2a1a; color: #e3b341; }
        .badge-minor { background: #1a2d1a; color: #3fb950; }
        .summary-bar { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 14px 20px; margin-bottom: 16px; display: flex; gap: 20px; align-items: center; }
        .summary-bar span { font-size: 13px; color: #8b949e; }
        .summary-bar strong { color: #e6edf3; }
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size:22px">⚡</span>
        <h1>DebugAI</h1>
        <span style="color:#8b949e; font-size:13px; margin-left:8px">AI-powered code analysis</span>
    </div>

    <div class="container">
        <div class="card">
            <label>GitHub Repo URL <span style="color:#f85149">*</span></label>
            <input id="repo" placeholder="https://github.com/username/repo" />

            <label>GitHub Token <span style="color:#6e7681">(only for private repos)</span></label>
            <input id="token" type="password" placeholder="ghp_xxxxxxxxxxxx" />
            <p class="note">Your token goes directly to GitHub — never stored on our servers.</p>

            <label>Error Log <span style="color:#6e7681">(optional — helps focus the analysis)</span></label>
            <textarea id="error" placeholder="Paste any error message here..."></textarea>

            <button id="btn" onclick="analyze()">🔍 Analyze Code</button>
        </div>

        <div class="loading" id="loading">
            <span class="spinner"></span> Fetching code and analyzing...
        </div>

        <div id="results"></div>
    </div>

    <script>
        async function analyze() {
            const repo = document.getElementById('repo').value.trim();
            const token = document.getElementById('token').value.trim();
            const error = document.getElementById('error').value.trim();

            if (!repo) { alert('Please enter a GitHub repo URL'); return; }

            document.getElementById('btn').disabled = true;
            document.getElementById('btn').textContent = 'Analyzing...';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo, token, error })
                });

                const data = await response.json();
                document.getElementById('loading').style.display = 'none';

                if (data.error) {
                    document.getElementById('results').innerHTML = 
                        '<div class="result-card"><p style="color:#f85149">⚠️ ' + data.error + '</p></div>';
                } else {
                    renderResults(data.result);
                }
            } catch(e) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('results').innerHTML = 
                    '<div class="result-card"><p style="color:#f85149">⚠️ Something went wrong. Try again.</p></div>';
            }

            document.getElementById('btn').disabled = false;
            document.getElementById('btn').textContent = '🔍 Analyze Code';
        }

        function getBadge(text) {
            const lower = text.toLowerCase();
            if (lower.includes('important') || lower.includes('high')) 
                return '<span class="badge badge-high">🔴 Important</span>';
            if (lower.includes('medium')) 
                return '<span class="badge badge-medium">🟡 Medium</span>';
            return '<span class="badge badge-minor">🟢 Minor</span>';
        }

        function renderResults(text) {
            const container = document.getElementById('results');
            
            const sections = text.split(/(?=🔴|(?:##\s*\d+\s*-))/g).filter(s => s.trim());
            
            if (sections.length <= 1) {
                container.innerHTML = '<div class="result-card">' + marked.parse(text) + '</div>';
                return;
            }

            let html = '<div class="summary-bar"><span>Found <strong>' + (sections.length) + ' issues</strong> in your code</span></div>';
            
            sections.forEach((section, i) => {
                const badge = getBadge(section);
                html += '<div class="result-card"><h2>Issue ' + (i+1) + ' ' + badge + '</h2>' + marked.parse(section) + '</div>';
            });

            container.innerHTML = html;
        }
    </script>
</body>
</html>
"""



def fetch_repo_code(repo_url, token=""):
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        headers = {}
        if token:
            headers['Authorization'] = f'token {token}'

        api_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
        response = requests.get(api_url, headers=headers)

        if response.status_code == 401:
            return "", "Private repo — please provide a GitHub token."
        if response.status_code == 404:
            return "", "Repo not found. Check the URL."

        files = response.json()
        code_context = ""

        for file in files:
            if file.get('type') == 'file' and file['name'].endswith(('.js', '.py', '.ts', '.java', '.go')):
                file_response = requests.get(file['download_url'], headers=headers)
                content = file_response.text[:3000]
                code_context += f"\n--- {file['name']} ---\n{content}\n"

        return code_context, ""
    except Exception as e:
        return "", f"Error fetching repo: {str(e)}"

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    repo_url = data.get('repo', '').strip()
    token = data.get('token', '').strip()
    error_log = data.get('error', '').strip()

    if not repo_url:
        return jsonify({"error": "Please provide a GitHub repo URL."})

    code_context, fetch_error = fetch_repo_code(repo_url, token)

    if fetch_error:
        return jsonify({"error": fetch_error})

    if not code_context:
        return jsonify({"error": "No supported code files found in repo."})

    prompt = f"""You are a helpful coding teacher explaining bugs to a beginner.

Look at this code and find problems. For each problem explain it like this:

🔴 Problem [number] - [one word: Important / Medium / Minor]

What's wrong: Explain in simple words what the mistake is.
Where it is: Tell the exact line number and function name.
What happens: Explain what goes wrong for the user because of this.
How to fix it: Show the exact corrected code.
Time to fix: How many minutes this takes.

Use very simple language. No technical jargon. 
Imagine you are explaining to someone who just started coding.
Be friendly and encouraging."""


    if error_log:
        prompt += f"\n\nThis error was also reported — use it to focus your analysis:\n{error_log}"

    prompt += f"\n\nActual codebase:\n{code_context}"

    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}]
    )

    
    result = response.choices[0].message.content
    result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
    return jsonify({"result": result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)