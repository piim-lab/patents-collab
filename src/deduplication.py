import re
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy import select, func, desc, asc

from settings import engine
from models import *
from utils import get_or_create

Session_eng = sessionmaker(engine)

def get_all_participants(session: Session):
    results = session.query(Participant).all()
    return results

def clean_name(name):
    firstPattern = re.compile('[.\/)]')
    secondPattern = re.compile('[\'\"-:]')

    name = name.strip().upper().replace('  ', ' ').replace('À', 'A')
    name = firstPattern.sub('', name)

    division = [name]
    for c in ['-', '?', '–', '/', '(']:
        if len(division) == 1:
            division = name.split(c)
                    
        if len(division) == 2:
            name, rest = division
            if len(rest) > len(name):
                name, rest = rest, name

        name = secondPattern.sub('', name).replace('  ', ' ').strip()

    return name

def deduplicate_participants(batch_size = 200):

    participants = []
    with Session_eng.begin() as session:
        participants = get_all_participants(session)

    total = len(participants)
    for i in range(0, total, batch_size):
        with Session_eng.begin() as session:
            for processed in range(i, min(i + batch_size, total)):
                participant = participants[processed]
                
                participant = session.merge(participant)
                name = clean_name(participant.name)
                unique_participant, created = get_or_create(session, UniqueParticipant, {}, name = name)
                participant.unique = unique_participant

                if processed % 2000 == 0:
                    print(f"{processed}/{total} - {((processed*100/total)):.2f}%")


def main():
    deduplicate_participants()

if __name__ == '__main__':
    main()

# Antes eram 430808 participantes, 73047 titulares e 376038 inventores
# Depois ficaram 420499 participantes, 67870 titulares e 371253 inventores
