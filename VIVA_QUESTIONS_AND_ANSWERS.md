# RescueAI: Comprehensive Viva & Academic Defense Guide
## Master Question & Answer Repository for Supervised Machine Learning & NLP

This document contains detailed academic answers to questions frequently asked during university project defenses, viva voce examinations, and technical ML interviews for the **RescueAI** project.

---

### Table of Contents
1. [Project Overview & Disaster Informatics](#1-project-overview--disaster-informatics)
2. [Dataset & Data Integrity](#2-dataset--data-integrity)
3. [NLP Preprocessing & Feature Engineering](#3-nlp-preprocessing--feature-engineering)
4. [Machine Learning Algorithms & Mathematical Foundations](#4-machine-learning-algorithms--mathematical-foundations)
5. [Evaluation Metrics & Error Analysis](#5-evaluation-metrics--error-analysis)
6. [System Deployment, Ethics & Limitations](#6-system-deployment-ethics--limitations)

---

## 1. Project Overview & Disaster Informatics

### Q1: What is the primary objective of RescueAI?
**Answer**:  
The objective is to build an automated, interpretable natural language processing system that classifies social media messages posted during major natural disasters into five actionable humanitarian categories. The system filters out non-humanitarian noise and prioritizes life-safety pleas and infrastructure failures for emergency response personnel.

### Q2: Why is social media text classification critical during disasters?
**Answer**:  
During natural disasters, terrestrial telecommunications often fail, causing citizens to post urgent updates on social media. Responders face massive information overload—thousands of posts per minute. Automated NLP triage identifies urgent casualty and rescue requests buried within noise, expediting response during the critical "Golden 72 Hours."

### Q3: Why is RescueAI framed as an assistive decision-support tool rather than an automated dispatch system?
**Answer**:  
Social media data contains rumors, bots, sarcasm, and unverified reports. Automating physical rescue dispatch without human verification would introduce severe liability and waste scarce physical resources on false alarms. RescueAI organizes and ranks incoming feeds to assist human coordinators in making informed decisions.

---

## 2. Dataset & Data Integrity

### Q4: Which dataset was used, and what are its key properties?
**Answer**:  
We used **QCRI CrisisMMD (Version 2.0)**, curated by Alam et al. (ICWSM 2018). It contains 18,082 text annotations collected from seven natural disasters in 2017 (Hurricanes Irma, Harvey, Maria; California Wildfires; Mexico and Iraq-Iran Earthquakes; Sri Lanka Floods). The dataset contains three annotation tasks; we specifically utilized **Task 2: Humanitarian Categories**.

### Q5: CrisisMMD is a multi-modal dataset. Why did you only train on text?
**Answer**:  
1. **Computational & Interpretability Constraints**: In emergency coordination, text messages (SMS, microblogs) are low-bandwidth, fast to transmit, and represent the primary channel for explicit emergency requests.
2. **Pedagogical Alignment**: The project specifically focuses on supervised NLP text classification principles (TF-IDF, n-grams, linear classifiers) rather than compute-intensive computer vision.
3. **Bandwidth in Disaster Zones**: Text requires kilobytes of data, whereas transmitting high-resolution images in degraded cellular networks is often impossible.

### Q6: How did you map the 8 original CrisisMMD labels into 5 categories?
**Answer**:  
We constructed a deterministic mapping based on humanitarian operational domains:
* `affected_individuals` (0), `injured_or_dead_people` (2), and `missing_or_found_people` (3) $\rightarrow$ **Affected People & Medical Emergencies** (Class 0)
* `infrastructure_and_utility_damage` (1) and `vehicle_damage` (7) $\rightarrow$ **Infrastructure Damage** (Class 1)
* `rescue_volunteering_or_donation_effort` (6) $\rightarrow$ **Rescue & Volunteering** (Class 2)
* `other_relevant_information` (5) $\rightarrow$ **Other Relevant Information** (Class 3)
* `not_humanitarian` (4) $\rightarrow$ **Not Humanitarian / Irrelevant** (Class 4)

### Q7: Why didn't you simply discard rare classes like `missing_or_found_people` (<2%) and `vehicle_damage` (<3%)?
**Answer**:  
Discarding records causes data loss and distorts real-world disaster distributions. Furthermore, `missing_or_found_people` represents critical life-safety information. Merging it into *Affected People & Medical Emergencies* consolidates all victim-tracking data into a unified triage bucket without losing a single training instance.

### Q8: How did you prevent data leakage during deduplication?
**Answer**:  
Because CrisisMMD annotated tweets alongside multiple images, some tweets appeared multiple times in the raw table. If we deduplicated across the combined dataset, messages could be shifted across split boundaries, causing data leakage. Instead, we:
1. Deduplicated the Training set strictly within its own boundary ($13,608 \rightarrow 11,584$ unique messages).
2. Verified that Development ($2,237$) and Test ($2,237$) sets already contained strictly unique messages.
3. Verified mathematically that $\text{Train} \cap \text{Dev} = \emptyset$, $\text{Train} \cap \text{Test} = \emptyset$, and $\text{Dev} \cap \text{Test} = \emptyset$.

---

## 3. NLP Preprocessing & Feature Engineering

### Q9: Why is standard stopword removal dangerous in disaster NLP?
**Answer**:  
Standard stopword lists (NLTK, spaCy) remove negations (`no`, `not`, `nor`, `without`) and spatial/locational adverbs (`under`, `over`, `down`, `out`, `need`). In disaster triage, this reverses semantic meaning:
* *"We have no drinking water"* $\rightarrow$ *"drinking water"* (inverts emergency into supply confirmation).
* *"Bridge is down"* $\rightarrow$ *"bridge"* (loses structural collapse signal).  
We constructed an **Emergency Whitelist** to preserve these critical tokens.

### Q10: Why did you keep hashtag words while stripping the `#` symbol?
**Answer**:  
Hashtags like `#wildfire`, `#HurricaneHarvey`, or `#FloodRelief` contain high-value domain vocabulary. Deleting the whole token destroys critical signal. Using regex substitution `#(\w+) \rightarrow \1` strips the symbol while preserving the topical keyword.

### Q11: What is the difference between stemming and lemmatization? Why choose lemmatization?
**Answer**:  
* **Stemming** (e.g., Porter Stemmer) applies crude heuristic slicing of word endings, often producing non-words (e.g., *"emergency"* $\rightarrow$ *"emergenc"*).
* **Lemmatization** uses morphological vocabulary lookup and grammar rules to return the canonical base form (*lemma*) (e.g., *"wildfires"* $\rightarrow$ *"wildfire"*, *"destroyed"* $\rightarrow$ *"destroy"*).
* Lemmatization produces semantically valid, interpretable tokens for academic reporting and dashboard presentation.

### Q12: What is the mathematical formulation of TF-IDF? What does `sublinear_tf=True` do?
**Answer**:  
TF-IDF calculates:
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$
With sublinear scaling (`sublinear_tf=True`):
$$\text{TF}_{\text{sublinear}}(t, d) = 1 + \ln(f_{t, d}) \quad \text{for } f_{t, d} > 0$$
$$\text{IDF}(t, D) = \ln\left(\frac{1 + |D|}{1 + |\text{df}(t)|}\right) + 1$$
In short tweets, a word appearing twice is not twice as important as a word appearing once. Logarithmic scaling prevents keyword repetition from dominating feature weights.

### Q13: Why did you expand the n-gram range to `ngram_range=(1, 2)`?
**Answer**:  
Unigrams treat each word as conditionally independent. However, disaster semantics rely on multi-word collocations: *"need help"*, *"power outage"*, *"flash flood"*, *"people killed"*, *"damage structure"*. Bigrams encode these word pairings into distinct feature dimensions.

### Q14: What is matrix sparsity, and what was the sparsity of your feature space?
**Answer**:  
Sparsity is the percentage of zero-valued cells in the matrix:
$$\text{Sparsity} = \left(1 - \frac{\text{Non-Zero Elements}}{\text{Rows} \times \text{Columns}}\right) \times 100\%$$
Our training feature matrix ($11,584 \times 10,000$) has a sparsity of **99.907%** because a clean tweet contains only $\approx 8$ to $14$ tokens. We store it as a Compressed Sparse Row (`csr_matrix`), reducing memory consumption from gigabytes to under 25 MB.

---

## 4. Machine Learning Algorithms & Mathematical Foundations

### Q15: Explain the difference between generative and discriminative classifiers using your models.
**Answer**:  
* **Generative Model (Multinomial Naive Bayes)**: Models the joint probability distribution $P(x, y) = P(y) P(x|y)$ and uses Bayes' rule to compute the posterior $P(y|x)$. It models how the data was generated for each class.
* **Discriminative Model (Logistic Regression, Linear SVM)**: Directly models the posterior probability $P(y|x)$ or maps inputs to decision boundaries without estimating the underlying data distribution. Discriminative models generally achieve higher asymptotic accuracy on text classification tasks.

### Q16: Why did default Multinomial Naive Bayes fail on Category 0 (Affected People)?
**Answer**:  
Under empirical estimation, Naive Bayes factors in the prior class probability $P(c) = \frac{N_c}{N}$. Since Category 0 accounts for only 5.2% of the training data, $P(c=0) \approx 0.052$. In short tweets with limited evidence, this small prior suppresses the posterior probability, causing default Naive Bayes to miss **94.87% of casualty tweets** (recall = 5.13%). Setting `fit_prior=False` (uniform prior) boosted recall to **31.62%**.

### Q17: How does cost-sensitive class balancing work in Logistic Regression?
**Answer**:  
In standard Logistic Regression, every sample contributes equally to the log-loss. Under `class_weight='balanced'`, scikit-learn weights each sample inversely proportional to its class frequency:
$$w_k = \frac{N}{K \cdot N_k}$$
For Category 0 (605 samples in 11,584 total), $w_0 \approx 3.83$, while for majority Category 4 (4,441 samples), $w_4 \approx 0.52$. Misclassifying an emergency casualty report incurs a loss penalty $\approx 7.3\times$ higher than misclassifying noise, shifting the decision threshold toward higher emergency sensitivity.

### Q18: Why did Linear SVM outperform Random Forest in this project?
**Answer**:  
1. **Dimensionality & Sparsity**: Our feature space has 10,000 dimensions with 99.91% sparsity. According to statistical learning theory, high-dimensional text is almost linearly separable by hyperplanes.
2. **Axis-Parallel Limitations**: Decision trees make orthogonal splits along single feature axes ($x_j \le \theta$). In sparse text where most $x_j = 0$, orthogonal splits isolate very few samples, requiring deep trees that overfit. Linear hyperplanes take linear combinations of thousands of words ($\sum w_j x_j$), capturing semantic themes far more effectively.

### Q19: What is Platt Scaling, and why was it applied to Linear SVM?
**Answer**:  
`LinearSVC` computes signed geometric distance from the separating hyperplane, not probabilities. Platt Scaling (`CalibratedClassifierCV`) fits an additional sigmoid calibration function:
$$P(y = 1 \mid f(x)) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$$
over internal cross-validation folds. This produces calibrated probabilities required for confidence estimation in the Streamlit dashboard.

---

## 5. Evaluation Metrics & Error Analysis

### Q20: Why is raw accuracy a misleading metric for this project?
**Answer**:  
In an imbalanced dataset where the majority class is 38.3% and the minority class is 5.2%, a naive trivial model predicting only the majority class would achieve 38.3% accuracy, while predicting majority + second-largest class would yield ~64% accuracy while achieving **0% recall on medical emergencies**. Raw accuracy masks catastrophic failures on minority life-safety classes.

### Q21: What is the mathematical difference between Macro F1 and Weighted F1?
**Answer**:  
* **Macro F1**: Unweighted arithmetic mean of F1-scores across all classes:
  $$\text{Macro F1} = \frac{1}{K} \sum_{k=1}^{K} \text{F1}_k$$
  Treats all classes equally, penalizing models that fail on minority classes.
* **Weighted F1**: Mean of F1-scores weighted by class support ($N_k$):
  $$\text{Weighted F1} = \sum_{k=1}^{K} \left(\frac{N_k}{N}\right) \text{F1}_k$$
  Biased toward performance on the majority class. Macro F1 is the proper academic metric for imbalanced crisis triage.

### Q22: What were the final test set results, and why was Logistic Regression selected as champion?
**Answer**:  
On the held-out test set ($N=2,237$):
* **Balanced Logistic Regression**: Macro F1 = **0.4746**, Accuracy = 50.60%, Cat 0 Recall = **48.48%**, Cat 0 F1 = **0.3616**.
* **Linear SVM**: Macro F1 = 0.4513, Accuracy = **52.88%**, Cat 0 Recall = 17.42%, Cat 0 F1 = 0.2659.
* **Multinomial Naive Bayes**: Macro F1 = 0.4383, Accuracy = 48.46%, Cat 0 Recall = 28.79%.
* **Random Forest**: Macro F1 = 0.4378, Accuracy = 47.56%, Cat 0 Recall = 35.61%.

**Selection Rationale**: Logistic Regression achieved the **highest Macro F1 (0.4746)** and caught nearly **$3\times$ more casualty reports (48.48%)** than Linear SVM (17.42%). In humanitarian disaster response, minimizing False Negatives on human casualties is paramount.

### Q23: What does the confusion matrix reveal about the main error modes?
**Answer**:  
1. *Affected People (Cat 0)* is mostly confused with *Rescue & Volunteering (Cat 2)* and *Infrastructure Damage (Cat 1)* because posts like *"house collapsed on family, need rescue boat"* contain vocabulary overlapping all three domains.
2. *Not Humanitarian (Cat 4)* achieves the highest precision (**67.05%**), successfully filtering out two-thirds of general noise without human intervention.

---

## 6. System Deployment, Ethics & Limitations

### Q24: Why use `joblib` instead of Python's standard `pickle` for model serialization?
**Answer**:  
`joblib` is optimized for large NumPy arrays and sparse SciPy matrices. It uses disk-mapped memory buffers, enabling faster serialization/deserialization and lower RAM overhead during cold starts in web applications.

### Q25: What are the main limitations of this system?
**Answer**:  
1. **Temporal/Geographic Drift**: Models trained on 2017 crises may underperform on future events with new slang or regional locations.
2. **Text Modality Only**: Ignores attached images, which could disambiguate severe damage from mild damage.
3. **Misinformation Vulnerability**: Does not verify tweet authenticity; malicious actors could spoof emergency alerts.

### Q26: If you had more compute resources, how would you improve RescueAI in the future?
**Answer**:  
1. Fine-tune a domain-adapted Transformer model (e.g., **CrisisBERT** or **Disaster-RoBERTa**).
2. Integrate Named Entity Recognition (NER) to automatically extract geolocation coordinates, street names, and medical supply quantities.
3. Construct a multimodal late-fusion network combining text embeddings with a Vision Transformer (ViT) for attached disaster photos.
