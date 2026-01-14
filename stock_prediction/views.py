from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
# FILE UPLOAD AND VIEW
from  django.core.files.storage import FileSystemStorage
# SESSION
from django.conf import settings
from .models import *
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Dense, LSTM
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for web applications
import matplotlib.pyplot as plt
import io
import base64
import os

def first(request):
    return render(request,'index.html')
def index(request):
    return render(request,'index.html')
def addreg(request):
    if request.method=="POST":
        a=request.POST.get('name')
        b=request.POST.get('phone_number')
        c=request.POST.get('email')
        d=request.POST.get('password')
        e=regtable(name=a,phone_number=b,email=c,password=d)
        e.save()
    return redirect(login) 

def register(request):
    return render(request,'register.html')

def login(request):
    return render(request,'login.html')

def addlogin(request):
    email = request.POST.get('email')
    password = request.POST.get('password')
    if email == 'admin@gmail.com' and password =='admin':
        request.session['admin'] = 'admin'
        return render(request,'index.html')

    elif regtable.objects.filter(email=email,password=password).exists():
            userdetails=regtable.objects.get(email=request.POST['email'], password=password)
            request.session['uid'] = userdetails.id
            return render(request,'index.html')

    else:
        return render(request, 'login.html', {'message':'Invalid Email or Password'})
    



def v_users(request):
    user=regtable.objects.all()
    return render(request,'viewusers.html',{'result':user})

