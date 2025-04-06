from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit
from PyQt6.QtCore import QDateTime

class TestTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.main_window = parent
        self.test_active = False
        self.test_start_time = None
        self.max_diff = None
        self.datum = None
        self.initUI()
        self.load_test_page()
        self.update_start_button_state() # Initial state of the button

    def initUI(self):
        layout = QVBoxLayout()

        self.test_label = QLabel("Select Joint for Mobility Test:")
        layout.addWidget(self.test_label)

        self.test_combobox = QComboBox()
        self.test_combobox.addItems(["Left Ankle", "Right Ankle", "Left Elbow", "Right Elbow"])
        self.test_combobox.currentIndexChanged.connect(self.load_test_page)
        layout.addWidget(self.test_combobox)

        self.test_info = QTextEdit()
        self.test_info.setReadOnly(True)
        layout.addWidget(self.test_info)

        self.start_test_button = QPushButton("Start 10s Test")
        self.start_test_button.clicked.connect(self.start_test)
        layout.addWidget(self.start_test_button)

        # Previous Results Section
        self.previous_results_label = QLabel("Previous Results:")
        layout.addWidget(self.previous_results_label)

        self.previous_results_text = QTextEdit()
        self.previous_results_text.setReadOnly(True)
        layout.addWidget(self.previous_results_text)

        # Highest Score Section
        self.highest_score_label = QLabel("Highest Score:")
        layout.addWidget(self.highest_score_label)

        self.highest_score_text = QLabel("No results yet")
        layout.addWidget(self.highest_score_text)

        self.setLayout(layout)

    def load_test_page(self):
        joint = self.test_combobox.currentText()
        test_descriptions = {
            "Left Ankle": "This test measures the range of motion of the left ankle.",
            "Right Ankle": "This test measures the range of motion of the right ankle.",
            "Left Elbow": "This test measures the flexibility and strength of the left elbow.",
            "Right Elbow": "This test measures the flexibility and strength of the right elbow."
        }
        self.test_info.setText(test_descriptions.get(joint, "Select a test to see details."))
        self.update_previous_results()

    def update_previous_results(self):
        joint = self.test_combobox.currentText()
        results_for_joint = [result for result in self.main_window.test_results if result[0] == joint]

        if results_for_joint:
            # Display the results
            results_text = "\n".join([f"Date: {result[2]}, Max Differences: {result[1]}" for result in results_for_joint])
            self.previous_results_text.setText(results_text)

            # Calculate and display the highest score
            highest_score = max(
                results_for_joint,
                key=lambda result: sum(abs(value) for value in result[1]),
                default=None
            )
            if highest_score:
                self.highest_score_text.setText(f"Date: {highest_score[2]}, Max Differences: {highest_score[1]}")
            else:
                self.highest_score_text.setText("No results yet")
        else:
            self.previous_results_text.setText("No previous results")
            self.highest_score_text.setText("No results yet")

    def start_test(self):
        self.datum = None
        self.test_active = True
        self.test_start_time = QDateTime.currentDateTime().toSecsSinceEpoch()
        self.max_diff = [0.0] * self.main_window.data_tab_widget.num_values
        self.start_test_button.setEnabled(False)
        self.test_info.setText("Test in progress... Please move the joint.")

    def process_test_data(self, current_values):
        if self.test_active:
            current_time = QDateTime.currentDateTime().toSecsSinceEpoch()
            elapsed_time = current_time - self.test_start_time

            if self.datum is None:
                self.datum = [float(v) for v in current_values]

            diffs = [abs(float(current_values[i]) - self.datum[i]) for i in range(self.main_window.data_tab_widget.num_values)]
            self.max_diff = [max(self.max_diff[i], diffs[i]) for i in range(self.main_window.data_tab_widget.num_values)]

            if elapsed_time >= 10:
                rounded_max_diff = [round(diff, 1) for diff in self.max_diff]
                self.main_window.test_results.append((self.test_combobox.currentText(), rounded_max_diff, QDateTime.currentDateTime().toString()))
                self.test_active = False
                self.start_test_button.setEnabled(True)
                self.test_info.setText(f"Test complete! Max differences: {rounded_max_diff}")
                self.update_previous_results()

    def update_start_button_state(self):
        """Enables or disables the start test button based on the serial connection status."""
        if self.main_window.serial_port and self.main_window.serial_port.is_open:
            self.start_test_button.setEnabled(True)
        else:
            self.start_test_button.setEnabled(False)

    def showEvent(self, event):
        """Called when the tab is shown, update the button state."""
        super().showEvent(event)
        self.update_start_button_state()

    def hideEvent(self, event):
        """Called when the tab is hidden."""
        super().hideEvent(event)
        # Optionally handle any cleanup if needed when the tab is hidden