"""Generate source-grounded study materials, or clearly labeled offline study extracts."""
import asyncio
import json
import math
import re
from pydantic import BaseModel, Field, ConfigDict
from app.services.language import resolve_language
from app.services.study_ai import TEXT, gemini_json, extract_keywords, source_fragments, fold, verify_citations, validate_output_language


class Citation(BaseModel):
    page: int = Field(ge=1)
    text: str = Field(min_length=12, max_length=6000)


class Lesson(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    short_summary: str = Field(min_length=10, max_length=3000)
    long_explanation: str = Field(min_length=10, max_length=10000)
    key_ideas: list[str] = Field(min_length=1, max_length=8)
    practical_insights: list[str] = Field(default_factory=list, max_length=6)
    examples: list[str] = Field(default_factory=list, max_length=6)
    action_items: list[str] = Field(default_factory=list, max_length=6)
    source_citations: list[Citation] = Field(min_length=1, max_length=8)
    mermaid_diagram: str = ""
    duration: str = ""
    order_index: int = 1


class Level(BaseModel):
    level_number: int = Field(ge=1, le=10)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(max_length=2000)
    lessons: list[Lesson] = Field(min_length=1, max_length=12)


class Card(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    answer: str = Field(min_length=5, max_length=3000)
    category: str = Field(max_length=100)
    source_citations: list[Citation] = Field(min_length=1, max_length=4)


class Quiz(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=5, max_length=3000)
    source_citations: list[Citation] = Field(min_length=1, max_length=4)


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=1, max_length=250)
    subtitle: str = Field(max_length=500)
    overview: str = Field(min_length=10, max_length=5000)
    target_audience: str = Field(max_length=500)
    estimated_duration: str = Field(max_length=100)
    levels: list[Level] = Field(min_length=1, max_length=3)
    flashcards: list[Card] = Field(default_factory=list, max_length=24)
    quizzes: list[Quiz] = Field(default_factory=list, max_length=16)


def build_content_aware_curriculum(book_title, author, extracted_text, language=None, source_pages=None,
                                   study_minutes=20, depth="standard", focus_keywords=None):
    language = resolve_language(extracted_text, language)["language"]
    labels = TEXT[language]
    pages = source_pages or [{"page": 1, "text": extracted_text}]
    fragments = list(source_fragments(pages))
    if not fragments:
        fragments = [{"page": pages[0]["page"], "text": extracted_text.strip()}]
    keywords = extract_keywords(extracted_text)
    focus = [fold(value) for value in (focus_keywords or [])]
    if focus:
        relevant = [fragment for fragment in fragments if any(term in fold(fragment["text"]) for term in focus)]
        if relevant:
            fragments = relevant
    budget = max(1, min(12, math.ceil(study_minutes / 5)))
    amount = {"brief": 1, "standard": 3, "deep": 6}.get(depth, 3)
    # Choose excerpts throughout the source instead of pretending a fixed sample covers an entire book.
    chunks = [fragments[i:i + amount] for i in range(0, len(fragments), amount)]
    if len(chunks) > budget:
        chunks = [chunks[round(index * (len(chunks) - 1) / max(1, budget - 1))] for index in range(budget)]
    lessons, cards, quizzes = [], [], []
    for index, chunk in enumerate(chunks):
        excerpts = [item["text"] for item in chunk]
        topic = extract_keywords(" ".join(excerpts), 1)
        lesson_title = topic[0].capitalize() if topic else f'{labels["concept"]} {index + 1}'
        lessons.append({
            "order_index": index + 1, "title": lesson_title, "short_summary": excerpts[0],
            "long_explanation": labels["extractive"] + "\n\n" + labels["step"] + "\n\n" + "\n\n".join(excerpts),
            "key_ideas": excerpts, "practical_insights": [], "examples": [],
            "action_items": [labels["check"]], "mermaid_diagram": "", "source_citations": chunk,
            "duration": f'{max(1, math.ceil(study_minutes / len(chunks)))} {labels["minutes"]}',
        })
        for excerpt in chunk[:2]:
            terms = extract_keywords(excerpt["text"], 4)
            if not terms or len(excerpt["text"].split()) < 6:
                continue
            term = terms[0]
            cards.append({"question": labels["card"].format(term=term), "answer": excerpt["text"], "category": labels["concept"], "source_citations": [excerpt]})
            alternatives = [word for word in keywords if fold(word) != fold(term)][:3]
            if len(alternatives) >= 2:
                # Cloze options all come from the source; no invented factual answers or distractor claims.
                masked = re.sub(re.escape(term), "_____", excerpt["text"], count=1, flags=re.IGNORECASE)
                correct_index = len(quizzes) % (len(alternatives) + 1)
                options = alternatives[:]
                options.insert(correct_index, term)
                quizzes.append({"question": labels["quiz"] + "\n" + masked, "options": options,
                                "correct_index": correct_index, "explanation": excerpt["text"], "source_citations": [excerpt]})
    return {"title": f'{labels["course"]}: {book_title}', "subtitle": labels["subtitle"], "overview": labels["overview"],
            "target_audience": labels["audience"], "estimated_duration": f'{study_minutes} {labels["minutes"]}',
            "levels": [{"level_number": 1, "title": labels["level"], "description": labels["extractive"], "lessons": lessons}],
            "flashcards": cards[:24], "quizzes": quizzes[:16], "keywords": keywords,
            "language": language, "generation_mode": "extractive"}


async def analyze_book_with_gemini(book_title, author, extracted_text, language=None, source_pages=None,
                                 study_minutes=20, depth="standard", focus_keywords=None):
    language = (await asyncio.to_thread(resolve_language, extracted_text, language))["language"]
    pages = source_pages or [{"page": 1, "text": extracted_text}]
    data = None
    if len(extracted_text) <= 100000:
        data = await gemini_json(
            "Create a focused study course in the document language. Respect the study time, depth and selected keywords. "
            "Use only document facts, patient teacher explanations, retrieval questions and source-based quizzes. "
            "Do not claim to cover the complete document if the study time is short. Return JSON matching this schema: " + json.dumps(Curriculum.model_json_schema()),
            {"title": book_title, "author": author, "source_pages": pages, "study_minutes": study_minutes, "depth": depth, "focus_keywords": focus_keywords or []}, language,
        )
    if isinstance(data, dict):
        try:
            result = Curriculum.model_validate(data).model_dump()
            items = [lesson for level in result["levels"] for lesson in level["lessons"]] + result["flashcards"] + result["quizzes"]
            for item in items:
                item["source_citations"] = verify_citations(item["source_citations"], pages)
                fields = [value for field, value in item.items() if isinstance(value, str) and field not in {"mermaid_diagram", "duration"}]
                fields += [value for field in ["key_ideas", "practical_insights", "examples", "action_items", "options"] for value in item.get(field, [])]
                validate_output_language(" ".join(fields), language)
                for value in fields:
                    if len(value.split()) >= 18:
                        validate_output_language(value, language)
                if "correct_index" in item and item["correct_index"] >= len(item["options"]):
                    raise ValueError("Invalid quiz index")
                # Render no provider-authored executable diagram syntax in the MVP.
                if "mermaid_diagram" in item:
                    item["mermaid_diagram"] = ""
            validate_output_language(" ".join(result[field] for field in ["title", "subtitle", "overview", "target_audience"]), language)
            # Exact citations establish provenance, not entailment of free-form model prose.
            # Rebuild factual bodies and practice from the verified excerpts selected by the AI.
            selected = [citation for level in result["levels"] for lesson in level["lessons"] for citation in lesson["source_citations"]]
            grounded = await asyncio.to_thread(build_content_aware_curriculum, book_title, author, extracted_text,
                                               language, selected, study_minutes, depth, focus_keywords)
            grounded.update(generation_mode="ai_grounded", generation_detail="ai_selected_source_extracts")
            return grounded
        except (ValueError, TypeError, KeyError):
            pass
    return await asyncio.to_thread(build_content_aware_curriculum, book_title, author, extracted_text, language, pages, study_minutes, depth, focus_keywords)