def add_stocks(request):
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        name = request.POST.get('name')
        data_file = request.FILES.get('data_file')
        
        if not symbol or not name or not data_file:
            return render(request, 'add_stocks.html', {'error': 'All fields are required'})
        
        # Save the uploaded file temporarily
        fs = FileSystemStorage()
        filename = fs.save(data_file.name, data_file)
        file_path = fs.path(filename)
        
        # Load data
        df = pd.read_csv(file_path)
        if 'Close' not in df.columns:
            fs.delete(filename)
            return render(request, 'add_stocks.html', {'error': 'CSV must have a Close column'})
        
        # Prepare data for training
        data = df.filter(['Close'])
        dataset = data.values
        training_data_len = int(np.ceil(len(dataset) * .8))
        
        scaler = MinMaxScaler(feature_range=(0,1))
        scaled_data = scaler.fit_transform(dataset)
        
        # Create training data
        train_data = scaled_data[0:training_data_len, :]
        x_train = []
        y_train = []
        
        for i in range(60, len(train_data)):
            x_train.append(train_data[i-60:i, 0])
            y_train.append(train_data[i, 0])
        
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
        
        # Build model
        model = Sequential()
        model.add(LSTM(128, return_sequences=True, input_shape=(x_train.shape[1], 1)))
        model.add(LSTM(64, return_sequences=False))
        model.add(Dense(25))
        model.add(Dense(1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.fit(x_train, y_train, batch_size=1, epochs=1)  # Use more epochs in production
        
        # Save model
        model_filename = f'{symbol}_model.h5'
        model_path = os.path.join(settings.BASE_DIR, 'stock_prediction', 'models', model_filename)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        model.save(model_path)
        
        # Save to database
        trained_stock = TrainedStock.objects.create(
            symbol=symbol,
            name=name,
            model_file=f'models/{model_filename}'
        )
        
        # Clean up
        fs.delete(filename)
        
        return render(request, 'add_stocks.html', {'success': f'Stock {name} trained and added successfully'})
    
    return render(request, 'add_stocks.html')





def profile(request):
    uid = request.session.get('uid')
    if not uid:
        return redirect(login)
    try:
        user = regtable.objects.get(id=uid)
    except regtable.DoesNotExist:
        return redirect(login)
    return render(request, 'profile.html', {'user': user})

def logout(request):
    session_keys=list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    return redirect(first)

def stock_prediction(request):
    stocks = TrainedStock.objects.all()
    if request.method == 'POST':
        stock_id = request.POST.get('stock')
        if not stock_id:
            return render(request, 'stock_prediction.html', {'stocks': stocks, 'error': 'Please select a stock'})
        
        try:
            trained_stock = TrainedStock.objects.get(id=stock_id)
        except TrainedStock.DoesNotExist:
            return render(request, 'stock_prediction.html', {'stocks': stocks, 'error': 'Stock not found'})
        
        # Load model
        model_path = os.path.join(settings.BASE_DIR, 'stock_prediction', trained_stock.model_file.name)
        model = load_model(model_path)
        
        # For demo, use sample data. In production, load historical data for the stock
        # Generate sample data (same as before)
        start_date = pd.to_datetime('2012-01-01')
        end_date = pd.to_datetime('2025-12-31')
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        base_price = 50
        prices = base_price + np.cumsum(np.random.randn(n) * 2)
        highs = prices + np.random.uniform(0, 5, n)
        lows = prices - np.random.uniform(0, 5, n)
        opens = prices + np.random.randn(n) * 1
        closes = prices
        adj_closes = closes * np.random.uniform(0.95, 1.05, n)
        volumes = np.random.randint(10000000, 100000000, n)
        data = {
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Adj Close': adj_closes,
            'Volume': volumes
        }
        df = pd.DataFrame(data, index=dates)
        
        # Prepare data for prediction
        data = df.filter(['Close'])
        dataset = data.values
        training_data_len = int(np.ceil(len(dataset) * .95))
        scaler = MinMaxScaler(feature_range=(0,1))
        scaled_data = scaler.fit_transform(dataset)
        # Create test data
        test_data = scaled_data[training_data_len - 60: , :]
        x_test = []
        y_test = dataset[training_data_len:, :]
        for i in range(60, len(test_data)):
            x_test.append(test_data[i-60:i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
        # Predict
        predictions = model.predict(x_test)
        predictions = scaler.inverse_transform(predictions)
        # Plot
        train = data[:training_data_len]
        valid = data[training_data_len:]
        valid = valid.copy()
        valid['Predictions'] = predictions
        plt.figure(figsize=(16,6))
        plt.title(f'{trained_stock.name} ({trained_stock.symbol}) Stock Price Prediction')
        plt.xlabel('Date', fontsize=18)
        plt.ylabel('Close Price USD ($)', fontsize=18)
        plt.plot(train['Close'])
        plt.plot(valid['Predictions'])
        plt.legend(['Train', 'Predictions'], loc='lower right')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        rmse = np.sqrt(np.mean(((predictions - y_test) ** 2)))
        
        # Save prediction to database
        uid = request.session.get('uid')
        if uid:
            try:
                user = regtable.objects.get(id=uid)
                Prediction.objects.create(
                    user=user,
                    stock_symbol=trained_stock.symbol,
                    stock_name=trained_stock.name,
                    predicted_price=predictions[-1][0],  # Latest prediction
                    rmse=rmse
                )
            except regtable.DoesNotExist:
                pass  # User not found, but continue
        
        return render(request, 'stock_prediction.html', {'stocks': stocks, 'plot': image_base64, 'rmse': rmse, 'selected_stock': trained_stock})
    return render(request, 'stock_prediction.html', {'stocks': stocks})

def add_feedback(request):
    uid = request.session.get('uid')
    if not uid:
        return redirect(login)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if subject and message:
            try:
                user = regtable.objects.get(id=uid)
                feedback = Feedback.objects.create(
                    user=user,
                    subject=subject,
                    message=message
                )
                return render(request, 'add_feedback.html', {'success': 'Feedback submitted successfully!'})
            except regtable.DoesNotExist:
                return render(request, 'add_feedback.html', {'error': 'User not found'})
        else:
            return render(request, 'add_feedback.html', {'error': 'Please fill in all fields'})

    return render(request, 'add_feedback.html')

def view_feedback(request):
    if not request.session.get('admin'):
        return redirect(login)

    feedbacks = Feedback.objects.all().order_by('-created_at')
    return render(request, 'view_feedback.html', {'feedbacks': feedbacks})

def prediction_history(request):
    uid = request.session.get('uid')
    if not uid:
        return redirect(login)
    
    try:
        user = regtable.objects.get(id=uid)
        predictions = Prediction.objects.filter(user=user).order_by('-prediction_date')
    except regtable.DoesNotExist:
        return redirect(login)
    
    return render(request, 'prediction_history.html', {'predictions': predictions})

def view_predictions(request):
    if not request.session.get('admin'):
        return redirect(login)

    predictions = Prediction.objects.all().select_related('user').order_by('-prediction_date')
    return render(request, 'view_predictions.html', {'predictions': predictions})