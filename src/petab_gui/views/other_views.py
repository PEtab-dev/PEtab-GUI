"""Collection of other views aside from the main ones."""
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class DoseTimeDialog(QDialog):
    """Pick dose and time (or steady state)."""

    def __init__(self, columns: list[str], dose_suggested: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Dose and Time")
        order = [c for c in dose_suggested if c in columns] + [c for c in columns if c not in dose_suggested]
        self._dose = QComboBox(self)
        self._dose.addItems(order)
        self._time = QLineEdit(self)
        self._time.setPlaceholderText("Enter constant time (e.g. 0, 5, 12.5). Use 'inf' for steady state")
        self._preeq_edit = QLineEdit(self)
        self._preeq_edit.setPlaceholderText("Optional preequilibrationConditionId")
        self._dose_lbl = QLabel("Dose column:", self)
        self._time_lbl = QLabel("Time:", self)
        self._preeq_lbl = QLabel("Preequilibration condition (optional):", self)
        ok = QPushButton("OK", self)
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel", self)
        cancel.clicked.connect(self.reject)
        lay = QVBoxLayout(self)
        row1 = QHBoxLayout()
        row1.addWidget(self._dose_lbl)
        row1.addWidget(self._dose)
        lay.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(self._time_lbl)
        row2.addWidget(self._time)
        lay.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(self._preeq_lbl)
        row3.addWidget(self._preeq_edit)
        lay.addLayout(row3)
        btns = QHBoxLayout()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)

    def get_result(self) -> tuple[str | None, str | None]:
        dose = self._dose.currentText() or None
        time_text = (self._time.text() or "").strip() or None
        preeq = (self._preeq_edit.text() or "").strip()
        return dose, time_text, preeq
