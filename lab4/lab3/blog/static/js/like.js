like_btn = document.querySelector('a.like-btn');
  like_icon = like_btn.querySelector('i.fa-heart');

  like_btn.addEventListener('click', (event) =>{
    event.preventDefault();
    if (like_icon.classList.contains('far')){
      if (confirm("Хотите сделать пост любимым?") == true)
        window.location.replace(like_btn.getAttribute("href"));
    }
    else if (like_icon.classList.contains('fas')){
      if (confirm("Хотите удалить пост из любимых?") == true){
        window.location.replace(like_btn.getAttribute("href"));
      }
    }
  });