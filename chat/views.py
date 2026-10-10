import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.db.models import Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Conversation, Message, UserProfile


def login_view(request):
    """
    Renders login screen and authenticates with either username OR email.
    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    error_message = None

    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '')

        if not login_id or not password:
            error_message = "Please provide both your username/email and password."
        else:
            user = authenticate(request, username=login_id, password=password)
            if user is not None:
                login(request, user)
                # Ensure UserProfile exists
                UserProfile.objects.get_or_create(user=user)
                return redirect('chat:dashboard')
            else:
                error_message = "Invalid username/email or password."

    return render(request, 'chat/auth.html', {
        'active_tab': 'login',
        'error_message': error_message
    })


def register_view(request):
    """
    Handles user registration with username, email, password, and preset avatar.
    """
    if request.user.is_authenticated:
        return redirect('chat:dashboard')

    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        avatar_id = request.POST.get('avatar_id', 'avatar_1')

        if not username or not email or not password:
            error_message = "All fields are required."
        elif password != confirm_password:
            error_message = "Passwords do not match."
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif User.objects.filter(username__iexact=username).exists():
            error_message = "That username is already taken."
        elif User.objects.filter(email__iexact=email).exists():
            error_message = "An account with that email already exists."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.avatar_id = avatar_id
            profile.save()

            # Auto-join default public group "#general" if exists or create it
            general_group, _ = Conversation.objects.get_or_create(
                name='general',
                is_direct_message=False,
                defaults={'created_by': user}
            )
            general_group.participants.add(user)

            login(request, user, backend='chat.backends.EmailOrUsernameModelBackend')
            return redirect('chat:dashboard')

    return render(request, 'chat/auth.html', {
        'active_tab': 'register',
        'error_message': error_message
    })


def logout_view(request):
    """Logs the user out and redirects to the login screen."""
    logout(request)
    return redirect('chat:login')


def forgot_password_view(request):
    """
    Generates password reset token and sends HTML recovery email via Brevo SMTP.
    """
    success_message = None
    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            error_message = "Please enter your email address."
        else:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset link using the active request host (e.g. ybchatapp.duckdns.org)
                scheme = 'https' if request.is_secure() or 'duckdns.org' in request.get_host() else 'http'
                reset_url = f"{scheme}://{request.get_host()}/reset-password/{uidb64}/{token}/"

                email_html = render_to_string('chat/emails/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                })

                try:
                    send_mail(
                        subject='Reset Your Tuko Chat Password',
                        message=f"Hello {user.username},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email.",
                        html_message=email_html,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False
                    )
                except Exception as e:
                    print("Error sending Brevo email:", e)

            # Always display generic success to prevent email enumeration
            success_message = "If an account exists with that email, a password reset link has been sent to your inbox."

    return render(request, 'chat/auth.html', {
        'active_tab': 'forgot',
        'success_message': success_message,
        'error_message': error_message
    })


def reset_password_confirm_view(request, uidb64, token):
    """
    Validates the password reset token and allows setting a new password.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    is_valid = user and default_token_generator.check_token(user, token)
    error_message = None
    success_message = None

    if not is_valid:
        error_message = "This password reset link is invalid or has expired."

    if request.method == 'POST' and is_valid:
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not password or len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error_message = "Passwords do not match."
        else:
            user.set_password(password)
            user.save()
            success_message = "Your password has been reset successfully! You can now log in."

    return render(request, 'chat/reset_password_confirm.html', {
        'is_valid': is_valid,
        'error_message': error_message,
        'success_message': success_message
    })


