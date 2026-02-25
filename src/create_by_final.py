import json, glob
from settings import engine
from models import *
import csv
from datetime import datetime

from sqlalchemy import func, case, select
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, joinedload, with_loader_criteria
from utils import *

#,holder_id,fullName,country,state,region,type,cluster_id

type_to_type = {'Company': 'E', 'Person': 'P', 'Institution': 'I'}
region_to_region = {
    "North": "NORTH",
    "Northeast": "NORTHEAST",
    "Central West": "CENTRAL_WEST",
    "Southeast": "SOUTHEAST",
    "South": "SOUTH"}

Session = sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False
)

def populate(batch_size=500):
    names = glob.glob('../data/final/*.json')

    # try:
    #    session = Session()
    #    create_all_holders(session)
    #    session.commit()
    #finally:
    #    session.close()

    #return

    session = Session()
    try:
        for i, name in enumerate(names[90000:], 1):
            with open(name, encoding="utf-8") as f:
                data = json.load(f)

            if 'title' in data:
                insert_record(session, data)

            if i % batch_size == 0:
                session.commit()
                session.expunge_all()  # libera memória
                print(f"{i}/{len(names)}")

        session.commit()
    finally:
        session.close()

def insert_record(session, data):
    production = insert_production(session, data)
    session.flush()

    holders = insert_holders(session, data)
    inventors = []
    if 'inventors' in data:
        inventors = insert_inventors(session, data)

    classifications = []
    if 'ipcCodes' in data:
        classifications = insert_classifications(session, production, data)
        session.flush() 
        
    participations = insert_participations(session, production, holders, inventors)

def insert_production(session, data):
    default_values = {'number': data['applicationNumber'], 'filling_date': datetime.strptime(data['filingDate'], "%d/%m/%Y")}
    production, _ = get_or_create(session, Patent, default_values, name = data['title'])
    return production

def create_all_holders(session):
    with open('PatentHolders.csv', encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        total = 67870
        i = 0

        for line, id, name, country, state, region, type, cluster_id in spamreader:
            unique, _ = create(session, UniqueParticipant, {"id": id, "name": name, "type": type_to_type[type]})
            region = region_to_region.get(region)
            hold, _ = create(session, Participant, {"id": id, "name": name, "country": country, "federative_unit": state, "region": region})
            hold.unique = unique
            session.add(hold)

            if i % 5000 == 0:
                print(f"{i} em {total}")
            i += 1
        
def insert_holders(session, data):
    holders = []
    for holder_data in data['holders']:
        holder, _ = get_model(session, Participant, {}, id = holder_data)
        holders.append(holder)

    return holders

def insert_inventors(session, data):
    inventors = []
    for name in data['inventors']:
        inventor, created = get_or_create(session, Participant, {}, name = name)
        
        unique_participant, _ = get_or_create(session, UniqueParticipant, {}, name = name)
        inventor.unique = unique_participant
        inventors.append(inventor)

    return inventors


def insert_participations(session, production, holders, inventors):
    objs = []

    objs.extend(
        Participation(
            patent_id=production.id,
            participant_id=h.id,
            participation_type=ParticipationType.holder
        )
        for h in holders
    )

    objs.extend(
        Participation(
            patent_id=production.id,
            participant_id=i.id,
            participation_type=ParticipationType.inventor
        )
        for i in inventors
    )

    session.bulk_save_objects(objs)


def insert_classifications(session, production, data):
    if not data.get("ipcCodes"):
        return []

    classifications = []

    for code in data["ipcCodes"]:
        c = session.query(InternationalClassification)\
                   .filter_by(code=code)\
                   .one_or_none()
        if not c:
            c = InternationalClassification(code=code)
            session.add(c)
        classifications.append(c)

    session.flush()  # garante IDs

    rows = [
        {
            "patent_id": production.id,
            "classification_id": c.id
        }
        for c in classifications
        if production.id is not None and c.id is not None
    ]

    if rows:  # 🔴 ESSENCIAL
        session.execute(icp_patent.insert(), rows)

    return classifications


def count_elements():
    with Session.begin() as session:
        count_patent = session.query(Patent).count()
        count_classification = session.query(InternationalClassification).count()
        count_participant = session.query(Participant).distinct().count()
        count_unique = session.query(UniqueParticipant).distinct().count()

        stmt = (
            select(
                Participation.participation_type,
                UniqueParticipant.id
            )
            .join(Participation.participant)
            .join(Participant.unique)
            .distinct()
        )

        counts_stmt = (
            select(
                Participation.participation_type,
                func.count(func.distinct(UniqueParticipant.id)).label("unique_participants_count")
            )
            .join(Participation.participant)
            .join(Participant.unique)
            .group_by(Participation.participation_type)
        )

        results = session.execute(counts_stmt).all()

        print(f'Patentes: {count_patent}')
        print(f'Classificações: {count_classification}')
        print(f'Participantes: {count_participant}')
        print(f'Participantes únicos: {count_unique}')
        for participation_type, count in results:
            print(f"{participation_type.name}: {count}")


if __name__ == '__main__':
    #create_models()
    populate()
    #deduplicate_participants()
    #count_elements()
    #classify_participants
    #save_data_as_json()
