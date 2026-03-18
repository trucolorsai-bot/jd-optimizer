import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Internal prompt to analyze the Job Description
ANALYSIS_PROMPT = """
You are an expert in Diversity, Equity, Inclusion, and Belonging (DEIB). 
Analyze the following Job Description. Your task is to:
1. Identify any non-inclusive, aggressively gendered, or biased words (e.g., "ninja", "aggressive", "digital native", "he/him" defaults).
2. Rewrite the text to be completely inclusive and welcoming to all underrepresented groups.

Return ONLY a valid JSON object with the following structure:
{
    "biased_words_found": ["word1", "word2"],
    "bias_score": "out of 100 (100 being perfectly inclusive, 0 being highly biased)",
    "optimized_text": "The completely rewritten, inclusive job description."
}

Job Description:
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    job_description = data.get('job_description', '')

    if not job_description:
        return jsonify({"error": "No Job Description provided"}), 400

    try:
        # Call Gemini to analyze and rewrite
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=ANALYSIS_PROMPT + job_description
        )
        
        # Clean the response to ensure it's pure JSON
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        analysis = json.loads(raw_text)

        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return jsonify({"error": "Failed to analyze Job Description"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
