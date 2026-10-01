import os
import json
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint
)

from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)


# ============================================================
# SETTINGS
# ============================================================

DATASET_DIR = "dataset"
MODEL_DIR = "model"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

INITIAL_EPOCHS = 12
FINE_TUNE_EPOCHS = 15

SEED = 42

CLASS_NAMES = [
    "cardboard",
    "glass",
    "metal",
    "paper",
    "plastic",
    "trash"
]


# ============================================================
# CREATE MODEL DIRECTORY
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# CHECK DATASET
# ============================================================

print("\n" + "=" * 60)
print("EcoSort AI - Waste Classification Training")
print("=" * 60)

print("\nChecking dataset...\n")


for class_name in CLASS_NAMES:

    class_path = os.path.join(
        DATASET_DIR,
        class_name
    )

    if not os.path.exists(class_path):

        raise FileNotFoundError(
            f"Missing dataset folder: {class_path}"
        )

    image_count = len([
        f for f in os.listdir(class_path)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ])

    print(
        f"{class_name.capitalize():12s}: "
        f"{image_count} images"
    )


# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading dataset...\n")


train_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    labels="inferred",

    label_mode="int",

    class_names=CLASS_NAMES,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    validation_split=0.20,

    subset="training",

    seed=SEED,

    shuffle=True
)


val_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    labels="inferred",

    label_mode="int",

    class_names=CLASS_NAMES,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    validation_split=0.20,

    subset="validation",

    seed=SEED,

    shuffle=False
)


print("\nDataset loaded successfully.")

print(
    "\nClasses:",
    train_ds.class_names
)


# ============================================================
# PERFORMANCE OPTIMIZATION
# ============================================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(
    AUTOTUNE
)

val_ds = val_ds.prefetch(
    AUTOTUNE
)


# ============================================================
# CALCULATE CLASS WEIGHTS
# ============================================================

print("\nCalculating class weights...\n")


image_counts = []

for class_name in CLASS_NAMES:

    class_path = os.path.join(
        DATASET_DIR,
        class_name
    )

    count = len([
        f for f in os.listdir(class_path)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ])

    image_counts.append(count)


y = []

for class_index, count in enumerate(
    image_counts
):

    y.extend(
        [class_index] * count
    )


class_weights_array = compute_class_weight(

    class_weight="balanced",

    classes=np.arange(
        len(CLASS_NAMES)
    ),

    y=np.array(y)

)


class_weights = {

    i: float(weight)

    for i, weight in enumerate(
        class_weights_array
    )

}


for i, class_name in enumerate(
    CLASS_NAMES
):

    print(
        f"{class_name:12s}: "
        f"{class_weights[i]:.3f}"
    )


# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = tf.keras.Sequential(

    [

        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.15
        ),

        layers.RandomZoom(
            0.15
        ),

        layers.RandomContrast(
            0.15
        ),

        layers.RandomTranslation(
            0.10,
            0.10
        )

    ],

    name="data_augmentation"

)


# ============================================================
# MOBILE NET V2
# ============================================================

print("\nBuilding MobileNetV2 model...\n")


base_model = MobileNetV2(

    input_shape=(
        IMG_SIZE[0],
        IMG_SIZE[1],
        3
    ),

    include_top=False,

    weights="imagenet"

)


# Freeze base model initially

base_model.trainable = False


# ============================================================
# BUILD CLASSIFIER
# ============================================================

inputs = layers.Input(
    shape=(
        IMG_SIZE[0],
        IMG_SIZE[1],
        3
    )
)


x = data_augmentation(
    inputs
)


x = preprocess_input(
    x
)


x = base_model(
    x,
    training=False
)


x = layers.GlobalAveragePooling2D()(
    x
)


x = layers.BatchNormalization()(
    x
)


x = layers.Dropout(
    0.35
)(
    x
)


x = layers.Dense(
    128,
    activation="relu"
)(
    x
)


x = layers.BatchNormalization()(
    x
)


x = layers.Dropout(
    0.30
)(
    x
)


outputs = layers.Dense(

    len(CLASS_NAMES),

    activation="softmax"

)(x)


model = models.Model(
    inputs,
    outputs
)


# ============================================================
# COMPILE INITIAL MODEL
# ============================================================

model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]

)


model.summary()


# ============================================================
# CALLBACKS
# ============================================================

best_model_path = os.path.join(

    MODEL_DIR,

    "waste_classifier.keras"

)


callbacks = [

    ModelCheckpoint(

        best_model_path,

        monitor="val_accuracy",

        save_best_only=True,

        mode="max",

        verbose=1

    ),

    EarlyStopping(

        monitor="val_accuracy",

        patience=5,

        restore_best_weights=True,

        mode="max",

        verbose=1

    ),

    ReduceLROnPlateau(

        monitor="val_loss",

        factor=0.3,

        patience=2,

        min_lr=1e-7,

        verbose=1

    )

]


# ============================================================
# INITIAL TRAINING
# ============================================================

print("\n" + "=" * 60)

print("PHASE 1 - TRAINING CLASSIFICATION HEAD")

print("=" * 60 + "\n")


history1 = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=INITIAL_EPOCHS,

    class_weight=class_weights,

    callbacks=callbacks

)


# ============================================================
# FINE TUNING
# ============================================================

print("\n" + "=" * 60)

print("PHASE 2 - FINE TUNING MOBILENETV2")

print("=" * 60 + "\n")


base_model.trainable = True


# Freeze earlier layers

fine_tune_from = 100


for layer in base_model.layers[

    :fine_tune_from

]:

    layer.trainable = False


model.compile(

    optimizer=tf.keras.optimizers.Adam(

        learning_rate=0.00005

    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]

)


