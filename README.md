# JalRakshak AI

A Streamlit demo for citizen water-safety reporting and ML-assisted outbreak-risk assessment.

## Features

- SQLite-backed citizen reports with tracking IDs and status workflow
- Optional photo evidence, GPS coordinates and an authority map
- Dashboard filters, charts and CSV export
- PDF acknowledgement downloads
- Random Forest training with accuracy, confusion matrix and feature importance artifacts
- Optional SMTP authority alerts configured only through a local `.env` file

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\generate_data.py
python src\train_model.py
python -m streamlit run app\app.py
```

## Optional email alerts

Copy `.env.example` to `.env`, then insert your SMTP credentials. Do not commit `.env`; it is ignored by Git.

## GitHub notes

The `.gitignore` excludes virtual environments, SQLite data, uploaded photos, trained models and secrets. Generated model/data files are reproducible using the commands above.
