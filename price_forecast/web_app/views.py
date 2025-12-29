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

            # 3. DATA-DRIVEN MOMENTUM ENGINE
            y_all = np.array(hist_prices)
            x_all = np.arange(len(y_all))
            
            # Find the index for Jan 2023 (where the market shifted)
            # This ensures we don't let 2005-2022 data drag down the current forecast
            shift_idx = 0
            for i, d in enumerate(hist_dates):
                if d.startswith('2023-01'):
                    shift_idx = i
                    break
            
            # Trend: Focus EXCLUSIVELY on the modern market (post-2023)
            y_modern = y_all[shift_idx:]
            x_modern = x_all[shift_idx:]
            
            # Linear Fit for the modern era
            slope, intercept = np.polyfit(x_modern, y_modern, 1)
            
            # 4. SEASONALITY (Using full history for stability)
            seasonals = [[] for _ in range(12)]
            for i, val in enumerate(y_all):
                month_obj = datetime.datetime.strptime(hist_dates[i], '%Y-%m-%d')
                m_idx = month_obj.month - 1
                # Use a combined trend for seasonality baseline
                # For old data, use a flat baseline; for modern, use the slope
                baseline = slope * i + intercept if i >= shift_idx else np.mean(y_all[:shift_idx])
                seasonals[m_idx].append(val / baseline)
            
            monthly_index = [sum(m)/len(m) if m else 1.0 for m in seasonals]
            
            # 5. GENERATE FUTURE DATA (Starting from the last real point)
            last_date = datetime.datetime.strptime(hist_dates[-1], '%Y-%m-%d')
            future_dates, future_prices, lower_ci, upper_ci = [], [], [], []
            
            start_price = float(hist_prices[-1])
            future_dates.append(last_date.strftime('%Y-%m'))
            future_prices.append(round(start_price, 2))
            lower_ci.append(round(start_price, 2))
            upper_ci.append(round(start_price, 2))

            # Error margin based on modern volatility
            std_dev = np.std(y_modern - (slope * x_modern + intercept))

            for i in range(1, months_to_forecast + 1):
                next_date = last_date + datetime.timedelta(days=31 * i)
                m = next_date.month - 1
                idx = len(y_all) + i - 1
                
                # Predict: Modern Trend + Global Seasonality
                pred_val = (slope * idx + intercept) * monthly_index[m]
                
                future_dates.append(next_date.strftime('%Y-%m'))
                future_prices.append(float(round(pred_val, 2)))
                # 90% Confidence Interval
                lower_ci.append(float(round(pred_val - 1.28 * std_dev, 2)))
                upper_ci.append(float(round(pred_val + 1.28 * std_dev, 2)))

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
