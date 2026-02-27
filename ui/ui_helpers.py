from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


def apply_card_shadow(card):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(18)
    effect.setOffset(0, 6)
    effect.setColor(QColor(0, 0, 0, 80))
    card.setGraphicsEffect(effect)
