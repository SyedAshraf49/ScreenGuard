from datetime import datetime, timedelta
from core.memory_store import SOCIAL

class SocialFeatures:
    def __init__(self):
        self.local_username = SOCIAL["privacy"].get("local_username", "you")

    def _now(self):
        return datetime.now().isoformat(timespec="seconds")

    def _next_id(self, key):
        next_value = SOCIAL["counters"][key]
        SOCIAL["counters"][key] += 1
        return next_value

    def get_privacy_settings(self):
        return dict(SOCIAL["privacy"])

    def update_privacy_settings(self, **settings):
        for key, value in settings.items():
            SOCIAL["privacy"][key] = str(value)
        self.local_username = SOCIAL["privacy"].get("local_username", "you")

    def add_friend(self, username, display_name=None):
        if not username:
            return False
        current = SOCIAL["friends"].get(username, {})
        SOCIAL["friends"][username] = {
            "username": username,
            "display_name": display_name or current.get("display_name"),
            "blocked": current.get("blocked", False),
            "added_at": self._now()
        }
        return True

    def list_friends(self, include_blocked=False):
        friends = list(SOCIAL["friends"].values())
        if not include_blocked:
            friends = [f for f in friends if not f["blocked"]]
        friends.sort(key=lambda f: f["username"])
        return friends

    def block_user(self, username, blocked=True):
        friend = SOCIAL["friends"].get(username)
        if not friend:
            return False
        friend["blocked"] = bool(blocked)
        return True

    def share_achievement(self, achievement_id, message=None, audience="friends", targets=None):
        if not achievement_id:
            return None
        share_id = self._next_id("share_id")
        SOCIAL["shares"].append({
            "id": share_id,
            "achievement_id": achievement_id,
            "message": message or "",
            "audience": audience,
            "targets": targets or [],
            "created_at": self._now()
        })
        return share_id

    def create_group(self, name, is_private=True):
        if not name:
            return None
        group_id = self._next_id("group_id")
        SOCIAL["groups"][group_id] = {
            "id": group_id,
            "name": name,
            "is_private": bool(is_private),
            "created_at": self._now()
        }
        SOCIAL["group_members"].append({
            "id": self._next_id("participant_id"),
            "group_id": group_id,
            "username": self.local_username,
            "role": "owner",
            "joined_at": self._now()
        })
        return group_id

    def list_groups(self):
        groups = list(SOCIAL["groups"].values())
        groups.sort(key=lambda g: g["created_at"], reverse=True)
        return groups

    def add_group_member(self, group_id, username, role="member"):
        if not group_id or not username:
            return False
        for member in SOCIAL["group_members"]:
            if member["group_id"] == group_id and member["username"] == username:
                return True
        SOCIAL["group_members"].append({
            "id": self._next_id("participant_id"),
            "group_id": group_id,
            "username": username,
            "role": role,
            "joined_at": self._now()
        })
        return True

    def send_group_message(self, group_id, content, sender=None):
        if not group_id or not content:
            return False
        SOCIAL["group_messages"].append({
            "id": self._next_id("message_id"),
            "group_id": group_id,
            "sender": sender or self.local_username,
            "content": content,
            "created_at": self._now()
        })
        return True

    def list_group_messages(self, group_id, limit=20):
        messages = [
            msg for msg in SOCIAL["group_messages"]
            if msg["group_id"] == group_id
        ]
        messages.sort(key=lambda m: m["id"], reverse=True)
        rows = [
            (msg["sender"], msg["content"], msg["created_at"])
            for msg in messages[:limit]
        ]
        return list(reversed(rows))

    def create_challenge(self, title, challenge_type, participants, duration_days, group_id=None, anonymous=False):
        if not title or duration_days <= 0:
            return None
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=duration_days)
        challenge_id = self._next_id("challenge_id")
        SOCIAL["challenges"][challenge_id] = {
            "id": challenge_id,
            "title": title,
            "challenge_type": challenge_type,
            "group_id": group_id,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "status": "active",
            "is_anonymous": bool(anonymous),
            "created_at": self._now()
        }
        for participant in participants:
            SOCIAL["challenge_participants"].append({
                "id": self._next_id("participant_id"),
                "challenge_id": challenge_id,
                "username": participant,
                "score": 0,
                "completed": False,
                "last_updated": self._now()
            })
        return challenge_id

    def list_challenges(self):
        challenges = list(SOCIAL["challenges"].values())
        challenges.sort(key=lambda c: c["created_at"], reverse=True)
        return challenges

    def update_challenge_score(self, challenge_id, username, score):
        for participant in SOCIAL["challenge_participants"]:
            if participant["challenge_id"] == challenge_id and participant["username"] == username:
                participant["score"] = score
                participant["last_updated"] = self._now()
                return True
        return False

    def close_challenge(self, challenge_id):
        challenge = SOCIAL["challenges"].get(challenge_id)
        if not challenge:
            return False
        challenge["status"] = "closed"
        return True

    def get_leaderboard(self, challenge_id, top_n=10):
        participants = [
            p for p in SOCIAL["challenge_participants"]
            if p["challenge_id"] == challenge_id
        ]
        participants.sort(key=lambda p: (-p["score"], p["username"]))
        return [(p["username"], p["score"]) for p in participants[:top_n]]
