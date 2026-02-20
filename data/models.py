from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, ForeignKey, TIMESTAMP, Interval
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import sys
import os

# Add the parent folder to the Python search path
parent_folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_folder_path)

# Base class for all models
Base = declarative_base()


class Paper(Base):
    __tablename__ = 'paper'
    # Primary Key
    id = Column(Integer, primary_key=True)
    pubmed_id = Column(Integer, nullable=True)
    # Columns
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    prediction_input = Column(Text, nullable=False)  # Title + Abstract
    key_terms = Column(Text, nullable=True)
    doi = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False)
    authors = Column(String(255), nullable=False)
    link_to_fulltext = Column(String(255), nullable=True)
    link_to_pubmed = Column(String(255), nullable=True)

    retrieval_id = Column(Integer, ForeignKey(
        'batch_retrieval.id'), nullable=False)

    # Relationship to BatchRetrieval (Many-to-One)
    batch_retrieval = relationship('BatchRetrieval', back_populates='papers')

    # Relationship to Prediction (One-to-Many)
    predictions = relationship('Prediction', back_populates='paper')

    ner_tags = relationship('NerTag', back_populates='paper')

    def __repr__(self):
        return f"<Paper(id={self.id}, title={self.title}, authors={self.authors})>"
    

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
    dosage_norm = relationship('DosageNormalization', back_populates='ner_tag', uselist=False)
    paper = relationship('Paper', back_populates='ner_tags')

    def __repr__(self):
        return f"<NerTag(id={self.id}, tag={self.tag}, text={self.text})>"


class DosageNormalization(Base):
    __tablename__ = 'dosage_normalization'

    id = Column(Integer, primary_key=True)

    ner_tag_id = Column(Integer, ForeignKey('ner_tag.id'), nullable=False, unique=True)
    norm_text= Column(String(255), nullable=False)
    min = Column(Float, nullable=False)
    max = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    per_weight_unit = Column(String(50), nullable=True)
    weight_reference = Column(Float, nullable=True)
    per_time_unit = Column(String(50), nullable=True)
    dose_type = Column(String(50), nullable=False)
    original_dosage = Column(String(255), nullable=False)

    ner_tag = relationship('NerTag', back_populates='dosage_norm')


class Prediction(Base):
    __tablename__ = 'prediction'

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
