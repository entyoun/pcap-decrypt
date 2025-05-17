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
- Optional drag and drop support (requires tkinterdnd2)

## Prerequisites

- Python 3.6 or higher
- Wireshark with tshark installed and available in system PATH
- Required Python packages (install using `pip install -r requirements.txt`)

### Optional Features

- **Drag and Drop Support**: Install `tkinterdnd2` for drag and drop functionality:
  ```bash
  pip install tkinterdnd2
  ```
  Note: Without this package, you can still add files using the "Add Files" button.

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
   python app.py
   ```

2. Add PCAP files using one of these methods:
   - Click the "Add Files" button to select one or more PCAP files
   - (If tkinterdnd2 is installed) Drag and drop PCAP files directly into the application window

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
   pyinstaller --onefile --windowed app.py
   ```

3. The executable will be created in the `dist` directory

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.
