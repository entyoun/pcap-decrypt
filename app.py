from flask import Flask, request, render_template, send_file
import os
import subprocess
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pcap_file' not in request.files:
        return "No file part"
    
    file = request.files['pcap_file']
    if file.filename == '':
        return "No selected file"
    
    if file:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        pcap_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pcap_path)
        
        # Create a temporary directory for key extraction and decrypted pcap
        with tempfile.TemporaryDirectory() as temp_dir:
            key_file = os.path.join(temp_dir, 'ssl-keys.txt')
            decrypted_pcap = os.path.join(temp_dir, 'decrypted.pcap')
            
            # Run tshark to extract F5 SSL keys
            try:
                # First create the key file with tshark
                subprocess.run([
                    'tshark',
                    '-r', pcap_path,
                    '-Y', 'f5ethtrailer.tls.keylog',
                    '-T', 'fields',
                    '-e', 'f5ethtrailer.tls.keylog'
                ], check=True, stdout=open(key_file, 'w'))
                
                # Process the key file to format it correctly
                subprocess.run([
                    'sed',
                    '-i',
                    's/,/\n/g',
                    key_file
                ], check=True)
                
                # Create decrypted pcap using editcap
                subprocess.run([
                    'editcap',
                    '--inject-secrets',
                    f'tls,{key_file}',
                    pcap_path,
                    decrypted_pcap
                ], check=True)
                
                # Run Wireshark with the decrypted pcap
                wireshark_process = subprocess.Popen([
                    'wireshark',
                    '-r', decrypted_pcap
                ])
                
                # Return a success message with the path to the decrypted pcap
                return jsonify({
                    'message': 'Successfully created decrypted pcap and opened in Wireshark',
                    'decrypted_pcap': decrypted_pcap,
                    'original_pcap': pcap_path
                })
                
                return "SSL keys extracted and Wireshark opened with decrypted SSL traffic"
                
            except subprocess.CalledProcessError as e:
                return f"Error processing pcap file: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
