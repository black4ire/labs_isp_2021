const form = document.querySelector('form')

form.addEventListener('submit', (event) => {
    event.preventDefault();

    categories = form.querySelectorAll('.category-check-item');
    categories.forEach(input => {
        if (!input.classList.contains('checked')){
            input.remove();
        }
    });

    event.currentTarget.submit();
});

