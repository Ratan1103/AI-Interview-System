/**
 * InterviewAI — main.js
 *
 * Global JS utilities shared across pages.
 * Page-specific JS (voice recording, interview loop) lives
 * inline in the respective templates to keep things simple.
 */

/* ── Auto-dismiss toast messages after 5 seconds ─────────── */
document.addEventListener('DOMContentLoaded', () => {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, 5000);
    });
});

/* ── Disable submit buttons on form submit (prevent double-submit) ── */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            // Skip the interview form — it has its own loading overlay
            if (form.id === 'answerForm') return;
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Please wait…';
            }
        });
    });
});
