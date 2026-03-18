import os
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

SYSTEM_PROMPT = """
You are an expert HR and Diversity, Equity, Inclusion, and Belonging (DEIB) consultant for True Belonging LLC.
Your job is to analyze Job Descriptions (JDs) for unconscious bias, exclusionary language, and aggressive corporate jargon 
(e.g., 'ninja', 'rockstar', 'digital native', 'brotherhood', 'aggressive').

The user will provide a job description. 
Please return a JSON block containing EXACTLY two keys:
1. "score": An integer from 0 to 100 representing how inclusive the text is (100 = perfect).
2. "rewritten": A fully rewritten, inclusive, and professional version of the job description.

Make sure the output can be parsed by Python's `json.loads()`. DO NOT wrap it in markdown codeblocks like ```json ... ```. Just return raw JSON.
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.get_json() or request.form
    jd_text = data.get("job_description", "").strip()

    if not jd_text:
        return jsonify({"error": "No job description provided."}), 400
        
    if not model:
        # Fallback if API key is not set
        return jsonify({
            "score": 45,
            "rewritten": "This is a placeholder rewritten inclusive version. (Gemini API Key missing on server)."
        })

    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nJob Description:\n{jd_text}")
        result_text = response.text.strip()
        
        # Clean up any unexpected markdown formatting
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        parsed = json.loads(result_text.strip())
        
        return jsonify({
            "score": parsed.get("score", 50),
            "rewritten": parsed.get("rewritten", "Error generating rewrite.")
        })
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return jsonify({"error": "Failed to generate optimized description."}), 502

# Required for Railway deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
