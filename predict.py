
import os
import json

import numpy as np
import tensorflow as tf

from PIL import Image


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "waste_classifier.keras"
)

CLASS_NAMES_PATH = os.path.join(
    MODEL_DIR,
    "class_names.json"
)

METADATA_PATH = os.path.join(
    MODEL_DIR,
    "metadata.json"
)


# ============================================================
# WASTE INFORMATION
# ============================================================

WASTE_INFO = {

    "cardboard": {
        "name": "Cardboard",
        "category": "Recyclable",
        "icon": "📦",
        "color": "blue",
        "advice": (
            "Flatten clean cardboard and place it "
            "in the appropriate recycling stream. "
            "Remove excessive food contamination "
            "and non-paper materials."
        ),
        "tip": (
            "Keep cardboard clean and dry before "
            "recycling."
        )
    },

    "glass": {
        "name": "Glass",
        "category": "Recyclable",
        "icon": "🫙",
        "color": "cyan",
        "advice": (
            "Empty and rinse glass containers. "
            "Place them in a glass recycling stream "
            "where accepted by your local facility."
        ),
        "tip": (
            "Recycling rules for glass can vary "
            "between locations."
        )
    },

    "metal": {
        "name": "Metal",
        "category": "Recyclable",
        "icon": "🥫",
        "color": "gray",
        "advice": (
            "Empty and rinse metal cans and containers "
            "before placing them in the appropriate "
            "recycling stream."
        ),
        "tip": (
            "Check your local recycling guidelines "
            "for accepted metal items."
        )
    },

    "paper": {
        "name": "Paper",
        "category": "Recyclable",
        "icon": "📄",
        "color": "yellow",
        "advice": (
            "Keep paper clean and dry and place it "
            "in an appropriate paper recycling stream."
        ),
        "tip": (
            "Avoid mixing food-soiled paper with "
            "clean recyclable paper."
        )
    },

    "plastic": {
        "name": "Plastic",
        "category": "Recyclable",
        "icon": "🥤",
        "color": "green",
        "advice": (
            "Empty and clean the plastic item before "
            "placing it in a recycling stream where "
            "that type of plastic is accepted."
        ),
        "tip": (
            "Not every type of plastic is accepted "
            "by every recycling facility."
        )
    },

    "trash": {
        "name": "Trash",
        "category": "General Waste",
        "icon": "🗑️",
        "color": "red",
        "advice": (
            "This item was classified as general waste. "
            "Dispose of it according to your local "
            "waste-management guidelines."
        ),
        "tip": (
            "When uncertain, check your local waste "
            "collection guidance."
        )
    }

}


# ============================================================
# MODEL LOADING
# ============================================================

_model = None
_class_names = None
_metadata = None


def load_model():

    global _model

    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            "Trained model not found: "
            f"{MODEL_PATH}"
        )

    print(
        "Loading EcoSort AI model..."
    )

    _model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print(
        "EcoSort AI model loaded successfully."
    )

    print(
        f"Model output shape: "
        f"{_model.output_shape}"
    )

    return _model


# ============================================================
# CLASS MAPPING
# ============================================================

