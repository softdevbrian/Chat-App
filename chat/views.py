from django.shortcuts import render

def index(request):
    """
    Renders the chat lobby landing page where users enter
    their username and choose/create a chat room.
    """
    return render(request, 'chat/index.html')

def room(request, room_name):
    """
    Renders the active chat room interface for the given room_name.
    """
    return render(request, 'chat/room.html', {
        'room_name': room_name
    })
