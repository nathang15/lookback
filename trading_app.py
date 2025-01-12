import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                           QHeaderView, QProgressBar, QTabWidget, QScrollArea, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from trader_engine import TraderEngine
from io import StringIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plot = 0
        self.plots = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Plot display area
        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        
        # Navigation controls
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setSpacing(10)
        
        self.prev_button = QPushButton('Previous')
        self.prev_button.setFixedWidth(100)
        self.prev_button.clicked.connect(self.show_previous_plot)
        self.prev_button.setEnabled(False)
        self.prev_button.setStyleSheet('''
            QPushButton {
                background-color: #3b82f6;
                border-radius: 6px;
                color: white;
                padding: 8px;
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
        
        self.next_button = QPushButton('Next')
        self.next_button.setFixedWidth(100)
        self.next_button.clicked.connect(self.show_next_plot)
        self.next_button.setEnabled(False)
        self.next_button.setStyleSheet('''
            QPushButton {
                background-color: #3b82f6;
                border-radius: 6px;
                color: white;
                padding: 8px;
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
        
        self.plot_counter = QLabel('No plots')
        self.plot_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_counter.setStyleSheet('''
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                padding: 5px 20px;
            }
        ''')
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.plot_counter)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        
        # Add scroll area for plots
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.plot_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('''
            QScrollArea {
                border: none;
                background: #1e293b;
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
        
        layout.addWidget(scroll_area)
        layout.addWidget(nav_container)

    def add_plot(self, figure, title):
        # Create canvas for the matplotlib figure
        canvas = FigureCanvas(figure)
        
        # Store the plot
        self.plots.append((canvas, title))
        
        # Update navigation controls
        if len(self.plots) == 1:
            self.show_plot(0)
        else:
            # Enable both buttons if we have multiple plots (for cycling)
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)
        
        self.update_counter()

    def show_plot(self, index):
        if not self.plots:
            return
            
        # Clear current plot
        for i in reversed(range(self.plot_layout.count())): 
            self.plot_layout.itemAt(i).widget().setParent(None)
        
        # Show new plot
        canvas, title = self.plots[index]
        self.plot_layout.addWidget(canvas)
        self.current_plot = index
        
        # Enable both buttons if we have multiple plots (for cycling)
        if len(self.plots) > 1:
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
        else:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        
        self.update_counter()

    def show_next_plot(self):
        if not self.plots:
            return
            
        # Cycle to the first plot if we're at the end
        next_index = (self.current_plot + 1) % len(self.plots)
        self.show_plot(next_index)

    def show_previous_plot(self):
        if not self.plots:
            return
            
        # Cycle to the last plot if we're at the beginning
        prev_index = (self.current_plot - 1) % len(self.plots)
        self.show_plot(prev_index)

    def update_counter(self):
        if len(self.plots) > 0:
            self.plot_counter.setText(f'Plot {self.current_plot + 1} of {len(self.plots)}')
        else:
            self.plot_counter.setText('No plots')

    def clear(self):
        # Clear all plots
        self.plots = []
        self.current_plot = 0
        
        # Clear layout
        for i in reversed(range(self.plot_layout.count())): 
            self.plot_layout.itemAt(i).widget().setParent(None)
        
        # Reset navigation
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.update_counter()

class AnalysisThread(QThread):
    finished = pyqtSignal(str, list)
    error = pyqtSignal(str)

    def __init__(self, trader, api_key, query):
        super().__init__()
        self.trader = trader
        self.api_key = api_key
        self.query = query
        self.output = StringIO()
        self.figures = []

    def run(self):
        try:
            old_stdout = sys.stdout
            sys.stdout = self.output

            # Store the current figure count
            initial_figures = plt.get_fignums()

            # Execute analysis
            self.trader.set_api_key(self.api_key)
            self.trader.query(self.query)

            # Get all new figures created during analysis
            final_figures = plt.get_fignums()
            new_figures = [plt.figure(num) for num in final_figures if num not in initial_figures]
            
            # Store figures and close them to prevent memory leaks
            self.figures = new_figures
            
            output = self.output.getvalue()
            self.finished.emit(output, self.figures)

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
            self.timer.start(50)
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
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
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
            QTableCornerButton::section {
                background-color: #1e293b;
                border: none;
            }
        ''')

    def update_metrics(self, text):
        metrics = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metrics[key.strip()] = value.strip()

        self.setRowCount(len(metrics))

        for i, (key, value) in enumerate(metrics.items()):
            metric_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(value)
            
            metric_item.setFont(QFont('Segoe UI', 10))
            value_item.setFont(QFont('Segoe UI', 10))
            
            self.setItem(i, 0, metric_item)
            self.setItem(i, 1, value_item)

        self.resizeRowsToContents()

class MainTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('''
            QTabWidget::pane {
                border: 1px solid #334155;
                background: #1e293b;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #94a3b8;
                padding: 8px 16px;
                border: 1px solid #334155;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #334155;
            }
        ''')
        
        self.setup_tabs()
        
    def setup_tabs(self):
        # Create Analysis tab (main input tab)
        self.analysis_tab = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_tab)
        self.analysis_layout.setSpacing(20)
        self.analysis_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add a container for centered content
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setSpacing(20)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to push content to center vertically
        self.analysis_layout.addStretch()
        self.analysis_layout.addWidget(center_container)
        self.analysis_layout.addStretch()
        
        # Create Metrics tab
        self.metrics_tab = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_tab)
        self.metrics_layout.setSpacing(20)
        self.metrics_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create Plots tab
        self.plots_tab = QWidget()
        self.plots_layout = QVBoxLayout(self.plots_tab)
        self.plots_layout.setSpacing(20)
        self.plots_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add tabs
        self.addTab(self.analysis_tab, "Analysis")
        self.addTab(self.metrics_tab, "Metrics")
        self.addTab(self.plots_tab, "Plots")
        
    def get_analysis_layout(self):
        return self.analysis_layout.itemAt(1).widget().layout()
        
    def get_metrics_layout(self):
        return self.metrics_layout
        
    def get_plots_layout(self):
        return self.plots_layout

class TradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trader = TraderEngine()
        self.analysis_thread = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Trading Analysis Platform')
        self.setMinimumSize(1200, 900)
        
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
        
        # Create main tab widget
        self.main_tabs = MainTabWidget()
        layout.addWidget(self.main_tabs)
        
        # Get layouts for each tab
        analysis_layout = self.main_tabs.get_analysis_layout()
        metrics_layout = self.main_tabs.get_metrics_layout()
        plots_layout = self.main_tabs.get_plots_layout()
        
        # Add components to Analysis tab (centered)
        api_label = QLabel('API Key')
        api_label.setFont(QFont('Segoe UI', 12))
        api_label.setStyleSheet('color: #94a3b8;')
        api_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        analysis_layout.addWidget(api_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText('Enter your API key')
        self.api_key_input.setFixedHeight(45)
        self.api_key_input.setFixedWidth(400)  # Limit width for better centering
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
        analysis_layout.addWidget(self.api_key_input, 0, Qt.AlignmentFlag.AlignCenter)
        
        query_label = QLabel('Query')
        query_label.setFont(QFont('Segoe UI', 12))
        query_label.setStyleSheet('color: #94a3b8;')
        query_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        analysis_layout.addWidget(query_label)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText('e.g., Short UBER for the past year')
        self.query_input.setFixedHeight(45)
        self.query_input.setFixedWidth(400)  # Limit width for better centering
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
        analysis_layout.addWidget(self.query_input, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Execute button
        self.execute_button = QPushButton('Run Analysis')
        self.execute_button.setFixedHeight(45)
        self.execute_button.setFixedWidth(200)  # Limit width for better centering
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
        analysis_layout.addWidget(self.execute_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add Metrics table to Metrics tab
        self.metrics_table = MetricsTable()
        metrics_layout.addWidget(self.metrics_table)
        
        # Add plot tabs to Plots tab
        self.plot_tabs = PlotTabWidget()
        self.plot_tabs.setMinimumHeight(400)
        plots_layout.addWidget(self.plot_tabs)
        
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
        self.plot_tabs.clear()
        self.spinner.start()

        self.analysis_thread = AnalysisThread(self.trader, api_key, query)
        self.analysis_thread.finished.connect(self.handle_analysis_complete)
        self.analysis_thread.error.connect(self.handle_analysis_error)
        self.analysis_thread.start()

    def handle_analysis_complete(self, output, figures):
        self.metrics_table.update_metrics(output)
        
        for i, fig in enumerate(figures):
            self.plot_tabs.add_plot(fig, f'Plot {i+1}')
            
        self.main_tabs.setCurrentIndex(1)
        
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