def load_class_names():

    global _class_names

    if _class_names is not None:
        return _class_names


    if not os.path.exists(
        CLASS_NAMES_PATH
    ):

        raise FileNotFoundError(
            "Class mapping not found: "
            f"{CLASS_NAMES_PATH}"
        )


    with open(
        CLASS_NAMES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        mapping = json.load(file)


    # Convert:
    #
    # {
    #   "0": "cardboard",
    #   "1": "glass"
    # }
    #
    # into:
    #
    # ["cardboard", "glass", ...]


    try:

        indexes = sorted(
            mapping.keys(),
            key=lambda value: int(value)
        )

        _class_names = [
            mapping[index]
            for index in indexes
        ]

    except Exception as error:

        raise ValueError(
            "Invalid class_names.json: "
            f"{error}"
        )


    if len(_class_names) != 6:

        raise ValueError(
            "Expected exactly 6 classes, "
            f"found {len(_class_names)}."
        )


    print(
        "Class mapping:"
    )

    for index, name in enumerate(
        _class_names
    ):

        print(
            f"  {index}: {name}"
        )


    return _class_names


# ============================================================
# METADATA
# ============================================================

def load_metadata():

    global _metadata

    if _metadata is not None:
        return _metadata


    if not os.path.exists(
        METADATA_PATH
    ):

        print(
            "Warning: metadata.json not found."
        )

        _metadata = {}

        return _metadata


    try:

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            _metadata = json.load(file)

    except Exception as error:

        print(
            "Warning: unable to read metadata:",
            error
        )

        _metadata = {}


    return _metadata


# ============================================================
# IMAGE PREPARATION
# ============================================================

def prepare_image(image_source):

    """
    Prepare an image for the trained model.

    IMPORTANT:

    The model itself already contains:

        mobilenet_v2.preprocess_input()

    Therefore we DO NOT call preprocess_input()
    here.

    The image remains in the 0-255 range.
    """


    # --------------------------------------------------------
    # PIL image object
    # --------------------------------------------------------

    if isinstance(
        image_source,
        Image.Image
    ):

        image = image_source.copy()


    # --------------------------------------------------------
    # File path
    # --------------------------------------------------------

    elif isinstance(
        image_source,
        (str, os.PathLike)
    ):

        image = Image.open(
            image_source
        )


    else:

        raise TypeError(
            "image_source must be a PIL Image "
            "or a valid image file path."
        )


    # --------------------------------------------------------
    # RGB
    # --------------------------------------------------------

    image = image.convert(
        "RGB"
    )


    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    image = image.resize(
        (224, 224),
        Image.Resampling.LANCZOS
    )


    # --------------------------------------------------------
    # NumPy
    # --------------------------------------------------------

    image_array = np.asarray(
        image,
        dtype=np.float32
    )


    # --------------------------------------------------------
    # Batch dimension
    # --------------------------------------------------------

    image_array = np.expand_dims(
        image_array,
        axis=0
    )


    # IMPORTANT:
    #
    # Do NOT normalize here.
    #
    # Do NOT call:
    #
    # preprocess_input()
    #
    # because the trained model performs
    # MobileNetV2 preprocessing internally.
    #


    return image_array


# ============================================================
# CONFIDENCE LEVEL
# ============================================================

def get_confidence_level(
    confidence
):

    if confidence >= 80:

        return "High"

    elif confidence >= 60:

        return "Moderate"

    else:

        return "Low"


# ============================================================
# PREDICTION
# ============================================================

def predict_image(
    image_source
):

    """
    Predict a waste category.

    Returns a dictionary suitable for
    Flask JSON responses.
    """


    # --------------------------------------------------------
    # Load everything
    # --------------------------------------------------------

    model = load_model()

    class_names = load_class_names()

    metadata = load_metadata()


    # --------------------------------------------------------
    # Prepare image
    # --------------------------------------------------------

    image_array = prepare_image(
        image_source
    )


    print(
        "\nRunning prediction..."
    )


    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    predictions = model.predict(
        image_array,
        verbose=0
    )


    probabilities = predictions[0]


    # --------------------------------------------------------
    # Validate output
    # --------------------------------------------------------

    if len(probabilities) != len(
        class_names
    ):

        raise ValueError(
            "Model output count does not match "
            "class mapping. "
            f"Model: {len(probabilities)}, "
            f"Classes: {len(class_names)}"
        )


    # --------------------------------------------------------
    # Predicted index
    # --------------------------------------------------------

    predicted_index = int(
        np.argmax(probabilities)
    )


    predicted_class = class_names[
        predicted_index
    ]


    confidence = float(
        probabilities[predicted_index]
    ) * 100


    # --------------------------------------------------------
    # Confidence level
    # --------------------------------------------------------

    confidence_level = (
        get_confidence_level(
            confidence
        )
    )


    # --------------------------------------------------------
    # Sort all probabilities
    # --------------------------------------------------------

    score_items = []


    for index, probability in enumerate(
        probabilities
    ):

        class_name = class_names[
            index
        ]


        score_items.append({

            "class": class_name,

            "name": WASTE_INFO.get(
                class_name,
                {}
            ).get(
                "name",
                class_name.title()
            ),

            "probability": round(
                float(probability) * 100,
                2
            )

        })


    score_items.sort(
        key=lambda item: item[
            "probability"
        ],
        reverse=True
    )


    # --------------------------------------------------------
    # Waste information
    # --------------------------------------------------------

    info = WASTE_INFO.get(

        predicted_class,

        {

            "name":
                predicted_class.title(),

            "category":
                "Unknown",

            "icon":
                "♻",

            "color":
                "green",

            "advice":
                "Check local waste-management guidance.",

            "tip":
                "Follow local recycling instructions."

        }

    )


    # --------------------------------------------------------
    # Low confidence
    # --------------------------------------------------------

    is_uncertain = (
        confidence < 50
    )


    if is_uncertain:

        display_name = (
            "Uncertain Classification"
        )

        category = (
            "Low Confidence"
        )

        advice = (
            "The AI could not classify this "
            "image confidently. Try taking a "
            "clearer photo with better lighting "
            "and a simpler background."
        )

    else:

        display_name = info[
            "name"
        ]

        category = info[
            "category"
        ]

        advice = info[
            "advice"
        ]


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {

        "success":
            True,

        "class":
            predicted_class,

        "name":
            display_name,

        "category":
            category,

        "confidence":
            round(
                confidence,
                2
            ),

        "confidence_level":
            confidence_level,

        "confidence_tip":
            (
                "Excellent visual match."
                if confidence >= 80
                else
                "Consider checking the image and lighting."
                if confidence >= 60
                else
                "Retake the image with better lighting and a clear background."
            ),

        "is_uncertain":
            is_uncertain,

        "icon":
            info.get(
                "icon",
                "♻"
            ),

        "color":
            info.get(
                "color",
                "green"
            ),

        "advice":
            advice,

        "tip":
            info.get(
                "tip",
                ""
            ),

        "scores":
            score_items,

        "model":
            metadata.get(
                "model_name",
                "MobileNetV2"
            )

    }


    # --------------------------------------------------------
    # Console logging
    # --------------------------------------------------------

    print(
        f"Predicted: "
        f"{predicted_class}"
    )

    print(
        f"Confidence: "
        f"{confidence:.2f}%"
    )

    print(
        f"Level: "
        f"{confidence_level}"
    )


    print(
        "Top probabilities:"
    )

    for item in score_items[:3]:

        print(
            f"  "
            f"{item['name']}: "
            f"{item['probability']:.2f}%"
        )


    return result


# ============================================================
# MODEL STATUS
# ============================================================

def get_model_status():

    model_exists = os.path.exists(
        MODEL_PATH
    )

    mapping_exists = os.path.exists(
        CLASS_NAMES_PATH
    )

    metadata_exists = os.path.exists(
        METADATA_PATH
    )


    status = {

        "model_exists":
            model_exists,

        "class_mapping_exists":
            mapping_exists,

        "metadata_exists":
            metadata_exists,

        "ready":
            (
                model_exists
                and mapping_exists
            )

    }


    if metadata_exists:

        metadata = load_metadata()

        status[
            "model_name"
        ] = metadata.get(
            "model_name",
            "MobileNetV2"
        )

        status[
            "validation_accuracy"
        ] = metadata.get(
            "validation_accuracy"
        )

        status[
            "test_accuracy"
        ] = metadata.get(
            "test_accuracy"
        )


    return status


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n"
        + "=" * 60
    )

    print(
        "       ECOSORT AI PREDICTION TEST"
    )

    print(
        "=" * 60
    )


    status = get_model_status()


    print(
        "\nModel status:"
    )

    print(
        json.dumps(
            status,
            indent=4
        )
    )


    if not status["ready"]:

        print(
            "\nModel is not ready."
        )

        print(
            "Run train.py first."
        )

        raise SystemExit


    print(
        "\nPrediction engine ready."
    )

    print(
        "\nUsage:"
    )

    print(
        "python predict.py path/to/image.jpg"
    )


    import sys


    if len(sys.argv) > 1:

        image_path = sys.argv[1]


        if not os.path.exists(
            image_path
        ):

            print(
                f"\nImage not found: "
                f"{image_path}"
            )

            raise SystemExit(1)


        result = predict_image(
            image_path
        )


        print(
            "\n"
            + "=" * 60
        )

        print(
            "PREDICTION RESULT"
        )

        print(
            "=" * 60
        )


        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )
        
        
        
# ============================================================
# FLASK COMPATIBILITY FUNCTIONS
# ============================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def is_model_trained():
    """
    Check whether the trained model and class mapping exist.
    """

    return (
        os.path.exists(MODEL_PATH)
        and os.path.exists(CLASS_NAMES_PATH)
    )


def get_model_metadata():
    """
    Return model metadata for the Flask application.
    """

    metadata = load_metadata()

    if not metadata:
        return {
            "model_name": "MobileNetV2",
            "trained": is_model_trained()
        }

    return metadata


def predict_waste(image_source):
    """
    Compatibility wrapper used by app.py.

    The Flask application can call:

        predict_waste(image)

    while the actual prediction engine uses:

        predict_image(image)
    """

    return predict_image(image_source)


def allowed_file(filename):
    """
    Check whether an uploaded file is supported.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS
