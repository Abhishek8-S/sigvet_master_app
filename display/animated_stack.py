"""
AnimatedStackedWidget
─────────────────────
A drop-in replacement for QStackedWidget that cross-fades between pages
using QGraphicsOpacityEffect + QPropertyAnimation.

Usage:
    stack = AnimatedStackedWidget()
    stack.setCurrentIndex(2)          # same API as QStackedWidget
    stack.slide_to(2)                 # explicit animated call (also used internally)
"""

from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore  import (QPropertyAnimation, QEasingCurve,
                           QParallelAnimationGroup, pyqtSlot)
from PyQt6.QtGui   import QPainter


class AnimatedStackedWidget(QStackedWidget):
    DURATION = 280   # ms for each fade animation

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animating = False

    # ── public API ─────────────────────────────────────────────────────────────
    def jump_to(self, index: int):
        """Switch instantly with NO animation — use for pages that must not flicker."""
        super().setCurrentIndex(index)

    def slide_to(self, index: int):
        """Fade out current page then fade in the target page."""
        if self._animating or index == self.currentIndex():
            return
        self._animating = True

        old_widget = self.currentWidget()
        self.setCurrentIndex(index)
        new_widget = self.currentWidget()

        if old_widget is None or new_widget is None or old_widget is new_widget:
            self._animating = False
            return

        # ── Fade-out the leaving page ────────────────────────────────────────
        old_fx = QGraphicsOpacityEffect(old_widget)
        old_widget.setGraphicsEffect(old_fx)
        out = QPropertyAnimation(old_fx, b"opacity", self)
        out.setStartValue(1.0)
        out.setEndValue(0.0)
        out.setDuration(self.DURATION // 2)
        out.setEasingCurve(QEasingCurve.Type.OutCubic)

        # ── Fade-in the arriving page ────────────────────────────────────────
        new_fx = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(new_fx)
        new_fx.setOpacity(0.0)
        inn = QPropertyAnimation(new_fx, b"opacity", self)
        inn.setStartValue(0.0)
        inn.setEndValue(1.0)
        inn.setDuration(self.DURATION)
        inn.setEasingCurve(QEasingCurve.Type.InOutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(out)
        group.addAnimation(inn)
        group.finished.connect(lambda: self._finish(old_widget, new_widget))
        group.start()

    @pyqtSlot()
    def _finish(self, old_w, new_w):
        # Remove effects so widgets paint normally afterwards
        if old_w is not None:
            old_w.setGraphicsEffect(None)
        if new_w is not None:
            new_w.setGraphicsEffect(None)
        self._animating = False

    # Override setCurrentIndex to automatically animate
    def setCurrentIndex(self, index: int):
        # Only animate if already shown (not during initial setup)
        if self.isVisible() and not self._animating and index != self.currentIndex():
            self.slide_to(index)
        else:
            super().setCurrentIndex(index)
