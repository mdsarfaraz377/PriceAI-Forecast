
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
import joblib
import warnings
warnings.filterwarnings('ignore')

def train_and_save_model():
    print("Loading data...")
    df = pd.read_csv('data.csv')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Interpolate if needed (basic cleaning)
    df['avg_monthly_price'] = df['avg_monthly_price'].interpolate(method='linear')
    
    print("Training SARIMA model...")
    # Using fixed order for demonstration; in prod use auto_arima
    model = SARIMAX(df['avg_monthly_price'], 
                    order=(1, 1, 1), 
                    seasonal_order=(1, 1, 1, 12),
                    enforce_stationarity=False,
                    enforce_invertibility=False)
    
    results = model.fit(disp=False)
    
    print("Saving model to 'sarima_model.pkl'...")
    # We save the results wrapper to make predictions later
    joblib.dump(results, 'sarima_model.pkl')
    print("Model saved successfully!")

if __name__ == "__main__":
    train_and_save_model()
