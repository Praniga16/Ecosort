import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from predict import predict_waste, is_model_trained, get_model_metadata, ALLOWED_EXTENSIONS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "predictions.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB Max Upload Limit


def load_history() -> list:
    """Load prediction history from predictions.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def save_history(history_data: list):
    """Save prediction history to predictions.json."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")


def calculate_stats(history: list) -> dict:
    """Calculate summary statistics and breakdown from prediction history."""
    total_scans = len(history)
    if total_scans == 0:
        return {
            "total_scans": 0,
            "recyclable_count": 0,
            "general_waste_count": 0,
            "avg_confidence": 0.0,
            "recyclable_percent": 0.0,
            "category_counts": {
                "cardboard": 0, "glass": 0, "metal": 0, "paper": 0, "plastic": 0, "trash": 0
            },
            "confidence_breakdown": {"high": 0, "moderate": 0, "low": 0}
        }

    recyclable_count = sum(1 for item in history if item.get("category") == "Recyclable")
    general_waste_count = total_scans - recyclable_count
    total_conf = sum(item.get("confidence", 0.0) for item in history)
    avg_conf = round(total_conf / total_scans, 1) if total_scans > 0 else 0.0
    recyclable_pct = round((recyclable_count / total_scans) * 100.0, 1) if total_scans > 0 else 0.0

    category_counts = {
        "cardboard": 0, "glass": 0, "metal": 0, "paper": 0, "plastic": 0, "trash": 0
    }
    for item in history:
        cls = item.get("class", "").lower()
        if cls in category_counts:
            category_counts[cls] += 1

    high_conf = sum(1 for item in history if item.get("confidence", 0) >= 80.0)
    mod_conf = sum(1 for item in history if 60.0 <= item.get("confidence", 0) < 80.0)
    low_conf = sum(1 for item in history if item.get("confidence", 0) < 60.0)

    return {
        "total_scans": total_scans,
        "recyclable_count": recyclable_count,
        "general_waste_count": general_waste_count,
        "avg_confidence": avg_conf,
        "recyclable_percent": recyclable_pct,
        "category_counts": category_counts,
        "confidence_breakdown": {
            "high": high_conf,
            "moderate": mod_conf,
            "low": low_conf
        }
    }


# ==================== PAGE ROUTES ====================

@app.route("/")
def index():
    """Dashboard & Waste Scanner page."""
    meta = get_model_metadata()
    history = load_history()
    stats = calculate_stats(history)
    return render_template("index.html", meta=meta, stats=stats)


@app.route("/history")
def history_page():
    """Prediction history page."""
    history = load_history()
    return render_template("history.html", history=history)


@app.route("/analytics")
def analytics_page():
    """Analytics dashboard page."""
    history = load_history()
    stats = calculate_stats(history)
    meta = get_model_metadata()
    return render_template("analytics.html", stats=stats, meta=meta)


@app.route("/about")
def about_page():
    """About & Project Explanation page."""
    meta = get_model_metadata()
    return render_template("about.html", meta=meta)


# ==================== API ENDPOINTS ====================

@app.route("/predict", methods=["POST"])
def predict():
    """Predict waste category from uploaded image file."""
    if 'image' not in request.files:
        return jsonify({
            "success": False,
            "error": "No image file provided in request."
        }), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No selected file."
        }), 400

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False,
            "error": "Please upload a valid JPG, PNG, or WEBP image."
        }), 400

    try:
        # Generate unique filename using UUID to prevent collisions & security risks
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{ext}"
        saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(saved_path)

        # Run waste prediction model
        result = predict_waste(saved_path)

        if not result.get("success", False):
            # Model missing or error occurred
            return jsonify(result), 200

        # Build history record
        web_filepath = f"/static/uploads/{filename}"
        record = {
            "id": unique_id,
            "filename": secure_filename(file.filename),
            "filepath": web_filepath,
            "class": result["class"],
            "name": result["name"],
            "category": result["category"],
            "confidence": result["confidence"],
            "confidence_level": result["confidence_level"],
            "confidence_tip": result.get("confidence_tip"),
            "icon": result["icon"],
            "advice": result["advice"],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scores": result["scores"]
        }

        # Save to predictions.json
        history = load_history()
        history.insert(0, record)  # Insert at top
        save_history(history)

        result["filepath"] = web_filepath
        result["record_id"] = unique_id
        return jsonify(result), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": str(ve)
        }), 400
    except Exception as e:
        print(f"Backend Prediction Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An internal error occurred while processing the image. Please try again."
        }), 500


@app.route("/api/history", methods=["GET"])
def get_history_api():
    """Returns JSON list of past predictions."""
    history = load_history()
    return jsonify({"success": True, "history": history})


@app.route("/api/history/clear", methods=["POST"])
def clear_history_api():
    """Clears all prediction history."""
    save_history([])
    return jsonify({"success": True, "message": "Prediction history cleared successfully."})


@app.route("/api/stats", methods=["GET"])
def get_stats_api():
    """Returns real-time analytics statistics."""
    history = load_history()
    stats = calculate_stats(history)
    meta = get_model_metadata()
    return jsonify({"success": True, "stats": stats, "meta": meta})


@app.route("/api/system-status", methods=["GET"])
def get_system_status():
    """Returns model status and metadata."""
    meta = get_model_metadata()
    return jsonify({
        "success": True,
        "model_trained": is_model_trained(),
        "meta": meta
    })


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        "success": False,
        "error": "File size exceeds the 10 MB limit. Please upload a smaller image."
    }), 413


if __name__ == "__main__":
    model_status = "Online" if is_model_trained() else "Model Not Trained Yet"
    print("==================================================")
    print(" ECO SORT AI — REAL-TIME WASTE SEGREGATION SYSTEM")
    print(f" Status: {model_status}")
    print(" Server: http://127.0.0.1:5000")
    print("==================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
