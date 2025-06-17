# Enhanced INPI Dataset

Os dados podem ser encontrados em:

-   `data/raw`: Banco de dados original, sem deduplicação e classificação.
-   `data/final`: Arquivos processados de cada revista utilizada.
-   `data/dicionario-dados.pdf`: Dicionário de dados explicando o que cada campo significa nos JSON's das patentes

## Pré-requisitos  

- Python 3
- MySQL

## Ínicio Rápido

1. Crie  e ative um ambiente virtual python

```
python -m venv venv
.\venv\Scripts\Activate
```

2. Instale as dependências:

```
pip install -r requirements.txt
```

Faça o download do arquivo binário da língua portuguesa em https://fasttext.cc/docs/en/crawl-vectors.html
e o adicione na pasta WordBank (o nome do arquivo é cc.pt.300.bin).

3. Crie um banco de dados relacional MySQL

```
mysql -u user -p password
create database name_database
```

4. Na pasta `.\src`, crie um arquivo `.env` e preencha com as seguintes informações sobre o BD:

```
DATABASE_NAME=name_database
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_PORT=port
DATABASE_HOST=host
```

3. Execute o arquivo dataset.py:

```
python dataset.py
```

Os dados de patentes deduplicados e classificados estarão disponíveis na pasta `data/final`. 
