"""
views.py — Core application views.

Flow:
  home → register → login → dashboard → upload_resume → configure_interview
       → interview (GET: first question) → interview (POST: answer loop)
       → end_interview (session summary)

Session keys used during interview:
  interview_config   : dict — experience, difficulty, topic, interview_type, years
  interview_question : str  — current question being answered
  interview_history  : list — [{question, answer}, ...] (last 10 kept)
  interview_count    : int  — total questions asked this session
"""

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import Resume
from .utils import extract_text_from_pdf
from .ai import generate_first_question, get_feedback_and_next


# ─── Public Views ─────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')

        if not all([username, email, password, confirm]):
            return render(request, 'register.html', {'error': 'All fields are required.'})
        if password != confirm:
            return render(request, 'register.html', {'error': 'Passwords do not match.'})
        if len(password) < 8:
            return render(request, 'register.html', {'error': 'Password must be at least 8 characters.'})
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already taken.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered.'})

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Account created! Please log in.')
        return redirect('login')

    return render(request, 'register.html')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            return render(request, 'login.html', {'error': 'Please enter your credentials.'})

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url else 'dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})

    return render(request, 'login.html')


def logout_view(request):
    for key in ['interview_config', 'interview_question', 'interview_history', 'interview_count']:
        request.session.pop(key, None)
    logout(request)
    return redirect('home')


# ─── Authenticated Views ───────────────────────────────────────────────────────

@login_required
def dashboard(request):
    resume = Resume.objects.filter(user=request.user).first()
    return render(request, 'dashboard.html', {
        'resume':     resume,
        'has_resume': bool(resume and resume.extracted_text),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def upload_resume(request):
    if request.method == 'POST':
        file = request.FILES.get('resume')

        if not file:
            return render(request, 'upload_resume.html', {'error': 'Please select a file.'})
        if not file.name.lower().endswith('.pdf'):
            return render(request, 'upload_resume.html', {'error': 'Only PDF files are supported.'})

        # Extract text BEFORE seeking back (extract reads the file)
        extracted_text = extract_text_from_pdf(file)

        if not extracted_text:
            return render(request, 'upload_resume.html', {
                'error': 'Could not extract text from this PDF. '
                         'Make sure it is not a scanned / image-only PDF.'
            })

        # Seek back so Django can save the file to disk
        file.seek(0)
        resume, _ = Resume.objects.get_or_create(user=request.user)
        resume.file = file
        resume.extracted_text = extracted_text
        resume.save()

        messages.success(request, 'Resume uploaded successfully!')
        return redirect('dashboard')

    return render(request, 'upload_resume.html')


@login_required
@require_http_methods(['POST'])
def configure_interview(request):
    """
    Receives interview config form (POST only).
    Saves config to session, clears old interview state, redirects to /interview/.
    """
    experience     = request.POST.get('experience', 'Fresher')
    years          = request.POST.get('years', '').strip()
    difficulty     = request.POST.get('difficulty', 'Medium')
    interview_type = request.POST.get('interview_type', 'Full Interview')
    topic          = request.POST.get('topic', '').strip() or None

    resume = Resume.objects.filter(user=request.user).first()
    if not resume or not resume.extracted_text:
        messages.error(request, 'Please upload your resume before starting an interview.')
        return redirect('dashboard')

    # Save config and reset all interview state atomically
    request.session['interview_config']   = {
        'experience':     experience,
        'years':          years,
        'difficulty':     difficulty,
        'interview_type': interview_type,
        'topic':          topic,
    }
    request.session['interview_question'] = None
    request.session['interview_history']  = []
    request.session['interview_count']    = 0
    # Force session save — needed because we're replacing mutable objects
    request.session.modified = True

    return redirect('interview')


@login_required
def interview(request):
    """
    GET  → Generate and show the first question of this session.
    POST → Accept the user's answer, get AI feedback + next question.

    Refreshing GET will re-generate question 1 (intentional — new session start).
    """
    config = request.session.get('interview_config')
    if not config:
        messages.error(request, 'Please configure your interview first.')
        return redirect('dashboard')

    resume = Resume.objects.filter(user=request.user).first()
    if not resume or not resume.extracted_text:
        messages.error(request, 'Resume not found. Please upload your resume.')
        return redirect('upload_resume')

    resume_text    = resume.extracted_text
    experience     = config.get('experience', 'Fresher')
    years          = config.get('years', '')
    difficulty     = config.get('difficulty', 'Medium')
    topic          = config.get('topic')

    exp_label = experience
    if experience == 'Experienced' and years:
        exp_label = f"Experienced ({years} years)"

    # ── GET: first question ───────────────────────────────────────────────────
    if request.method == 'GET':
        try:
            question = generate_first_question(
                resume=resume_text,
                experience=exp_label,
                difficulty=difficulty,
                topic=topic,
            )
        except Exception as e:
            messages.error(request, f'AI error: {e}. Please check your Gemini API key.')
            return redirect('dashboard')

        request.session['interview_question'] = question
        request.session['interview_count']    = 1
        request.session['interview_history']  = []
        request.session.modified = True

        return render(request, 'interview.html', {
            'question':        question,
            'question_number': 1,
            'config':          config,
            'feedback':        None,
        })

    # ── POST: evaluate answer, next question ─────────────────────────────────
    answer           = request.POST.get('answer', '').strip()
    current_question = request.session.get('interview_question', '')
    history          = list(request.session.get('interview_history', []))  # copy — avoid mutation issues
    count            = request.session.get('interview_count', 1)

    if not answer:
        return render(request, 'interview.html', {
            'question':        current_question,
            'question_number': count,
            'config':          config,
            'feedback':        None,
            'error':           'Please provide an answer before submitting.',
        })

    try:
        result = get_feedback_and_next(
            resume=resume_text,
            experience=exp_label,
            difficulty=difficulty,
            topic=topic,
            history=history,
            current_question=current_question,
            candidate_answer=answer,
        )
    except Exception as e:
        return render(request, 'interview.html', {
            'question':        current_question,
            'question_number': count,
            'config':          config,
            'feedback':        None,
            'error':           f'AI error: {e}. Please try again.',
        })

    # Update history and session
    history.append({'question': current_question, 'answer': answer})
    history = history[-10:]
    next_question = result.get('next_question', current_question)
    count += 1

    request.session['interview_question'] = next_question
    request.session['interview_history']  = history
    request.session['interview_count']    = count
    request.session.modified = True

    return render(request, 'interview.html', {
        'question':        next_question,
        'question_number': count,
        'config':          config,
        'feedback':        result,
        'prev_question':   current_question,
        'prev_answer':     answer,
    })


@login_required
def end_interview(request):
    """GET or POST — works from the <a> link in interview.html."""
    history = list(request.session.get('interview_history', []))
    config  = dict(request.session.get('interview_config', {}))

    for key in ['interview_config', 'interview_question', 'interview_history', 'interview_count']:
        request.session.pop(key, None)
    request.session.modified = True

    return render(request, 'interview_end.html', {
        'history': history,
        'config':  config,
        'total':   len(history),
    })
