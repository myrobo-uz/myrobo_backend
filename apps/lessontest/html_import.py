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

    if not isinstance(data, list):
        raise HTMLImportError("QUESTIONS massivi noto'g'ri formatda.")

    # Har bir savol mazmuni tekshirilmaydi — nima kelsa, shu holicha (eng yaqin
    # mos keladigan ko'rinishda) saqlanadi; noto'g'ri/yetishmayotgan qiymatlar
    # xatolik chiqarish o'rniga bo'sh/standart qiymat bilan almashtiriladi.
    questions = []
    for item in data:
        if not isinstance(item, dict):
            item = {}

        text = item.get("q")
        text = text if isinstance(text, str) else ("" if text is None else str(text))

        options = item.get("o")
        options = options if isinstance(options, list) else []
        options = [o if isinstance(o, str) else str(o) for o in options]

        correct_index = item.get("a")
        if isinstance(correct_index, bool) or not isinstance(correct_index, int) or not (0 <= correct_index < len(options)):
            correct_index = -1

        explanation = item.get("e")
        explanation = explanation if isinstance(explanation, str) else ("" if explanation is None else str(explanation))

        questions.append({
            "text": text.strip(),
            "options": [o.strip() for o in options],
            "correct_index": correct_index,
            "explanation": explanation.strip(),
        })

    return questions
