import sys
import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QProgressBar, QMessageBox, QCheckBox,
    QLineEdit, QFrame, QSizePolicy, QStyle
)
from PySide6.QtCore import Qt, QSize, QSettings, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor, QPainter, QPen

# Suppress qt-material 'Fusion style does not exist' warnings
logging.getLogger('root').setLevel(logging.ERROR)

# Import qt-material after suppressing warnings
from qt_material import apply_stylesheet

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    progress = Signal(int)
    status = Signal(str)
    finished = Signal()
    error = Signal(str)

class DropListWidget(QListWidget):
    """A QListWidget with centered placeholder when empty."""
    def __init__(self, placeholder_text='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.placeholder_text = placeholder_text
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0 and self.placeholder_text:
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor('#90caf9')))
            painter.setFont(self.font())
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, self.placeholder_text)

class PcapDecrypter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCAP Decrypter")
        self.setMinimumSize(800, 700)
        
        # Initialize settings
        self.settings = QSettings("PCAPDecrypter", "PCAPDecrypter")
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # Initialize output directory and user preference tracking
        self.output_dir = os.path.expanduser("~")
        self.output_dir_set_by_user = False
        
        # Apply dark_blue theme before UI is created
        self.apply_base_theme()
        
        # Initialize UI
        self.init_ui()
        
        # Load saved settings after UI is initialized
        self.load_settings()
        

    
    def apply_base_theme(self):
        """Apply the dark blue theme before the UI is fully initialized"""
        try:
            # Always use dark_blue theme
            apply_stylesheet(self, theme='dark_blue.xml', css_file=None)
        except Exception as e:
            print(f"Error applying theme: {str(e)}")
    
    
    # Theme-related methods removed since we always use dark_blue.xml
    
    def init_ui(self):
        """Initialize the user interface"""
        # Header with title
        header = QHBoxLayout()
        
        # Title
        title = QLabel("PCAP Decrypter")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        
        header.addWidget(title, 1)
        
        self.main_layout.addLayout(header)
        
        # Modern, simple drag-and-drop area with centered placeholder
        self.file_list = DropListWidget("Drag and drop PCAP files here\nSupports .pcap and .pcapng")
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 2px dashed #42a5f5;
                border-radius: 8px;
                padding: 10px;
                background-color: rgba(66, 165, 245, 0.05);
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 4px 0;
            }
            QListWidget::item:selected {
                background-color: #1565c0;
                color: white;
            }
        """)
        self.main_layout.addWidget(self.file_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Files")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.add_btn.clicked.connect(self.browse_files)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.remove_btn.clicked.connect(self.remove_selected_files)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.clear_btn.clicked.connect(self.clear_files)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        self.main_layout.addLayout(button_layout)
        
        # Output directory section
        output_label = QLabel("Output Directory:")
        output_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        self.main_layout.addWidget(output_label, alignment=Qt.AlignLeft)
        
        # Output path and browse button
        path_layout = QHBoxLayout()
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setStyleSheet("")
        self.output_path_edit.setPlaceholderText("Files will be saved in the same directory as the input PCAP")
        
        browse_btn = QPushButton("Change...")
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(self.browse_output_dir)
        
        path_layout.addWidget(self.output_path_edit, 1)
        path_layout.addWidget(browse_btn)
        
        self.main_layout.addLayout(path_layout)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
        """)
        self.main_layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #2e7d32; font-style: italic;")
        self.main_layout.addWidget(self.status_label)
        
        # Process button
        self.process_btn = QPushButton("Decrypt PCAP Files")
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumWidth(200)
        # Remove custom teal style, let qt-material theme handle button appearance
        self.process_btn.setStyleSheet("")
        self.process_btn.clicked.connect(self.process_files)
        self.main_layout.addWidget(self.process_btn, 0, Qt.AlignCenter)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connect signals
        self.file_list.itemSelectionChanged.connect(self.update_ui_state)

        # Update UI state
        self.update_ui_state()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() 
                    if url.isLocalFile() and url.toLocalFile().lower().endswith(('.pcap', '.pcapng'))]
            self.add_files(files)
            event.acceptProposedAction()
    
    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PCAP Files",
            "",
            "PCAP Files (*.pcap *.pcapng);;All Files (*)"
        )
        if files:
            self.add_files(files)
    
    def add_files(self, files):
        existing_files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        new_files = [f for f in files if f not in existing_files]
        
        if not new_files:
            return
        
        # Add files to the list
        for file in new_files:
            self.file_list.addItem(file)
        
        # Only update output directory if it hasn't been set by the user yet
        if self.file_list.count() > 0 and (not hasattr(self, 'output_dir_set_by_user') or not self.output_dir_set_by_user):
            first_file = self.file_list.item(0).text()
            self.output_dir = os.path.dirname(os.path.abspath(first_file))
            self.output_path_edit.setText(self.output_dir)
        
        self.update_ui_state()
    
    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self.update_ui_state()
    
    def clear_files(self):
        self.file_list.clear()
        self.update_ui_state()
    
    def browse_output_dir(self):
        current_dir = self.output_dir if hasattr(self, 'output_dir') else os.path.expanduser("~")
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            current_dir
        )
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_set_by_user = True
            self.output_path_edit.setText(dir_path)
    
    def update_ui_state(self):
        has_files = self.file_list.count() > 0
        self.process_btn.setEnabled(has_files)
        self.remove_btn.setEnabled(has_files and len(self.file_list.selectedItems()) > 0)
        self.clear_btn.setEnabled(has_files)

    def load_settings(self):
        # Load window geometry
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        
        # Initialize output directory from settings or use home directory
        self.output_dir = self.settings.value("output_dir", os.path.expanduser("~"))
        if hasattr(self, 'output_path_edit'):
            self.output_path_edit.setText(self.output_dir)
    
    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("output_dir", self.output_dir)
    
    def closeEvent(self, event):
        self.save_settings()
        event.accept()
    
    def check_tshark_available(self):
        """Check if tshark is available in the system PATH"""
        try:
            tshark_path = shutil.which("tshark")
            return tshark_path is not None
        except Exception:
            return False
    
    def extract_f5_keylog(self, input_file, key_file):
        """Extract F5 keylog data and format it properly"""
        try:
            # Run tshark to extract F5 keylog data
            result = subprocess.run(
                [
                    'tshark',
                    '-r', input_file,
                    '-Y', 'f5ethtrailer.tls.keylog',
                    '-T', 'fields',
                    '-e', 'f5ethtrailer.tls.keylog'
                ],
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit code
                shell=False
            )
            
            # Check if there was any error output that's not just a warning
            if result.stderr and not any(warning in result.stderr.lower() for warning in ['warning', 'cut short']):
                return False, f"Error running tshark: {result.stderr}"
            
            # Get the output and split by commas, then join with newlines
            key_data = result.stdout.strip()
            if not key_data:
                return False, "No F5 keylog data found in the capture"
                
            # Replace commas with newlines and write to key file
            with open(key_file, 'w') as f:
                f.write(key_data.replace(',', '\n'))
                
            # If we got here, we have valid key data, even if there were warnings
            return True, "Successfully extracted F5 keylog data"
            
        except Exception as e:
            return False, f"Error processing F5 keylog: {str(e)}"

    def process_files(self):
        """Process the selected PCAP files"""
        if not self.check_tshark_available():
            QMessageBox.critical(
                self,
                "Error",
                "Wireshark's tshark not found in PATH. Please install Wireshark and ensure it's in your system PATH.",
                QMessageBox.Ok
            )
            return
        
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "No Files", "No PCAP files selected!")
            return
        
        # Disable UI during processing
        self.setEnabled(False)
        self.status_label.setText("Processing files...")
        self.progress.setValue(0)
        QApplication.processEvents()
        
        success_count = 0
        failed_files = []
        last_successful_output = None
        
        try:
            output_dir = self.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            total_files = self.file_list.count()
            
            for i in range(total_files):
                input_file = self.file_list.item(i).text()
                file_name = os.path.basename(input_file)
                output_file = os.path.join(output_dir, f"decrypted_{file_name}")
                
                # Update progress
                progress = int((i / total_files) * 100)
                self.progress.setValue(progress)
                self.status_label.setText(f"Processing {i+1} of {total_files}: {file_name}")
                QApplication.processEvents()
                
                try:
                    if not os.path.isfile(input_file):
                        error_msg = f"File not found: {input_file} (Absolute: {os.path.abspath(input_file)})"
                        failed_files.append((file_name, error_msg))
                        continue
                    
                    # Create a temporary key file
                    key_file = os.path.join(tempfile.gettempdir(), 'ssl-keys.txt')
                    
                    # Extract F5 keylog data
                    success, message = self.extract_f5_keylog(input_file, key_file)
                    
                    if not success:
                        failed_files.append((file_name, f"Keylog extraction failed: {message}"))
                        continue
                        
                    # Check if key file is not empty
                    if os.path.getsize(key_file) == 0:
                        failed_files.append((file_name, "No F5 keylog data found"))
                        continue
                    
                    # Create decrypted pcap using editcap
                    subprocess.run([
                        'editcap',
                        '--inject-secrets',
                        f'tls,{key_file}',
                        input_file,
                        output_file
                    ], check=True, shell=False)
                    
                    success_count += 1
                    last_successful_output = output_file
                    
                except subprocess.CalledProcessError as e:
                    failed_files.append((file_name, f"Decryption failed: {str(e)}"))
                except Exception as e:
                    failed_files.append((file_name, f"Error: {str(e)}"))
            
            # Build result message
            result_message = []
            
            if success_count > 0:
                result_message.append(f"✅ Successfully processed {success_count} file{'s' if success_count > 1 else ''}.")
                self.output_dir = os.path.dirname(last_successful_output)
                self.output_path_edit.setText(self.output_dir)
            
            if failed_files:
                result_message.append(f"❌ Failed to process {len(failed_files)} file{'s' if len(failed_files) > 1 else ''}:")
                max_errors = 5  # Show max 5 errors in the dialog
                for i, (file, error) in enumerate(failed_files[:max_errors], 1):
                    result_message.append(f"   {i}. {file}: {error}")
                
                if len(failed_files) > max_errors:
                    result_message.append(f"   ... and {len(failed_files) - max_errors} more errors (see console for details)")
                    
                # Log all errors to console
                print("\nDetailed error log:")
                for file, error in failed_files:
                    print(f"Failed to process {file}: {error}")
            
            # Show result dialog
            if success_count > 0 or failed_files:
                QMessageBox.information(
                    self,
                    "Processing Complete",
                    "\n".join(result_message)
                )
            
            # Ask to open output folder if any files were successfully processed
            if success_count > 0 and QMessageBox.question(
                self,
                "Success",
                "Would you like to open the output folder?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            ) == QMessageBox.Yes:
                output_path = os.path.abspath(os.path.dirname(last_successful_output))
                if os.name == 'nt':  # Windows
                    os.startfile(output_path)
                elif os.name == 'posix':  # macOS and Linux
                    if sys.platform == 'darwin':  # macOS
                        subprocess.Popen(['open', output_path])
                    else:  # Linux
                        subprocess.Popen(['xdg-open', output_path])
            
            # Update progress to 100%
            self.progress.setValue(100)
            self.status_label.setText("Processing complete!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        
        finally:
            # Re-enable UI
            self.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("PCAP Decrypter")
    app.setOrganizationName("PCAPDecrypter")
    
    # Create and show the main window
    window = PcapDecrypter()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
