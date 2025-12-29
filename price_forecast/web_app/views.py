from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import os
import csv
import json
import datetime
import numpy as np

def index(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        try:
            months_to_forecast = int(request.GET.get('months', 12))
            
            # 1. FIND DATA FILE
            possible_paths = [
                os.path.join(settings.BASE_DIR, '..', 'data.csv'),
                os.path.join(settings.BASE_DIR, 'data.csv'),
                'data.csv'
            ]
            data_path = next((p for p in possible_paths if os.path.exists(p)), 'data.csv')
            
            # 2. READ DATA (Using built-in CSV for speed/size)
            hist_dates = []
            hist_prices = []
            with open(data_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    hist_dates.append(row['date'])
                    hist_prices.append(float(row['avg_monthly_price']))

            # 3. ADVANCED MOMENTUM ENGINE
            # Use all data for seasonality, but only recent data for trend momentum
            y = np.array(hist_prices)
            x = np.arange(len(y))
            
            # Trend: Weighted towards recent years (last 48 months) to capture growth
            # We give 3x more weight to recent data
            weights = np.ones(len(y))
            weights[-48:] *= 3  
            
            # Weighted Polyfit for trend line
            coeffs = np.polyfit(x, y, 1, w=weights)
            slope, intercept = coeffs
            trend = slope * x + intercept
            
            # 4. SEASONALITY (Multiplicative)
            seasonals = [[] for _ in range(12)]
            for i, val in enumerate(y):
                month_obj = datetime.datetime.strptime(hist_dates[i], '%Y-%m-%d')
                m_idx = month_obj.month - 1
                seasonals[m_idx].append(val / trend[i])
            
            monthly_index = [sum(m)/len(m) if m else 1.0 for m in seasonals]
            
            # Ensure the slope is positive if the recent 12 months show growth
            recent_avg = np.mean(y[-12:])
            prior_avg = np.mean(y[-24:-12])
            if recent_avg > prior_avg and slope < 0:
                slope = abs(slope) # Correction for momentum shift
            
            # 5. GENERATE FUTURE DATA
            last_date = datetime.datetime.strptime(hist_dates[-1], '%Y-%m-%d')
            future_dates, future_prices, lower_ci, upper_ci = [], [], [], []
            
            # Seed Point
            start_price = float(hist_prices[-1])
            future_dates.append(last_date.strftime('%Y-%m'))
            future_prices.append(round(start_price, 2))
            lower_ci.append(round(start_price, 2))
            upper_ci.append(round(start_price, 2))

            std_dev = np.std(y - trend)

            for i in range(1, months_to_forecast + 1):
                next_date = last_date + datetime.timedelta(days=31 * i)
                m = next_date.month - 1
                idx = len(y) + i - 1
                
                # Predict: (Trend * Seasonality)
                pred_val = (slope * idx + intercept) * monthly_index[m]
                
                future_dates.append(next_date.strftime('%Y-%m'))
                future_prices.append(float(round(pred_val, 2)))
                lower_ci.append(float(round(pred_val - 1.5 * std_dev, 2)))
                upper_ci.append(float(round(pred_val + 1.5 * std_dev, 2)))

            # 6. SLICE HISTORY (Last 36 months)
            ctx_start = max(0, len(hist_dates) - 36)
            ctx_dates = [datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%Y-%m') for d in hist_dates[ctx_start:]]
            ctx_prices = [float(round(p, 2)) for p in hist_prices[ctx_start:]]

            return JsonResponse({
                'hist_dates': ctx_dates, 'hist_prices': ctx_prices,
                'dates': future_dates, 'prices': future_prices,
                'lower_ci': lower_ci, 'upper_ci': upper_ci
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'web_app/index.html')
