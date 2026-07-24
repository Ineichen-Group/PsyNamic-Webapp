document.addEventListener('click', function (e) {
    // Check if the clicked element (or its child icon) is a share button
    const btn = e.target.closest('.share-paper-btn');
    if (!btn) return;

    const paperId = btn.getAttribute('data-paper-id');
    if (!paperId) return;

    // Construct full absolute URL using current browser window origin & path
    const fullUrl = window.location.origin + window.location.pathname + '?study_id=' + paperId;

    // Write to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(fullUrl).then(() => {
            showSuccessFeedback(btn);
        }).catch(() => {
            fallbackCopy(fullUrl, btn);
        });
    } else {
        fallbackCopy(fullUrl, btn);
    }
});

function showSuccessFeedback(btn) {
    const origText = btn.innerHTML;
    btn.innerHTML = '✓ Copied!';
    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-success');
    setTimeout(() => {
        btn.innerHTML = origText;
        btn.classList.remove('btn-success');
        btn.classList.add('btn-outline-secondary');
    }, 2000);
}

function fallbackCopy(text, btn) {
    const dummy = document.createElement('input');
    document.body.appendChild(dummy);
    dummy.value = text;
    dummy.select();
    document.execCommand('copy');
    document.body.removeChild(dummy);
    showSuccessFeedback(btn);
}