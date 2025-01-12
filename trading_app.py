import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                           QHeaderView, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from trader_engine import TraderEngine
from io import StringIO

class AnalysisThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, trader, api_key, query):
        super().__init__()
        self.trader = trader
        self.api_key = api_key
        self.query = query
        self.output = StringIO()

    def run(self):
        try:
            # Redirect stdout to capture output
            old_stdout = sys.stdout
            sys.stdout = self.output

            # Execute analysis
            self.trader.set_api_key(self.api_key)
            self.trader.query(self.query)

            # Get captured output and emit it
            output = self.output.getvalue()
            self.finished.emit(output)

            # Restore stdout
            sys.stdout = old_stdout

        except Exception as e:
            self.error.emit(str(e))
        finally:
            sys.stdout = old_stdout

class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.angle = 0
        self.timer = None
        self.hide()

    def paintEvent(self, event):
        if not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create a rotating arc
        pen = QPen()
        pen.setWidth(3)
        pen.setColor(QColor("#3b82f6"))
        painter.setPen(pen)

        rect = QRectF(5, 5, 30, 30)
        painter.drawArc(rect, self.angle * 16, 300 * 16)

    def start(self):
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.rotate)
            self.timer.start(50)  # Update every 50ms
        self.show()

    def stop(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        self.hide()

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

class MetricsTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # Disable selection
        self.setStyleSheet('''
            QTableWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #c5f6fa;
                gridline-color: #334155;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #3b82f6;
                border: none;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                font-size: 12px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e293b;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 5px;
                min-height: 20px;
            }
        ''')

    def update_metrics(self, text):
        # Parse the metrics from the text output
        metrics = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metrics[key.strip()] = value.strip()

        # Clear existing rows
        self.setRowCount(len(metrics))

        # Add metrics directly to table
        for i, (key, value) in enumerate(metrics.items()):
            metric_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(value)
            
            # Set fonts
            metric_item.setFont(QFont('Segoe UI', 10))
            value_item.setFont(QFont('Segoe UI', 10))
            
            self.setItem(i, 0, metric_item)
            self.setItem(i, 1, value_item)

        self.resizeRowsToContents()

class OutputRedirector(StringIO):
    def __init__(self, metrics_table):
        super().__init__()
        self.metrics_table = metrics_table
        self.captured_text = ""

    def write(self, text):
        super().write(text)
        self.captured_text += text
        self.metrics_table.update_metrics(self.captured_text)

class TradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trader = TraderEngine()
        self.analysis_thread = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Trading Analysis Platform')
        self.setMinimumSize(1000, 800)
        
        # Main layout setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title and spinner setup
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel('Trading Analysis')
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet('color: white; margin-bottom: 20px;')
        title_layout.addWidget(title)
        
        # Status container
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spinner = LoadingSpinner()
        status_layout.addWidget(self.spinner)
        
        self.status_label = QLabel('')
        self.status_label.setFont(QFont('Segoe UI', 11))
        self.status_label.setStyleSheet('color: #94a3b8;')
        status_layout.addWidget(self.status_label)
        
        title_layout.addWidget(status_container)
        layout.addWidget(title_container)
        
        # Input fields setup
        api_label = QLabel('API Key')
        api_label.setFont(QFont('Segoe UI', 12))
        api_label.setStyleSheet('color: #94a3b8;')
        layout.addWidget(api_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText('Enter your API key')
        self.api_key_input.setFixedHeight(45)
        self.api_key_input.setFont(QFont('Segoe UI', 11))
        self.api_key_input.setStyleSheet('''
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 15px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #1e293b;
            }
        ''')
        layout.addWidget(self.api_key_input)
        
        query_label = QLabel('Query')
        query_label.setFont(QFont('Segoe UI', 12))
        query_label.setStyleSheet('color: #94a3b8;')
        layout.addWidget(query_label)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText('e.g., Short UBER for the past year')
        self.query_input.setFixedHeight(45)
        self.query_input.setFont(QFont('Segoe UI', 11))
        self.query_input.setStyleSheet('''
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 15px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #1e293b;
            }
        ''')
        layout.addWidget(self.query_input)
        
        # Execute button
        self.execute_button = QPushButton('Execute Analysis')
        self.execute_button.setFixedHeight(45)
        self.execute_button.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        self.execute_button.clicked.connect(self.execute_query)
        self.execute_button.setStyleSheet('''
            QPushButton {
                background-color: #3b82f6;
                border-radius: 6px;
                color: white;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
        ''')
        layout.addWidget(self.execute_button)
        
        # Metrics table
        results_label = QLabel('Analysis Results')
        results_label.setFont(QFont('Segoe UI', 12))
        results_label.setStyleSheet('color: #94a3b8;')
        layout.addWidget(results_label)
        
        self.metrics_table = MetricsTable()
        layout.addWidget(self.metrics_table)
        
        # Window styling
        self.setStyleSheet('''
            QMainWindow {
                background-color: #0f172a;
            }
            QWidget {
                background-color: #0f172a;
            }
        ''')

    def execute_query(self):
        query = self.query_input.text()
        api_key = self.api_key_input.text()
        
        if not query or not api_key:
            self.status_label.setText('Please fill in both API key and query')
            self.status_label.setStyleSheet('color: #ef4444;')
            return

        self.execute_button.setEnabled(False)
        self.status_label.setText('Executing analysis...')
        self.status_label.setStyleSheet('color: #3b82f6;')
        self.metrics_table.setRowCount(0)
        self.spinner.start()

        # Create and start analysis thread
        self.analysis_thread = AnalysisThread(self.trader, api_key, query)
        self.analysis_thread.finished.connect(self.handle_analysis_complete)
        self.analysis_thread.error.connect(self.handle_analysis_error)
        self.analysis_thread.start()

    def handle_analysis_complete(self, output):
        self.metrics_table.update_metrics(output)
        self.status_label.setText('Analysis completed successfully')
        self.status_label.setStyleSheet('color: #22c55e;')
        self.execute_button.setEnabled(True)
        self.spinner.stop()

    def handle_analysis_error(self, error_msg):
        self.status_label.setText(f'Error: {error_msg}')
        self.status_label.setStyleSheet('color: #ef4444;')
        self.execute_button.setEnabled(True)
        self.spinner.stop()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    window = TradingApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()