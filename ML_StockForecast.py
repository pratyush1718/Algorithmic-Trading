import pandas_datareader as pdr
from Secret import TTINGO_API_TOKEN
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
import math
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

def get30dayForecast(ticker):

    try:
        #api calls and retrieving data
        df = pdr.get_data_tiingo(ticker, api_key = TTINGO_API_TOKEN)
        print(df.head())

        df1 = df.reset_index()['close'] #returns all closing prices
        scaler = MinMaxScaler(feature_range=(0,1))
        df1 = scaler.fit_transform(np.array(df1).reshape(-1,1)) #converts df1 into an array and transforms values to range from 0 to 1

        #splitting dataset into train and test split
        training_size=int(len(df1)*0.80) #allocated 80% of df for training
        test_size=len(df1)-training_size #rest is for testing
        train_data,test_data=df1[0:training_size,:],df1[training_size:len(df1),:1]


        # convert an array of values into a dataset matrix and return independent and dependent training/testing values
        def create_dataset(dataset, time_step=1):
            dataX, dataY = [], []
            for i in range(len(dataset)-time_step-1):
                dataX.append(dataset[i:(i+time_step), 0]) #Xdata goes up until timestep + current iteration
                dataY.append(dataset[i + time_step, 0]) #Ydata is the next closing price after the last element of Xdata
            return np.array(dataX), np.array(dataY)

        time_step = 100
        x_train,y_train = create_dataset(train_data, time_step)
        x_test,y_test = create_dataset(test_data, time_step)

        #print(x_test.shape)

        # reshape input to be [samples, time steps, features] which is required for LSTM
        x_train = x_train.reshape(x_train.shape[0],x_train.shape[1], 1)
        x_test = x_test.reshape(x_test.shape[0],x_test.shape[1], 1)

        #print(len(test_data))

        #Creating a Stacked LSTM Sequential Model
        model = Sequential()
        model.add(LSTM(50,return_sequences=True,input_shape=(100,1)))
        model.add(Dropout(0.2)) #Dropout after every stack decreases error
        model.add(LSTM(50,return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(50))
        model.add(Dropout(0.2))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error',optimizer='adam')

        model.fit(x_train,y_train,validation_data=(x_test,y_test),epochs=100,batch_size=64,verbose=1)

        train_predict = model.predict(x_train)
        test_predict = model.predict(x_test)
        #inverse transform since we did fitTransform in line 21 and we need real closing prices now
        train_predict=scaler.inverse_transform(train_predict)
        test_predict=scaler.inverse_transform(test_predict)

        print(math.sqrt(mean_squared_error(y_train,train_predict)))#calculating RMSE for training data(root mean sqaured error)
        print(math.sqrt(mean_squared_error(y_test,test_predict))) #calculating RMSE for testing data(root mean sqaured error)


        #previous 100 days closing price is necessary for forecast
        previous100Days = len(test_data) - 100
        x_input=test_data[previous100Days:].reshape(1,-1)

        temp_input=list(x_input)
        temp_input=temp_input[0].tolist()

        print(temp_input)

        lst_output=[]
        n_steps=100
        i=0
        while(i<30):

            if(len(temp_input)>100):
                #adjusts temp_input in case length > 100. And then it also predicts next-day closing price as well.
                try:
                    x_input=np.array(temp_input[1:])
                    #print("{} day input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, n_steps, 1))
                    #print(x_input)
                    yhat = model.predict(x_input, verbose=0)
                    #print("{} day output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    #print(temp_input)
                    lst_output.extend(yhat.tolist())
                    i+=1
                except ValueError:
                    return 'Unavailable'
            else:
                #predicting next day closing price and putting predicted forecast into lst_output AND temp_input
                #we put it in temp_input because it is time-series data!
                x_input = x_input.reshape((1, n_steps,1))
                yhat = model.predict(x_input, verbose=0)
                model.fit(x_test,y_test,validation_data=(x_input,yhat),epochs=100,batch_size=64,verbose=1) #fitting the model again with test values instead
                #this 2nd fit only happens once since the else case only happens the first time during the while loop
                #print(yhat[0])
                temp_input.extend(yhat[0].tolist())
                lst_output.extend(yhat.tolist())
                i+=1

        #Plotting
        # day_new=np.arange(1,101)
        # day_pred=np.arange(101,131)
        # plt.plot(day_new,scaler.inverse_transform(df1[(len(df1)-100):]))
        # plt.plot(day_pred,scaler.inverse_transform(lst_output))
        # plt.show()
        print(lst_output)
        lst_output = scaler.inverse_transform(lst_output)
        print(lst_output)
        if(ticker == 'NVDA'):
            if(lst_output[-1] > 400):
                return lst_output[-1] * 0.6 #handles NVDA exception since ML algorithm is inaccurate because of NVDA's stock split
        return lst_output[-1]
    except IndexError:
        return "Unavailable" #for stocks with insufficient data for forecast
