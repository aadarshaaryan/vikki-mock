import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Question, Option, Answer

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database extension
db.init_app(app)

# Ensure database tables exist in Supabase on app startup
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database initialization warning: {e}")


@app.route('/')
def home():
    # Use UTC time to match Render's server clock and ensure accurate scheduling
    now = datetime.utcnow()

    # Filter questions scheduled to be active right now
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
        question_type = request.form.get('question_type', 'mcq')  # 'mcq', 'subjective', or 'code'

        # Schedule Inputs
        visible_at_str = request.form.get('visible_at')
        hide_at_str = request.form.get('hide_at')

        if not all([uploader_name, question_text, subject, unit, visible_at_str, hide_at_str]):
            flash("Please fill in all required fields.")
            return redirect(url_for('create_question'))

        try:
            visible_at = datetime.strptime(visible_at_str, '%Y-%m-%dT%H:%M')
            hide_at = datetime.strptime(hide_at_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash("Invalid date/time format provided.")
            return redirect(url_for('create_question'))

        # 1. Create Base Question
        question = Question(
            uploader_name=uploader_name,
            question_text=question_text,
            subject=subject,
            unit=unit,
            question_type=question_type,
            visible_at=visible_at,
            hide_at=hide_at
        )
        db.session.add(question)
        db.session.flush()  # Generate question.id before commit

        # 2. Process Options if question type is MCQ
        if question_type == 'mcq':
            options_list = request.form.getlist('options')
            correct_index_raw = request.form.get('correct_option')

            if not options_list or correct_index_raw is None:
                flash("Please enter options and select the correct answer for the MCQ.")
                db.session.rollback()
                return redirect(url_for('create_question'))

            correct_index = int(correct_index_raw)
            created_options = []

            for text in options_list:
                opt = Option(question_id=question.id, option_text=text.strip())
                db.session.add(opt)
                created_options.append(opt)

            db.session.flush()

            # Guard against invalid choice index selection
            if 0 <= correct_index < len(created_options):
                question.correct_option_id = created_options[correct_index].id
            else:
                question.correct_option_id = created_options[0].id

        db.session.commit()
        flash("Question published and scheduled successfully! 🚀")
        return redirect(url_for('home'))

    return render_template('create_question.html')


@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = db.get_or_404(Question, question_id)

    if request.method == 'POST':
        user_name = request.form.get('user_name', '').strip()

        if not user_name:
            flash("Please enter your name before submitting your response.")
            return redirect(url_for('view_question', question_id=question.id))

        if question.question_type == 'mcq':
            selected_option_id = request.form.get('selected_option', type=int)

            if not selected_option_id:
                flash("Please select an answer choice.")
                return redirect(url_for('view_question', question_id=question.id))

            # Auto-grade MCQ against uploader's choice
            is_correct = (selected_option_id == question.correct_option_id)

            answer = Answer(
                question_id=question.id,
                user_name=user_name,
                selected_option_id=selected_option_id,
                is_correct=is_correct
            )
        else:
            # Handle subjective or code response
            answer_text = request.form.get('answer_text', '').strip()

            if not answer_text:
                flash("Please enter your answer response text.")
                return redirect(url_for('view_question', question_id=question.id))

            answer = Answer(
                question_id=question.id,
                user_name=user_name,
                answer_text=answer_text,
                is_correct=None  # Requires manual review
            )

        db.session.add(answer)
        db.session.commit()

        flash("Your answer has been submitted! ✅")
        return redirect(url_for('view_question', question_id=question.id))

    return render_template('view_question.html', question=question)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)