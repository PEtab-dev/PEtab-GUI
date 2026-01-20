"""Collection of other views aside from the main ones."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)


class DoseTimeDialog(QDialog):
    """Pick dose and time (or steady state)."""

    def __init__(
        self, columns: list[str], dose_suggested: list[str], parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Dose and Time")
        order = [c for c in dose_suggested if c in columns] + [
            c for c in columns if c not in dose_suggested
        ]
        self._dose = QComboBox(self)
        self._dose.addItems(order)
        self._time = QLineEdit(self)
        self._time.setPlaceholderText(
            "Enter constant time (e.g. 0, 5, 12.5). Use 'inf' for steady state"
        )
        self._preeq_edit = QLineEdit(self)
        self._preeq_edit.setPlaceholderText(
            "Optional preequilibrationConditionId"
        )
        self._dose_lbl = QLabel("Dose column:", self)
        self._time_lbl = QLabel("Time:", self)
        self._preeq_lbl = QLabel(
            "Preequilibration condition (optional):", self
        )
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

    def get_result(self) -> tuple[str | None, str | None, str]:
        dose = self._dose.currentText() or None
        time_text = (self._time.text() or "").strip() or None
        preeq = (self._preeq_edit.text() or "").strip()
        return dose, time_text, preeq


class NextStepsPanel(QDialog):
    """Non-modal panel showing possible next steps after saving."""

    dont_show_again_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Possible next steps")
        self.setModal(False)
        self.setMinimumWidth(450)
        self.setMaximumWidth(600)
        self.setMinimumHeight(360)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Description
        desc = QLabel(
            "This parameter estimation problem can now be used in the following tools:"
        )
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Main suggestions
        suggestions_layout = QVBoxLayout()
        suggestions_layout.setSpacing(8)

        # Benchmark Collection action
        benchmark_frame = QFrame()
        benchmark_frame.setStyleSheet(
            "QFrame { background-color: rgba(255, 193, 7, 0.08); "
            "border-radius: 4px; padding: 8px; }"
        )
        benchmark_layout = QVBoxLayout(benchmark_frame)
        benchmark_layout.setContentsMargins(8, 8, 8, 8)
        benchmark_layout.setSpacing(4)

        benchmark_text = QTextBrowser()
        benchmark_text.setOpenExternalLinks(True)
        benchmark_text.setFrameStyle(QFrame.NoFrame)
        benchmark_text.setStyleSheet(
            "QTextBrowser { background: transparent; }"
        )
        benchmark_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        benchmark_text.setHtml(
            '<p style="margin:0; line-height:1.3;">'
            "<b>📚 Contribute to Benchmark Collection</b><br/>"
            "Share your PEtab problem with the community to validate it, "
            "enable reproducibility, and support benchmarking<br/>"
            '<a href="https://github.com/Benchmarking-Initiative/'
            'Benchmark-Models-PEtab">Benchmark Collection</a></p>'
        )
        benchmark_layout.addWidget(benchmark_text)
        suggestions_layout.addWidget(benchmark_frame)

        # pyPESTO action
        pypesto_frame = QFrame()
        pypesto_frame.setStyleSheet(
            "QFrame { background-color: rgba(100, 149, 237, 0.08); "
            "border-radius: 4px; padding: 8px; }"
        )
        pypesto_layout = QVBoxLayout(pypesto_frame)
        pypesto_layout.setContentsMargins(8, 8, 8, 8)
        pypesto_layout.setSpacing(4)

        pypesto_text = QTextBrowser()
        pypesto_text.setOpenExternalLinks(True)
        pypesto_text.setFrameStyle(QFrame.NoFrame)
        pypesto_text.setStyleSheet("QTextBrowser { background: transparent; }")
        pypesto_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        pypesto_text.setHtml(
            '<p style="margin:0; line-height:1.3;">'
            "<b>▶ Parameter Estimation with pyPESTO</b><br/>"
            "Use pyPESTO for parameter estimation, uncertainty analysis, "
            "and model selection<br/>"
            '<a href="https://pypesto.readthedocs.io/en/latest/example/'
            'petab_import.html">pyPESTO documentation</a></p>'
        )
        pypesto_layout.addWidget(pypesto_text)
        suggestions_layout.addWidget(pypesto_frame)

        # COPASI action
        copasi_frame = QFrame()
        copasi_frame.setStyleSheet(
            "QFrame { background-color: rgba(169, 169, 169, 0.08); "
            "border-radius: 4px; padding: 8px; }"
        )
        copasi_layout = QVBoxLayout(copasi_frame)
        copasi_layout.setContentsMargins(8, 8, 8, 8)
        copasi_layout.setSpacing(4)

        copasi_text = QTextBrowser()
        copasi_text.setOpenExternalLinks(True)
        copasi_text.setFrameStyle(QFrame.NoFrame)
        copasi_text.setStyleSheet("QTextBrowser { background: transparent; }")
        copasi_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        copasi_text.setHtml(
            '<p style="margin:0; line-height:1.3;">'
            "<b>⚙ Advanced Model Adaptation and Simulation</b><br/>"
            "Use COPASI for further model adjustment and advanced "
            "simulation with a graphical interface<br/>"
            '<a href="https://copasi.org">COPASI website</a></p>'
        )
        copasi_layout.addWidget(copasi_text)
        suggestions_layout.addWidget(copasi_frame)

        main_layout.addLayout(suggestions_layout)

        # Collapsible section for other tools
        self._other_tools_btn = QPushButton(
            "📊 ▶ Other tools supporting PEtab"
        )
        self._other_tools_btn.setCheckable(True)
        self._other_tools_btn.setFlat(True)
        self._other_tools_btn.setStyleSheet(
            "QPushButton { text-align: left; padding: 6px; "
            "font-weight: normal; }"
            "QPushButton:checked { font-weight: bold; }"
        )
        self._other_tools_btn.clicked.connect(self._toggle_other_tools)
        main_layout.addWidget(self._other_tools_btn)

        # Other tools frame (initially hidden)
        self._other_tools_frame = QFrame()
        self._other_tools_frame.setStyleSheet(
            "QFrame { background-color: rgba(144, 238, 144, 0.08); "
            "border-radius: 4px; padding: 8px; }"
        )
        self._other_tools_frame.setVisible(False)
        other_tools_layout = QVBoxLayout(self._other_tools_frame)
        other_tools_layout.setContentsMargins(8, 8, 8, 8)
        other_tools_layout.setSpacing(4)

        # Framing text
        framing_text = QLabel("Additional tools in the PEtab ecosystem:")
        framing_text.setWordWrap(True)
        other_tools_layout.addWidget(framing_text)

        other_tools_text = QTextBrowser()
        other_tools_text.setOpenExternalLinks(True)
        other_tools_text.setMaximumHeight(120)
        other_tools_text.setFrameStyle(QFrame.NoFrame)
        other_tools_text.setStyleSheet(
            "QTextBrowser { background: transparent; }"
        )
        other_tools_text.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        other_tools_text.setHtml(
            '<ul style="margin:4px 0; padding-left: 20px; '
            'line-height: 1.6;">'
            '<li style="margin-bottom: 4px;">'
            '<a href="https://amici.readthedocs.io/en/latest/examples/'
            'example_petab/petab.html">AMICI</a> - '
            "Efficient simulation and sensitivity analysis</li>"
            '<li style="margin-bottom: 4px;">'
            '<a href="https://sebapersson.github.io/PEtab.jl/stable/">'
            "PEtab.jl</a> - "
            "High-performance Julia parameter estimation</li>"
            '<li style="margin-bottom: 4px;">'
            '<a href="https://github.com/Data2Dynamics/d2d/wiki">'
            "Data2Dynamics</a> - "
            "MATLAB-based comprehensive modeling framework</li>"
            '<li style="margin-bottom: 4px;">'
            '<a href="https://petab.readthedocs.io/en/latest/v1/'
            'software_support.html">PEtab documentation</a> - '
            "Full list of supporting tools</li>"
            "</ul>"
        )
        other_tools_layout.addWidget(other_tools_text)

        main_layout.addWidget(self._other_tools_frame)

        # Spacer
        main_layout.addStretch()

        # Reassurance text
        reassurance = QLabel(
            "<small><i>You can always access this dialog from the "
            "Help menu.</i></small>"
        )
        reassurance.setWordWrap(True)
        reassurance.setStyleSheet("QLabel { color: gray; padding: 0; }")
        main_layout.addWidget(reassurance)

        # Bottom section with checkbox and close button
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        self._dont_show_checkbox = QCheckBox("Don't show after saving")
        self._dont_show_checkbox.toggled.connect(
            self.dont_show_again_changed.emit
        )
        bottom_layout.addWidget(self._dont_show_checkbox)

        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setDefault(True)
        bottom_layout.addWidget(close_btn)

        main_layout.addLayout(bottom_layout)

    def _toggle_other_tools(self, checked):
        """Toggle visibility of other tools section."""
        self._other_tools_frame.setVisible(checked)
        # Update button text to show expand/collapse state
        arrow = "▼" if checked else "▶"
        icon = "📊"
        self._other_tools_btn.setText(
            f"{icon} {arrow} Other tools supporting PEtab"
        )
        # Adjust window size
        self.adjustSize()

    def set_dont_show_again(self, dont_show: bool):
        """Set the 'don't show again' checkbox state."""
        self._dont_show_checkbox.setChecked(dont_show)

    def show_panel(self):
        """Show the panel and center it on the parent."""
        if self.parent():
            # Center on parent window
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2,
            )
        self.show()
        self.raise_()
        self.activateWindow()
