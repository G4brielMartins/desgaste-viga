import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Classe que define o Autoencoder
class AutoEncoder:
    def __init__(self, input_shape, latent_dim, epochs=10, batch_size=32):
        """
        Inicializa o Autoencoder.

        Parâmetros:
        - input_shape: tupla representando a forma (dimensionalidade) da entrada.
        - latent_dim: dimensão do espaço latente onde os dados serão comprimidos.
        - epochs: número de épocas para o treinamento.
        - batch_size: tamanho do lote para o treinamento.
        """
        self.input_shape = input_shape
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.encoder = None
        self.decoder = None
        self.autoencoder = None
        self.history = None

    def build(self):
        """
        Constrói o Autoencoder, que inclui o encoder e o decoder.
        """
        # Definindo a camada de entrada
        input_img = layers.Input(shape=self.input_shape)
        
        # Definindo a camada do encoder, que comprime a entrada no espaço latente
        encoded = layers.Dense(self.latent_dim, activation='relu')(input_img)
        
        # Definindo a camada do decoder, que reconstrói a entrada a partir do espaço latente
        decoded = layers.Dense(self.input_shape[0], activation='sigmoid')(encoded)
        
        # Criando os modelos para o encoder e o decoder
        self.encoder = models.Model(input_img, encoded)
        self.decoder = models.Model(encoded, decoded)
        
        # Criando o modelo completo do Autoencoder
        self.autoencoder = models.Model(input_img, self.decoder(self.encoder(input_img)))
        
        # Compilando o Autoencoder com o otimizador Adam e a função de perda de erro quadrático médio
        self.autoencoder.compile(optimizer='adam', loss='mean_squared_error')
        
        # Exibindo um resumo da arquitetura do Autoencoder
        self.autoencoder.summary()

    def train(self, X_train, X_test):
        """
        Treina o Autoencoder nos dados de treino.

        Parâmetros:
        - X_train: conjunto de dados de treino.
        - X_test: conjunto de dados de teste (para validação durante o treino).
        """
        # Treinando o Autoencoder, com validação no conjunto de teste
        self.history = self.autoencoder.fit(X_train, X_train,epochs=self.epochs, batch_size=self.batch_size, shuffle=True, validation_data=(X_test, X_test))

    def plot_loss(self):
        """
        Plota a perda (loss) durante o treinamento para os dados de treino e validação.
        """
        plt.plot(self.history.history['loss'])
        plt.plot(self.history.history['val_loss'])
        plt.title('Model Loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()

    def encode(self, X):
        """
        Codifica os dados de entrada para o espaço latente usando o encoder treinado.

        Parâmetros:
        - X: dados de entrada a serem codificados.

        Retorna:
        - Representação codificada dos dados no espaço latente.
        """
        return self.encoder.predict(X)

    def decode(self, X):
        """
        Decodifica os dados do espaço latente de volta para o formato original usando o decoder treinado.

        Parâmetros:
        - X: dados codificados no espaço latente.

        Retorna:
        - Dados reconstruídos no formato original.
        """
        return self.decoder.predict(X)

    def save(self, path):
        """
        Salva o modelo do Autoencoder treinado.

        Parâmetros:
        - path: caminho onde o modelo será salvo.
        """
        self.autoencoder.save(path)

    def load(self, path):
        """
        Carrega um modelo do Autoencoder previamente salvo.

        Parâmetros:
        - path: caminho de onde o modelo será carregado.
        """
        self.autoencoder = models.load_model(path)
        self.encoder = models.Model(self.autoencoder.input, self.autoencoder.layers[1].output)
        self.decoder = models.Model(self.autoencoder.layers[1].input, self.autoencoder.layers[2].output)

# Função principal que executa o processo
def main():
    # Carrega o dataset MNIST (dígitos escritos à mão)
    (X_train, y_train), (X_test, y_test) = mnist.load_data()
    
    # Normaliza os dados para o intervalo [0, 1]
    X_train = X_train.astype('float32') / 255.
    X_test = X_test.astype('float32') / 255.
    
    # Remodela os dados para uma única dimensão (necessário para a entrada no Autoencoder)
    X_train = X_train.reshape((len(X_train), np.prod(X_train.shape[1:])))
    X_test = X_test.reshape((len(X_test), np.prod(X_test.shape[1:])))
    
    # Inicializa o Autoencoder com um espaço latente de dimensão 32
    autoencoder = AutoEncoder(input_shape=(784,), latent_dim=32, epochs=10, batch_size=32)
    
    # Constrói a arquitetura do Autoencoder
    autoencoder.build()
    
    # Treina o Autoencoder com os dados de treino
    autoencoder.train(X_train, X_test)
    
    # Plota a perda durante o treinamento
    autoencoder.plot_loss()

    # Codifica os dados de treino e teste no espaço latente
    X_train_encoded = autoencoder.encode(X_train)
    X_test_encoded = autoencoder.encode(X_test)

    # Treina um classificador de Regressão Logística usando as features extraídas pelo encoder
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X_train_encoded, y_train)
    
    # Faz previsões no conjunto de teste
    y_pred = classifier.predict(X_test_encoded)

    # Avalia a acurácia do classificador
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Acurácia do classificador: {accuracy:.2f}")

    # Salva o modelo completo do Autoencoder
    autoencoder.save('autoencoder_with_classifier.h5')

if __name__ == '__main__':
    main()

