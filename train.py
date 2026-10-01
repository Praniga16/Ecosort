import os
import sys
import json
import time
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from PIL import Image

try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
except ImportError:
    print("Error: TensorFlow is required to run train.py. Install it via 'pip install tensorflow'.")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "waste_classifier.keras")
META_PATH = os.path.join(MODEL_DIR, "model_meta.json")

CLASS_NAMES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 15
FINE_TUNE_EPOCHS = 10


def validate_dataset():
    """Verify dataset directory and count valid images per class."""
    print("Validating dataset structure...")
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR, exist_ok=True)

    counts = {}
    total_images = 0

    for class_name in CLASS_NAMES:
        class_folder = os.path.join(DATASET_DIR, class_name)
        if not os.path.exists(class_folder):
            os.makedirs(class_folder, exist_ok=True)

        valid_count = 0
        corrupted_count = 0

        files = os.listdir(class_folder)
        for fname in files:
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                fpath = os.path.join(class_folder, fname)
                try:
                    with Image.open(fpath) as img:
                        img.verify()
                        valid_count += 1
                except Exception:
                    corrupted_count += 1

        counts[class_name] = valid_count
        total_images += valid_count

        display_name = class_name.capitalize()
        print(f"  {display_name}: {valid_count} images" + (f" ({corrupted_count} corrupted skipped)" if corrupted_count > 0 else ""))

    if total_images == 0:
        print("\n[WARNING] Dataset is empty!")
        print("Please place the TrashNet images inside the dataset/ subfolders:")
        for c in CLASS_NAMES:
            print(f"  - dataset/{c}/")
        print("\nGenerating temporary synthetic sample dataset to allow model training demonstration...")
        generate_synthetic_dataset()
        return validate_dataset()

    return counts, total_images


def generate_synthetic_dataset(samples_per_class=10):
    """Generates synthetic noise/color images if user hasn't downloaded TrashNet dataset yet."""
    for class_name in CLASS_NAMES:
        folder = os.path.join(DATASET_DIR, class_name)
        os.makedirs(folder, exist_ok=True)

        # Base color seeds for classes
        seed_colors = {
            "cardboard": (180, 140, 100),
            "glass": (200, 230, 240),
            "metal": (190, 190, 200),
            "paper": (240, 240, 245),
            "plastic": (100, 180, 240),
            "trash": (80, 80, 80)
        }

        base_rgb = seed_colors.get(class_name, (128, 128, 128))

        for i in range(samples_per_class):
            # Create synthetic 224x224 image with color variations
            noise = np.random.randint(-30, 30, (224, 224, 3), dtype=np.int16)
            arr = np.clip(base_rgb + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
            img.save(os.path.join(folder, f"sample_{i+1:03d}.jpg"))

    print(f"Successfully generated {samples_per_class * len(CLASS_NAMES)} synthetic dataset samples.")


def build_mobilenetv2_model():
    """Build MobileNetV2 transfer learning model with custom 6-class head."""
    # Data Augmentation Layer
    data_augmentation = models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.1)
    ], name="data_augmentation")

    # MobileNetV2 Base Model pretrained on ImageNet
    base_model = tf.keras.applications.MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(224, 224, 3)
    )
    base_model.trainable = False  # Freeze feature extractor initially

    # Construct complete architecture
    inputs = layers.Input(shape=(224, 224, 3), name="input_image")
    x = data_augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(0.3, name="dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="dense_128")(x)
    x = layers.Dropout(0.2, name="dropout_2")(x)
    outputs = layers.Dense(len(CLASS_NAMES), activation="softmax", name="classification_head")(x)

    model = models.Model(inputs, outputs, name="EcoSort_MobileNetV2")
    return model, base_model


def train():
    print("========================================")
    print("ECOSORT AI MODEL TRAINING")
    print("Dataset:\n  TrashNet")
    print("Classes:")
    for c in CLASS_NAMES:
        print(f"  {c.capitalize()}")
    print("Model:\n  MobileNetV2")
    print("Image size:\n  224x224")
    print("========================================")

    counts, total_images = validate_dataset()

    os.makedirs(MODEL_DIR, exist_ok=True)

    print("\nLoading image datasets...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical"
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical"
    )

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=autotune)
    val_ds = val_ds.prefetch(buffer_size=autotune)

    print("\nBuilding MobileNetV2 architecture...")
    model, base_model = build_mobilenetv2_model()

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.summary()

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, verbose=1),
        ModelCheckpoint(MODEL_PATH, monitor="val_accuracy", save_best_only=True, verbose=1)
    ]

    print("\nTraining Phase 1: Classification Head Training...")
    start_time = time.time()
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks
    )

    # Optional Phase 2: Fine-Tuning top layers of MobileNetV2
    print("\nTraining Phase 2: Fine-Tuning MobileNetV2 Base...")
    base_model.trainable = True
    # Freeze lower layers, unfreeze top 30 layers
    fine_tune_at = len(base_model.layers) - 30
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    history_fine = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=callbacks
    )

    # Evaluate final validation metrics
    val_loss, val_accuracy = model.evaluate(val_ds, verbose=0)
    best_val_acc_pct = round(val_accuracy * 100.0, 2)
    elapsed_min = round((time.time() - start_time) / 60.0, 1)

    # Save final model
    model.save(MODEL_PATH)

    # Save metadata JSON
    meta = {
        "trained": True,
        "model_name": "MobileNetV2 Transfer Learning",
        "classes": CLASS_NAMES,
        "dataset_images": total_images,
        "val_accuracy": best_val_acc_pct,
        "val_loss": round(val_loss, 4),
        "training_time_minutes": elapsed_min,
        "trained_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\n========================================")
    print("Training completed!")
    print(f"Best validation accuracy:\n  {best_val_acc_pct}%")
    print(f"Model saved:\n  model/waste_classifier.keras")
    print("========================================")


if __name__ == "__main__":
    train()