@login_required
@ensure_csrf_cookie
def dashboard_view(request):
    """
    The main WhatsApp / Slack style chat hub (Desktop & PWA).
    Renders conversations, direct messages, user search, and active messages.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Ensure default "#general" group exists and user is participant
    general_group, _ = Conversation.objects.get_or_create(
        name='general',
        is_direct_message=False,
        defaults={'created_by': request.user}
    )
    if request.user not in general_group.participants.all():
        general_group.participants.add(request.user)

    return render(request, 'chat/dashboard.html', {
        'user': request.user,
        'profile': profile
    })


# ==============================================================================
# REST / JSON API ENDPOINTS FOR CLIENT-SIDE VUE INTERACTIVITY
# ==============================================================================

@login_required
@require_GET
def api_conversations_list(request):
    """
    Returns all active conversations (DMs and public Groups) for the current user.
    """
    user_conversations = Conversation.objects.filter(
        Q(participants=request.user) | Q(is_direct_message=False)
    ).distinct()

    groups_data = []
    dms_data = []

    for conv in user_conversations:
        last_msg = conv.messages.order_by('-timestamp').first()
        last_msg_text = last_msg.text if last_msg else "No messages yet"
        last_msg_time = last_msg.timestamp.strftime("%I:%M %p") if last_msg else ""

        if conv.is_direct_message:
            other_user = conv.get_other_user(request.user)
            other_profile = getattr(other_user, 'profile', None) if other_user else None
            dms_data.append({
                'id': conv.id,
                'name': other_user.username if other_user else 'Unknown',
                'other_user_id': other_user.id if other_user else None,
                'avatar_id': other_profile.avatar_id if other_profile else 'avatar_1',
                'is_online': other_profile.is_online if other_profile else False,
                'last_message': last_msg_text,
                'last_time': last_msg_time,
                'is_group': False
            })
        else:
            is_creator = (conv.created_by_id == request.user.id)
            groups_data.append({
                'id': conv.id,
                'name': conv.name,
                'created_by': conv.created_by.username if conv.created_by else 'System',
                'is_creator': is_creator,
                'member_count': conv.participants.count(),
                'last_message': last_msg_text,
                'last_time': last_msg_time,
                'is_group': True
            })

    return JsonResponse({
        'groups': groups_data,
        'dms': dms_data
    })


@login_required
@require_GET
def api_conversation_messages(request, conversation_id):
    """
    Returns up to the last 100 messages and full member list for a given conversation.
    """
    conv = get_object_or_404(Conversation, id=conversation_id)

    # If it's a group, automatically join user as participant upon opening
    if not conv.is_direct_message and request.user not in conv.participants.all():
        conv.participants.add(request.user)
    elif conv.is_direct_message and request.user not in conv.participants.all():
        return JsonResponse({'error': 'Unauthorized to view this direct message'}, status=403)
    
    # Auto-prune beyond 100 messages if any excess exist
    conv.prune_messages(max_count=100)

    messages = conv.messages.select_related('sender', 'sender__profile').order_by('timestamp')[:100]

    messages_data = []
    for m in messages:
        sender_profile = getattr(m.sender, 'profile', None)
        messages_data.append({
            'id': m.id,
            'sender': m.sender.username,
            'sender_id': m.sender.id,
            'avatar_id': sender_profile.avatar_id if sender_profile else 'avatar_1',
            'is_me': m.sender.id == request.user.id,
            'text': m.text,
            'timestamp': m.timestamp.strftime("%I:%M %p")
        })

    # Build full member list for the members drawer
    members_data = []
    for p in conv.participants.select_related('profile').all():
        prof = getattr(p, 'profile', None)
        members_data.append({
            'id': p.id,
            'username': p.username,
            'avatar_id': prof.avatar_id if prof else 'avatar_1',
            'is_creator': (not conv.is_direct_message and conv.created_by_id == p.id),
            'is_me': (p.id == request.user.id),
        })

    is_creator = (not conv.is_direct_message and conv.created_by_id == request.user.id)

    return JsonResponse({
        'conversation_id': conv.id,
        'name': conv.get_display_name(request.user),
        'is_group': not conv.is_direct_message,
        'is_creator': is_creator,
        'created_by': conv.created_by.username if conv.created_by else 'System',
        'member_count': conv.participants.count(),
        'members': members_data,
        'messages': messages_data
    })


@login_required
@require_GET
def api_search_users(request):
    """
    Searches registered users by username or email (excluding current user).
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'users': []})

    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=request.user.id)[:15]

    results = []
    for u in users:
        prof = getattr(u, 'profile', None)
        results.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'avatar_id': prof.avatar_id if prof else 'avatar_1',
            'is_online': prof.is_online if prof else False
        })

    return JsonResponse({'users': results})


@login_required
@require_POST
def api_start_dm(request):
    """
    Finds or creates a 1-on-1 direct message conversation between current user and target user.
    """
    try:
        data = json.loads(request.body)
        target_user_id = data.get('target_user_id')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request payload'}, status=400)

    target_user = get_object_or_404(User, id=target_user_id)
    if target_user.id == request.user.id:
        return JsonResponse({'error': 'Cannot start DM with yourself'}, status=400)

    # Check if a 1-on-1 DM already exists between these two users
    existing_dm = Conversation.objects.filter(
        is_direct_message=True,
        participants=request.user
    ).filter(
        participants=target_user
    ).first()

    if existing_dm:
        conv = existing_dm
    else:
        conv = Conversation.objects.create(is_direct_message=True)
        conv.participants.add(request.user, target_user)

    return JsonResponse({
        'id': conv.id,
        'name': target_user.username,
        'other_user_id': target_user.id
    })


@login_required
@require_POST
def api_create_group(request):
    """
    Creates a new user-owned chat group. The creator is granted admin/deletion privileges.
    """
    try:
        data = json.loads(request.body)
        group_name = data.get('name', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request payload'}, status=400)

    if not group_name:
        return JsonResponse({'error': 'Group name cannot be empty'}, status=400)

    # Enforce clean group name
    clean_name = "".join(c for c in group_name if c.isalnum() or c in (' ', '_', '-')).strip()
    if not clean_name:
        return JsonResponse({'error': 'Group name must contain letters or numbers'}, status=400)

    # Create group with creator recorded
    group = Conversation.objects.create(
        name=clean_name,
        is_direct_message=False,
        created_by=request.user
    )
    group.participants.add(request.user)

    return JsonResponse({
        'id': group.id,
        'name': group.name,
        'is_creator': True,
        'created_by': request.user.username,
        'member_count': 1
    })


@login_required
@require_POST
def api_delete_group(request, group_id):
    """
    CREATOR-ONLY Group Deletion:
    Permits ONLY the user who created the group (created_by) to delete it.
    Notifies all active participants via WebSocket channel layer to dismiss the room.
    """
    group = get_object_or_404(Conversation, id=group_id, is_direct_message=False)

    # Security check: creator only
    if group.created_by_id != request.user.id:
        return JsonResponse({
            'error': 'Permission denied: Only the creator of this group has permission to delete it.'
        }, status=403)

    room_group_channel = f"conv_{group.id}"

    # Broadcast group_deleted event to all active WebSocket clients in this room
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            room_group_channel,
            {
                'type': 'group_deleted',
                'group_id': group.id,
                'group_name': group.name,
                'deleted_by': request.user.username
            }
        )

    # Delete from database (cascade deletes all related messages)
    group.delete()

    return JsonResponse({
        'success': True,
        'message': f"Group '{group.name}' successfully deleted."
    })
