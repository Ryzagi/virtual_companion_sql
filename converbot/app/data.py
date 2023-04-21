from pydantic import BaseModel


class CompanionList(BaseModel):
    user_id: int


class CompanionListOut(BaseModel):
    description: dict
    companion_id: str
    image_path_on_s3: str

class Tone(BaseModel):
    user_id: int
    content: str

class SelfieRequest(BaseModel):
    user_id: int


class SelfieWebRequest(BaseModel):
    user_id: int
    companion_id: str


class NewUser(BaseModel):
    user_id: int


class SQLHistory(BaseModel):
    user_id: int
    companion_id: str


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


class DeleteHistoryCompanion(BaseModel):
    user_id: int
    companion_id: str


class DeleteAllCompanions(BaseModel):
    user_id: int


class Message(BaseModel):
    user_id: int
    content: str


class Debug(BaseModel):
    user_id: int


class CompanionExists(BaseModel):
    user_id: int
