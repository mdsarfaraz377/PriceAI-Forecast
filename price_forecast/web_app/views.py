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

            # 3. PRECISION MOMENTUM ENGINE (2025-Focused)
            y_all = np.array(hist_prices)
            x_all = np.arange(len(y_all))
            
            # Use only the last 12 months for the modern growth trend
            # This captures the current ₹11k -> ₹15k trajectory perfectly
            y_recent = y_all[-12:]
            x_recent = x_all[-12:]
            
            # Linear Fit for current growth trajectory
            slope, intercept = np.polyfit(x_recent, y_recent, 1)
            
            # 4. SUBTLE SEASONALITY (Dampened to prevent artificial drops)
            # Calculate seasonal factors but dampen them so they don't cause huge drops
            seasonals = [[] for _ in range(12)]
            for i, val in enumerate(y_all):
                month_obj = datetime.datetime.strptime(hist_dates[i], '%Y-%m-%d')
                m_idx = month_obj.month - 1
                baseline = slope * i + intercept
                # Multiplicative factor
                factor = val / baseline if baseline > 0 else 1.0
                seasonals[m_idx].append(factor)
            
            # Dampen: (original_index + 1) / 2 pulls factors closer to 1.0 (neutral)
            raw_monthly_index = [sum(m)/len(m) if m else 1.0 for m in seasonals]
            monthly_index = [(idx + 1.0) / 2.0 for idx in raw_monthly_index]
            
            # 5. GENERATE FUTURE DATA
            last_date = datetime.datetime.strptime(hist_dates[-1], '%Y-%m-%d')
            future_dates, future_prices, lower_ci, upper_ci = [], [], [], []
            
            start_price = float(hist_prices[-1])
            # Current price as seed
            future_dates.append(last_date.strftime('%Y-%m'))
            future_prices.append(round(start_price, 2))
            lower_ci.append(round(start_price, 2))
            upper_ci.append(round(start_price, 2))

            # Modern volatility for confidence
            std_dev = np.std(y_recent - (slope * x_recent + intercept))

            for i in range(1, months_to_forecast + 1):
                next_date = last_date + datetime.timedelta(days=31 * i)
                m = next_date.month - 1
                idx = len(y_all) + i - 1
                
                # Formula: Current Trend Position x Dampened Seasonality
                pred_val = (slope * idx + intercept) * monthly_index[m]
                
                # Ensure the forecast doesn't fall below the current start 
                # if the slope is positive (Momentum Preservation)
                if slope > 0:
                    pred_val = max(pred_val, start_price * 0.98) # Floor it near current price

                future_dates.append(next_date.strftime('%Y-%m'))
                future_prices.append(float(round(pred_val, 2)))
                # Confidence intervals
                lower_ci.append(float(round(pred_val - 1.0 * std_dev, 2)))
                upper_ci.append(float(round(pred_val + 1.2 * std_dev, 2)))

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
