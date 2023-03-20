from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import os

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///grades.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.session.commit()

# CONFIGURE TABLES
class Grades(db.Model):
    __tablename__ = "grades"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(150), unique=True, nullable=False)
    grade = db.Column(db.String(10))
    assignments = relationship("Assignments", back_populates="subject")


class Assignments(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(150), nullable=False)
    grade = db.Column(db.String(10))
    score = db.Column(db.String(50))
    subject_id = db.Column(db.Integer, ForeignKey("grades.id"))
    subject = relationship("Grades", back_populates="assignments")


def add_new_grade(subject, grade):
    new_grade = Grades(
        subject=subject,
        grade=grade,
    )
    db.session.add(new_grade)
    db.session.commit()


def add_new_assignment(subject_id, description, grade, score):
    new_assignment = Assignments(
        description=description,
        grade=grade,
        score=score,
        subject_id=subject_id
    )
    db.session.add(new_assignment)
    db.session.commit()


def update_subject_grade(subject, new_grade):
    subject.grade = new_grade
    db.session.commit()


def update_assignment_grade(assignment, new_grade):
    assignment.grade = new_grade
    db.session.commit()


def get_subject(subject):
    grade = Grades.query.filter_by(subject=subject).first()
    return grade


def get_assignment(assignment_description):
    assignment = Assignments.query.filter_by(description=assignment_description).first()
    return assignment


def assignment_exist(assignment_description):
    assignment = Assignments.query.filter_by(description=assignment_description).first()
    if assignment:
        return True
    else:
        return False