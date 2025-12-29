
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

def index(request):
    forecast_plot = None
    error_message = None
    forecast_data = []

    if request.method == 'POST':
        try:
            months = int(request.POST.get('months', 12))
            
            # Load model
            model_path = os.path.join(settings.BASE_DIR.parent, 'sarima_model.pkl')
            if not os.path.exists(model_path):
                error_message = "Model file not found. Please train the model first."
            else:
                model_results = joblib.load(model_path)
                
                # Forecast
                forecast = model_results.get_forecast(steps=months)
                predicted_mean = forecast.predicted_mean
                conf_int = forecast.conf_int()
                
                # Create plot
                plt.figure(figsize=(10, 5))
                plt.plot(predicted_mean.index, predicted_mean.values, label='Forecast', color='#4F46E5')
                plt.fill_between(predicted_mean.index, 
                                 conf_int.iloc[:, 0], 
                                 conf_int.iloc[:, 1], color='#4F46E5', alpha=0.1)
                plt.title(f'Price Forecast for next {months} Months')
                plt.xlabel('Date')
                plt.ylabel('Price')
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                # Save to buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                string = base64.b64encode(buf.read())
                forecast_plot =  string.decode('utf-8')
                plt.close()
                
                # Prepare data for table
                for date, price in zip(predicted_mean.index, predicted_mean.values):
                    forecast_data.append({
                        'date': date.strftime('%Y-%m'),
                        'price': round(price, 2)
                    })
                    
        except Exception as e:
            error_message = f"Error: {str(e)}"

    return render(request, 'web_app/index.html', {
        'forecast_plot': forecast_plot,
        'forecast_data': forecast_data,
        'error_message': error_message
    })
