all_cats = document.querySelectorAll('.category-check-item')

all_cats.forEach(btn => {
    btn.addEventListener('click', () => {
        btn.classList.toggle('checked');
    });  
});