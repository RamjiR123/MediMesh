# MediMesh  
MediMesh is an intelligent hospital operations analytics platform that uses real-time data and predictive modeling to optimize patient flow, staff allocation, and resource utilization. By forecasting demand and identifying bottlenecks, the platform empowers healthcare administrators to reduce wait times, improve efficiency, and deliver more equitable patient care.

---

## 🌐 Vision  
MediMesh aims to become the AI-powered operational intelligence layer for hospitals and clinics. The platform transforms raw operational data into actionable insights through a combination of machine learning, time-series forecasting, and interactive analytics.

By providing a transparent, open-source toolset, MediMesh bridges the gap between complex data science and frontline clinical decision-making. The long-term goal is to evolve into a scalable, cloud-deployable system that supports hospitals of all sizes with real-time operational foresight.

---

## 🧩 Core Capabilities  
- **Predictive analytics** for ER wait times, bed occupancy, and staff load  
- **Real-time dashboards** for patient flow and resource utilization  
- **Modular architecture** designed for future SaaS deployment  
- **Model interpretability** using SHAP and transparent forecasting pipelines  
- **Open-source infrastructure** with containerized deployment and extensible APIs  

---

## 🚧 Current Development Focus  
MediMesh is under active development. The current phase focuses on building a robust foundation for long-term growth while delivering a functional end-to-end prototype.

### Data & Backend
- FastAPI backend with local SQLite fallback for quick demo usage
- Synthetic data generation engine for ER visits, bed usage, and staffing patterns
- Clean, modular database schema for hospital workflow data

> Tip: Run locally with SQLite by leaving `DATABASE_URL` unset, or set `DATABASE_URL="sqlite:///./medimesh.db"`.

### Modeling
- Baseline forecasting models using Scikit-learn and Prophet  
- Advanced models (XGBoost) for improved accuracy and latency  
- Model explainability via SHAP  

### Dashboard  
- MVP built in Streamlit for rapid iteration  
- Transition to Plotly Dash for long-term modularity and interactivity  
- Automated alerts for predicted overloads and resource shortages  

### Infrastructure  
- Dockerized environment for reproducibility  
- Cloud-ready architecture (Azure/GCP)  
- Comprehensive documentation and technical white paper  

---

## 📅 Implementation

### Phase 1 — Foundation & Architecture  
- Define system architecture and data pipelines  
- Set up backend, database, and synthetic data generation  
- Build initial API endpoints  

### Phase 2 — Predictive Modeling
- Train baseline forecasting models  
- Validate predictions on synthetic and public datasets  
- Integrate advanced models for improved accuracy  

### Phase 3 — Dashboard & Visualization (in progress)
- Build real-time operational dashboard  
- Add historical trends, alerts, and interpretability features  
- Migrate to a scalable dashboard framework  

### Phase 4 — Integration & Deployment (in progress)
- Full pipeline integration and testing  
- Cloud deployment optimization  
- Publish documentation and open-source contribution guidelines  

### Phase 5 — Long-Term Expansion (in progress)
- Integration with real hospital datasets (where permitted)  
- Multi-hospital benchmarking and cross-site analytics  
- Automated staffing recommendations  
- Simulation tools for surge planning and resource allocation  
- Full SaaS architecture with multi-tenant support  

---

## 🎥 Demo (in progress)  
The evolving demo will allow hospital administrators to:  
- Monitor real-time ER load, bed occupancy, and staff utilization  
- Receive 24-hour predictive insights  
- Understand model reasoning through interpretability tools  
- Interact with a cloud-deployable analytics platform  

## Predictive Scenario Checks

Run the deterministic unit and simulation scenarios from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The hospital scenarios use fixed synthetic arrivals on matching weekdays. They check a quiet Sunday, an ER peak, separate ER and ICU histories, and a hospital-wide total. Expected arrival and staffing estimates are asserted, so a change in the forecast behavior is visible in test output.

These checks validate internal consistency on controlled data; they are not an estimate of real hospital accuracy. Current patient records do not include measured wait times, so ER wait-model evaluation uses synthetic fallback labels until observed `wait_time_minutes` data is available. Staffing estimates also depend on the configured patients-per-staff ratio and should not be used as clinical or shift-roster guidance.

## Operational Alert Thresholds

The health metrics response includes warnings for bed occupancy at 90% or above, doctor availability at 10% or below, and 50 or more patient arrivals in the preceding 24 hours. Patient volume escalates to critical at 100 arrivals. These are initial demo settings, not hospital-specific safety standards; tune thresholds to local capacity and review alert frequency against observed operations.

## ER Model Summary

Initialize the predictive models to show ER training metrics and the five most important input features in the Predictive dashboard.

Feature importance is a relative measure of how the random forest used an input when splitting training data. It is not evidence that a feature causes longer or shorter waits.

MAE and RMSE describe error on the model's held-out split. The current sample data has no measured wait-time labels, so those scores are based on synthetic targets unless `wait_time_minutes` observations are supplied.

Check the model-specific scenarios with:

```powershell
python -m unittest discover -s tests -p test_er_wait_predictor.py -v
```

Use real, representative wait-time observations and a time-based holdout before comparing model quality for operational use.

### Scenario Results
| Scenario | Arrivals / hour | Estimated staff |
| --- | ---: | ---: |
| Quiet ER | 1 | 1 |
| Peak ER | 8 | 2 |
| Combined ER and ICU | 10 | 3 |

Run only the hospital scenarios with:

```powershell
python -m unittest discover -s tests -p test_hospital_scenarios.py -v
```

For real-world evaluation, collect timestamped arrivals and measured wait times before treating any model score as operational evidence.

Reserve a later time period as a holdout set to avoid evaluating against training history.
Compare predictions with observed outcomes using MAE and RMSE, and document the dataset period.

---