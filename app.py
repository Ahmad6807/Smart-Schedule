"""SmartSchedule - Web Application (Flask)."""
from flask import Flask, render_template, jsonify, request, send_file, abort
from smartschedule.models.course import Course, Section, SectionType, Day, SelectedCourse, WEEKDAYS
from smartschedule.models.preference import UserPreference, PreferenceType, ConstraintPriority
from smartschedule.models.schedule import Schedule, ScheduleEntry
from smartschedule.engine.solver import TimetableCSP, find_alternatives
from smartschedule.engine.optimizer import score_schedule
from smartschedule.engine.recommender import detect_clashes, suggest_resolutions
from smartschedule.utils.persistence import export_csv, import_csv
import json, csv, io, os, re, uuid
from dotenv import load_dotenv
from smartschedule.engine.ai_service import (
    extract_text_from_pdf,
    get_or_create_session,
    chat as ai_chat,
    extract_sections_from_response,
    reset_session,
)

# Load .env file
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# In-memory state
sections = {}  # section_id -> Section dict (serializable)
current_schedule = None

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")

def valid_times(start, end):
    """Times must be HH:MM and end strictly after start."""
    if not TIME_RE.match(start or "") or not TIME_RE.match(end or ""):
        return False
    def mins(t):
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    return mins(end) > mins(start)

def valid_day(day_str):
    try:
        return Day(day_str)
    except ValueError:
        return None

def unique_section_id(base_id):
    """Guarantee a fresh section_id (reloads / repeat imports must not overwrite)."""
    sid, n = base_id, 2
    while sid in sections:
        sid = f"{base_id}-{n}"
        n += 1
    return sid

def section_to_dict(s):
    return {
        "section_id": s.section_id,
        "course_code": s.course_code,
        "section_type": s.section_type.value,
        "instructor": s.instructor,
        "room": s.room,
        "days": [d.value for d in s.days],
        "start_time": s.start_time,
        "end_time": s.end_time,
    }

def dict_to_section(d):
    return Section(
        section_id=d["section_id"],
        course_code=d["course_code"],
        section_type=SectionType(d["section_type"]),
        instructor=d.get("instructor", ""),
        room=d.get("room", ""),
        days=[Day(day) for day in d["days"]],
        start_time=d["start_time"],
        end_time=d["end_time"],
    )

def schedule_to_dict(schedule):
    entries = []
    for e in schedule.entries:
        entries.append({
            "section_id": e.section.section_id,
            "course_code": e.section.course_code,
            "section_type": e.section.section_type.value,
            "instructor": e.section.instructor,
            "room": e.section.room,
            "day": e.day.value,
            "start_time": e.start_time,
            "end_time": e.end_time,
        })
    return {"entries": entries}

@app.route("/")
def index():
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/api/sections", methods=["GET"])
def get_sections():
    return jsonify({"sections": list(sections.values())})

@app.route("/api/sections", methods=["POST"])
def add_section():
    data = request.json
    if not valid_times(data.get("start_time"), data.get("end_time")):
        return jsonify({"error": "Invalid times: use HH:MM and make sure the end time is after the start time."}), 400
    section = Section(
        section_id=unique_section_id(data["section_id"]),
        course_code=data["course_code"],
        section_type=SectionType(data["section_type"]),
        instructor=data.get("instructor", ""),
        room=data.get("room", ""),
        days=[Day(d) for d in data["days"]],
        start_time=data["start_time"],
        end_time=data["end_time"],
    )
    sections[section.section_id] = section_to_dict(section)
    return jsonify({"ok": True, "section": section_to_dict(section)})

@app.route("/api/sections/<section_id>", methods=["DELETE"])
def delete_section(section_id):
    if section_id in sections:
        del sections[section_id]
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/sections/clear", methods=["POST"])
def clear_sections():
    sections.clear()
    return jsonify({"ok": True})

@app.route("/api/generate", methods=["POST"])
def generate():
    global current_schedule
    data = request.json
    prefs_data = data.get("preferences", [])
    section_dicts = list(sections.values())

    if not section_dicts:
        return jsonify({"error": "No sections added"}), 400

    # Build CSP
    all_sections = {s["section_id"]: dict_to_section(s) for s in section_dicts}
    course_codes = list(dict.fromkeys(s["course_code"] for s in section_dicts))
    selected_courses = []
    for code in course_codes:
        types = list(dict.fromkeys(SectionType(s["section_type"]) for s in section_dicts if s["course_code"] == code))
        selected_courses.append(SelectedCourse(course_code=code, required_section_types=types))

    # Build preferences
    preferences = []
    for p in prefs_data:
        preferences.append(UserPreference(
            preference_type=PreferenceType(p["type"]),
            value=p.get("value", ""),
            priority=ConstraintPriority(p.get("priority", "Medium")),
        ))

    csp = TimetableCSP(selected_courses, all_sections, preferences)
    schedule = csp.solve(time_limit=5.0)

    if schedule is None:
        return jsonify({"error": "No valid schedule found. Try removing some courses or relaxing constraints."}), 422

    current_schedule = schedule
    score = score_schedule(schedule, preferences)
    schedule_dict = schedule_to_dict(schedule)
    schedule_dict["score"] = round(score, 2)
    schedule_dict["total_hours"] = round(schedule.total_hours(), 1)

    return jsonify(schedule_dict)

