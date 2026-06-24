import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_error(error_log):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
{
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
                }
            
        ]
    )
    return response.choices[0].message.content

print("DebugAI - Production Error Analyzer")
print("=" * 40)
print("Paste your error log below.")
print("Press Enter twice when done.")
print("=" * 40)

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

error_log = "\n".join(lines)

if error_log.strip():
    print("\nAnalyzing...")
    print("=" * 40)
    print(analyze_error(error_log))
else:
    print("No error provided.")