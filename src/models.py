import enum
from typing import List

from sqlalchemy import String, DateTime, Enum, ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.schema import Index

from utils import *
from settings import engine

class Base(DeclarativeBase):
    pass

class ParticipationType(enum.Enum):
    holder = 1
    inventor = 2

class HolderType(enum.Enum):
    I = 1
    E = 2
    P = 3

icp_patent = Table(
    "icp_patent",
    Base.metadata,
    Column("patent_id", ForeignKey("patent.id"), primary_key=True),
    Column("classification_id", ForeignKey("international_classification.id"), primary_key=True),
)

class Patent(Base):
    __tablename__ = "patent"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    filling_date = mapped_column(DateTime)
    participations: Mapped[List["Participation"]] = relationship(back_populates="patent")
    international_classifications: Mapped[List["InternationalClassification"]] = relationship(
        secondary = icp_patent, 
        back_populates = "patents"
    )

    def __repr__(self) -> str:
        return f"{self.name}"


class InternationalClassification(Base):
    __tablename__ = "international_classification"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    date = mapped_column(DateTime)

    patents: Mapped[List["Patent"]] = relationship(
        secondary = icp_patent, 
        back_populates = "international_classifications"
    )

    def __repr__(self) -> str:
        return f"{self.code}"

class Participation(Base):
    __tablename__ = "participation"

    id: Mapped[int] = mapped_column(primary_key=True)
    participation_type = mapped_column(Enum(ParticipationType))

    patent_id: Mapped[int] = mapped_column(ForeignKey("patent.id"))
    patent: Mapped["Patent"] = relationship(back_populates="participations")

    participant_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    participant: Mapped["Participant"] = relationship(back_populates="participations")

    def __repr__(self) -> str:
        return f"{self.participant.name} - {self.patent.name}"


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    country: Mapped[str] = mapped_column(String(4), nullable=True)
    federative_unit: Mapped[str] = mapped_column(String(2), nullable=True)
    region: Mapped[str] = mapped_column(Enum(Region), nullable = True)
    participations: Mapped[List["Participation"]] = relationship(back_populates="participant")

    unique_id: Mapped[int] = mapped_column(ForeignKey("unique_participant.id"), nullable=True)
    unique: Mapped["UniqueParticipant"] = relationship(back_populates="participants")

    def __repr__(self) -> str:
        return f"{self.name}"


class UniqueParticipant(Base):
    __tablename__ = "unique_participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type = mapped_column(Enum(HolderType), nullable=True)
    participants: Mapped[List["Participant"]] = relationship(back_populates="unique")

    def __repr__(self) -> str:
        return f"{self.name}"


Index("idx_patent_name", Patent.name)
Index("idx_classification_name", InternationalClassification.code)
Index("idx_participant_name", Participant.name)
Index("idx_unique_participant_name", UniqueParticipant.name)

def create_models():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_models()