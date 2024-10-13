class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///service.db"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECRET_KEY = "IITMBSMAD1"
    UPLOAD_FOLDER ='uploads/'