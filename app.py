from flask import Flask, render_template, request, redirect, url_for, make_response
from pathlib import Path
import json
import time
import jwt
import re
from typing import Tuple
import os
import dotenv

dotenv.load_dotenv()

# JWT_SECRET = secrets.token_urlsafe(64)  # In production, use a fixed secret stored securely
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGO = "HS256"
JWT_EXP_SECONDS = 7 * 24 * 3600  # 7 days

LEVELS_FILE = Path("levels.json")

app = Flask(__name__)

def validate_and_score_pattern(pattern: str, target_list: list, avoid_list: list) -> Tuple[bool, dict]:
    try:
        regex = re.compile(pattern)
    except re.error:
        return False, {"error": "invalid_regex"}

    results = {"targets": [], "avoids": [], "passed_targets": 0, "failed_avoids": 0}

    for t in target_list:
        matched = bool(regex.search(t))
        results["targets"].append({"text": t, "matched": matched})
        if matched:
            results["passed_targets"] += 1

    for a in avoid_list:
        matched = bool(regex.search(a))
        results["avoids"].append({"text": a, "matched": matched})
        if matched:
            results["failed_avoids"] += 1

    return True, results

def make_progress_token(max_level_unlocked: int):
    now = int(time.time())
    payload = {"max_level": int(max_level_unlocked), "iat": now, "exp": now + JWT_EXP_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def verify_progress_token_from_request():
    token = request.cookies.get("progress")
    if not token:
        return 0
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return int(data.get("max_level", 0))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return 0

def get_level(level_id):
    try:
        with LEVELS_FILE.open("r", encoding="utf-8") as f:
            levels = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return ([], [])
    for lvl in levels:
        try:
            if int(lvl.get("id")) == int(level_id):
                targets = lvl.get("target_list", [])
                avoids = lvl.get("avoid_list", [])
                description = lvl.get("description", "")
                hint = lvl.get("hint", "")
                return (list(map(str, targets)), list(map(str, avoids)), description, hint)
        except (TypeError, ValueError):
            continue
    return ([], [], "", "")
@app.route("/")
def index():
    return redirect(url_for('level', level_id=1))

@app.route("/<int:level_id>", methods=["GET", "POST"])
def level(level_id):
    if request.method == "GET":
        max_unlocked = verify_progress_token_from_request()
        allowed = max_unlocked + 1 if max_unlocked >= 0 else 1
        if level_id > allowed:
            return redirect(url_for("level", level_id=allowed if allowed >= 1 else 1))
        try:
            target_list, avoid_list, description, hint = get_level(level_id)
        except Exception as e:
            print(f"Error fetching level {level_id}: {e}")
            target_list, avoid_list, description, hint = get_level(1)
        return render_template("index.html", level_id=level_id, target_list=target_list, avoid_list=avoid_list, description=description, hint=hint)

    if request.method == "POST":
        try:
            current = int(request.form.get("level_id", 1))
        except (TypeError, ValueError):
            current = 1

        pattern = request.form.get("pattern", "")
        # simple length limit to reduce ReDoS risk
        if len(pattern) > 300:
            return redirect(url_for('level', level_id=current))

        target_list, avoid_list, description, hint = get_level(current)

        is_valid, score = validate_and_score_pattern(pattern, target_list, avoid_list)
        if not is_valid:
            return redirect(url_for('level', level_id=current))

        completed = (score["passed_targets"] == len(target_list)) and (score["failed_avoids"] == 0)
        # print(completed)
        # print(score)
        # print(target_list)
        # print("PATTERN REPR:", repr(pattern))
        # print("TARGETS REPR:", [repr(t) for t in target_list])
        # print("AVOIDS REPR:", [repr(a) for a in avoid_list])

        if not completed:
            return redirect(url_for('level', level_id=current))

        next_level = current + 1

        try:
            with LEVELS_FILE.open("r", encoding="utf-8") as f:
                levels = json.load(f)
            valid_ids = {int(l.get("id")) for l in levels if "id" in l}
        except Exception:
            valid_ids = set()

        if next_level not in valid_ids:
            next_level = 1

        old_max = verify_progress_token_from_request()
        unlocked_level = next_level
        new_max = max(old_max, unlocked_level)
        token = make_progress_token(new_max)

        resp = make_response(redirect(url_for('level', level_id=next_level)))
        secure=True # requires HTTPS; set True in production
        resp.set_cookie("progress", token, httponly=True, secure=False, samesite="Lax")
        return resp


if __name__ == "__main__":
    app.run()
