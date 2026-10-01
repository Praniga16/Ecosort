import os
import sys
import json
import numpy as np
from PIL import Image

try:
    import tensorflow as tf
except ImportError:
    print("Error: TensorFlow is required. Run: pip install tensorflow")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "waste_classifier.keras")
CLASS_MAPPING_PATH = os.path.join(BASE_DIR, "model", "class_names.json")
DATASET_DIR = os.path.join(BASE_DIR, "dataset-resized")
if not os.path.exists(DATASET_DIR) or len(os.listdir(DATASET_DIR)) == 0:
    DATASET_DIR = os.path.join(BASE_DIR, "dataset")


def load_class_mapping():
    """Load class mapping JSON."""
    if not os.path.exists(CLASS_MAPPING_PATH):
        print(f"[ERROR] Class mapping file not found at {CLASS_MAPPING_PATH}")
        sys.exit(1)
    with open(CLASS_MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    # Return list of class names ordered by integer key
    return [mapping[str(i)] for i in range(len(mapping))]


def run_evaluation():
    print("========================================")
    print("ECOSORT AI — MODEL EVALUATION UTILITY")
    print("========================================\n")

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Trained model file not found at {MODEL_PATH}")
        print("Please train the model first by running: python train.py")
        sys.exit(1)

    class_names = load_class_mapping()
    print(f"Loaded {len(class_names)} classes: {class_names}")

    print("Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully.\n")

    total_tested = 0
    total_correct = 0

    print("Testing sample images per class:")
    print("-" * 60)

    for class_name in class_names:
        c_folder = os.path.join(DATASET_DIR, class_name)
        if not os.path.exists(c_folder):
            continue

        files = [f for f in os.listdir(c_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if not files:
            continue

        # Test first 5 images per class
        samples = files[:5]

        for fname in samples:
            fpath = os.path.join(c_folder, fname)
            try:
                img = Image.open(fpath).convert("RGB").resize((224, 224))
                arr = np.array(img, dtype=np.float32)
                batch = np.expand_dims(arr, axis=0)  # Raw 0..255 float array, preprocess_input is inside model

                preds = model.predict(batch, verbose=0)[0]
                pred_idx = np.argmax(preds)
                pred_class = class_names[pred_idx]
                confidence = float(preds[pred_idx]) * 100.0

                is_correct = (pred_class.lower() == class_name.lower())
                total_tested += 1
                if is_correct:
                    total_correct += 1

                status_str = "✓ Correct" if is_correct else "✗ Incorrect"
                print(f"Image: {fname.ljust(20)} | Actual: {class_name.ljust(10)} | Pred: {pred_class.ljust(10)} | Conf: {confidence:6.2f}% | {status_str}")

            except Exception as e:
                print(f"Error testing {fname}: {e}")

    if total_tested > 0:
        overall_acc = (total_correct / total_tested) * 100.0
        print("-" * 60)
        print(f"\nSample Evaluation Results: {total_correct}/{total_tested} correct")
        print(f"Test Accuracy: {overall_acc:.2f}%\n")
    else:
        print("[WARNING] No test images found to evaluate.")


if __name__ == "__main__":
    run_evaluation()
