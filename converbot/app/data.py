from pydantic import BaseModel


class CompanionList(BaseModel):
    user_id: int


class CompanionListOut(BaseModel):
    description: str
    companion_id: str


class SelfieRequest(BaseModel):
    user_id: int


class NewUser(BaseModel):
    user_id: int


class NewCompanion(BaseModel):
    user_id: int
    name: str
    age: str
    gender: str
    interest: str
    profession: str
    appearance: str
    relationship: str
    mood: str


class SwitchCompanion(BaseModel):
    user_id: int
    companion_id: str


class DeleteCompanion(BaseModel):
    user_id: int
    companion_id: str


class DeleteAllCompanions(BaseModel):
    user_id: int


class Message(BaseModel):
    user_id: int
    content: str


class Debug(BaseModel):
    user_id: int
