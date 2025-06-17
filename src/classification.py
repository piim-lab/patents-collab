import pandas as pd
import numpy as np
import tensorflow as tf
import fasttext
import fasttext.util as fu
import keras

from sklearn.preprocessing import LabelEncoder, StandardScaler

from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy import select, func, desc, asc

from settings import engine
from models import *


Session_eng = sessionmaker(engine)

def load_data(path, model):
    df_pop = pd.read_csv(path)

    X = df_pop["name"].__array__()
    labels = X
    embeddings = []
    error = 0
    for x in X:
        try:
            embeddings.append(get_embedding(x, model))
        except Exception as e:
            error += 1
            print('Embedding error!')

    print(f'Errors: {error}')
    X = np.array(embeddings)

    return X, labels

def predict(model, X):
    Y_pred = model.predict(X)
    Y_pred = np.argmax(Y_pred, axis=1)

    return Y_pred

def get_embedding(phrase, model):
    lst_word = phrase.split()
    vec = [model[w] for w in lst_word]
    
    return np.mean(vec, axis=0)

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def generate_csv(session: Session):
    participants = (session.query(UniqueParticipant.name).all())
    
    df_participant = pd.DataFrame(participants)
    df_participant = df_participant[["name"]]
    df_participant["name"] = df_participant["name"].str.lower()
    df_participant['type'] = ''

    print(len(df_participant))
    df_participant.to_csv("participants.csv", index=False)

def classify(session, result, labels, classes):
    total = len(labels)
    error = 0
    for i, label in enumerate(labels):
        name = None
        try:
            pred_type = classes[result[i]]
            name = label.upper()
            participant = session.query(UniqueParticipant).filter_by(name = name).first()
            if not participant:
                error += 1
                continue
            participant.type = pred_type
            session.add(participant)
        except Exception as e:
            print(f'Erro em {name}')

        if i % 2000 == 0:
            print(f'{i}/{total} - {((i / total) * 100):.2f}% - {error} erros')

def print_layers(Y_pred, classes, labels):
    dic = {}

    for i, y in enumerate(Y_pred):
        dic[labels[i]] = classes[y]

    return dic

def prepare_data(X):
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X


def classify_participants():
    with Session_eng.begin() as session:
        generate_csv(session)

    model = fasttext.load_model('../data/WordBank/cc.pt.300.bin')
    new_model = keras.models.load_model("../models/model_nn.keras")
    print(keras.__version__)

    X, labels = load_data("participants.csv", model)
    new_X = prepare_data(X)
    Y_pred = predict(new_model, new_X)

    with Session_eng.begin() as session:
        classify(session, Y_pred, labels, ["E", 'I', 'P'])

if __name__ == '__main__':
    classify_participants()