@app.route("/api/export/csv", methods=["GET"])
def export_csv_route():
    if current_schedule is None:
        return jsonify({"error": "No schedule to export"}), 400
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Day", "Start Time", "End Time", "Course Code", "Section Type", "Section ID", "Room", "Instructor"])
    for entry in current_schedule.entries:
        writer.writerow([
            entry.day.value, entry.start_time, entry.end_time,
            entry.section.course_code, entry.section.section_type.value,
            entry.section.section_id, entry.section.room, entry.section.instructor,
        ])
    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="timetable.csv")

@app.route("/api/import/csv", methods=["POST"])
def import_csv_route():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    content = f.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    for row in reader:
        code = row.get("course_code", "").strip()
        day_str = row.get("day", "").strip()
        start = row.get("start_time", "").strip()
        end = row.get("end_time", "").strip()
        if not code or not day_str or not start or not end:
            continue
        if not valid_times(start, end):
            continue
        try:
            st = SectionType(row.get("section_type", "Lecture").strip())
        except ValueError:
            st = SectionType.LECTURE
        try:
            day = Day(day_str)
        except ValueError:
            day_map = {"mon": Day.MONDAY, "tue": Day.TUESDAY, "wed": Day.WEDNESDAY,
                       "thu": Day.THURSDAY, "fri": Day.FRIDAY, "sat": Day.SATURDAY}
            day = day_map.get(day_str.lower()[:3])
            if day is None:
                continue
        sec_id = unique_section_id(f"{code}-{st.value[:3].upper()}-{len(sections)+1:02d}")
        section = Section(
            section_id=sec_id, course_code=code, section_type=st,
            instructor=row.get("instructor", "").strip(),
            room=row.get("room", "").strip(),
            days=[day], start_time=start, end_time=end,
        )
        sections[sec_id] = section_to_dict(section)
        imported += 1
    return jsonify({"ok": True, "imported": imported})

@app.route("/api/upload-pdf", methods=["POST"])
def upload_pdf():
    f = request.files.get("file")
    if f is None or not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file."}), 400
    path = os.path.join(app.config["UPLOAD_FOLDER"], uuid.uuid4().hex + ".pdf")
    f.save(path)
    try:
        pdf_text = extract_text_from_pdf(path)
    except Exception:
        return jsonify({"error": "Could not read that PDF."}), 400
    session_id = "session-" + uuid.uuid4().hex
    messages = get_or_create_session(session_id, pdf_text)
    summary = (
        "PDF received (" + str(len(pdf_text)) + " characters extracted). AI is not configured: "
        "add OPENAI_API_KEY to your .env file and reload to enable course extraction."
    )
    try:
        summary = ai_chat(messages, "Briefly summarize the courses and sections found in this document.")
    except ValueError:
        pass  # no API key: keep the friendly fallback summary
    except Exception:
        return jsonify({"error": "AI service error while summarizing."}), 502
    return jsonify({"ok": True, "session_id": session_id,
                    "pdf_text_length": len(pdf_text), "summary": summary})

@app.route("/api/chat", methods=["POST"])
def chat_route():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is empty."}), 400
    session_id = data.get("session_id") or "session-" + uuid.uuid4().hex
    messages = get_or_create_session(session_id)
    try:
        reply = ai_chat(messages, message)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "AI request failed. Check your API key and connection."}), 502

    # Insert any course sections the AI proposed (validated like every other path)
    sections_added = 0
    for s in extract_sections_from_response(reply):
        if not isinstance(s, dict):
            continue
        code = str(s.get("course_code", "")).strip().upper()
        start = str(s.get("start_time", "")).strip()
        end = str(s.get("end_time", "")).strip()
        days = [valid_day(str(d).strip()) for d in (s.get("days") or [])]
        days = [d for d in days if d is not None]
        if not code or not days or not valid_times(start, end):
            continue
        try:
            st = SectionType(str(s.get("section_type", "Lecture")).strip())
        except ValueError:
            st = SectionType.LECTURE
        sec = Section(
            section_id=unique_section_id(f"{code}-{st.value[:3].upper()}-{uuid.uuid4().hex[:4].upper()}"),
            course_code=code, section_type=st,
            instructor=str(s.get("instructor", "")).strip(),
            room=str(s.get("room", "")).strip(),
            days=days, start_time=start, end_time=end,
        )
        sections[sec.section_id] = section_to_dict(sec)
        sections_added += 1
    return jsonify({"ok": True, "reply": reply, "sections_added": sections_added})

@app.route("/api/schedule", methods=["GET"])
def get_schedule():
    if current_schedule is None:
        return jsonify({"entries": []})
    return jsonify(schedule_to_dict(current_schedule))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
