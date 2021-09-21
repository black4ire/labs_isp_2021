function readURL(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
            document.querySelector('#preview').setAttribute('src', e.target.result)
        };

        reader.readAsDataURL(input.files[0]);
    }
}

const pic_input = document.querySelector('#id_pic');
pic_input.setAttribute('onchange', 'readURL(this);');

//onchange="readURL(this);"