---
id: "proj-health-premium-overview"
type: "project"
title: "Health Premium Predictor — Machine Learning (ML) Project Overview"
source_section: "J1, J2, J3 (Project C)"
source_url: "https://github.com/aamir-coding/health-prem-predict"
tags: ["health-premium-predictor", "ml", "machine-learning", "xgboost", "streamlit", "regression", "solo", "ml-project"]
draft: true
private: false
---

The Health Premium Predictor is Aamir's primary machine learning (ML) project, built completely solo by Aamir Mohammed Khan. It is an educational ML web application that estimates health-insurance premiums using an XGBoost regression model and an interactive Streamlit interface. Aamir owns everything in the project.

The project demonstrates how structured user inputs (such as age, health factors, and lifestyle data) can be passed through a regression pipeline to estimate a premium. It is an educational prediction tool, not a guarantee of an actual insurer's quote.

The stack includes Python, XGBoost regression, Streamlit for the UI, and scikit-learn tooling for preprocessing and model evaluation. The Streamlit interface accepts structured user inputs, processes them through the preprocessing pipeline used during training, and the trained XGBoost model produces a numeric premium estimate displayed in the interface.

---
id: "proj-health-premium-metrics"
type: "project"
title: "Health Premium Predictor — Reported Metrics"
source_section: "J7, J14 (Project C)"
source_url: "https://github.com/aamir-coding/health-prem-predict"
tags: ["health-premium-predictor", "metrics", "r-squared", "evaluation", "xgboost"]
draft: true
private: false
---

The resume reports an R² of 0.99 and approximately 3% prediction error for the Health Premium Predictor model. Aamir has stated he can defend these metrics.

However, several evaluation details require confirmation before these figures can be fully contextualised:

- The exact dataset source and record count are not yet documented.
- The held-out train/test split strategy and random seed need to be recorded.
- The exact formula behind "3% error" (e.g., mean absolute percentage error, median percentage error, or another metric) needs a precise definition.
- Leakage and overfitting checks that were actually performed have not been documented.
- Feature engineering steps and reasoning need to be confirmed from the code.

R² describes how much target variance the model explains relative to a mean-prediction baseline on the evaluated dataset. It does not prove future real-world accuracy. These metrics should not be presented as implying universal or real-world insurance-grade accuracy.

---
id: "proj-health-premium-links"
type: "project"
title: "Health Premium Predictor — Links and Status"
source_section: "J10, J11, V1, V2 (Project C)"
source_url: "https://github.com/aamir-coding/health-prem-predict"
tags: ["health-premium-predictor", "links", "streamlit", "live-app"]
draft: true
private: false
---

- Live app: https://health-prem-prediction.streamlit.app/
- Repository: https://github.com/aamir-coding/health-prem-predict

No login is required to use the application. The app was confirmed working as of 01 November 2026.

Demo/screenshots: not yet available. Predictions should be described as estimates from a project model, not quotes from a real insurer.
