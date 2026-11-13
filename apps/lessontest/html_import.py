"""HTML fayl ichidagi `const QUESTIONS = [...]` massivini xavfsiz o'qish.

Hech qanday JavaScript kodi ishga tushirilmaydi — faqat matn ustida ishlaydi:
massiv qavslari muvozanati bo'yicha ajratib olinadi, so'ng JS obyekt
literali JSON formatiga aylantirilib, standart `json.loads` bilan o'qiladi.
"""

import json
import re


class HTMLImportError(ValueError):
    pass


def _extract_questions_literal(html_text: str) -> str:
    match = re.search(r"QUESTIONS\s*=\s*", html_text)
    if not match:
        raise HTMLImportError("Fayl ichida QUESTIONS massivi topilmadi.")

    try:
        start = html_text.index("[", match.end())
    except ValueError:
        raise HTMLImportError("QUESTIONS massivi boshlanishi ([) topilmadi.")

    depth = 0
    in_string = False
    quote_char = ""
    i = start
    n = len(html_text)
    while i < n:
        ch = html_text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == quote_char:
                in_string = False
        else:
            if ch in ("'", '"', "`"):
                in_string = True
                quote_char = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return html_text[start:i + 1]
        i += 1

    raise HTMLImportError("QUESTIONS massivi to'liq yopilmagan.")


def _js_array_to_json(js_array: str) -> str:
    # `{q: ...` / `, a: ...` ko'rinishidagi tirnoqsiz kalitlarni tirnoqqa oladi.
    quoted = re.sub(r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', js_array)
    # JS massiv/obyektlarda ruxsat etilgan ortiqcha vergulni olib tashlaydi.
    return re.sub(r',\s*([}\]])', r'\1', quoted)


def parse_questions_from_html(html_text: str) -> list[dict]:
    """Qaytaradi: [{"text", "options": [...], "correct_index", "explanation"}, ...]"""

    literal = _extract_questions_literal(html_text)
    json_text = _js_array_to_json(literal)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise HTMLImportError(f"QUESTIONS massivini o'qib bo'lmadi: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise HTMLImportError("QUESTIONS massivi bo'sh yoki noto'g'ri formatda.")

    questions = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise HTMLImportError(f"{idx}-savol noto'g'ri formatda.")

        text = item.get("q")
        options = item.get("o")
        correct_index = item.get("a")
        explanation = item.get("e") or ""

        if not isinstance(text, str) or not text.strip():
            raise HTMLImportError(f"{idx}-savolda matn (q) yo'q.")
        if not isinstance(options, list) or len(options) < 2:
            raise HTMLImportError(f"{idx}-savolda kamida 2 ta variant (o) bo'lishi kerak.")
        if not all(isinstance(o, str) and o.strip() for o in options):
            raise HTMLImportError(f"{idx}-savoldagi variantlar matn bo'lishi kerak.")
        if isinstance(correct_index, bool) or not isinstance(correct_index, int) or not (0 <= correct_index < len(options)):
            raise HTMLImportError(f"{idx}-savolda to'g'ri javob indeksi (a) noto'g'ri.")
        if not isinstance(explanation, str):
            raise HTMLImportError(f"{idx}-savoldagi tushuntirish (e) matn bo'lishi kerak.")

        questions.append({
            "text": text.strip(),
            "options": [o.strip() for o in options],
            "correct_index": correct_index,
            "explanation": explanation.strip(),
        })

    return questions
