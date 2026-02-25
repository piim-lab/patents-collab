import enum
class Region(enum.Enum):
    NORTH = 1
    NORTHEAST = 2
    CENTRAL_WEST = 3
    SOUTHEAST = 4
    SOUTH = 5

region = {
    Region.NORTH: 'North',
    Region.NORTHEAST: 'Northeast',
    Region.CENTRAL_WEST: 'Central West',
    Region.SOUTHEAST: 'Southeast',
    Region.SOUTH: 'South'
}

uf_to_region = {
    # Norte
    "AC": Region.NORTH,
    "AP": Region.NORTH,
    "AM": Region.NORTH,
    "PA": Region.NORTH,
    "RO": Region.NORTH,
    "RR": Region.NORTH,
    "TO": Region.NORTH,

    # Nordeste
    "AL": Region.NORTHEAST,
    "BA": Region.NORTHEAST,
    "CE": Region.NORTHEAST,
    "MA": Region.NORTHEAST,
    "PB": Region.NORTHEAST,
    "PE": Region.NORTHEAST,
    "PI": Region.NORTHEAST,
    "RN": Region.NORTHEAST,
    "SE": Region.NORTHEAST,

    # Centro-Oeste
    "DF": Region.CENTRAL_WEST,
    "GO": Region.CENTRAL_WEST,
    "MT": Region.CENTRAL_WEST,
    "MS": Region.CENTRAL_WEST,

    # Sudeste
    "ES": Region.SOUTHEAST,
    "MG": Region.SOUTHEAST,
    "RJ": Region.SOUTHEAST,
    "SP": Region.SOUTHEAST,

    # Sul
    "PR": Region.SOUTH,
    "RS": Region.SOUTH,
    "SC": Region.SOUTH
}

def get_or_create(session, model, default_values=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        if instance not in session:
            instance = session.merge(instance)
        return instance, False
    else:
        params = {**kwargs}
        if default_values:
            params.update(default_values)
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True
    

def create(session, model, default_values=None):
    instance = model(**default_values)
    session.add(instance)
    session.flush()
    return instance, True


def get_model(session, model, default_values=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance and instance not in session:
        instance = session.merge(instance)
    return instance, False
