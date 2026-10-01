# ♻️ EcoSort AI — Real-Time Waste Segregation System Using CNN & Transfer Learning

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15%2B-orange.svg)](https://www.tensorflow.org/)
[![MobileNetV2](https://img.shields.io/badge/Model-MobileNetV2-emerald.svg)](https://keras.io/api/applications/mobilenet/)

**EcoSort AI** is an intelligent, real-time waste classification and segregation web application powered by Computer Vision, Convolutional Neural Networks (CNN), and Transfer Learning with MobileNetV2.

Developed as a college mini-project, EcoSort AI enables users to instantly upload or capture waste images (cardboard, glass, metal, paper, plastic, trash) via a browser camera, get real-time predictions with confidence scores, view detailed material probabilities, and receive actionable recycling and disposal guidance.

---

## 🌟 Features

- 📸 **Real-Time Webcam Scanner**: Integrated camera module with real-time video feed and instant snapshot classification.
- 📁 **Drag & Drop Image Upload**: Supports JPG, PNG, and WEBP images up to 10 MB with client-side preview and image validation.
- 🧠 **MobileNetV2 Transfer Learning**: Pretrained ImageNet feature extractor fine-tuned for 6 waste categories with data augmentation.
- 📊 **Confidence & Class Breakdown**: Displays overall prediction confidence (High, Moderate, Low) with horizontal animated probability bars for all 6 classes.
- ♻️ **Actionable Disposal Guidance**: Instant recycling recommendations based on material type.
- 📜 **Prediction History**: Local history storage (`predictions.json`) with search, filter, and clear options.
- 📈 **Interactive Analytics Dashboard**: Real-time charts powered by Chart.js showcasing scan statistics, recyclable vs general waste distribution, and confidence metrics.
- 🛡️ **Robust Error & Missing Model Handling**: Graceful fallback if the trained model is not present, showing clear instructions rather than fake predictions.
- 📱 **Responsive Design**: Professional glassmorphism UI designed with Vanilla CSS and responsive navigation drawer for mobile screens.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Vanilla Glassmorphism), JavaScript (ES6+ async/await), Lucide Icons, Chart.js (CDN) |
| **Backend** | Python 3, Flask, Werkzeug |
| **Machine Learning** | TensorFlow, Keras, MobileNetV2 Pretrained Weights, Transfer Learning |
| **Image Processing** | Pillow (PIL), NumPy |
| **Dataset** | TrashNet Dataset (6 Classes: Cardboard, Glass, Metal, Paper, Plastic, Trash) |

---

## 📁 Project Structure

```
EcoSort_AI/
│
├── app.py                  # Flask web server & REST API endpoints
├── train.py                # Dataset validation & MobileNetV2 model training script
├── predict.py              # Image validation, preprocessing, & Keras classifier module
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation
├── .gitignore              # Git ignore rules
│
├── model/                  # Saved Keras model & metadata
│   └── waste_classifier.keras
│
├── dataset/                # TrashNet image dataset subfolders
│   ├── cardboard/
│   ├── glass/
│   ├── metal/
│   ├── paper/
│   ├── plastic/
│   └── trash/
│
├── static/
│   ├── css/
│   │   └── style.css       # Main UI CSS with design system & glassmorphism
│   ├── js/
│   │   └── app.js          # Interactive frontend controller & camera logic
│   ├── images/             # Static UI icons/graphics
│   └── uploads/            # Temporary storage for uploaded waste images
│
├── templates/
│   ├── base.html           # Layout template with sidebar & navigation
│   ├── index.html          # Dashboard & Waste Scanner
│   ├── history.html        # Classification history table
│   ├── analytics.html      # Chart.js metrics & breakdown
│   ├── about.html          # Project architecture & workflow
│   └── 404.html            # Custom error page
│
└── data/
    └── predictions.json    # JSON storage for prediction history
```

---

## 🚀 Quick Start Guide (Windows / VS Code)

### 1. Clone or Open Workspace
Open VS Code in the project folder:
```powershell
cd c:\Users\Win\OneDrive\Documents\EcoSort
```

### 2. Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. (Optional) Download TrashNet & Train Model
Place your dataset images in `dataset/<class_name>/` subfolders.
Run the training script:
```powershell
python train.py
```
> *Note: If no custom dataset is placed, `train.py` automatically generates a synthetic sample dataset for immediate testing.*

### 5. Run the Flask Web Application
```powershell
python app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧠 Machine Learning Architecture

```
Input Image (224x224x3)
      │
      ▼
Data Augmentation (Flip, Rotation, Zoom, Contrast)
      │
      ▼
MobileNetV2 Preprocessing (Scaling [-1, 1])
      │
      ▼
MobileNetV2 Base (Pretrained ImageNet Feature Extractor)
      │
      ▼
Global Average Pooling 2D
      │
      ▼
Dropout (0.3) ──► Dense (128 units, ReLU) ──► Dropout (0.2)
      │
      ▼
Dense (6 units, Softmax Activation)
      │
      ▼
Class Probabilities: [Cardboard, Glass, Metal, Paper, Plastic, Trash]
```

---

## 🔮 Future Improvements

- 🤖 **IoT & Raspberry Pi Integration**: Deploying on smart waste bins equipped with camera hardware and servo motor sorting.
- ⚡ **Edge AI Deployment**: Quantizing the model to TensorFlow Lite (TFLite) for low-latency offline edge devices.
- 🎥 **Multi-Object Detection**: Integrating YOLO for real-time video stream detection of multiple objects on conveyor belts.
- 📊 **Municipal Cloud Dashboard**: Aggregating city-wide waste classification metrics to optimize recycling logistics.

---

## 📜 License & Acknowledgments

This project is created for educational and college mini-project demonstration purposes.
Dataset credits: **TrashNet Dataset** (Mindico / Yang & Thung).
