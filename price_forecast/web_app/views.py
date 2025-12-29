from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import pandas as pd
import os
import warnings
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings('ignore')

def index(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        try:
            months = int(request.GET.get('months', 12))
            data_path = os.path.join(settings.BASE_DIR, '..', 'data.csv')
            
            # Load Data
            df = pd.read_csv(data_path)
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)
            df.set_index('date', inplace=True)
            
            # 1. TRAIN MODEL ON THE FLY (Bypasses the heavy 35MB .pkl file limit)
            # SARIMA is fast on small datasets (data.csv is ~4KB)
            model = SARIMAX(df['avg_monthly_price'], 
                            order=(1, 1, 1), 
                            seasonal_order=(1, 1, 1, 12),
                            enforce_stationarity=False,
                            enforce_invertibility=False)
            model_results = model.fit(disp=False)
            
            # 2. GENERATE FORECAST
            forecast = model_results.get_forecast(steps=months)
            predicted_mean = forecast.predicted_mean
            conf_int = forecast.conf_int()
            
            # 3. FORMAT DATA (Last 36 months + Future)
            hist_df = df.iloc[-36:] 
            hist_dates = [str(d.strftime('%Y-%m')) for d in hist_df.index]
            hist_prices = [float(round(p, 2)) for p in hist_df['avg_monthly_price']]

            last_date = hist_df.index[-1]
            last_price = float(hist_df['avg_monthly_price'].iloc[-1])
            
            # Connect history to forecast
            dates = [str(last_date.strftime('%Y-%m'))] + [str(d.strftime('%Y-%m')) for d in predicted_mean.index]
            prices = [last_price] + [float(round(p, 2)) for p in predicted_mean.values]
            lower_ci = [last_price] + [float(round(p, 2)) for p in conf_int.iloc[:, 0]]
            upper_ci = [last_price] + [float(round(p, 2)) for p in conf_int.iloc[:, 1]]

            return JsonResponse({
                'hist_dates': hist_dates, 'hist_prices': hist_prices,
                'dates': dates, 'prices': prices,
                'lower_ci': lower_ci, 'upper_ci': upper_ci
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'web_app/index.html')
