import os
from dotenv import load_dotenv
from groq import Groq
from flask import Flask, request, jsonify, render_template_string

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
        textarea { width: 100%; height: 200px; background: #161b22; color: #e6edf3; border: 1px solid #30363d; padding: 10px; border-radius: 6px; font-size: 14px; }
        button { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 10px; font-size: 16px; }
        button:hover { background: #2ea043; }
        #result { margin-top: 20px; background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; white-space: pre-wrap; display: none; }
        #loading { display: none; color: #58a6ff; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>⚡ DebugAI</h1>
    <p>Paste your production error. Get root cause in seconds.</p>
    <textarea id="error" placeholder="Paste your error log here..."></textarea>
    <br>
    <button onclick="analyze()">Analyze Error</button>
    <p id="loading">Analyzing...</p>
    <div id="result"></div>
    <script>
        async function analyze() {
            const error = document.getElementById('error').value;
            if (!error.trim()) return;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ error: error })
            });
            const data = await response.json();
            document.getElementById('loading').style.display = 'none';
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerText = data.result;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    error_log = request.json.get('error', '')
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""You are a senior SRE with 10 years experience.

Analyze this production error and give:

1. ROOT CAUSE: One specific sentence.
2. AFFECTED SERVICE: Exact service name.
3. FIX: Exact code or command to run.
4. TIME TO FIX: Estimate in minutes.
5. PREVENTION: One thing to stop this happening again.

Error:
{error_log}"""
        }]
    )
    return jsonify({ "result": response.choices[0].message.content })

if __name__ == '__main__':
    app.run(debug=True, port=5000)