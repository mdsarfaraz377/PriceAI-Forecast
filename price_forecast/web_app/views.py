
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
            
            if not os.path.exists(model_path):
                return JsonResponse({'error': 'Model file not found'}, status=404)
            
            model_results = joblib.load(model_path)
            forecast = model_results.get_forecast(steps=months)
            predicted_mean = forecast.predicted_mean
            conf_int = forecast.conf_int()
            
            dates = [d.strftime('%Y-%m') for d in predicted_mean.index]
            prices = [round(p, 2) for p in predicted_mean.values]
            lower_ci = [round(p, 2) for p in conf_int.iloc[:, 0]]
            upper_ci = [round(p, 2) for p in conf_int.iloc[:, 1]]
            
            return JsonResponse({
                'dates': dates,
                'prices': prices,
                'lower_ci': lower_ci,
                'upper_ci': upper_ci
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # Standard page load
    return render(request, 'web_app/index.html')
