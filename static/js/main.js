document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('verify-form');
    const loadingModal = document.getElementById('loading-modal');
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name-display');

    // Display chosen filename on upload box
    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = `Selected File: ${fileInput.files[0].name}`;
                fileNameDisplay.classList.remove('hidden');
            }
        });
    }

    // Show step-by-step terminal loading window on form submit
    if (form && loadingModal) {
        form.addEventListener('submit', () => {
            loadingModal.classList.remove('hidden');

            const steps = [
                { id: 'step-ocr', delay: 400 },
                { id: 'step-db', delay: 1000 },
                { id: 'step-ela', delay: 1800 },
                { id: 'step-ai', delay: 2500 }
            ];

            steps.forEach(step => {
                setTimeout(() => {
                    const el = document.getElementById(step.id);
                    if (el) {
                        el.classList.remove('text-gray-500');
                        el.classList.add('text-green-400', 'font-bold');
                    }
                }, step.delay);
            });
        });
    }
});