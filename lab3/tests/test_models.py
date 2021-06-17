import pytest
from note.models import Note, NoteForm
from django.contrib.auth.models import User
from django.utils.timezone import now


@pytest.fixture
def user():
    return User.objects.create_user("Vasya", "vasya@gmail.com", "vasyapassword")


@pytest.fixture
def note(user):
    return Note.objects.create(user=user, title="Sample note")


@pytest.mark.django_db
def test_create_note(note):
    assert Note.objects.count() == 1


@pytest.mark.django_db
def test_note_type(note):
    assert isinstance(note, Note)


@pytest.mark.django_db
def test_owner(note, user):
    assert note.user == user


@pytest.mark.django_db
def test_str(note):
    assert note.title == str(note)
