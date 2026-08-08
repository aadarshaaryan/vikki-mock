from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    uploader_name = db.Column(db.String(100), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(100), nullable=False)
    
    # Question type: 'mcq', 'subjective', or 'code'
    question_type = db.Column(db.String(20), nullable=False, default='mcq')

    # Foreign key reference for MCQ correct choice (nullable for non-MCQ)
    correct_option_id = db.Column(db.Integer, nullable=True)
    
    # Visibility schedule settings
    visible_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hide_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    options = db.relationship(
        'Option', 
        backref='question', 
        cascade="all, delete-orphan", 
        foreign_keys='Option.question_id'
    )
    answers = db.relationship('Answer', backref='question', cascade="all, delete-orphan")

    def is_currently_visible(self):
        now = datetime.utcnow()
        return self.visible_at <= now <= self.hide_at


class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    option_text = db.Column(db.String(255), nullable=False)


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    
    # Nullable choice for MCQs
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
    
    # Response text for Subjective / Code questions
    answer_text = db.Column(db.Text, nullable=True)
    
    # Auto-grading boolean (True/False for MCQ, None for Subjective/Code)
    is_correct = db.Column(db.Boolean, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    selected_option = db.relationship('Option')