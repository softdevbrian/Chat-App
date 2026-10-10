from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends standard Django User with avatar selection, online presence,
    and last activity timestamps.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_id = models.CharField(max_length=50, default='avatar_1')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class Conversation(models.Model):
    """
    Unified conversation entity supporting:
    1. Public / User-created Chat Groups (name is set, created_by is owner)
    2. 1-on-1 Direct Messages (is_direct_message=True, name is blank)
    """
    name = models.CharField(max_length=100, blank=True)
    is_direct_message = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conversations'
    )
    participants = models.ManyToManyField(User, related_name='conversations', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.is_direct_message:
            return f"DM: {', '.join([u.username for u in self.participants.all()[:2]])}"
        return f"Group: {self.name}"

    def prune_messages(self, max_count=100):
        """
        Auto-prunes messages so this conversation strictly retains only the
        100 most recent messages, auto-deleting older ones to keep the database lightweight.
        """
        excess_ids = list(self.messages.order_by('-timestamp').values_list('id', flat=True)[max_count:])
        if excess_ids:
            self.messages.filter(id__in=excess_ids).delete()

    def get_display_name(self, for_user):
        """Returns the appropriate title for the UI depending on who is viewing."""
        if self.is_direct_message:
            other = self.participants.exclude(id=for_user.id).first()
            return other.username if other else "Direct Chat"
        return self.name

    def get_other_user(self, for_user):
        """For direct messages, returns the other participant."""
        if self.is_direct_message:
            return self.participants.exclude(id=for_user.id).first()
        return None


class Message(models.Model):
    """
    Individual text chat message tied to a conversation and sender.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:30]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Touch conversation's updated_at
        self.conversation.save(update_fields=['updated_at'])
        # Automatically prune messages beyond the 100 most recent
        self.conversation.prune_messages(max_count=100)
