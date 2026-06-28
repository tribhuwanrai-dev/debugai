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
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #0d1117; color: #e6edf3; }
        h1 { color: #58a6ff; }
        input, textarea { width: 100%; background: #161b22; color: #e6edf3; border: 1px solid #30363d; padding: 10px; border-radius: 6px; font-size: 14px; margin-bottom: 10px; }
        textarea { height: 150px; }
        label { font-size: 13px; color: #8b949e; display: block; margin-bottom: 4px; }
        .note { font-size: 11px; color: #6e7681; margin-bottom: 10px; }
        button { background: #238636; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 15px; }
        button:hover { background: #2ea043; }
        #result { margin-top: 20px; background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; white-space: pre-wrap; display: none; line-height: 1.6; }
        #loading { display: none; color: #58a6ff; margin-top: 10px; }
        .divider { border-top: 1px solid #30363d; margin: 16px 0; }
    </style>
</head>
<body>
    <h1>⚡ DebugAI</h1>
    <p>Connect your GitHub repo for real diagnosis. Paste an error for deeper context.</p>

    <label>GitHub repo URL <span style="color:#f85149">*</span></label>
    <input id="repo" placeholder="https://github.com/username/repo" />

    <label>GitHub token <span style="color:#6e7681">(only needed for private repos)</span></label>
    <input id="token" type="password" placeholder="ghp_xxxxxxxxxxxx" />
    <p class="note">Your token is sent directly to GitHub and never stored on our servers.</p>

    <div class="divider"></div>

    <label>Error log <span style="color:#6e7681">(optional — adds more context)</span></label>
    <textarea id="error" placeholder="Paste your error log here for even more specific analysis..."></textarea>

    <button onclick="analyze()">Analyze Repo</button>
    <p id="loading">Fetching code and analyzing...</p>
    <div id="result"></div>

    <script>
        async function analyze() {
            const repo = document.getElementById('repo').value.trim();
            const token = document.getElementById('token').value.trim();
            const error = document.getElementById('error').value.trim();

            if (!repo) {
                alert('Please enter a GitHub repo URL');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';

            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo, token, error })
            });

            const data = await response.json();
            document.getElementById('loading').style.display = 'none';
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerText = data.result || data.error;
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

    prompt = f"""You are a senior software engineer doing a production code review.

Analyze this codebase and identify:
1. BUGS: Real bugs that would cause production failures
2. ROOT CAUSE: Why each bug would fail
3. AFFECTED FUNCTION: Exact function/line where it breaks
4. FIX: Exact corrected code
5. SEVERITY: High/Medium/Low

Be specific to this actual code. No generic advice."""

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
    app.run(debug=True, port=5001)