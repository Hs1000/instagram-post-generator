
import os
import re

_generator = None
MAX_WORDS = 150
MIN_HASHTAGS = 5
MAX_HASHTAGS = 10
STOP_WORDS = {
    "a",
    "an",
    "and",
    "the",
    "for",
    "to",
    "of",
    "in",
    "on",
    "with",
    "at",
    "by",
    "from",
}
SHORT_KEEPERS = {"ai", "ml", "vr", "ar", "ux", "ui"}


def _get_generator():
    """Lazily build the model pipeline so app import cannot crash."""
    global _generator
    # Default to fallback mode; opt in to local model with ENABLE_LOCAL_MODEL=1.
    if os.getenv("ENABLE_LOCAL_MODEL", "0") != "1":
        return None
    if _generator is None:
        from transformers import pipeline

        # Newer transformers builds expose text-generation in this environment.
        _generator = pipeline("text-generation", model="google/flan-t5-large")
    return _generator


def _topic_keywords(topic: str):
    words = re.findall(r"[a-zA-Z0-9]+", topic.lower())
    filtered = [w for w in words if w not in STOP_WORDS and (len(w) > 2 or w in SHORT_KEEPERS)]
    return filtered or ["topic"]


def _tagify(term: str):
    return "#" + "".join(part.capitalize() for part in re.findall(r"[a-zA-Z0-9]+", term) if part)


def _pick_variant(options, topic: str, tone: str, salt: str):
    key = f"{topic}|{tone}|{salt}".lower()
    index = sum(ord(ch) for ch in key) % len(options)
    return options[index]


def _topic_based_hashtags(topic: str):
    keywords = _topic_keywords(topic)
    topic_compound = _tagify(" ".join(keywords))
    tags = [topic_compound]

    for k in keywords[:3]:
        tags.append(_tagify(k))

    context_map = {
        "ai": ["#ArtificialIntelligence", "#MachineLearning", "#FutureTech"],
        "healthcare": ["#HealthcareInnovation", "#DigitalHealth", "#MedTech"],
        "fitness": ["#FitnessJourney", "#HealthyLifestyle", "#WorkoutMotivation"],
        "travel": ["#TravelGoals", "#Wanderlust", "#AdventureTime"],
        "food": ["#Foodie", "#FoodLovers", "#InstaFood"],
        "fashion": ["#StyleInspo", "#FashionDaily", "#OOTD"],
        "finance": ["#FinancialLiteracy", "#MoneyTips", "#Investing"],
        "education": ["#LearningEveryday", "#EdTech", "#StudyMotivation"],
        "business": ["#BusinessGrowth", "#EntrepreneurLife", "#StartupLife"],
    }

    joined = " ".join(keywords)
    for key, extra_tags in context_map.items():
        if key in joined:
            tags.extend(extra_tags)

    tags.extend(["#ContentCreator", "#InstagramPost", "#DailyUpdate"])
    return tags


