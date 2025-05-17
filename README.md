# PCAP Decrypter

A simple GUI application for decrypting PCAP files using Wireshark's tshark utility. This tool extracts F5 keylog data from PCAP files and uses it to decrypt the traffic.

## Features

- User-friendly graphical interface
- Extracts F5 keylog data from PCAP files
- Creates decrypted PCAP files in a dedicated output directory
- Progress tracking during decryption
- Easy access to output directory

## Prerequisites

- Python 3.6 or higher
- Wireshark with tshark installed and available in system PATH
- Required Python packages (install using `pip install -r requirements.txt`)

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

2. Click the "Browse" button to select a PCAP file

3. Click the "Decrypt PCAP" button to start the decryption process

4. Once complete, you can click the "Open Folder" button to access the decrypted PCAP file

## Output

Decrypted PCAP files are saved in a `decrypted_pcaps` directory within the application folder, with the prefix `decrypted_` added to the original filename.

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
