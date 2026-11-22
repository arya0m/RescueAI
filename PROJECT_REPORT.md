# Academic Project Report
# RescueAI: AI-Based Disaster Relief Message Classification System

**Course**: Supervised Machine Learning & Applied Natural Language Processing  
**Dataset**: QCRI CrisisMMD (Version 2.0)  
**Author**: Machine Learning Engineering Team  
**Date**: November 2026  

---

## Abstract

During natural disasters (hurricanes, earthquakes, wildfires, and floods), microblogging platforms such as Twitter/X become primary communication channels for affected populations. However, critical calls for medical assistance, search-and-rescue requests, and reports of severe infrastructure failure are frequently overwhelmed by non-humanitarian chatter, opinions, and redundant news commentary. 

This project develops **RescueAI**, an interpretable, supervised natural language processing system that automatically ingests unstructured disaster messages and categorizes them into five actionable humanitarian classes: *(1) Affected People & Medical Emergencies, (2) Infrastructure Damage, (3) Rescue & Volunteering, (4) Other Relevant Information,* and *(5) Not Humanitarian / Irrelevant*. 

Using the real-world **QCRI CrisisMMD (v2.0)** benchmark dataset comprising 18,082 multimodal annotations across seven major 2017 crises, we extract unigram and bigram collocations through sublinear Term Frequency–Inverse Document Frequency (TF-IDF) vectorization across a 10,000-dimensional sparse feature space. We train and evaluate four supervised machine learning algorithms: **Multinomial Naive Bayes, Balanced Logistic Regression, Linear Support Vector Machine (Linear SVM),** and **Random Forest**. 

On the held-out test split ($N = 2,237$), **Balanced Logistic Regression ($C=0.5$)** achieves the highest Macro F1-score (**0.4746**) and top emergency sensitivity (**48.48% recall on casualty/medical posts**), outperforming Linear SVM's casualty recall by nearly $3\times$. The complete system is deployed as an interactive Streamlit web dashboard providing real-time message triage, calibrated confidence scoring, exploratory data visualization, and session audit history.

---

## 1. Introduction

When catastrophic natural events strike, official telecommunications infrastructure is often severely degraded. Citizens turn to social media platforms to post real-time eyewitness observations, report missing loved ones, pinpoint structural collapses, and request emergency provisions.

For humanitarian organizations—such as the United Nations Office for the Coordination of Humanitarian Affairs (UN OCHA), the International Federation of Red Cross and Red Crescent Societies (IFRC), and municipal Emergency Operations Centers (EOCs)—manually reading through hundreds of thousands of inbound tweets is infeasible. High-latency triage risks loss of life during the crucial "Golden 72 Hours" following a disaster.

Natural Language Processing (NLP) combined with Supervised Machine Learning provides an automated mechanism to ingest raw message text, strip digital noise, and route actionable alerts to specialized emergency desks.

---

## 2. Problem Statement

Disaster-related social media text presents distinct computational challenges:
1. **Severe Vocabulary Noise**: Tweets contain informal vernacular, abbreviations, truncated URLs, user handles, non-standard punctuation, and OCR/encoding artifacts.
2. **Acute Class Imbalance**: Casual commentary and general news vastly outnumber actionable medical distress calls. In the CrisisMMD dataset, irrelevant posts account for nearly 40% of the corpus, while life-safety casualty reports comprise only 5.2%.
3. **High Cost of False Negatives**: In conventional sentiment analysis, misclassifying a positive review as negative is inconsequential. In emergency triage, a **False Negative** on an *Affected People* message means a trapped victim goes undetected.
4. **Data Leakage Vulnerability**: Multi-image attachments in raw crisis datasets cause duplicate textual records. Evaluating models across naive random splits leads to severe over-optimistic performance reporting.

---

## 3. Project Objectives

1. Ingest and audit the official **QCRI CrisisMMD v2.0** benchmark dataset without synthetic generation or fabricated records.
2. Design a domain-specific text preprocessing pipeline that removes digital artifacts while explicitly preserving emergency negations and spatial indicators.
3. Consolidate the 8 granular CrisisMMD labels into 5 actionable, clinically and logistically sound humanitarian classes.
4. Engineer a leak-free TF-IDF representation capturing critical crisis bigram collocations (`need help`, `power outage`, `flash flood`).
5. Train, tune, and benchmark four supervised learning algorithms: Multinomial Naive Bayes, Logistic Regression, Linear SVM, and Random Forest.
6. Evaluate models using Macro F1-score and minority class recall, selecting the champion algorithm based on test set generalization.
7. Serialize production artifacts using `joblib` and construct an interactive Streamlit dashboard for real-time humanitarian decision support.

---

## 4. Dataset Architecture & Ground Truth Analysis