history2 = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=FINE_TUNE_EPOCHS,

    class_weight=class_weights,

    callbacks=callbacks

)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print("\nLoading best model...\n")


model = tf.keras.models.load_model(
    best_model_path
)


# ============================================================
# FINAL EVALUATION
# ============================================================

print("\n" + "=" * 60)

print("FINAL MODEL EVALUATION")

print("=" * 60)


loss, accuracy = model.evaluate(
    val_ds,
    verbose=1
)


print(
    f"\nValidation Accuracy: "
    f"{accuracy * 100:.2f}%"
)


print(
    f"Validation Loss: "
    f"{loss:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\nGenerating confusion matrix...")


y_true = []

y_pred = []


for images, labels in val_ds:

    predictions = model.predict(
        images,
        verbose=0
    )

    predicted_classes = np.argmax(
        predictions,
        axis=1
    )

    y_true.extend(
        labels.numpy()
    )

    y_pred.extend(
        predicted_classes
    )


y_true = np.array(y_true)

y_pred = np.array(y_pred)


cm = confusion_matrix(

    y_true,

    y_pred

)


print("\nConfusion Matrix:\n")

print(cm)


plt.figure(
    figsize=(9, 8)
)


disp = ConfusionMatrixDisplay(

    confusion_matrix=cm,

    display_labels=[
        name.capitalize()
        for name in CLASS_NAMES
    ]

)


disp.plot(
    cmap="Greens",
    values_format="d"
)


plt.title(
    "EcoSort AI - Waste Classification Confusion Matrix"
)


plt.tight_layout()


confusion_path = os.path.join(

    MODEL_DIR,

    "confusion_matrix.png"

)


plt.savefig(
    confusion_path,
    dpi=200
)


plt.close()


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)

print("CLASSIFICATION REPORT")

print("=" * 60)


report = classification_report(

    y_true,

    y_pred,

    target_names=CLASS_NAMES,

    digits=4

)


print("\n")

print(report)


report_path = os.path.join(

    MODEL_DIR,

    "classification_report.txt"

)


with open(
    report_path,
    "w"
) as f:

    f.write(report)


# ============================================================
# TRAINING GRAPHS
# ============================================================

print(
    "\nGenerating training graphs..."
)


acc = (
    history1.history["accuracy"]
    +
    history2.history["accuracy"]
)


val_acc = (
    history1.history["val_accuracy"]
    +
    history2.history["val_accuracy"]
)


loss_values = (
    history1.history["loss"]
    +
    history2.history["loss"]
)


val_loss = (
    history1.history["val_loss"]
    +
    history2.history["val_loss"]
)


epochs_range = range(
    1,
    len(acc) + 1
)


plt.figure(
    figsize=(10, 6)
)


plt.plot(
    epochs_range,
    acc,
    label="Training Accuracy"
)


plt.plot(
    epochs_range,
    val_acc,
    label="Validation Accuracy"
)


plt.xlabel(
    "Epoch"
)


plt.ylabel(
    "Accuracy"
)


plt.title(
    "EcoSort AI Training Accuracy"
)


plt.legend()


plt.grid(
    alpha=0.3
)


plt.tight_layout()


plt.savefig(

    os.path.join(
        MODEL_DIR,
        "accuracy_graph.png"
    ),

    dpi=200

)


plt.close()


# ============================================================
# LOSS GRAPH
# ============================================================

plt.figure(
    figsize=(10, 6)
)


plt.plot(
    epochs_range,
    loss_values,
    label="Training Loss"
)


plt.plot(
    epochs_range,
    val_loss,
    label="Validation Loss"
)


plt.xlabel(
    "Epoch"
)


plt.ylabel(
    "Loss"
)


plt.title(
    "EcoSort AI Training Loss"
)


plt.legend()


plt.grid(
    alpha=0.3
)


plt.tight_layout()


plt.savefig(

    os.path.join(
        MODEL_DIR,
        "loss_graph.png"
    ),

    dpi=200

)


plt.close()


# ============================================================
# SAVE METADATA
# ============================================================

metadata = {

    "model": "MobileNetV2 Transfer Learning",

    "image_size": [
        IMG_SIZE[0],
        IMG_SIZE[1]
    ],

    "classes": CLASS_NAMES,

    "num_classes": len(
        CLASS_NAMES
    ),

    "validation_accuracy": round(
        float(accuracy * 100),
        2
    ),

    "validation_loss": round(
        float(loss),
        4
    ),

    "dataset_size": int(
        sum(image_counts)
    ),

    "class_counts": {

        CLASS_NAMES[i]:
            int(image_counts[i])

        for i in range(
            len(CLASS_NAMES)
        )

    },

    "class_weights": {

        CLASS_NAMES[i]:
            round(
                float(class_weights[i]),
                4
            )

        for i in range(
            len(CLASS_NAMES)
        )

    }

}


metadata_path = os.path.join(

    MODEL_DIR,

    "model_meta.json"

)


with open(
    metadata_path,
    "w"
) as f:

    json.dump(
        metadata,
        f,
        indent=4
    )


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 60)

print("TRAINING COMPLETED SUCCESSFULLY")

print("=" * 60)

print(
    f"\nBest model saved to:"
    f"\n{best_model_path}"
)

print(
    f"\nMetadata saved to:"
    f"\n{metadata_path}"
)

print(
    f"\nConfusion matrix saved to:"
    f"\n{confusion_path}"
)

print(
    f"\nClassification report saved to:"
    f"\n{report_path}"
)

print(
    "\nFinal Validation Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print("\nEcoSort AI is ready for testing.")