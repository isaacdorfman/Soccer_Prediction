import numpy as np
from keras.utils import np_utils
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import Input,merge
from keras.optimizers import SGD, Adam, RMSprop
from keras.engine.topology import Layer
from keras import backend as K


number_of_teams = 107
margin = 1/3

# Prepare data for the neural net    

def prepare_batch(games_mat):
    start_year = 5
    year_column = games_mat[:,0].reshape(-1,1) - start_year
    home_mat = np_utils.to_categorical(games_mat[:,1], nb_classes=number_of_teams)
    away_mat = np_utils.to_categorical(games_mat[:,2], nb_classes=number_of_teams)    

    dif_column = games_mat[:,3]
    dif_column[dif_column > 0] = 1 # Home wins
    dif_column[dif_column < 0] = 2 # Away wins
    y = np_utils.to_categorical(dif_column, nb_classes=3)

    return (year_column,home_mat,away_mat,games_mat[:,3])

mat = np.genfromtxt("games.csv", delimiter=',', dtype='int')
# Eliminate home vs away favoring:
# mat = np.vstack([mat, mat[:, np.argsort([0,2,1,3])]])
np.random.shuffle(mat)

pieces = np.vsplit(mat, 6)

(train_years,train_home,train_away,train_y) = prepare_batch(np.vstack(pieces[:4]))
(test_years,test_home,test_away,test_y) = prepare_batch(pieces[4])
(valid_years,valid_home,valid_away,valid_y) = prepare_batch(pieces[5])

# Use neural net on data

batch_size = 64
nb_epoch = 10

#Creating the network

Year = Input(shape=(1,))

input1 = Input(shape=(number_of_teams,))
input2 = Input(shape=(number_of_teams,))

input1f = merge([input1,Year],mode='concat')
input2f = merge([input2,Year],mode='concat')

shared_layer = Dense(64,activation='relu')
x1 = shared_layer(input1f)
x2 = shared_layer(input2f)

shared_layer = Dropout(0.5)
x1 = shared_layer(x1)
x2 = shared_layer(x2)

shared_layer = Dense(64,activation='relu')
x1 = shared_layer(x1)
x2 = shared_layer(x2)

shared_layer = Dropout(0.5)
x1 = shared_layer(x1)
x2 = shared_layer(x2)

shared_layer = Dense(32)
x1 = shared_layer(x1)
x2 = shared_layer(x2)

props = merge([x1,x2],mode='concat')

#From here we define NN2

y = Dense(64,activation='relu')(props)
y = Dropout(0.5)(y)
y = Dense(64,activation='relu')(y)
y = Dropout(0.5)(y)
output = Dense(1)(y)


Network = Model(input=[input1,input2,Year],output=output)

#Compiling the Network

Network.summary()

Network.compile(loss='hinge',
              optimizer=RMSprop(lr=0.0001),
              metrics=['accuracy']) #To Ziv and Itay: you can change this to
                                    #SVM if you want.
         
history = Network.fit([train_home,train_away,train_years],train_y/margin,
                    batch_size=batch_size, nb_epoch=nb_epoch,
                    verbose=1, validation_data=([valid_home,valid_away,valid_years], valid_y/margin))
   
           
(score, accuracy) = Network.evaluate([test_home,test_away,test_years], test_y, verbose=0)


predicted = (Network.predict([test_home,test_away,test_years], verbose=0) * margin)
predicted = predicted.reshape((predicted.shape[0],))

print("The predicted scores are; " + str(predicted))
print("The difference between the predicted scores and the real scores is; " + str(predicted-test_y))
print("The average error is: " + str(np.mean(np.abs(predicted-test_y))))