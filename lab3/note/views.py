from datetime import time
from django.core.checks import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from .models import Note, NoteForm
from django.shortcuts import get_object_or_404

def index(request):
    if request.user.is_authenticated:
        notes = Note.objects.filter(user__exact=request.user).order_by('create_time')

        return render(request, 'note/notes_list.html', {'notes': notes})
    else:
        return redirect('authentication/login')


def add(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)

            note.user = request.user
            now = timezone.now()
            note.create_time = now
            note.update_time = now
            note.save()

            return redirect('index')
        else:
            messages.error(request, "note is not valid")

    form = NoteForm()
    return render(request, 'note/add_note.html', {'form': form})


def delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
    else:
        note.delete()

    return redirect('index')


def edit(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('index')
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)

            note.user = request.user
            now = timezone.now()
            note.update_time = now
            note.save()

            return redirect('index')
    else:
        form = NoteForm(initial={
            'title': note.title,
            'content': note.content
        }, instance=note)
        return render(request, 'note/add_note.html', {'form': form})