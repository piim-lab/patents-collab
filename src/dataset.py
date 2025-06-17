import json, glob
from settings import engine
from models import *

from sqlalchemy import func, case, select
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, joinedload, with_loader_criteria
from utils import get_or_create

Session = sessionmaker(engine)


def populate():
    names = glob.glob('..\data\\raw\\*.json')
    total = len(names)

    for i in range(0, total):
        with Session.begin() as session:
            name = names[i]
            data = {}
            with open(name, encoding="utf-8") as f:
                data = json.load(f)
            try:
                if 'titulo' in data:
                    insert_record(session, data)
            except Exception as e:
                print(f'Erro ao inserir {data["numero"]}')

        if i % 3000 == 0:
            print(f'{min(i, total)}/{total} - {(i * 100 / total):.2f} %')


def insert_record(session, data):
    production = insert_production(session, data)

    holders = insert_holders(session, data)
    inventors = []
    if 'inventores' in data:
        inventors = insert_inventors(session, data)

    classifications = []
    if 'IPC' in data:
        classifications = insert_classifications(session, data)
        
    participations = insert_participations(session, production, holders, inventors)

    production.participations.extend(participations)
    production.international_classifications = []
    production.international_classifications.extend(classifications)


def insert_production(session, data):
    default_values = {'number': data['numero'], 'filling_date': data['dataDeposito']}
    production, _ = get_or_create(session, Patent, default_values, name = data['titulo'])
    return production


def insert_holders(session, data):
    holders = []
    for holder_data in data['titulares']:
        name = holder_data['nomeCompleto']
        country = holder_data.get('pais', '')
        unit = None
        if 'uf' in holder_data:
            unit = holder_data['uf']
        
        default_values = {
            'country': country,
            'federative_unit': unit,
            'region': uf_to_region.get(unit, None)
        }

        holder, _ = get_or_create(session, Participant, default_values, name = name)
        holders.append(holder)

    return holders


def insert_inventors(session, data):
    inventors = []
    for name in data['inventores']:
        inventor, _ = get_or_create(session, Participant, {}, name = name)
        inventors.append(inventor)

    return inventors


def insert_participations(session, production, holders, inventors):
    participations = []

    for holder in holders:
        p = Participation(
            patent = production,
            participant = holder,
            participation_type = "holder"
        )
        session.add(p)
        participations.append(p)

    for inventor in inventors:
        p = Participation(
            patent = production,
            participant = inventor,
            participation_type = "inventor"
        )
        session.add(p)
        participations.append(p)

    return participations


def insert_classifications(session, data):
    classifications = list()
    for code in data['IPC']:
        classification, _ = get_or_create(session, InternationalClassification, {}, code = code)
        classifications.append(classification)

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


def save_data_as_json():
    old_path = '..\data\\raw\\'
    final_path = '..\data\\final\\'
    
    types = {HolderType.E: 'Company', HolderType.P: 'Person', HolderType.I: 'Institution'}
    with Session.begin() as session:
        total = session.query(Patent).count()
        BATCH_SIZE = 2000
        offset = 0
        errors = 0
        while True:
            patents_batch = session.query(Patent).options(
                joinedload(Patent.participations)
                .joinedload(Participation.participant)
                .joinedload(Participant.unique),
                joinedload(Patent.international_classifications)
            ).offset(offset).limit(BATCH_SIZE).all()

            if not patents_batch:
                break

            if offset % 4000 == 0:
                print(f'{min(offset, total)}/{total} - {(offset * 100 / total):.2f} % - Erros: {errors}')
            offset += BATCH_SIZE

            for patent in patents_batch:
                old_data = {}
                
                try:
                    with open(f'{old_path}{patent.number}.json', 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                except Exception as e:
                    print(e)
                    errors += 1

                data = {
                    'applicationNumber': patent.number,
                    'filingDate': patent.filling_date or old_data.get('dataDeposito'),
                    'grantDate': old_data.get('dataConcessao'),
                    'title': patent.name,
                }

                if 'dataFaseNacional' in old_data:
                    data['nationalPhaseDate'] = old_data['dataFaseNacional'],

                international_application = None
                if 'pedidoInternacional' in old_data:
                    application = old_data['pedidoInternacional']
                    international_application = {
                        'pctNumber': application.get('numeroPCT'),
                        'pctDate': application.get('dataPCT'),
                        'wipoNumber': application.get('numeroOMPI'),
                        'wipoDate': application.get('dataOMPI'),
                    }
                    data['internationalApplication'] = international_application

                priority_claims = []
                if 'prioridadesUnionistas' in old_data:
                    for priority in old_data['prioridadesUnionistas']:
                        priority_claims.append({
                            'countryCode': priority.get('siglaPais'),
                            'priorityNumber': priority.get('numeroPrioridade'),
                            'priorityDate': priority.get('dataPrioridade'),
                        })
                    data['priorityClaims'] = priority_claims

                divisional_application = None
                if 'divisaoPedido' in old_data:
                    application = old_data['divisaoPedido']
                    divisional_application = {
                        'filingDate': application.get('dataDeposito'),
                        'applicationNumber': application.get('numero'),
                    }
                    data['divisionalApplication'] = divisional_application

                parent_application = None
                if 'pedidoPrincipal' in old_data:
                    application = old_data['pedidoPrincipal']
                    parent_application = {
                        'filingDate': application.get('dataDeposito'),
                        'applicationNumber': application.get('numero'),
                    }
                    data['parentApplication'] = parent_application

                events = []
                if 'despachos' in old_data:
                    for event in old_data['despachos']:
                        events.append({
                            'code': event.get('codigo'),
                            'description': event.get('titulo'),
                            'bulletinNumber ': event.get('rpi'),
                        })
                    data['events'] = events

                inventors = []
                holders = []
                for p in patent.participations:
                    if p.participation_type == ParticipationType.inventor:
                        inventors.append(p.participant.unique.name,)

                    elif p.participation_type == ParticipationType.holder:
                        holders.append({
                            'fullName': p.participant.unique.name,
                            'country': p.participant.country,
                            'state': p.participant.federative_unit,
                            'region': region.get(p.participant.region, None),
                            'type': types.get(p.participant.unique.type, None),
                        })

                data['inventors'] = inventors
                data['holders'] = holders

                classifications = [classification.code for classification in patent.international_classifications]
                data['ipcCodes'] = classifications

                with open(f'{final_path}{data["applicationNumber"]}.json', 'w') as f:
                    json.dump(data, f, indent = 4)

if __name__ == '__main__':
    create_models()
    populate()
    deduplicate_participants()
    count_elements()
    classify_participants
    save_data_as_json()
