import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=ANALYSIS_PROMPT + job_description
        )
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        analysis = json.loads(raw_text)
        return jsonify(analysis)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return jsonify({"error": "Failed to analyze Job Description"}), 500

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session for $1 unlock."""
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Inclusive JD Optimizer — Full Rewrite Unlock',
                        'description': 'AI-powered inclusive job description rewrite by True Belonging LLC',
                    },
                    'unit_amount': 100,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + '?payment=success&session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + '?payment=cancelled',
        )
        return jsonify({'checkout_url': session.url})
    except Exception as e:
        print(f"Stripe error: {e}")
        return jsonify({"error": "Payment session creation failed"}), 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    """Verify Stripe payment and release optimized text."""
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        data = request.json
        session_id = data.get('session_id')
        optimized_text = data.get('optimized_text', '')
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            return jsonify({"success": True, "optimized_text": optimized_text})
        return jsonify({"success": False}), 402
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "Inclusive JD Optimizer", "powered_by": "True Belonging LLC"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
