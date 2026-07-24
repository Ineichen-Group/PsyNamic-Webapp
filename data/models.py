import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (TIMESTAMP, Boolean, Column, Float, ForeignKey, Index,
                        Integer, Interval, String, Text, UniqueConstraint,
                        create_engine)
from sqlalchemy.orm import declarative_base, relationship

load_dotenv()
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Add the parent folder to the Python search path
parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

# Base class for all models
Base = declarative_base()


class Paper(Base):
    __tablename__ = 'paper'
    __table_args__ = (
        Index('idx_paper_date', 'date'),
        Index('idx_paper_entrez_year', 'entrez_year'),
        Index('idx_paper_pubmed_id', 'pubmed_id'),
    )
    # Primary Key
    id = Column(Integer, primary_key=True)
    pubmed_id = Column(Integer, nullable=True)
    # Columns
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    prediction_input = Column(Text, nullable=False)  # Title + Abstract
    key_terms = Column(Text, nullable=True)
    doi = Column(String(100), nullable=True)
    date = Column(TIMESTAMP, nullable=True)
    entrez_year = Column(Integer, nullable=True)
    authors = Column(Text, nullable=False)
    link_to_fulltext = Column(String(255), nullable=True)
    link_to_pubmed = Column(String(255), nullable=True)
    other_url = Column(Text, nullable=True)

    retrieval_id = Column(Integer, ForeignKey(
        'batch_retrieval.id'), nullable=False)

    # Relationship to BatchRetrieval (Many-to-One)
    batch_retrieval = relationship('BatchRetrieval', back_populates='papers')

    # Relationship to Prediction (One-to-Many)
    predictions = relationship('Prediction', back_populates='paper')

    ner_tags = relationship('NerTag', back_populates='paper')

    def __repr__(self):
        return f"<Paper(id={self.id}, title={self.title}, authors={self.authors})>"

    @property
    def url(self):
        if self.doi:
            return f"https://doi.org/{self.doi}"
        elif self.link_to_pubmed:
            return self.link_to_pubmed
        elif self.other_url:
            return self.other_url
        else:
            return None


class BatchRetrieval(Base):
    __tablename__ = 'batch_retrieval'

    # Primary Key
    id = Column(Integer, primary_key=True)

    # Columns
    date = Column(TIMESTAMP, default=datetime.utcnow)
    number_new_papers = Column(Integer, nullable=False)
    relevant_pred_time = Column(Interval, nullable=False)
    source_file = Column(String(255), nullable=True)

    # Relationship to Paper (One-to-Many)
    papers = relationship('Paper', back_populates='batch_retrieval')

    def __repr__(self):
        return f"<BatchRetrieval(id={self.id}, date={self.date}, number_new_papers={self.number_new_papers}, source_file={self.source_file})>"


class NerTag(Base):
    __tablename__ = 'ner_tag'
    __table_args__ = (
        UniqueConstraint('paper_id', 'start_id', 'end_id', 'tag',
                         'text', name='uq_nertag_paper_span_tag_text'),
        Index('idx_nertag_paper_tag', 'paper_id', 'tag'),
    )

    id = Column(Integer, primary_key=True)
    # Columns
    tag = Column(String(255), nullable=False)
    start_id = Column(Integer, nullable=False)
    end_id = Column(Integer, nullable=False)
    text = Column(String(255), nullable=False)
    probability = Column(Float, nullable=False)
    model = Column(String(255), nullable=False)

    paper_id = Column(Integer, ForeignKey('paper.id'), nullable=False)

    # Correct back_populates should match 'ner_tags' in Paper
    dosage_norm = relationship(
        'DosageNormalization', back_populates='ner_tag', uselist=False)
    paper = relationship('Paper', back_populates='ner_tags')

    def __repr__(self):
        return f"<NerTag(id={self.id}, tag={self.tag}, text={self.text})>"


class DosageNormalization(Base):
    __tablename__ = 'dosage_normalization'

    id = Column(Integer, primary_key=True)

    ner_tag_id = Column(Integer, ForeignKey('ner_tag.id'),
                        nullable=False, unique=True)
    norm_text = Column(String(255), nullable=False)
    min = Column(Float, nullable=False)
    max = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    per_weight_unit = Column(String(50), nullable=True)
    weight_reference = Column(Float, nullable=True)
    per_time_unit = Column(String(50), nullable=True)
    dose_type = Column(String(50), nullable=False)

    ner_tag = relationship('NerTag', back_populates='dosage_norm')


class Prediction(Base):
    __tablename__ = 'prediction'
    __table_args__ = (
        UniqueConstraint('paper_id', 'task', 'label', 'model',
                         name='uq_prediction_paper_task_label_model'),
        Index('idx_prediction_task_label_paper', 'task', 'label', 'paper_id'),
        Index('idx_prediction_paper_task', 'paper_id', 'task'),
    )
    # Primary Key
    id = Column(Integer, primary_key=True)

    # Foreign Key to Paper
    paper_id = Column(Integer, ForeignKey('paper.id'), nullable=False)

    # Columns
    task = Column(String(255), nullable=False)
    label = Column(String(255), nullable=False)
    probability = Column(Float, nullable=False)
    model = Column(String(255), nullable=False)
    is_multilabel = Column(Boolean, default=False)

    # Relationship to Paper (Many-to-One)
    paper = relationship('Paper', back_populates='predictions')

    def __repr__(self):
        return f"<Prediction(id={self.id}, task={self.task}, label={self.label}, probability={self.probability})>"


def init_db():
    # Names from the settings are used

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://{0}:{1}@{2}:{3}/{4}".format(
            DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)
    )
    engine = create_engine(DATABASE_URL, echo=True)

    Base.metadata.create_all(engine)


if __name__ == '__main__':
    init_db()
