# PCAP Decrypter

A simple GUI application for decrypting PCAP files using Wireshark's tshark utility. This tool extracts F5 keylog data from PCAP files and uses it to decrypt the traffic. Supports batch processing of multiple files with a summary of results.

## Features

- User-friendly graphical interface
- Batch process multiple PCAP files at once
- Extracts F5 keylog data from PCAP files
- Creates decrypted PCAP files in a dedicated output directory
- Progress tracking during decryption
- Summary of successful and failed decryptions
- Easy access to output directory
- Drag and drop PCAP files directly into the application window

## Prerequisites

- Python 3.6 or higher
- Wireshark with tshark installed and available in system PATH
- Required Python packages (install using `pip install -r requirements.txt`)

## For Users Without Python

If you don't have Python installed, follow these steps:

### Windows
1. Download and install Python from the official website:
   - Visit [Python Downloads](https://www.python.org/downloads/)
   - Click "Download Python" (get the latest stable version)
   - **IMPORTANT**: During installation, check the box that says "Add Python to PATH"
   - Complete the installation

2. Verify Python installation:
   - Open Command Prompt (press Win+R, type `cmd`, and press Enter)
   - Run: `python --version`
   - Run: `pip --version`
   - Both commands should show version numbers without errors

3. Proceed with the [Installation](#installation) instructions below

### macOS
1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python:
   ```bash
   brew install python
   ```

3. Verify Python installation:
   - Open Terminal
   - Run: `python3 --version`
   - Run: `pip3 --version`

4. Proceed with the [Installation](#installation) instructions below

### Linux (Debian/Ubuntu)
1. Open Terminal and run:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. Verify installation:
   ```bash
   python3 --version
   pip3 --version
   ```

3. Proceed with the [Installation](#installation) instructions below

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pcap-decrypt.git
   cd pcap-decrypt
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python pcap_decrypter_modern.py
   ```

2. Add PCAP files using one of these methods:
   - Click the "Add Files" button to select one or more PCAP files
   - Drag and drop PCAP files directly into the application window

3. Optionally, use the interface to:
   - Remove selected files from the list
   - Clear all files
   
4. Click the "Decrypt PCAP Files" button to start the decryption process

5. View the progress in the status bar and progress indicator

6. After completion:
   - A summary will show how many files were processed successfully/failed
   - Optionally open the output folder directly from the dialog
   - The "Open Folder" button will be enabled to access the output directory later

## Output

Decrypted PCAP files are saved in a `decrypted_pcaps` directory within the application folder, with the prefix `decrypted_` added to the original filename.

### Output Format
- Successfully decrypted files: `decrypted_<original_filename>.pcap`
- Detailed error logs are printed to the console if any files fail to process

## Building Executable

To create a standalone executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller --onefile --windowed pcap_decrypter_modern.py
   ```

3. The executable will be created in the `dist` directory

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.