def _fallback_caption(topic, tone):
    tone_key = str(tone).lower()
    keywords = _topic_keywords(topic)
    keyword_text = ", ".join(keywords[:3])

    openers = [
        f"New thoughts on {topic}.",
        f"A quick breakdown on {topic}.",
        f"Spending time today exploring {topic}.",
        f"Fresh perspective from my notes on {topic}.",
    ]
    insights = {
        "professional": [
            "The biggest opportunity right now is practical implementation, not just theory.",
            "Results usually improve when teams focus on measurable outcomes and consistent iteration.",
            "Clear process and communication are what turn ideas into execution.",
        ],
        "motivational": [
            "Progress starts with one small step and compounds faster than expected.",
            "Consistency beats intensity when the goal is long-term growth.",
            "Most breakthroughs come after staying patient through the messy middle.",
        ],
        "friendly": [
            "One thing I find useful is keeping it simple and testing what actually works.",
            "If you are getting started, start small and stay curious.",
            "This topic gets easier when you focus on one practical action at a time.",
        ],
        "casual": [
            "Not overthinking it, just sharing what seems genuinely helpful.",
            "Still learning, but this approach has been working well lately.",
            "Simple note for today: practical beats perfect almost every time.",
        ],
        "default": [
            "The practical angle matters most when turning ideas into outcomes.",
            "Small improvements in process can create outsized long-term impact.",
            "A focused approach usually gives better results than doing everything at once.",
        ],
    }
    ctas = {
        "professional": [
            "Curious how your team is approaching this this quarter.",
            "Would love to hear what strategy has worked best for you.",
            "What metric would you prioritize first here?",
        ],
        "motivational": [
            "Save this as a reminder and take one action today.",
            "If this resonates, share your next step below.",
            "What is one commitment you can make this week?",
        ],
        "friendly": [
            "If you have tried this, share your experience below.",
            "Tell me which part you want me to cover next.",
            "Drop your thoughts, always happy to learn from your take.",
        ],
        "casual": [
            "Let me know if you want a part 2 on this.",
            "Open to ideas, what would you add?",
            "What are you experimenting with lately?",
        ],
        "default": [
            "What has worked best for you so far?",
            "Would love to hear your take in the comments.",
            "Let me know what angle you want next.",
        ],
    }

    opener = _pick_variant(openers, topic, tone_key, "opener")
    insight = _pick_variant(insights.get(tone_key, insights["default"]), topic, tone_key, "insight")
    cta = _pick_variant(ctas.get(tone_key, ctas["default"]), topic, tone_key, "cta")
    hashtags = _normalize_hashtags([], topic)
    return (
        f"{opener} Focus areas: {keyword_text}. {insight} {cta}"
        f"\n\n{' '.join(hashtags)}"
    )


def _extract_hashtags(text: str):
    return re.findall(r"#\w+", text)


def _normalize_hashtags(hashtags, topic):
    cleaned = []
    seen = set()
    for tag in hashtags:
        normalized = "#" + re.sub(r"[^a-zA-Z0-9_]", "", tag.lstrip("#"))
        if len(normalized) <= 1:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        cleaned.append(normalized)
        seen.add(lowered)

    defaults = _topic_based_hashtags(topic)
    for tag in defaults:
        lowered = tag.lower()
        if lowered not in seen and len(cleaned) < MAX_HASHTAGS:
            cleaned.append(tag)
            seen.add(lowered)

    if len(cleaned) < MIN_HASHTAGS:
        filler = ["#Community", "#Inspiration", "#GrowthMindset", "#LearnAndGrow"]
        for tag in filler:
            lowered = tag.lower()
            if lowered not in seen and len(cleaned) < MIN_HASHTAGS:
                cleaned.append(tag)
                seen.add(lowered)

    return cleaned[:MAX_HASHTAGS]


def _normalize_caption(raw_text: str, topic: str):
    hashtags = _normalize_hashtags(_extract_hashtags(raw_text), topic)
    text_without_tags = re.sub(r"#\w+", "", raw_text).strip()
    words = text_without_tags.split()
    trimmed_caption = " ".join(words[:MAX_WORDS]).strip()
    if not trimmed_caption:
        trimmed_caption = f"Sharing a quick update about {topic}."
    return {
        "caption": trimmed_caption,
        "hashtags": hashtags,
        "word_count": len(trimmed_caption.split()),
        "full_text": f"{trimmed_caption}\n\n{' '.join(hashtags)}",
    }


def generate_caption_data(topic, tone):
    prompt = (
        f"Write an Instagram caption about {topic} in a {tone} tone. "
        "Keep it within 150 words. Include 5 to 10 relevant hashtags at the end."
    )
    try:
        generator = _get_generator()
        if generator is None:
            raw_text = _fallback_caption(topic, tone)
            return _normalize_caption(raw_text, topic)
        result = generator(prompt, max_length=220, num_return_sequences=1)
        normalized = _normalize_caption(result[0]["generated_text"], topic)
        if len(normalized["hashtags"]) < MIN_HASHTAGS:
            normalized["hashtags"] = _normalize_hashtags(normalized["hashtags"], topic)
            normalized["full_text"] = f"{normalized['caption']}\n\n{' '.join(normalized['hashtags'])}"
        return normalized
    except Exception:
        # Keep API functional even when local model/runtime dependencies are missing.
        raw_text = _fallback_caption(topic, tone)
        return _normalize_caption(raw_text, topic)


def generate_caption(topic, tone):
    return generate_caption_data(topic, tone)["full_text"]
