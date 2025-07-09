
# Enhanced INPI Dataset

The data can be found in:

- `data/raw`: Original database, without deduplication and classification. It can also be obtained at https://github.com/cie-cefet-mg/inpi-db/tree/main/data/processos/patente.
- `data/final`: Processed files from each magazine used.
- `data/dicionario-dados.pdf`: Data dictionary explaining what each field means in the patents' JSON files.

## Prerequisites

- Python 3  
- MySQL

## Quick Start

1. Create and activate a Python virtual environment:

```
python -m venv venv
.\venv\Scripts\Activate
```

2. Install the dependencies:

```
pip install -r requirements.txt
```

Download the Portuguese language binary file from https://fasttext.cc/docs/en/crawl-vectors.html  
and add it to the `WordBank` folder (the file name is `cc.pt.300.bin`).

3. Create a MySQL relational database:

```
mysql -u user -p password
create database name_database
```

4. In the `.\src` folder, create a `.env` file and fill it with the following database information:

```
DATABASE_NAME=name_database
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_PORT=port
DATABASE_HOST=host
```

5. Run the `dataset.py` file:

```
python dataset.py
```

The deduplicated and classified patent data will be available in the `data/final` folder.
