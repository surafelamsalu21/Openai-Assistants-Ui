// static/landing.js
document.addEventListener('DOMContentLoaded', function() {
    const assistantCards = document.querySelectorAll('.assistant-card');
    
    assistantCards.forEach(card => {
        card.addEventListener('click', function() {
            const assistantId = this.getAttribute('data-assistant-id');
            if (assistantId) {
                window.location.href = `/chat?assistant_id=${assistantId}`;
            } else {
                console.error('Assistant ID not found.');
            }
        });
    });
});
