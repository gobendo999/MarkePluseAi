import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class MarketIntelligenceAIService:
    """
    Topic 46: Google Gemini AI Market Intelligence Service
    Generates structured market analysis, pros/cons, sentiment score, 
    and a smart Price Verdict (Buy / Wait) based on historical price drops.
    """

    @classmethod
    def generate_product_insights(cls, product) -> dict:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"success": False, "error": "GEMINI_API_KEY is not configured."}

        # ১. প্রোডাক্টের দামের ইতিহাস ও স্ট্যাটস সংগ্রহ
        history = product.price_history.all()
        history_summary = []
        for h in history[:5]:
            history_summary.append(f"{h.price} {h.currency} recorded at {h.recorded_at.strftime('%Y-%m-%d')}")

        # ২. জেমিনির জন্য প্রম্পট প্রস্তুত করা
        prompt = f"""
You are an expert E-Commerce Market Intelligence and Pricing Analyst.
Analyze the following tracked product and give a structured purchasing verdict:

Product Title: {product.title}
Store / Marketplace: {product.store_name}
Current Live Price: {product.current_price} {product.currency}
Target Price: {product.target_price or 'None'}
Stock Status: {product.stock_status}
Historical Price Changes: {', '.join(history_summary) if history_summary else 'Only initial price recorded'}

Please respond ONLY with a valid JSON object matching this exact schema:
{{
  "summary": "Short 2-sentence executive summary of the product quality and market positioning.",
  "pros": ["Key advantage 1", "Key advantage 2", "Key advantage 3"],
  "cons": ["Potential drawback or common complaint 1", "Drawback 2"],
  "sentiment_score": 85,
  "price_verdict": "STRONG_BUY",
  "verdict_reason": "Explain why the buyer should buy now or wait, referencing historical price drops."
}}
Valid values for price_verdict: "STRONG_BUY", "FAIR_PRICE", "WAIT_FOR_DROP".
"""

        try:
            client = genai.Client(api_key=api_key)
            models_to_try = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
            last_error = None
            response = None

            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                    if response and response.text:
                        break
                except Exception as model_err:
                    last_error = model_err
                    logger.warning(f"Model {model_name} failed with {model_err}, trying fallback...")
                    continue

            if not response or not response.text:
                raise last_error or Exception("All Gemini models failed to generate content.")

            result_json = json.loads(response.text)
            return {
                "success": True,
                "data": result_json
            }
        except Exception as e:
            logger.error(f"Gemini AI error for Product {product.id}: {e}")
            return {"success": False, "error": f"AI Generation failed: {str(e)}"}
