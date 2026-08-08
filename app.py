import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Question, Option, Answer

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Create database tables automatically inside application context
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    now = datetime.now()
    # Filter questions active right now
    active_questions = Question.query.filter(
        Question.visible_at <= now,
        Question.hide_at >= now
    ).order_by(Question.created_at.desc()).all()

    return render_template('index.html', questions=active_questions)


@app.route('/create', methods=['GET', 'POST'])
def create_question():
    if request.method == 'POST':
        uploader_name = request.form.get('uploader_name', '').strip()
        question_text = request.form.get('question_text', '').strip()
        subject = request.form.get('subject', '').strip()
        unit = request.form.get('unit', '').strip()
        
        # Schedule Inputs
        visible_at_str = request.form.get('visible_at')
        hide_at_str = request.form.get('hide_at')

        if not all([uploader_name, question_text, subject, unit, visible_at_str, hide_at_str]):
            flash("Please fill in all required fields.")
            return redirect(url_for('create_question'))

        visible_at = datetime.strptime(visible_at_str, '%Y-%m-%dT%H:%M')
        hide_at = datetime.strptime(hide_at_str, '%Y-%m-%dT%H:%M')

        # 1. Create Question
        question = Question(
            uploader_name=uploader_name,
            question_text=question_text,
            subject=subject,
            unit=unit,
            visible_at=visible_at,
            hide_at=hide_at
        )
        db.session.add(question)
        db.session.flush()  # Generates question.id

        # 2. Process Options
        options_list = request.form.getlist('options')
        correct_index_raw = request.form.get('correct_option')

        if not options_list or correct_index_raw is None:
            flash("Please enter options and select the correct answer.")
            db.session.rollback()
            return redirect(url_for('create_question'))

        correct_index = int(correct_index_raw)
        created_options = []

        for text in options_list:
            opt = Option(question_id=question.id, option_text=text.strip())
            db.session.add(opt)
            created_options.append(opt)

        db.session.flush()

        # 3. Assign Correct Option ID
        question.correct_option_id = created_options[correct_index].id
        db.session.commit()

        flash("Question created and scheduled successfully! 🚀")
        return redirect(url_for('home'))

    return render_template('create_question.html')


@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = db.get_or_404(Question, question_id)

    if request.method == 'POST':
        user_name = request.form.get('user_name', '').strip()
        selected_option_id = request.form.get('selected_option', type=int)

        if not user_name or not selected_option_id:
            flash("Please enter your name and choose an answer option.")
            return redirect(url_for('view_question', question_id=question.id))

        # Check correctness against correct_option_id
        is_correct = (selected_option_id == question.correct_option_id)

        answer = Answer(
            question_id=question.id,
            user_name=user_name,
            selected_option_id=selected_option_id,
            is_correct=is_correct
        )
        db.session.add(answer)
        db.session.commit()

        flash("Answer submitted successfully!")
        return redirect(url_for('view_question', question_id=question.id))

    return render_template('view_question.html', question=question)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)