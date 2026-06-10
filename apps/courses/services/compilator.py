
from django.conf import settings

TIME_LIMITS = {
    "Python3": 3000,
    "Cpp": 2000,
    "CSharp": 2000,
    "Java": 4000,
}

import os
import tempfile
from pathlib import Path

import requests
import re
def slugify_title(title):
    title = title.lower().strip()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[\s_-]+', '_', title)
    return title

def get_problem_id(task) -> str:
    return f"task_{slugify_title(task.title)}"


COMPILATOR_URL = getattr(settings, "COMPILATOR_URL", "http://compilator:8080")
LANGUAGE_MAP = {
    "python3": {
        "compiler_lang": "python3",
        "ext": ".py",
    },
    "cpp": {
        "compiler_lang": "cpp",
        "ext": ".cpp",
    },
    "c": {
        "compiler_lang": "c",
        "ext": ".c",
    },
    "java": {
        "compiler_lang": "java",
        "ext": ".java",
    },
}


def judge_submission(task, code: str, language: str) -> dict:
    lang_info = LANGUAGE_MAP.get(language.lower())

    if not lang_info:
        return {
            "status": "error",
            "message": f"Unsupported language: {language}",
        }

    problem_id = get_problem_id(task)

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=lang_info["ext"],
            delete=False,
            encoding="utf-8",
        ) as tmp:

            tmp.write(code)
            tmp_path = tmp.name

        data = {
            "problem": problem_id,
            "language": lang_info["compiler_lang"],
            "timeLimitMs": TIME_LIMITS.get(language.lower(), 2000),
            "memoryLimitMb": 256,
        }

        with open(tmp_path, "rb") as f:
            files = {
                "file": (
                    Path(tmp_path).name,
                    f,
                )
            }

            response = requests.post(
                f"{COMPILATOR_URL}/api/judge/submit",
                data=data,
                files=files,
                timeout=60,
            )

        response.raise_for_status()

        return response.json()

    except requests.Timeout:
        return {
            "status": "error",
            "message": "Compilator timeout",
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)