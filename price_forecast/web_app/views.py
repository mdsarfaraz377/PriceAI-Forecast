
import os
import io
import base64
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings
import pandas as pd

from django.http import JsonResponse

def index(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        try:
            months = int(request.GET.get('months', 12))
            model_path = os.path.join(settings.BASE_DIR.parent, 'sarima_model.pkl')
            data_path = os.path.join(settings.BASE_DIR.parent, 'data.csv')
            
            print(f"DEBUG: Loading model from {model_path}")
            if not os.path.exists(model_path):
                return JsonResponse({'error': f'Model not found at {model_path}'}, status=404)
            
            model_results = joblib.load(model_path)
            forecast = model_results.get_forecast(steps=months)
            predicted_mean = forecast.predicted_mean
            conf_int = forecast.conf_int()
            
            print(f"DEBUG: Loading data from {data_path}")
            df = pd.read_csv(data_path)
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)
            df.set_index('date', inplace=True)
            hist_df = df.iloc[-36:] 
            
            hist_dates = [str(d.strftime('%Y-%m')) for d in hist_df.index]
            hist_prices = [float(round(p, 2)) for p in hist_df['avg_monthly_price']]

            last_date = hist_df.index[-1]
            last_price = hist_df['avg_monthly_price'].iloc[-1]
            
            dates = [str(last_date.strftime('%Y-%m'))] + [str(d.strftime('%Y-%m')) for d in predicted_mean.index]
            prices = [float(round(last_price, 2))] + [float(round(p, 2)) for p in predicted_mean.values]
            
            lower_ci = [float(round(last_price, 2))] + [float(round(p, 2)) for p in conf_int.iloc[:, 0]]
            upper_ci = [float(round(last_price, 2))] + [float(round(p, 2)) for p in conf_int.iloc[:, 1]]

            print("DEBUG: Returning JSON response successfully")
            return JsonResponse({
                'hist_dates': hist_dates,
                'hist_prices': hist_prices,
                'dates': dates,
                'prices': prices,
                'lower_ci': lower_ci,
                'upper_ci': upper_ci
            })
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    # Standard page load
    return render(request, 'web_app/index.html')
