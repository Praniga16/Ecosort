import os
import json
import numpy as np
from PIL import Image

# Import TensorFlow lazily or handle import errors gracefully
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "waste_classifier.keras")
META_PATH = os.path.join(BASE_DIR, "model", "model_meta.json")

# Classes in alphabetical order as formatted by Keras image_dataset_from_directory
CLASS_NAMES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

CLASS_METADATA = {
    "cardboard": {
        "name": "Cardboard",
        "category": "Recyclable",
        "icon": "📦",
        "advice": "Flatten clean cardboard and place it in the appropriate recycling bin."
    },
    "glass": {
        "name": "Glass",
        "category": "Recyclable",
        "icon": "🫙",
        "advice": "Rinse glass containers and place them in glass recycling where available."
    },
    "metal": {
        "name": "Metal",
        "category": "Recyclable",
        "icon": "🥫",
        "advice": "Empty and rinse metal cans before recycling."
    },
    "paper": {
        "name": "Paper",
        "category": "Recyclable",
        "icon": "📄",
        "advice": "Keep paper clean and dry before placing it in paper recycling."
    },
    "plastic": {
        "name": "Plastic",
        "category": "Recyclable",
        "icon": "🥤",
        "advice": "Clean the plastic item and place it in the appropriate plastic recycling bin."
    },
    "trash": {
        "name": "Trash",
        "category": "General Waste",
        "icon": "🗑️",
        "advice": "Dispose of the item as general waste when it cannot be recycled."
    }
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

_cached_model = None


def is_model_trained() -> bool:
    """Check if the trained model file exists on disk."""
    return os.path.exists(MODEL_PATH)


def get_model_metadata() -> dict:
    """Get metadata about the trained model if available."""
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "trained": is_model_trained(),
        "model_name": "MobileNetV2 Transfer Learning",
        "classes": CLASS_NAMES,
        "val_accuracy": None
    }


def load_classifier_model():
    """Load and cache the trained Keras model."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    if not is_model_trained():
        raise FileNotFoundError(
            "Model file not found at 'model/waste_classifier.keras'. "
            "Please train the model using train.py before making real predictions."
        )

    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow is not installed in the environment.")

    print(f"Loading MobileNetV2 waste classifier model from {MODEL_PATH}...")
    _cached_model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully!")
    return _cached_model


def validate_image_file(file_path: str):
    """Validate image file extension, size, and integrity."""
    if not os.path.exists(file_path):
        raise ValueError("Image file does not exist.")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Please upload a valid JPG, PNG, or WEBP image.")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds maximum limit of 10 MB.")

    try:
        with Image.open(file_path) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"Corrupted or unreadable image file: {str(e)}")


def preprocess_image(file_path: str) -> np.ndarray:
    """Load image, convert to RGB, resize to 224x224, and apply MobileNetV2 preprocessing."""
    try:
        img = Image.open(file_path).convert("RGB")
        img = img.resize((224, 224), Image.Resampling.BILINEAR)
        img_array = np.array(img, dtype=np.float32)
        img_batch = np.expand_dims(img_array, axis=0)

        if TF_AVAILABLE:
            processed_batch = tf.keras.applications.mobilenet_v2.preprocess_input(img_batch)
        else:
            # Fallback MobileNetV2 scaling [-1, 1] if TF module unavailable during standalone checks
            processed_batch = (img_batch / 127.5) - 1.0

        return processed_batch
    except Exception as e:
        raise ValueError(f"Failed to preprocess image: {str(e)}")


def predict_waste(file_path: str) -> dict:
    """
    Validates, preprocesses, and classifies an image using the MobileNetV2 waste classifier.
    Returns structured JSON dictionary with probabilities, advice, and confidence level.
    """

    # 1. Check if model is trained
    if not is_model_trained():
        return {
            "success": False,
            "error": "Model not trained yet. Train the model using train.py before making real predictions.",
            "model_loaded": False
        }

    # 2. Validate input image
    validate_image_file(file_path)

    # 3. Preprocess image
    img_batch = preprocess_image(file_path)

    # 4. Load model & Predict
    model = load_classifier_model()
    predictions = model.predict(img_batch, verbose=0)[0]

    # Convert predictions to float list and normalize
    raw_scores = [float(p) for p in predictions]
    sum_scores = sum(raw_scores) or 1.0
    normalized_scores = [p / sum_scores for p in raw_scores]

    # Map scores to class names
    class_probabilities = {}
    for idx, name in enumerate(CLASS_NAMES):
        percent = round(normalized_scores[idx] * 100.0, 1)
        class_probabilities[name] = percent

    # Sort probabilities descending
    sorted_scores = dict(sorted(class_probabilities.items(), key=lambda item: item[1], reverse=True))

    # Top class selection
    top_class = list(sorted_scores.keys())[0]
    top_confidence = sorted_scores[top_class]

    # Determine confidence level & message
    if top_confidence > 80.0:
        confidence_level = "High confidence"
        confidence_tip = None
    elif top_confidence >= 60.0:
        confidence_level = "Moderate confidence"
        confidence_tip = "Consider taking a closer photo for a higher confidence rating."
    else:
        confidence_level = "Low confidence"
        confidence_tip = "Try taking a clearer photo with better lighting and a simpler background."

    meta = CLASS_METADATA.get(top_class, CLASS_METADATA["trash"])

    result = {
        "success": True,
        "model_loaded": True,
        "class": top_class,
        "name": meta["name"],
        "category": meta["category"],
        "confidence": top_confidence,
        "confidence_level": confidence_level,
        "confidence_tip": confidence_tip,
        "advice": meta["advice"],
        "icon": meta["icon"],
        "scores": sorted_scores
    }

    return result
