Este projeto se dedica à aplicação de modelos de classificação de Machine Learning utilizando a biblioteca Keras, para analisar leituras vibracionais em uma viga metálica. Essas leituras são causadas por atuadores que estimulam ruído branco na viga, com o propósito de identificar a saúde estrutural da viga. O processo envolve a coleta de dados tanto da viga em sua condição intacta quanto em seu estado desgastado, além de dados intermediários durante esse processo de degradação.

Para realizar essa identificação, empregou-se técnicas como tensores, especificamente os autoencoders, que permitem a extração de características significativas dos dados vibracionais. Além disso, são aplicadas técnicas de tratamento e análise dos dados obtidos da viga, visando uma compreensão mais profunda dos padrões associados ao seu estado de saúde.

Basicamente, trata-se de um projeto de aplicação de auto encoders na análise de dados de vibração obtidos em uma viga biengastada.

Reúne:
- Modelo auto encoder para detecção de anomalia empregado nos experimentos a fim de identificar vigas desgastadas
- Script para teste de integridade e plot dos dados obtidos

Utiliza o firmware [ActVib](https://github.com/eduardobatista/ActVib) na coleta e visualização dos dados.

Os dados utilizados no projeto estão disponíveis para [download](https://drive.google.com/drive/folders/1nfSXZpppbwbpL-gQndGk6RyV4bpzjW-h). 
