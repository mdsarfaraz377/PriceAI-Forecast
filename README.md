
# Price Forecasting Project

## 1. Setup Environment
Ensure Python 3.8+ is installed.
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Train Model
Train the SARIMA model and save it as `sarima_model.pkl`.
```bash
python train_model.py
```

## 3. Run Web App
Start the Django development server.
```bash
cd price_forecast
python manage.py runserver
```

Open your browser at `http://127.0.0.1:8000/`.

## 4. Run Notebook
To view the analysis and answers to business questions:
```bash
jupyter notebook solution.ipynb
```