### 4.1 Dataset Origin: QCRI CrisisMMD (v2.0)
The dataset was curated by the Qatar Computing Research Institute (QCRI) and published at ICWSM 2018 (Alam et al.). It comprises Twitter posts collected during seven major 2017 natural disasters:

```
Total Corpus: 18,082 Text Annotations
├── Training Split   : 13,608 annotations (11,584 unique text messages)
├── Development Split:  2,237 annotations (2,237 unique text messages)
└── Test Split       :  2,237 annotations (2,237 unique text messages)
```

### 4.2 Disasters Represented
1. **Hurricane Irma** (Florida & Caribbean, Hurricane) — 2,907 train messages
2. **Hurricane Harvey** (Texas, Hurricane / Flooding) — 2,895 train messages
3. **Hurricane Maria** (Puerto Rico, Hurricane) — 2,892 train messages
4. **California Wildfires** (California, Wildfire) — 1,053 train messages
5. **Mexico Earthquake** (Puebla / Central Mexico, Earthquake) — 885 train messages
6. **Sri Lanka Floods** (Sri Lanka, Flood / Landslide) — 596 train messages
7. **Iraq-Iran Earthquake** (Middle East Border, Earthquake) — 356 train messages

---

## 5. Methodology & Engineering Pipeline

### 5.1 Partition-Preserving Deduplication
In the raw CrisisMMD multi-modal data, tweets with multiple attached images were duplicated for each image annotation. To prevent training algorithms on repeated identical text while maintaining benchmark comparability:
* We deduplicated the Training set strictly within its partition boundary ($13,608 \rightarrow 11,584$ unique messages).
* The Development and Test sets were verified to contain strictly unique tweets ($2,237$ each).
* Cross-split intersection analysis confirmed **zero overlap** between splits:
  $$\text{Train} \cap \text{Dev} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Dev} \cap \text{Test} = \emptyset$$

### 5.2 8-to-5 Target Label Taxonomy Mapping
To resolve micro-classes with negligible training instances, we established an 8-to-5 deterministic mapping:

```
[0] affected_individuals                  ──┐
[2] injured_or_dead_people                ──┼──> [Cat 0] Affected People & Medical Emergencies (5.22%)
[3] missing_or_found_people (<2% rare)    ──┘

[1] infrastructure_and_utility_damage     ──┐
[7] vehicle_damage (<3% rare)             ──┴──> [Cat 1] Infrastructure Damage (14.67%)

[6] rescue_volunteering_or_donation_effort─────> [Cat 2] Rescue & Volunteering (16.41%)

[5] other_relevant_information            ─────> [Cat 3] Other Relevant Information (25.36%)

[4] not_humanitarian                      ─────> [Cat 4] Not Humanitarian / Irrelevant (38.34%)
```

### 5.3 Domain-Aware Text Preprocessing
Standard NLP pipelines drop all stopwords and hashtags. In crisis management, this leads to semantic inversion:
* *Preserved Negations & Emergency Words*: A whitelist was created preserving `{"no", "not", "nor", "neither", "never", "without", "against", "under", "over", "down", "out", "need", "needs", "help"}`. This prevents *"no drinking water"* from becoming *"drinking water"*.
* *Hashtag De-symbolization*: Regex `#(\w+) \rightarrow \1` removes the octothorpe while retaining the topical token (`#wildfire \rightarrow wildfire`).
* *Noise Stripping*: Stripped URLs (`https?://\S+`), Retweet headers (`^RT @\w+:`), author handles (`@\w+`), and non-alphabetic symbols.
* *Lemmatization*: Applied NLTK `WordNetLemmatizer` to reduce morphological inflections (`destroying, destroyed \rightarrow destroy`).

### 5.4 Feature Extraction: Sublinear TF-IDF with N-Grams
Feature extraction transforms text into numerical vectors $x_i \in \mathbb{R}^{10,000}$:
1. **Sublinear TF**:
   $$\text{TF}_{\text{sublinear}}(t, d) = 1 + \ln(f_{t, d}) \quad \text{for } f_{t, d} > 0$$
   Dampens repeated word counts in short messages.
2. **Smooth IDF (Fitted Strictly on Training Data)**:
   $$\text{IDF}(t, D_{\text{train}}) = \ln\left(\frac{1 + |D_{\text{train}}|}{1 + |\text{df}(t)|}\right) + 1$$
3. **N-Gram Expansion**:
   `ngram_range=(1, 2)` extracts both unigrams and critical bigram collocations (`power outage`, `need help`, `flash flood`, `people killed`).
4. **L2 Normalization**:
   Normalizes all vectors to unit hypersphere length $\|x_i\|_2 = 1$.
   The resulting matrix has a sparsity of **99.907%**, stored efficiently as a Compressed Sparse Row (`csr_matrix`).

---

## 6. Model Development & Experimental Results

