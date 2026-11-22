# RescueAI: AI-Based Disaster Relief Message Classification System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Dataset: CrisisMMD](https://img.shields.io/badge/Dataset-CrisisMMD%20v2.0-blue.svg)](https://crisisnlp.qcri.org/crisismmd)
[![License: Academic](https://img.shields.io/badge/License-Academic%20Use-green.svg)](#)

> **RescueAI** is an NLP-based Supervised Machine Learning system engineered to ingest, clean, and classify high-velocity social media posts during natural disasters into actionable humanitarian categories.

---

## 📌 1. Project Overview & Humanitarian Need

During catastrophic events such as hurricanes, earthquakes, wildfires, and floods, thousands of messages are published every minute across social media platforms. Emergency coordinators and humanitarian relief agencies struggle with severe information overload: critical life-safety pleas and urgent infrastructure failures frequently get lost among opinions, general banter, and media commentary.

**RescueAI** automates this triage by extracting linguistic features using **Sublinear TF-IDF (Unigram + Bigram Collocations)** and classifying inbound messages into **five actionable categories** using cost-sensitive supervised learning.

---

## 🏷️ 2. Dataset & Classification Taxonomy

### Dataset Characteristics: QCRI CrisisMMD (Version 2.0)
* **Total Annotations**: 18,082 records
* **Cleaned Unique Messages (Training)**: 11,584 distinct posts
* **Crises Covered (7 Major Natural Disasters)**:
  1. *Hurricane Irma* (2,907 messages)
  2. *Hurricane Harvey* (2,895 messages)
  3. *Hurricane Maria* (2,892 messages)
  4. *California Wildfires* (1,053 messages)
  5. *Mexico Earthquake* (885 messages)
  6. *Sri Lanka Floods* (596 messages)
  7. *Iraq-Iran Earthquake* (356 messages)

### 8-to-5 Scientific Label Consolidation
| Class ID | Target Category Name | Original QCRI Labels Mapped | Operational Action |
|:---:|---|---|---|
| **0** | **Affected People & Medical Emergencies** | `affected_individuals`, `injured_or_dead_people`, `missing_or_found_people` | Immediate triage; casualty search & rescue |
| **1** | **Infrastructure Damage** | `infrastructure_and_utility_damage`, `vehicle_damage` | Route to public works & engineering corps |
| **2** | **Rescue & Volunteering** | `rescue_volunteering_or_donation_effort` | Route to NGO relief & supply coordination |
| **3** | **Other Relevant Information** | `other_relevant_information` | Route to meteorological & advisory feed |
| **4** | **Not Humanitarian / Irrelevant** | `not_humanitarian` | Automated noise suppression |

---

## 🏆 3. Machine Learning Algorithms & Test Performance

All algorithms were trained on the **Training set ($N=11,584$)**, tuned on the **Development set ($N=2,237$)**, and evaluated on the **held-out Test set ($N=2,237$)**:

| Supervised Model | Test Accuracy | Macro Precision | Macro Recall | **Macro F1-Score** | Weighted F1 | **Cat 0 Recall (Affected People)** | Cat 0 F1-Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Multinomial Naive Bayes** ($\alpha=0.3$, uniform) | 48.46% | 0.4334 | 0.4512 | **0.4383** | 0.4886 | 28.79% | 0.2705 |
| **Random Forest Classifier** ($B=200$, depth=40) | 47.56% | 0.4356 | 0.4551 | **0.4378** | 0.4765 | 35.61% | 0.3287 |
| **Linear SVM** ($C=0.1$, Calibrated) | **52.88%** | **0.5179** | 0.4362 | **0.4513** | **0.5149** | 17.42% | 0.2659 |
| **Logistic Regression (Balanced)** ($C=0.5$) ⭐ | 50.60% | 0.4655 | **0.5040** | **0.4746** | 0.5120 | **48.48%** | **0.3616** |

### Why Balanced Logistic Regression was Selected as Champion:
1. **Highest Macro F1-Score (0.4746)** across the 5 imbalanced classes.
2. **Superior Life-Safety Recall (48.48%)**: Catches nearly **$3\times$ more casualty reports** than Linear SVM (17.42%). In disaster response, false negatives on medical emergencies carry catastrophic consequences.
3. **Calibrated Probabilities**: Softmax activation outputs exact confidence distributions for human verification.

---

## 🚀 4. Installation & Local Execution

### Prerequisites
* Python 3.10, 3.11, 3.12, 3.13, or 3.14
* Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/RescueAI.git
cd RescueAI
```

### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

You can run either the **Streamlit Operations Console** (interactive analyst UI) or the **FastAPI Operations Backend**:

#### Option A: Streamlit Operations Console (Analyst UI)
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

#### Option B: Unified Operations Server (FastAPI REST API)
```bash
python -m rescueai serve --port 8000
```
Interactive OpenAPI / Swagger documentation is available at `http://localhost:8000/docs`.

#### Option C: Run Automated Tests
```bash
pytest tests/test_api.py -v
```

> **Shared Database**: Both the Streamlit Console and FastAPI server share the same SQLite database (`data/rescueai.db`). Messages classified, pinned, flagged, or reviewed in one interface persist seamlessly across both.

---

## 💻 5. Python API Usage

To integrate RescueAI into external pipelines or disaster dispatch bots:

```python
from src.predict import RescueAIInferencePipeline

# Initialize inference pipeline (loads serialized champion model & vectorizer)
pipeline = RescueAIInferencePipeline(model_name="champion")

# Single Message Inference
message = "URGENT: Flood waters rising fast on Pine Street, family of 4 trapped in attic, need boat immediately!"
result = pipeline.predict(message)

print(f"Predicted Category : {result['icon']} {result['predicted_category']}")
print(f"Confidence Score   : {result['confidence'] * 100:.1f}%")
print(f"Cleaned Tokens     : {result['clean_text']}")
print(f"Probability Map    : {result['probabilities']}")
```

---

## 📁 6. Repository Structure

```
RescueAI/
├── app.py                                # Streamlit Interactive Web Application
├── RescueAI_Colab_Notebook.ipynb         # Complete End-to-End Google Colab Notebook
├── requirements.txt                      # Production Python Dependencies
├── README.md                             # Installation & Technical Documentation
├── PROJECT_REPORT.md                     # Academic Research & Engineering Report
├── VIVA_QUESTIONS_AND_ANSWERS.md         # Comprehensive Viva Preparation Guide
│
├── data/
│   ├── raw/                              # Original CrisisMMD Parquet Datasets
│   └── processed/                        # Cleaned, Normalized & Encoded Parquets
│
├── models/
│   ├── tfidf_vectorizer.joblib           # Fitted 10,000-Dimension TF-IDF Vectorizer
│   ├── logistic_regression_champion.joblib # Production Logistic Regression Model
│   ├── linear_svm_model.joblib           # Calibrated Linear SVM Model
│   ├── naive_bayes_model.joblib          # Multinomial Naive Bayes Model
│   ├── random_forest_model.joblib        # Random Forest Model
│   └── model_metadata.joblib             # Taxonomy & Schema Metadata
│
├── reports/
│   ├── model_benchmarks.json             # Benchmark Performance Metrics
│   └── figures/                          # Publication-Ready Visualizations
│       ├── fig1_category_distribution.png
│       ├── fig2_disaster_distribution.png
│       ├── fig3_top_words.png
│       ├── fig4_wordclouds.png
│       ├── fig5_text_length_distribution.png
│       └── fig6_all_models_confusion_matrices.png
│
└── src/
    ├── __init__.py
    ├── preprocessing.py                  # Domain-Specific NLP Text Cleaner
    └── predict.py                        # Modular Inference Pipeline Class
```

---

## ⚖️ 7. Operational & Ethical Disclaimer

RescueAI is an assistive decision-support classifier intended to prioritize social media streams for human emergency coordinators. 
* Predictions do **NOT** establish verified ground truth.
* Social media feeds contain rumors, bot spam, and satire.
* This system must **NOT** replace official emergency 911/999/112 dispatch protocols or automate physical resource deployment without human validation.

---

## 📚 8. Academic References

1. Alam, F., Ofli, F., & Imran, M. (2018). *CrisisMMD: Multimodal Twitter Datasets from Natural Disasters*. Proceedings of the International AAAI Conference on Web and Social Media (ICWSM).
2. Imran, M., Castillo, C., Diaz, F., & Vieweg, S. (2015). *Processing Social Media Messages in Mass Emergency: A Survey*. ACM Computing Surveys (CSUR).
3. Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research (JMLR).
