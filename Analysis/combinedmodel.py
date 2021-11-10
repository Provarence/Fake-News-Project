# -*- coding: utf-8 -*-
"""Combinedmodel.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MAOJoebz8O1yqRpWAjtSL1rqX0MVM2Nz
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pandas
import numpy as numpy
import tensorflow as tf

from keras_preprocessing.text import Tokenizer
from gensim.models import KeyedVectors
from keras_preprocessing.sequence import pad_sequences
from keras import Sequential, Model
from keras.layers import Conv1D, Dropout, Dense, Embedding, MaxPooling1D, Concatenate, Flatten, Input
from keras.layers.merge import concatenate
from sklearn.utils import resample

PATH = '/content/drive/MyDrive/Georgia Tech (1)/code/datasets/'

PATH = '/content/drive/MyDrive/College/BDBI/FakeNews/'

PATH = '/content/drive/MyDrive/Georgia Tech (1)/code/datasets/'

RANDOM_SEED = 42
numpy.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt
def load_test_data():     
    #create Pandas dataframes from the two csv files
    train_bodies = pandas.read_csv(PATH + "competition_test_bodies.csv", encoding='utf-8')
    train_headlines = pandas.read_csv(PATH + "competition_test_stances.csv", encoding='utf-8')

    #merge the csv files on Body ID
    test_data_set = pandas.merge(train_bodies, train_headlines, how='left', on='Body ID')
    stances = {
        'Stance': {
          'agree': 0,
          'disagree': 1,
          'discuss': 2,
          'unrelated': 3,
        }
    }
    test_data_set.replace(stances, inplace=True)
    print(test_data_set['Stance'].value_counts())
    # print(test_data_set)
    
    return test_data_set

def load_train_data():     
    #create Pandas dataframes from the two csv files
    train_bodies = pandas.read_csv(PATH + "train_bodies.csv", encoding='utf-8')
    train_headlines = pandas.read_csv(PATH + "train_stances.csv", encoding='utf-8')

    #merge the csv files on Body ID
    train_data_set = pandas.merge(train_bodies, train_headlines, how='left', on='Body ID')
    stances = {
        'Stance': {
          'agree': 0,
          'disagree': 1,
          'discuss': 2,
          'unrelated': 3,
        }
    }
    train_data_set.replace(stances, inplace=True)
    print(train_data_set)
    #print(train_data_set)
    return train_data_set

# load the data set from the train csv files
def load_train_data():     
    #create Pandas dataframes from the two csv files
    train_bodies = pandas.read_csv(PATH + "train_bodies.csv", encoding='utf-8')
    train_headlines = pandas.read_csv(PATH + "train_stances.csv", encoding='utf-8')

    #merge the csv files on Body ID
    train_data_set = pandas.merge(train_bodies, train_headlines, how='left', on='Body ID')
    stances = {
        'Stance': {
          'agree': 0,
          'disagree': 1,
          'discuss': 2,
          'unrelated': 3,
        }
    }
    train_data_set.replace(stances, inplace=True)
    print("original here")
    print(train_data_set)
    # print(train_data_set['Stance'].value_counts())
   
    # average to 8909 or 3678? because 36545 is a lot but 840 is very small
    # 3 - 36545, 2 - 8909, 0 - 3678, 1 - 840
    # print(train_data_set['Stance'].value_counts())
    data_length = 8909


    unrelated_resampled = resample(train_data_set.loc[train_data_set['Stance'] == 3], replace = False, n_samples = data_length, random_state = RANDOM_SEED)
    discuss_resampled = resample(train_data_set.loc[train_data_set['Stance'] == 2], replace = False, n_samples = data_length, random_state = RANDOM_SEED)
    agree_resampled = resample(train_data_set.loc[train_data_set['Stance'] == 0], replace=True, n_samples=data_length, random_state=RANDOM_SEED)
    disagree_resampled = resample(train_data_set.loc[train_data_set['Stance'] == 1], replace=True, n_samples=data_length, random_state=RANDOM_SEED)
  

    all_resampled = [unrelated_resampled, discuss_resampled, agree_resampled, disagree_resampled]
    result = pandas.concat(all_resampled)
    result = result.sample(frac=1)

    print(result['Stance'].value_counts())
    print("result here")
    print(result)

    return result

import pickle as pkl
def prepare_data(data_set, length=None):
    #tokenize the data set
    bodies_tokenizer, headlines_tokenizer = (Tokenizer(), Tokenizer())

    #find the max length of each dataset
    bodies_max_length = 0
    headlines_max_length = 0
    if not length:
      bodies_max_length = data_set['articleBody'].map(lambda x : len(x.split())).max()
      headlines_max_length = data_set['Headline'].map(lambda x : len(x.split())).max()
    else:
      bodies_max_length = length[0]
      headlines_max_length = length[1]
    
    #fit the tokenizer on the data set
    bodies_tokenizer.fit_on_texts(data_set['articleBody'])
    headlines_tokenizer.fit_on_texts(data_set['Headline'])

    with open('bodies_tokenizer.pkl', 'wb') as handle:
      pkl.dump(bodies_tokenizer, handle, protocol=pkl.HIGHEST_PROTOCOL)
    with open('headlines_tokenizer.pkl', 'wb') as handle:
      pkl.dump(headlines_tokenizer, handle, protocol=pkl.HIGHEST_PROTOCOL)
    

    #convert the texts to sequences
    bodies_sequences = bodies_tokenizer.texts_to_sequences(data_set['articleBody'])
    headlines_sequences = headlines_tokenizer.texts_to_sequences(data_set['Headline'])

    #pad the data to be the max length
    bodies_sequences = pad_sequences(bodies_sequences, maxlen=bodies_max_length, padding='post', truncating='post')
    headlines_sequences = pad_sequences(headlines_sequences, maxlen=headlines_max_length, padding='post', truncating='post')

    
    return bodies_sequences, headlines_sequences, bodies_tokenizer.word_index, headlines_tokenizer.word_index, data_set['Stance']

def create_embeddings(bodies_word_index, headlines_word_index):
    # create empty dictionaries for the embeddings
    bodies_embeddings_index, headlines_embeddings_index = ({},{})
    word2vec_model = KeyedVectors.load_word2vec_format(PATH + "GoogleNews-vectors-negative300.bin", binary=True)

    def getVector(str):
      if str in word2vec_model:
        return word2vec_model[str]
      else:
        return None;

    #save the vector for each word to the matrix
    bodies_embeddings_matrix = numpy.zeros((len(bodies_word_index)+1, 300))
    for word, i in bodies_word_index.items():
        embedding_vector = getVector(word)
        if embedding_vector is not None:
            bodies_embeddings_matrix[i] = embedding_vector

    headlines_embeddings_matrix = numpy.zeros((len(headlines_word_index)+1, 300))
    for word, i in headlines_word_index.items():
        embedding_vector = getVector(word)
        if embedding_vector is not None:
            headlines_embeddings_matrix[i] = embedding_vector

    return bodies_embeddings_matrix, headlines_embeddings_matrix
    
    #save the wector for each word to the matrix
    bodies_embeddings_matrix = numpy.zeros((len(bodies_word_index)+1, 100))
    for word, i in bodies_word_index.items():
        embedding_vector = bodies_embeddings_index.get(word)
        if embedding_vector is not None:
            bodies_embeddings_matrix[i] = embedding_vector

    headlines_embeddings_matrix = numpy.zeros((len(headlines_word_index)+1, 100))
    for word, i in headlines_word_index.items():
        embedding_vector = headlines_embeddings_index.get(word)
        if embedding_vector is not None:
            headlines_embeddings_matrix[i] = embedding_vector

    return bodies_embeddings_matrix, headlines_embeddings_matrix

if __name__ == '__main__':
    train_data = load_train_data()
    # train_data = train_data[train_data['Stance'] != 3]

    # g = train_data.groupby('Stance')
    # train_data = g.apply(lambda x: x.sample(g.size().min()).reset_index(drop=True))


    test_data = load_test_data()

    # f = test_data.groupby('Stance')
    # test_data = f.apply(lambda x: x.sample(f.size().min()).reset_index(drop=True))
    # test_data = test_data[test_data['Stance'] != 3]
    
    bodies_sequences, headlines_sequences, bodies_word_index, headlines_word_index, stances = prepare_data(train_data)
    test_bodies_sequences, test_headlines_sequences, test_bodies_word_index, test_headlines_word_index, test_stances = prepare_data(test_data,[bodies_sequences.shape[1],headlines_sequences.shape[1]])

    
    bodies_embeddings_matrix, headlines_embeddings_matrix = create_embeddings(bodies_word_index=bodies_word_index, headlines_word_index=headlines_word_index)

    bodies_vocab_size, headlines_vocab_size = len(bodies_word_index), len(headlines_word_index)

def create_model(embedding_matrix, vocab_size, input_length):
    model = Sequential()
   # model.add(Input())
    model.add(Embedding(vocab_size + 1,300, weights = [embedding_matrix], trainable=False, input_length=input_length))

    model.add(Conv1D(256, 3, activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling1D(pool_size=2, padding="same"))

    model.add(Conv1D(256, 3, activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling1D(pool_size=2,padding="same"))

    model.add(Conv1D(512, 3, activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling1D(pool_size=2,padding="same"))
  

    model.add(Conv1D(512, 3, activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling1D(pool_size=2,padding="same"))


    print(input_length)
    if input_length >= 512:
      print("issue5 starting")
      model.add(Conv1D(512, 3, activation='relu'))
      model.add(Dropout(0.5))
      model.add(MaxPooling1D(pool_size=2,padding="same"))
      print("issue5")
      

    print("issue6 starting")
    model.add(Conv1D(768, 1, activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling1D(pool_size=2,padding="same"))
    print("issue6")

    model.add(Flatten())

    return model

bodies_model = create_model(embedding_matrix=bodies_embeddings_matrix, vocab_size=bodies_vocab_size, input_length=bodies_sequences.shape[1])

headlines_model = create_model(embedding_matrix=headlines_embeddings_matrix, vocab_size=headlines_vocab_size, input_length=headlines_sequences.shape[1])

print(bodies_vocab_size)
print(headlines_vocab_size)

#bodies_model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])
#print(bodies_model.summary())

#headlines_model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])
#print(headlines_model.summary())
finalModel = Sequential()
print(bodies_model.input)
print(headlines_model.input)
print(bodies_model.output)
print(headlines_model.output)
finalModel = Concatenate()([bodies_model.output, headlines_model.output])
finalModel = Flatten()(finalModel)
finalModel = Dense(1024, activation='relu') (finalModel)
finalModel = Dense(1024, activation='relu') (finalModel)
finalModel = Dense(1024, activation='relu') (finalModel)
finalModel = Dense(4, activation='softmax') (finalModel)
#0,1,2,3
#0: [1,0,0,0]
#1: [0,1,0,0]
#2: [0,0,1,0]

model = Model(inputs=[bodies_model.input, headlines_model.input], outputs = finalModel)

opt = tf.keras.optimizers.Adam(learning_rate=0.0001)
model.compile(loss='categorical_crossentropy',optimizer=opt,metrics=['accuracy'])


print(model.summary())
from keras.utils.vis_utils import plot_model

plot_model(model, to_file= PATH + 'model_plot.png', show_shapes=True, show_layer_names=True)

import keras
from IPython.display import clear_output
from matplotlib import pyplot as plt
class PlotLearning(keras.callbacks.Callback):
    def on_train_begin(self, logs={}):
        self.i = 0
        self.x = []
        self.losses = []
        self.val_losses = []
        self.acc = []
        self.val_acc = []
        self.fig = plt.figure()
        
        self.logs = []

    def on_epoch_end(self, epoch, logs={}):
        
        self.logs.append(logs)
        self.x.append(self.i)
        self.losses.append(logs.get('loss'))
        self.val_losses.append(logs.get('val_loss'))
        self.acc.append(logs.get('acc'))
        self.val_acc.append(logs.get('val_acc'))
        self.i += 1
        f, (ax1, ax2) = plt.subplots(1, 2, sharex=True)
        
        clear_output(wait=True)
        
        ax1.set_yscale('log')
        ax1.plot(self.x, self.losses, label="loss")
        ax1.plot(self.x, self.val_losses, label="val_loss")
        ax1.legend()
        
        ax2.plot(self.x, self.acc, label="accuracy")
        ax2.plot(self.x, self.val_acc, label="validation accuracy")
        ax2.legend()
        
        plt.show();
        
plot = PlotLearning()

filepath= PATH + "test.best.hdf5"

# print(headlines_sequences[4].size)
from keras.utils import to_categorical
from keras.callbacks import ModelCheckpoint

print(bodies_sequences.shape)
print(headlines_sequences.shape)
print(stances)
onehot_stances = to_categorical(stances)
print(onehot_stances)


stances_counts = train_data['Stance'].value_counts();
count_total = stances_counts.sum()
count_unrelated, count_dicuss, count_agree, count_disagree = stances_counts[3], stances_counts[2], stances_counts[0], stances_counts[1]
weight_unrelated = 1/(count_unrelated) * (count_total) / 2.0
weight_discuss = 1/(count_dicuss) * (count_total) / 2.0
weight_agree = 1/(count_agree) * (count_total) / 2.0
weight_disagree = 1/(count_disagree) * (count_total) / 2.0

class_weights = {0: weight_agree, 1: weight_disagree, 2: weight_discuss, 3: weight_unrelated}

checkpoint = ModelCheckpoint(filepath, monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
callbacks_list = [checkpoint, plot_losses]

model.fit([bodies_sequences, headlines_sequences],
              onehot_stances,batch_size=16,
              epochs=100, callbacks=callbacks_list,
              validation_split=0.05, 
              shuffle=True,
              )


model.save(PATH + 'model')

model.load_weights(PATH + "weights.best.hdf5")

from keras.utils import to_categorical
test_onehot_stances = to_categorical(test_stances)
print(len(bodies_sequences))
print(len(test_bodies_sequences), test_headlines_sequences[0], test_onehot_stances[0])
model.evaluate([test_bodies_sequences, test_headlines_sequences], test_onehot_stances)

import pandas as pd
import numpy as np
def test(headline, body):
  data = {'Headline': [headline], 'articleBody':[body], 'Stance': [None]}
  df = pd.DataFrame.from_dict(data)
  bodies_sequences, headlines_sequences, bodies_word_index, headlines_word_index, stances = prepare_data(df, [2243,40])
  stances = {
      0: "agree",
      1: "disagree",
      2: "discuss",
      3: "unrelated"
  }
  prediction = model.predict([bodies_sequences, headlines_sequences])
  print(prediction)
  print(stances[np.argmax(prediction)])
test("Pope Francis loves Donald Trump", '''Pope Francis hates Donlad Trump''')