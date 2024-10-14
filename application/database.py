import enum
from flask_sqlalchemy import SQLAlchemy
import datetime
db = SQLAlchemy()


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=False)

    professional = db.relationship('Professional', backref='user', uselist=False)
    customer = db.relationship('Customers', backref='user', uselist=False)

class Services(db.Model):
    service_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    min_price = db.Column(db.Integer, nullable=False)
    min_time_req = db.Column(db.String(200), nullable=False)

    requests = db.relationship('Requests', backref='services')

class Professional(db.Model): 
    proff_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=True)
    experience = db.Column(db.Integer,nullable=True)
    desc = db.Column(db.String(500), nullable=True)
    city = db.Column(db.String(150), nullable=False)
    docs_url = db.Column(db.String(1000), nullable=True)
    is_occupied = db.Column(db.Boolean, default=False) 

    services = db.relationship('Services', 
                             backref='professionals')
    requests = db.relationship('Requests', backref='professional')

class Customers(db.Model):
    cust_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    city = db.Column(db.String(150), nullable=False)

    requests= db.relationship("Requests", backref="customers", lazy=True)

class Requests(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('customers.cust_id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    requested_time= db.Column(db.DateTime, default=datetime.datetime.now)
    proff_id = db.Column(db.Integer, db.ForeignKey('professional.proff_id'), default=None)  
    status= db.Column(db.String(150), nullable=False)

    reviews=db.relationship("Reviews", backref="requests", lazy=True)

class Reviews(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.request_id'), nullable=False)
    proff_id = db.Column(db.Integer, db.ForeignKey('professional.proff_id'), nullable=False)  
    rating= db.Column(db.String(150), nullable=False)
    review= db.Column(db.String(150), nullable=False)

class Complains(db.Model):
    complain_id= db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.request_id'), nullable=False)
    proff_id = db.Column(db.Integer, db.ForeignKey('professional.proff_id'), nullable=False)  
    desc= db.Column(db.String(1000), nullable=False)
