from pydantic import BaseModel


class Patent(BaseModel):
    id: str
    registration_date: str
    receipt_date: str
    full_name: str
    type: str
    name_of_work: str
    work_creation_date: str
    status: str
