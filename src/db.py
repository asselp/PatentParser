from sqlalchemy import create_engine, exc
from sqlalchemy import Column, MetaData, String, Table, Date
from sqlalchemy.sql import func

from src.conf import ENGINE
from src.models import Patent
from src.utils import get_logger


class Saver:
    """Saves/updates/ deletes patents"""

    def __init__(self):
        self.engine = create_engine(ENGINE)
        self.meta = MetaData(self.engine)
        self.table = Table('patentss', self.meta,
                           Column('id', String, primary_key=True),
                           Column('registration_date', Date),
                           Column('receipt_date', Date),
                           Column('full_name', String),
                           Column('type', String),
                           Column('name_of_work', String),
                           Column('work_creation_date', Date),
                           Column('status', String))
        self.logger = get_logger('Saver')

        if not self.engine.has_table("patentss"):
            self.table.create()

    def save_patents(self, records: Patent):
        with self.engine.connect() as conn:
            insert_statement = self.table.insert().values(id=records.id,
                                                          registration_date=func.to_date(records.registration_date,
                                                                                         'DD.MM.YYYY'),
                                                          receipt_date=func.to_date(records.receipt_date, 'DD.MM.YYYY'),
                                                          full_name=records.full_name,
                                                          type=records.type,
                                                          name_of_work=records.name_of_work,
                                                          work_creation_date=func.to_date(records.work_creation_date,
                                                                                          'DD.MM.YYYY'),
                                                          status=records.status)
            try:
                conn.execute(insert_statement)
                self.logger.info('Row was writen to DB')
            except exc.ObjectNotExecutableError as e:
                self.logger.error(f'Transaction error: {e}')
