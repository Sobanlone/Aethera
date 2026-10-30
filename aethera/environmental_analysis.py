from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from aethera.knowledge_base import EnvironmentalKnowledgeBase


class EnvironmentalAnalyzer:
    def __init__(self, knowledge_base: EnvironmentalKnowledgeBase | None = None):
        self.knowledge_base = knowledge_base or EnvironmentalKnowledgeBase()

    def parse_env_issue(self, description: str) -> Dict[str, Any]:
        text = description.lower()
        issue_keywords = {
            "illegal_dumping": ["dumping", "dump", "garbage", "trash", "waste", "discard", "fly tipping", "illegal dumping", "rubbish", "tires", "vacant lot"],
            "deforestation": ["deforestation", "tree cut", "trees cut", "tree removal", "trees removed", "logging", "cleared forest", "cut down", "forest cleared", "forest clearing", "clearing forest", "cutting trees"],
            "water_pollution": ["pond", "river", "lake", "stream", "canal", "water pollution", "polluted water", "contaminated water", "water is dirty", "sewage", "runoff", "algae blooms", "cloudy water", "dead fish", "floating rubbish", "plastic waste", "oil spill", "contaminated", "waste and chemicals", "chemical runoff"],
            "habitat_destruction": ["habitat", "wildlife", "animals disappearing", "nest destroyed", "nests destroyed", "nesting area", "animal habitat", "habitat damaged", "wetland", "marsh", "ecosystem damage", "destroyed nests", "fragmented habitat"],
            "biodiversity_loss": ["biodiversity", "species", "animal", "bird", "plant decline", "wildlife decline", "species decline", "fewer frogs", "fewer reptiles", "bird numbers", "species diversity", "animals are avoiding", "declining biodiversity"],
            "air_pollution": ["smoke", "burning", "fire", "fumes", "air quality", "emissions", "smell", "odour", "haze", "visible haze", "air pollution"],
        }

        category = "general_environmental_concern"
        confidence = 0.55

        if any(token in text for token in ["dumping", "dump", "garbage", "trash", "rubbish", "tires", "vacant lot", "illegal dumping", "fly tipping"]) and any(token in text for token in ["dump", "garbage", "trash", "rubbish", "waste", "tires", "vacant lot", "dumping"]) and any(token in text for token in ["forest", "river", "near"]) and not any(token in text for token in ["cut", "logging", "clearing", "tree"]) and not any(token in text for token in ["wetland", "marsh", "habitat", "wildlife"]):
            category = "illegal_dumping"
            confidence = 0.8
        elif any(token in text for token in ["bird", "species", "biodiversity", "frog", "reptile"]) and any(token in text for token in ["fewer", "declining", "falling", "reducing", "disappearing", "diversity"]) and not any(token in text for token in ["wetland", "marsh", "habitat", "wildlife"]):
            category = "biodiversity_loss"
            confidence = 0.75
        elif any(token in text for token in ["forest", "trees", "cut down", "clearing", "logging", "deforestation"]) and any(token in text for token in ["tree", "trees", "forest", "logging", "cut", "clearing", "removed"]):
            category = "deforestation"
            confidence = 0.8
        elif any(token in text for token in ["river", "pond", "lake", "stream", "canal", "water"]) and any(token in text for token in ["waste", "rubbish", "trash", "pollution", "sewage", "chemical", "foam", "algae", "runoff", "contaminated", "smell", "blooms", "floating"]) and not any(token in text for token in ["dumping", "garbage", "trash", "rubbish", "tires", "vacant lot"]):
            category = "water_pollution"
            confidence = 0.8
        elif any(token in text for token in ["nest", "habitat", "wildlife", "marsh", "wetland"]) and any(token in text for token in ["destroyed", "damaged", "fragmented", "declining", "avoiding", "stressed", "fewer"]):
            category = "habitat_destruction"
            confidence = 0.75
        elif any(token in text for token in ["smoke", "fumes", "haze", "odor", "smell", "air pollution"]) and any(token in text for token in ["burning", "emissions", "visible", "bad", "quality"]):
            category = "air_pollution"
            confidence = 0.75
        else:
            best_score = 0
            matched_key = category
            for key, keywords in issue_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > best_score:
                    best_score = score
                    matched_key = key
            if matched_key != "general_environmental_concern":
                category = matched_key
                confidence = 0.8

        if any(word in text for word in ["unknown", "not sure", "maybe", "unclear"]):
            confidence = max(0.45, confidence - 0.15)

        summary = f"Likely environmental concern: {category.replace('_', ' ')}"
        explanation = (
            "This issue appears to involve environmental degradation or biodiversity stress. "
            "The assessment is based on the user description and should be treated as a preliminary evaluation, not a confirmed legal or scientific finding."
        )

        follow_up_questions = [
            "What is the approximate location or area involved?",
            "When did you first notice the issue, and how often is it occurring?",
            "Do you have photos, videos, or other evidence that can help document the concern?",
            "Are there any signs of immediate risk to people, wildlife, or water sources?",
        ]

        impacts = {
            "illegal_dumping": ["soil and water contamination", "harm to wildlife", "reduced neighbourhood cleanliness"],
            "deforestation": ["loss of habitat", "increased erosion", "reduced carbon storage"],
            "water_pollution": ["damage to aquatic species", "poor water quality", "ecosystem imbalance"],
            "habitat_destruction": ["loss of shelter for animals", "declining biodiversity", "increased human-wildlife conflict"],
            "biodiversity_loss": ["species decline", "disrupted food webs", "reduced ecosystem resilience"],
            "air_pollution": ["respiratory harm", "lower air quality", "ecosystem stress"],
            "general_environmental_concern": ["ecosystem stress", "public health concerns", "reduced environmental resilience"],
        }

        next_steps = {
            "illegal_dumping": [
                "Avoid direct contact with waste materials or suspicious chemicals.",
                "Document the site with photos and notes while keeping a safe distance.",
                "Report the issue to the relevant local authority or waste-management office if appropriate."
            ],
            "deforestation": [
                "Document the affected area with timestamped photos.",
                "Identify whether any protected or sensitive habitats are nearby.",
                "Consult local environmental or forestry officials for guidance."
            ],
            "water_pollution": [
                "Avoid entering or touching the water if it may be contaminated.",
                "Note any visible signs such as foam, odour, algae, or waste.",
                "Contact local water or environmental authorities for site assessment."
            ],
            "habitat_destruction": [
                "Record the location and signs of habitat damage.",
                "Avoid disturbing wildlife or entering unsafe areas.",
                "Seek advice from local conservation organisations or environmental officers."
            ],
            "biodiversity_loss": [
                "Document species observations and habitat changes over time.",
                "Assess whether there are pressures such as noise, pollution, or encroachment.",
                "Consult a conservation expert or local ecological group."
            ],
            "air_pollution": [
                "Avoid exposure to smoke, fumes, or suspicious emissions.",
                "Record the source, timing, and any visible pollutants.",
                "Report the concern to local environmental or public health authorities if needed."
            ],
            "general_environmental_concern": [
                "Gather more factual details before drawing conclusions.",
                "Document what you observed, including time, place, and visible materials.",
                "Seek professional environmental guidance if the situation involves hazards or wildlife."
            ],
        }

        structured = {
            "category": category,
            "confidence": round(confidence, 2),
            "summary": summary,
            "explanation": explanation,
            "follow_up_questions": follow_up_questions,
            "possible_impacts": impacts.get(category, impacts["general_environmental_concern"]),
            "suggested_next_steps": next_steps.get(category, next_steps["general_environmental_concern"]),
            "observed_facts": [
                "Issue description was provided by the user.",
                "Classification is preliminary and may require additional information."
            ],
            "unverified_info": [
                "The exact cause, legal status, and scale of the issue are not confirmed.",
                "Any conclusions should be validated with local evidence and professional guidance."
            ],
        }

        return structured

    def build_report_prompt(self, description: str) -> str:
        analysis = self.parse_env_issue(description)
        basis = "\n".join([f"- {item}" for item in analysis["observed_facts"]])
        return (
            "You are an environmental assistant.\n"
            f"Analyse this environmental issue: {description}\n\n"
            f"Likely category: {analysis['category']}\n"
            f"Confidence: {analysis['confidence']}\n"
            f"Observed facts:\n{basis}\n\n"
            "Return a JSON object with keys: category, confidence, summary, explanation, follow_up_questions, possible_impacts, suggested_next_steps, observed_facts, unverified_info.\n"
            "Use clear English, keep each list concise, and avoid fabricating facts."
        )

    def retrieve_knowledge(self, query: str):
        return self.knowledge_base.retrieve(query)

    def validate_json(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("AI output must be a JSON object.")
        required = ["category", "summary", "explanation", "follow_up_questions", "possible_impacts", "suggested_next_steps", "observed_facts", "unverified_info"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")
        return data

    def extract_structured_analysis(self, raw_text: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in AI output.")
        parsed = json.loads(match.group(0))
        return self.validate_json(parsed)
