from sqlalchemy import sql, Column, Sequence

from utils.db_api.database import db




class User(db.Model):
    __tablename__ = "users"
    query: sql.Select

    id = Column(db.Integer, Sequence("user_id_seq"), primary_key=True)
    tg_id = Column(db.Integer)
    username = Column(db.String(200))
    firstname = Column(db.String(200))
    lastname = Column(db.String(200))
    fullname = Column(db.String(200))
    groups = Column(db.String)

class Group(db.Model):
    __tablename__ = "groups"
    query: sql.Select

    id = Column(db.Integer, Sequence("user_id_seq"), primary_key=True)
    group_id = Column(db.Integer, Sequence("group_id_seq"), primary_key=True)
    name = Column(db.String(200))
    owner = Column(db.Integer)
    admins = Column(db.String)
    users = Column(db.String)
    isOpen = Column(db.Boolean)
    code = Column(db.String(200))


