import csv
from settings import engine
from models import *
from sqlalchemy import func, case, select
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, joinedload, with_loader_criteria, selectinload
from utils import get_or_create

Session = sessionmaker(engine)

def create_edges():
    PAGE_SIZE = 100
    page = 0
    total = 0
    with Session.begin() as session:
        stmt = select(func.count()).select_from(Patent)
        total = session.execute(stmt).scalar()

    print(f'Total de patentes: {total}')

    adj = dict()

    while True:
        with Session.begin() as session:
            stmt = (
                select(Patent)
                .options(
                    with_loader_criteria(
                        Participation,
                        lambda cls: cls.participation_type == ParticipationType.holder,
                        include_aliases=True,
                    ),
                    selectinload(Patent.participations)
                    .selectinload(Participation.participant)
                    .selectinload(Participant.unique),
                    selectinload(Patent.international_classifications)
                )
                .limit(PAGE_SIZE)
                .offset(page * PAGE_SIZE)
            )

            if page % 20 == 0:
                print(f'{page * PAGE_SIZE}/{total} - {((page * PAGE_SIZE * 100) / total):.2f}')

            results = session.execute(stmt).scalars().all()

            if not results:
                break

            for patent in results:

                granted = 0
                if patent.granted == True:
                    granted = 1

                initials = dict()
                
                for classification in patent.international_classifications:
                    code = classification.code[0]
                    initials[code] = 1

                for p1 in patent.participations:
                    for p2 in patent.participations:
                        id1 = p1.participant.unique_id
                        id2 = p2.participant.unique_id
                        if id1 != id2:
                            s = p1.participant_id
                            d = p2.participant_id

                            # Ja inseriu
                            if s > d:
                                break
                            
                            edge = (s, d)
                            if edge not in adj:
                                adj[edge] = {
                                    'jointly_granted_patents': granted, 
                                    'jointly_filed_patents': 1,
                                    'c_filed': dict(),
                                    'c_granted': dict()}
                            else:
                                adj[edge]['jointly_granted_patents'] += granted
                                adj[edge]['jointly_filed_patents'] += 1

                            data = adj[edge]
                            name = 'c_filed'
                            if granted:
                                name = 'c_granted'

                            for c in 'ABCDEFGH':
                                data[name][c] = data[name].get(c, 0) + initials.get(c, 0)

            page += 1

    with open('../data/network/edges.csv', 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = [
            'holder_u_id', 
            'holder_v_id', 
            'jointly_granted_patents', 
            'jointly_filed_patents', 
            'jointly_granted_patents_per_ipc',
            'jointly_filed_patents_per_ipc'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for s, d in adj:
            data = adj[(s, d)]
            granted, filed = [], []
            for c in 'ABCDEFGH':
                granted.append(data['c_granted'].get(c, 0))
                filed.append(data['c_filed'].get(c, 0))
            data.pop('c_granted')
            data.pop('c_filed')
            object = {
                "holder_u_id": s, 
                "holder_v_id": d, 
                **adj[(s, d)], 
                "jointly_granted_patents_per_ipc": granted,
                "jointly_filed_patents_per_ipc": filed
            }
            writer.writerow(object)
            
if __name__ == '__main__':
    create_edges()
