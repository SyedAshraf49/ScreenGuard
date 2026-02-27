from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QScrollArea
)
from core.social_features import SocialFeatures
from ui.ui_helpers import apply_card_shadow

class SocialPage(QWidget):
    def __init__(self):
        super().__init__()
        self.social = SocialFeatures()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Social & Accountability")
        title.setObjectName("title")
        layout.addWidget(title)

        layout.addWidget(self._build_friends_card())
        layout.addWidget(self._build_groups_card())
        layout.addWidget(self._build_challenges_card())
        layout.addWidget(self._build_sharing_card())
        layout.addWidget(self._build_privacy_card())

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.refresh_friends()
        self.refresh_groups()
        self.refresh_challenges()
        self._load_privacy_settings()

    def _build_friends_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Friends")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        row = QHBoxLayout()
        self.friend_input = QLineEdit()
        self.friend_input.setPlaceholderText("Add friend by username")
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(90)
        add_btn.clicked.connect(self.on_add_friend)
        row.addWidget(self.friend_input, 1)
        row.addWidget(add_btn)
        v.addLayout(row)

        block_row = QHBoxLayout()
        self.block_input = QLineEdit()
        self.block_input.setPlaceholderText("Block or unblock username")
        block_btn = QPushButton("Block")
        unblock_btn = QPushButton("Unblock")
        block_btn.setFixedWidth(90)
        unblock_btn.setFixedWidth(90)
        block_btn.clicked.connect(lambda: self.on_block_friend(True))
        unblock_btn.clicked.connect(lambda: self.on_block_friend(False))
        block_row.addWidget(self.block_input, 1)
        block_row.addWidget(block_btn)
        block_row.addWidget(unblock_btn)
        v.addLayout(block_row)

        self.friends_list = QListWidget()
        self.friends_list.setMinimumHeight(90)
        v.addWidget(self.friends_list)

        self.friend_status = QLabel("")
        v.addWidget(self.friend_status)

        card.setLayout(v)
        return card

    def _build_groups_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Groups & Messaging")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        row = QHBoxLayout()
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Group name")
        self.group_private_cb = QCheckBox("Private")
        self.group_private_cb.setChecked(True)
        create_btn = QPushButton("Create Group")
        create_btn.setFixedWidth(130)
        create_btn.clicked.connect(self.on_create_group)
        row.addWidget(self.group_name_input, 1)
        row.addWidget(self.group_private_cb)
        row.addWidget(create_btn)
        v.addLayout(row)

        self.groups_list = QListWidget()
        self.groups_list.setMinimumHeight(90)
        self.groups_list.currentItemChanged.connect(self.on_group_selected)
        v.addWidget(self.groups_list)

        member_row = QHBoxLayout()
        self.member_input = QLineEdit()
        self.member_input.setPlaceholderText("Add member username")
        member_btn = QPushButton("Add Member")
        member_btn.setFixedWidth(120)
        member_btn.clicked.connect(self.on_add_member)
        member_row.addWidget(self.member_input, 1)
        member_row.addWidget(member_btn)
        v.addLayout(member_row)

        msg_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Send a group message")
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(90)
        send_btn.clicked.connect(self.on_send_message)
        msg_row.addWidget(self.message_input, 1)
        msg_row.addWidget(send_btn)
        v.addLayout(msg_row)

        self.messages_list = QListWidget()
        self.messages_list.setMinimumHeight(90)
        v.addWidget(self.messages_list)

        self.group_status = QLabel("")
        v.addWidget(self.group_status)

        card.setLayout(v)
        return card

    def _build_challenges_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Challenges & Leaderboards")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        row = QHBoxLayout()
        self.challenge_title_input = QLineEdit()
        self.challenge_title_input.setPlaceholderText("Challenge title")
        self.challenge_type_box = QComboBox()
        self.challenge_type_box.addItems([
            "Screen-Free Sunday",
            "Most Focus Sessions",
            "Lowest Social Media Usage",
            "Team Goal"
        ])
        self.challenge_days = QSpinBox()
        self.challenge_days.setRange(1, 60)
        self.challenge_days.setValue(7)
        self.challenge_type_box.setFixedWidth(180)
        self.challenge_days.setFixedWidth(80)
        row.addWidget(self.challenge_title_input, 1)
        row.addWidget(self.challenge_type_box)
        row.addWidget(self.challenge_days)
        v.addLayout(row)

        row2 = QHBoxLayout()
        self.challenge_participants_input = QLineEdit()
        self.challenge_participants_input.setPlaceholderText("Participants (comma-separated usernames)")
        self.challenge_anonymous_cb = QCheckBox("Anonymous leaderboard")
        create_btn = QPushButton("Create Challenge")
        create_btn.setFixedWidth(150)
        create_btn.clicked.connect(self.on_create_challenge)
        row2.addWidget(self.challenge_participants_input, 1)
        row2.addWidget(self.challenge_anonymous_cb)
        row2.addWidget(create_btn)
        v.addLayout(row2)

        self.challenges_list = QListWidget()
        self.challenges_list.setMinimumHeight(90)
        self.challenges_list.currentItemChanged.connect(self.on_challenge_selected)
        v.addWidget(self.challenges_list)

        leaderboard_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Leaderboard")
        refresh_btn.clicked.connect(self.on_refresh_leaderboard)
        leaderboard_row.addWidget(refresh_btn)
        leaderboard_row.addStretch()
        v.addLayout(leaderboard_row)

        self.leaderboard_list = QListWidget()
        self.leaderboard_list.setMinimumHeight(90)
        v.addWidget(self.leaderboard_list)

        self.challenge_status = QLabel("")
        v.addWidget(self.challenge_status)

        card.setLayout(v)
        return card

    def _build_sharing_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Share Achievements")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        row = QHBoxLayout()
        self.achievement_id_input = QLineEdit()
        self.achievement_id_input.setPlaceholderText("Achievement ID or name")
        self.share_message_input = QLineEdit()
        self.share_message_input.setPlaceholderText("Optional message")
        row.addWidget(self.achievement_id_input, 1)
        row.addWidget(self.share_message_input, 1)
        v.addLayout(row)

        row2 = QHBoxLayout()
        self.share_audience_box = QComboBox()
        self.share_audience_box.addItems(["friends", "group", "public"])
        self.share_targets_input = QLineEdit()
        self.share_targets_input.setPlaceholderText("Targets (usernames or group ID)")
        share_btn = QPushButton("Share")
        share_btn.setFixedWidth(100)
        share_btn.clicked.connect(self.on_share_achievement)
        self.share_audience_box.setFixedWidth(120)
        row2.addWidget(self.share_audience_box)
        row2.addWidget(self.share_targets_input, 1)
        row2.addWidget(share_btn)
        v.addLayout(row2)

        self.share_status = QLabel("")
        v.addWidget(self.share_status)

        card.setLayout(v)
        return card

    def _build_privacy_card(self):
        card = QFrame()
        card.setObjectName("card")
        apply_card_shadow(card)
        v = QVBoxLayout()
        v.setSpacing(10)
        header = QLabel("Privacy Controls")
        header.setObjectName("cardTitle")
        v.addWidget(header)

        self.share_achievements_cb = QCheckBox("Allow achievement sharing")
        self.share_stats_cb = QCheckBox("Allow statistics sharing")
        self.anonymous_leaderboard_cb = QCheckBox("Use anonymous leaderboards")

        v.addWidget(self.share_achievements_cb)
        v.addWidget(self.share_stats_cb)
        v.addWidget(self.anonymous_leaderboard_cb)

        row = QHBoxLayout()
        self.local_username_input = QLineEdit()
        self.local_username_input.setPlaceholderText("Local username")
        save_btn = QPushButton("Save Privacy Settings")
        save_btn.setFixedWidth(180)
        save_btn.clicked.connect(self.on_save_privacy)
        row.addWidget(self.local_username_input, 1)
        row.addWidget(save_btn)
        v.addLayout(row)

        self.privacy_status = QLabel("")
        v.addWidget(self.privacy_status)

        card.setLayout(v)
        return card

    def refresh_friends(self):
        self.friends_list.clear()
        friends = self.social.list_friends(include_blocked=True)
        if not friends:
            self.friends_list.addItem("No friends yet")
            return
        for friend in friends:
            status = "blocked" if friend["blocked"] else "active"
            label = f"{friend['username']} ({status})"
            item = QListWidgetItem(label)
            self.friends_list.addItem(item)

    def refresh_groups(self):
        self.groups_list.clear()
        groups = self.social.list_groups()
        if not groups:
            self.groups_list.addItem("No groups yet")
            return
        for group in groups:
            label = f"{group['name']} (ID {group['id']})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, group["id"])
            self.groups_list.addItem(item)

    def refresh_challenges(self):
        self.challenges_list.clear()
        challenges = self.social.list_challenges()
        if not challenges:
            self.challenges_list.addItem("No challenges yet")
            return
        for challenge in challenges:
            label = f"{challenge['title']} [{challenge['status']}] (ID {challenge['id']})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, challenge["id"])
            self.challenges_list.addItem(item)

    def _load_privacy_settings(self):
        settings = self.social.get_privacy_settings()
        self.share_achievements_cb.setChecked(settings.get("share_achievements", "1") == "1")
        self.share_stats_cb.setChecked(settings.get("share_stats", "1") == "1")
        self.anonymous_leaderboard_cb.setChecked(settings.get("anonymous_leaderboards", "0") == "1")
        self.local_username_input.setText(settings.get("local_username", "you"))

    def _get_selected_group_id(self):
        item = self.groups_list.currentItem()
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _get_selected_challenge_id(self):
        item = self.challenges_list.currentItem()
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def on_add_friend(self):
        username = self.friend_input.text().strip()
        if not username:
            self.friend_status.setText("Enter a username to add.")
            return
        self.social.add_friend(username)
        self.friend_input.clear()
        self.friend_status.setText(f"Added {username}.")
        self.refresh_friends()

    def on_block_friend(self, blocked):
        username = self.block_input.text().strip()
        if not username:
            self.friend_status.setText("Enter a username to block or unblock.")
            return
        if self.social.block_user(username, blocked=blocked):
            action = "Blocked" if blocked else "Unblocked"
            self.friend_status.setText(f"{action} {username}.")
        else:
            self.friend_status.setText("User not found.")
        self.refresh_friends()

    def on_create_group(self):
        name = self.group_name_input.text().strip()
        if not name:
            self.group_status.setText("Enter a group name.")
            return
        group_id = self.social.create_group(name, is_private=self.group_private_cb.isChecked())
        if group_id:
            self.group_status.setText(f"Group created with ID {group_id}.")
            self.group_name_input.clear()
        else:
            self.group_status.setText("Group creation failed.")
        self.refresh_groups()

    def on_group_selected(self, current, _previous):
        group_id = self._get_selected_group_id()
        self.messages_list.clear()
        if not group_id:
            return
        messages = self.social.list_group_messages(group_id)
        if not messages:
            self.messages_list.addItem("No messages yet")
            return
        for sender, content, created_at in messages:
            self.messages_list.addItem(f"{created_at} {sender}: {content}")

    def on_add_member(self):
        group_id = self._get_selected_group_id()
        username = self.member_input.text().strip()
        if not group_id or not username:
            self.group_status.setText("Select a group and enter a username.")
            return
        self.social.add_group_member(group_id, username)
        self.member_input.clear()
        self.group_status.setText(f"Added {username} to group.")

    def on_send_message(self):
        group_id = self._get_selected_group_id()
        content = self.message_input.text().strip()
        if not group_id or not content:
            self.group_status.setText("Select a group and enter a message.")
            return
        self.social.send_group_message(group_id, content)
        self.message_input.clear()
        self.group_status.setText("Message sent.")
        self.on_group_selected(self.groups_list.currentItem(), None)

    def on_create_challenge(self):
        title = self.challenge_title_input.text().strip()
        challenge_type = self.challenge_type_box.currentText()
        duration = self.challenge_days.value()
        participants_text = self.challenge_participants_input.text().strip()
        participants = [p.strip() for p in participants_text.split(",") if p.strip()]
        if self.social.local_username not in participants:
            participants.append(self.social.local_username)
        if not title:
            self.challenge_status.setText("Enter a challenge title.")
            return
        challenge_id = self.social.create_challenge(
            title,
            challenge_type,
            participants,
            duration,
            group_id=self._get_selected_group_id(),
            anonymous=self.challenge_anonymous_cb.isChecked()
        )
        if challenge_id:
            self.challenge_status.setText(f"Challenge created with ID {challenge_id}.")
            self.challenge_title_input.clear()
            self.challenge_participants_input.clear()
        else:
            self.challenge_status.setText("Challenge creation failed.")
        self.refresh_challenges()

    def on_challenge_selected(self, current, _previous):
        self.on_refresh_leaderboard()

    def on_refresh_leaderboard(self):
        challenge_id = self._get_selected_challenge_id()
        self.leaderboard_list.clear()
        if not challenge_id:
            return
        leaderboard = self.social.get_leaderboard(challenge_id)
        if not leaderboard:
            self.leaderboard_list.addItem("No scores yet")
            return
        for username, score in leaderboard:
            self.leaderboard_list.addItem(f"{username}: {score}")

    def on_share_achievement(self):
        achievement_id = self.achievement_id_input.text().strip()
        message = self.share_message_input.text().strip()
        audience = self.share_audience_box.currentText()
        targets = []
        targets_text = self.share_targets_input.text().strip()
        if targets_text:
            targets = [t.strip() for t in targets_text.split(",") if t.strip()]
        share_id = self.social.share_achievement(achievement_id, message, audience, targets)
        if share_id:
            self.share_status.setText(f"Shared achievement ({share_id}).")
            self.achievement_id_input.clear()
            self.share_message_input.clear()
            self.share_targets_input.clear()
        else:
            self.share_status.setText("Share failed.")

    def on_save_privacy(self):
        self.social.update_privacy_settings(
            share_achievements="1" if self.share_achievements_cb.isChecked() else "0",
            share_stats="1" if self.share_stats_cb.isChecked() else "0",
            anonymous_leaderboards="1" if self.anonymous_leaderboard_cb.isChecked() else "0",
            local_username=self.local_username_input.text().strip() or "you"
        )
        self.privacy_status.setText("Privacy settings saved.")

    def refresh(self):
        self.refresh_friends()
        self.refresh_groups()
        self.refresh_challenges()
        self._load_privacy_settings()
