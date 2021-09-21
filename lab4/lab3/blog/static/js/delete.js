delete_btn = document.querySelector('a.delete-btn');
  
delete_btn.addEventListener('click', (event) =>{
    event.preventDefault();
    if (confirm("Хотите удалить пост?") == true){
        window.location.replace(delete_btn.getAttribute("href"));
    }
});