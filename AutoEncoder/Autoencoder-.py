import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from multiprocessing import Pool
from keras import layers
from keras.layers import Input, Dense
from keras.models import Model
from keras.optimizers import Adam
from ActVibModules.CantileverBeam import CantileverBeam
from ActVibModules.DSPFuncs import easyFourier
from DataImporter import achar_feathers, achar_ressonancias, agrupar_por_desgaste, import_data, importar_respostas_em_frequencia

# Caminho para os dados
PASTA_DADOS = r"C:\Users\jpsfb\OneDrive\Área de Trabalho\DADOS" 

# Carregar dados
df = importar_respostas_em_frequencia(PASTA_DADOS, ['imu1accz', 'imu2accz'])

# Separar os dados em intactos e desgastados
df_intactos = df.loc[0]  # Dados intactos
df_desgastados = df.loc[1:]  # Dados desgastados

# Normalização
x_train = (df_intactos - np.mean(df_intactos)) / np.std(df_intactos)
x_test = (df_desgastados - np.mean(df_intactos)) / np.std(df_intactos)

# Autoencoder
input_dim = x_train.shape[1]
encoding_dim = 32  # Dimensão do espaço latente

input_layer = Input(shape=(input_dim,))
encoded1 = Dense(500, activation='relu')(input_layer)
encoded2 = Dense(200, activation='relu')(encoded1)
encoded = Dense(encoding_dim, activation='relu')(encoded2)
decoded2 = Dense(200, activation='relu')(encoded)
decoded1 = Dense(500, activation='relu')(decoded2)
decoded = Dense(input_dim, activation='relu')(decoded1)

autoencoder = Model(inputs=input_layer, outputs=decoded)
encoder = Model(inputs=input_layer, outputs=encoded)
encoded_input = Input(shape=(encoding_dim,))
decoder_layer2 = autoencoder.layers[-3]
decoder_layer1 = autoencoder.layers[-2]
decoder_layer = autoencoder.layers[-1]
decoder = Model(encoded_input, decoder_layer(decoder_layer1(decoder_layer2(encoded_input))))

# Compilação e Treinamento
initial_learning_rate = 0.01
lr_schedule = Adam(learning_rate=initial_learning_rate)
autoencoder.compile(optimizer=lr_schedule, loss='mse')

history = autoencoder.fit(x_train, x_train, epochs=200, batch_size=100, shuffle=True, validation_split=0.1)

# Análise
reconstrucoes = autoencoder.predict(x_test)
mse = np.mean(np.power(x_test - reconstrucoes, 2), axis=1)
limiar = np.percentile(mse, 95)

# Detecção de anomalias
anomalias = mse > limiar

# Resultados
plt.hist(mse, bins=50)
plt.axvline(limiar, color='red')
plt.title("Distribuição dos Erros de Reconstrução")
plt.show()

print(f"Número de anomalias detectadas: {np.sum(anomalias)}")
