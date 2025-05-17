import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import tempfile
from pathlib import Path
import shutil


class PcapDecrypterApp:
    def check_tshark_available(self):
        """Check if tshark is available in the system PATH"""
        try:
            tshark_path = shutil.which("tshark")
            return tshark_path is not None
        except Exception:
            return False

    def __init__(self, root):
        self.root = root
        self.root.title("PCAP Decrypter")
        self.root.geometry("600x400")
        
        # Configure styles
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=6)
        
        # Main container
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="PCAP Decrypter", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.pack(pady=10)
        
        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="Select a PCAP file to decrypt SSL/TLS traffic",
            wraplength=500
        )
        instructions.pack(pady=10)
        
        # File selection
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            file_frame, 
            text="Browse...", 
            command=self.browse_file
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Status
        self.status_var = tk.StringVar()
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            wraplength=500,
            foreground="green"
        )
        status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, 
            orient=tk.HORIZONTAL, 
            length=400, 
            mode='determinate'
        )
        self.progress.pack(pady=10)
        
        # Process button
        self.process_btn = ttk.Button(
            main_frame,
            text="Decrypt PCAP",
            command=self.process_file,
            state=tk.DISABLED
        )
        self.process_btn.pack(pady=20)
        
        # Output path
        self.output_path = tk.StringVar()
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="Output:").pack(anchor=tk.W)
        
        output_entry = ttk.Entry(
            output_frame, 
            textvariable=self.output_path, 
            state='readonly',
            width=50
        )
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.open_btn = ttk.Button(
            output_frame,
            text="Open Folder",
            command=self.open_output_folder,
            state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.RIGHT)
        
        # Bind file path changes
        self.file_path.trace_add('write', self.check_file)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select PCAP File",
            filetypes=[("PCAP files", "*.pcap"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
    
    def check_file(self, *args):
        file_path = self.file_path.get()
        if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.pcap'):
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set("Ready to decrypt")
        else:
            self.process_btn.config(state=tk.DISABLED)
            self.status_var.set("Please select a valid PCAP file")
    
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
                check=False  # Don't raise exception on non-zero exit code
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

    def process_file(self):
        input_file = self.file_path.get()
        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Error", "Please select a valid PCAP file")
            return
        
        self.progress['value'] = 0
        self.status_var.set("Processing...")
        self.root.update_idletasks()
        
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decrypted_pcaps")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(
            output_dir,
            f"decrypted_{os.path.basename(input_file)}"
        )
        
        key_file = os.path.join(tempfile.gettempdir(), 'ssl-keys.txt')
        
        try:
            # Update progress
            self.progress['value'] = 20
            self.root.update_idletasks()
            
            # Check if tshark is available before proceeding
            if not self.check_tshark_available():
                messagebox.showerror("Error", "tshark is not available. Please download Wireshark from https://www.wireshark.org/ and make sure tshark is in your system PATH.")
                return

            # Extract F5 keylog data
            success, message = self.extract_f5_keylog(input_file, key_file)
            
            if not success:
                raise Exception(f"Failed to extract F5 keylog data: {message}")
                
            # Check if key file is not empty
            if os.path.getsize(key_file) == 0:
                raise Exception("No F5 keylog data was found in the PCAP file")
                
            self.progress['value'] = 60
            self.root.update_idletasks()
            
            # Create decrypted pcap using editcap
            subprocess.run([
                'editcap',
                '--inject-secrets',
                f'tls,{key_file}',
                input_file,
                output_file
            ], check=True)
            
            self.progress['value'] = 100
            self.status_var.set("Decryption completed successfully")
            self.output_path.set(output_file)
            self.open_btn.config(state=tk.NORMAL)
            
            if messagebox.askyesno(
                "Success", 
                "PCAP file decrypted successfully!\n\n" +
                f"Output file: {output_file}\n\n" +
                "Would you like to open the output folder?"
            ):
                self.open_output_folder()
            
            self.status_var.set("Decryption completed successfully")
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Error", 
                f"Failed to process PCAP file:\n{str(e)}"
            )
            self.status_var.set("Error processing file")
            self.progress['value'] = 0
    
    def open_output_folder(self):
        output_path = self.output_path.get()
        if output_path and os.path.isfile(output_path):
            folder_path = os.path.dirname(output_path)
            os.startfile(folder_path)

if __name__ == '__main__':
    root = tk.Tk()
    app = PcapDecrypterApp(root)
    root.mainloop()