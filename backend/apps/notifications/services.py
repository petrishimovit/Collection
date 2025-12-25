from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification


class NotificationService:
    """Notification domain service."""

    @transaction.atomic
    def create(self, *, for_user, type: str, info: dict | None = None) -> Notification:
        """Create a notification for a user."""
        return Notification.objects.create(
            for_user=for_user,
            type=type,
            info=info or {},
        )

    @transaction.atomic
    def check_all(self, *, for_user) -> int:
        """Mark all user notifications as checked."""
        return Notification.objects.filter(
            for_user=for_user,
            is_checked=False,
        ).update(
            is_checked=True,
            updated_at=timezone.now(),
        )

    @transaction.atomic
    def create_follow(self, *, target_user, follower_user) -> Notification:
        """Create a follow notification for target user."""
        return self.create(
            for_user=target_user,
            type=Notification.Type.FOLLOW,
            info={"user_id": str(follower_user.pk)},
        )

    @transaction.atomic
    def create_post_for_followers(self, *, author, post) -> int:
        """Create post notifications for all author followers."""
        from apps.accounts.models import Follow

        follower_ids = list(
            Follow.objects.filter(following=author).values_list("follower_id", flat=True)
        )
        if not follower_ids:
            return 0

        items = [
            Notification(
                for_user_id=follower_id,
                type=Notification.Type.POST_CREATE,
                info={"user_id": str(author.pk), "post_id": str(post.pk)},
                is_checked=False,
            )
            for follower_id in follower_ids
        ]
        Notification.all_objects.bulk_create(items, batch_size=1000)
        return len(items)

    @transaction.atomic
    def create_post_reaction(self, *, post, actor, reaction_type: str) -> Notification | None:
        """Create a reaction notification for post author."""
        author = getattr(post, "author", None)
        if author is None or author == actor:
            return None

        return self.create(
            for_user=author,
            type=Notification.Type.POST_LIKE,
            info={
                "user_id": str(actor.pk),
                "post_id": str(post.pk),
                "reaction_type": reaction_type,
            },
        )

    @transaction.atomic
    def create_comment_like(self, *, comment, actor) -> Notification | None:
        """Create comment-like notification for comment author."""
        author = getattr(comment, "author", None)
        actor_id = getattr(actor, "id", None)

        if author is None or actor_id is None or author.id == actor_id:
            return None

        return self.create(
            for_user=author,
            type=Notification.Type.COMMENT_LIKE,
            info={
                "user_id": str(actor_id),
                "comment_id": str(comment.pk),
                "post_id": str(comment.post_id),
            },
        )

    @transaction.atomic
    def create_collection_for_followers(self, *, owner, collection) -> int:
        """Notify all followers about new collection."""
        from apps.accounts.models import Follow

        if collection.privacy != "public":
            return

        follower_ids = list(
            Follow.objects.filter(following=owner).values_list("follower_id", flat=True)
        )
        if not follower_ids:
            return 0

        items = [
            Notification(
                for_user_id=follower_id,
                type=Notification.Type.COLLECTION_CREATE,
                info={
                    "user_id": str(owner.id),
                    "collection_id": str(collection.id),
                },
                is_checked=False,
            )
            for follower_id in follower_ids
        ]
        Notification.all_objects.bulk_create(items, batch_size=1000)
        return len(items)

    @transaction.atomic
    def create_item_for_followers(self, *, item) -> int:
        """Notify followers about new public item in public collection."""
        collection = item.collection
        owner = collection.owner

        if collection.privacy != "public":
            return 0
        if item.privacy != "public":
            return 0

        from apps.accounts.models import Follow

        follower_ids = list(
            Follow.objects.filter(following=owner).values_list("follower_id", flat=True)
        )
        if not follower_ids:
            return 0

        notifications = [
            Notification(
                for_user_id=follower_id,
                type=Notification.Type.ITEM_CREATE,
                info={
                    "user_id": str(owner.id),
                    "collection_id": str(collection.id),
                    "item_id": str(item.id),
                },
            )
            for follower_id in follower_ids
        ]
        Notification.all_objects.bulk_create(notifications, batch_size=1000)
        return len(notifications)
