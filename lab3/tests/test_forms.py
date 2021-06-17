import pytest
from note.models import Note, NoteForm
from authentication.models import SignupForm
from django.contrib.auth.models import User
from django.utils.timezone import now


@pytest.fixture
def note_data(user):
    return {"user": user, "title": "test title", "content": "sample content"}


@pytest.fixture
def user_data():
    return {"username": "Vasya", "email": "vasya@gmail.com", "password1": "vasyapassword", "password2": "vasyapassword"}


@pytest.fixture
def user():
    return User.objects.create_user("Vasya", "vasya@gmail.com", "vasyapassword")


@pytest.fixture
def note(note_data):
    return Note.objects.create(**note_data)


@pytest.fixture
def note_form(note_data):
    return NoteForm(data=note_data)


@pytest.fixture
def signup_form(user_data):
    return SignupForm(data=user_data)


@pytest.mark.django_db
def test_user_type(signup_form):
    assert signup_form.is_valid()
    assert isinstance(signup_form.save(commit=False), User)

@pytest.mark.django_db
def test_note_type(note_form):
    assert note_form.is_valid()
    assert isinstance(note_form.save(commit=False), Note)


@pytest.mark.django_db
def test_add_same_user(signup_form, user):
    assert not signup_form.is_valid()


@pytest.mark.django_db
def test_note_values(note_form, note_data):
    note = note_form.save(commit=False)
    assert note.title == note_data["title"]
    assert note.content == note_data["content"]