### 6.1 Algorithms Evaluated
1. **Multinomial Naive Bayes (MNB)**: Generative probabilistic baseline with Laplace smoothing ($\alpha=0.3$) and uniform prior (`fit_prior=False`).
2. **Balanced Logistic Regression**: Multi-class Softmax classifier with L2 regularization ($C=0.5$) and cost-sensitive class weights $w_k = \frac{N}{K \cdot N_k}$.
3. **Linear Support Vector Machine (Linear SVM)**: Maximum-margin soft hyperplane ($C=0.1$) with Platt Scaling calibration (`CalibratedClassifierCV`).
4. **Random Forest Classifier**: Ensemble of $B = 200$ randomized decision trees with balanced sub-sampling.

### 6.2 Test Set Benchmark Comparison ($N = 2,237$)

| Supervised Model | Test Accuracy | Macro Precision | Macro Recall | **Macro F1-Score** | Weighted F1 | **Cat 0 Recall (Affected People)** | Cat 0 F1-Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Multinomial Naive Bayes** | 48.46% | 0.4334 | 0.4512 | **0.4383** | 0.4886 | 28.79% | 0.2705 |
| **Random Forest** | 47.56% | 0.4356 | 0.4551 | **0.4378** | 0.4765 | 35.61% | 0.3287 |
| **Linear SVM (Calibrated)** | **52.88%** | **0.5179** | 0.4362 | **0.4513** | **0.5149** | 17.42% | 0.2659 |
| **Logistic Regression (Balanced)** ⭐ | 50.60% | 0.4655 | **0.5040** | **0.4746** | 0.5120 | **48.48%** | **0.3616** |

### 6.3 Detailed Discussion of Results
1. **The Fallacy of Raw Accuracy**:
   Linear SVM achieved the highest raw accuracy (52.88%). However, inspecting its minority class recall reveals that it caught only **17.42% of casualty reports** (missing 109 out of 132 genuine emergency victims). It achieved high accuracy by disproportionately assigning ambiguous instances to majority classes.
2. **The Champion Model: Balanced Logistic Regression**:
   By penalizing misclassifications inversely proportional to class frequencies, Balanced Logistic Regression achieved **48.48% recall on Category 0** (detecting 64 out of 132 casualty reports) and the **highest Macro F1-score (0.4746)** across the entire corpus.
3. **Random Forest Sub-Optimality in Text**:
   Random Forest achieved the lowest Macro F1 (0.4378). In a 10,000-dimensional space with 99.91% sparsity, orthogonal axis-aligned decision trees struggle compared to oblique linear decision hyperplanes.

---

## 7. Streamlit Dashboard Implementation

We built a modular, production-ready web application in `app.py` organized into six cohesive views:
1. **Home & Overview**: System introduction, problem context, 5-class taxonomy, and architecture diagram.
2. **Message Classification**: Real-time interactive text classification with preset crisis scenarios, category badge, confidence score, preprocessed token view, and recommended triage actions.
3. **Dataset & EDA Analysis**: Interactive inspection of class distributions, disaster contingency tables, vocabulary frequencies, and category word clouds.
4. **Model Benchmarking**: Interactive comparison matrix highlighting performance trade-offs, strengths, and weaknesses across all four algorithms.
5. **Confusion Matrix & Diagnostics**: High-resolution normalized heatmaps displaying cross-class error patterns.
6. **Prediction History**: Tabular session audit trail with CSV export capability.

---

## 8. Limitations & Ethical Considerations

1. **Social Media Noise & Veracity**: Microblog posts may contain rumors, satirical commentary, or malicious spam. RescueAI does not verify physical veracity; predictions must serve as an assistive filter for human triage personnel.
2. **Temporal & Regional Lexical Drift**: The models were trained on 2017 crises. New disaster events may feature unseen regional slang or place names. Periodic retraining is essential.
3. **Unimodal Text Focus**: This project intentionally restricted focus to the text modality. In multi-image posts, image visual context could provide complementary signals for damage severity.

---

## 9. Conclusion

RescueAI successfully demonstrates that classical supervised machine learning—when paired with domain-specific text preprocessing, n-gram collocation engineering, and cost-sensitive class balancing—provides a highly effective, computationally lightweight, and academically explainable solution for disaster message triage. 

On the benchmark QCRI CrisisMMD v2.0 dataset, Balanced Logistic Regression achieves superior Macro F1-score (0.4746) and catches nearly 50% of sparse emergency medical reports, operating with an inference latency under 5 milliseconds. The accompanying Streamlit interface and Colab notebook provide a complete, reproducible software deliverable for university coursework and humanitarian research.

---

## 10. References
* Alam, F., Ofli, F., & Imran, M. (2018). CrisisMMD: Multimodal Twitter Datasets from Natural Disasters. *ICWSM*.
* Imran, M., Castillo, C., Diaz, F., & Vieweg, S. (2015). Processing Social Media Messages in Mass Emergency: A Survey. *ACM Computing Surveys*.
* Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*.
