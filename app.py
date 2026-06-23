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
                "content": f"""You are a production debugging expert.

Analyze this error and provide:
1. Root cause (1-2 sentences)
2. Which service is affected
3. Specific fix

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