import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import tempfile
from pathlib import Path
import shutil
import re

# Import tkinterdnd2 for drag and drop support
try:
    import tkinterdnd2
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    print("tkinterdnd2 not found. Drag and drop will be disabled.")
    print("To enable it, run: pip install tkinterdnd2")
    HAS_DND = False


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
        
        # Store if we have drag and drop support
        self.has_dnd = HAS_DND
        
        # Configure styles
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=6)
        
        # Set initial window size and minimum size
        self.root.geometry("800x800")
        self.root.minsize(700, 800)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
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
        self.instructions = ttk.Label(
            main_frame,
            text="Select PCAP files to decrypt SSL/TLS traffic",
            wraplength=500
        )
        self.instructions.pack(pady=5)
        
        # Drag and drop hint
        self.dnd_hint = ttk.Label(
            main_frame,
            text="Drag and drop PCAP files here or click 'Add Files' below",
            foreground="gray",
            wraplength=500
        )
        self.dnd_hint.pack(pady=5)
        
        # Selected files list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox with scrollbar for selected files
        scrollbar = ttk.Scrollbar(list_frame)
        self.file_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            height=8,
            font=('TkDefaultFont', 10),
            selectbackground='#4a6984',
            selectforeground='#ffffff'
        )
        scrollbar.config(command=self.file_listbox.yview)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Add files button
        add_btn = ttk.Button(
            button_frame,
            text="Add Files...",
            command=self.browse_files
        )
        add_btn.pack(side=tk.LEFT, padx=2)
        
        # Remove selected button
        remove_btn = ttk.Button(
            button_frame,
            text="Remove Selected",
            command=self.remove_selected_files
        )
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        # Clear all button
        clear_btn = ttk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_files
        )
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Store the list of files
        self.selected_files = []
        
        # Configure drag and drop for the main window
        if self.has_dnd:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
            
            # Also make the listbox a drop target
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
        

        
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
            text="Decrypt PCAP Files",
            command=self.process_file,
            state=tk.DISABLED
        )
        self.process_btn.pack(pady=20)
        
        # Output path
        self.output_path = tk.StringVar()
        self.use_custom_output = tk.BooleanVar(value=False)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        # Output directory selection
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_dir_frame, text="Output Directory:").pack(anchor=tk.W)
        
        output_entry = ttk.Entry(
            output_dir_frame,
            textvariable=self.output_path,
            state='readonly',
            width=50
        )
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            output_dir_frame,
            text="Browse...",
            command=self.browse_output_dir
        )
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Use custom output directory checkbox
        self.custom_output_cb = ttk.Checkbutton(
            output_frame,
            text="Use custom output directory (uncheck to save in same directory as input file)",
            variable=self.use_custom_output,
            command=self.toggle_output_dir
        )
        self.custom_output_cb.pack(anchor=tk.W, pady=5)
        
        # Set initial state
        self.toggle_output_dir()
        
        self.open_btn = ttk.Button(
            output_frame,
            text="Open Folder",
            command=self.open_output_folder,
            state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.RIGHT)
        
        # Configure window for drag and drop if available
        if self.has_dnd:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
    
    def browse_files(self):
        # Set initial directory to the Downloads folder
        initial_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        file_paths = filedialog.askopenfilenames(
            title="Select PCAP Files",
            initialdir=initial_dir,  # Start in Downloads folder
            filetypes=[("PCAP files", "*.pcap* .pcap0 .pcap1 .pcap2 .pcap3 .pcap4 .pcap5 .pcap6 .pcap7 .pcap8 .pcap9"), ("All files", "*")]
        )
        if file_paths:
            self.add_files(file_paths)
    
    def add_files(self, file_paths):
        """Add files to the list if they're not already there"""
        count_added = 0
        for file_path in file_paths:
            # Convert to absolute path and normalize
            file_path = os.path.abspath(os.path.normpath(file_path))
            if (file_path and 
                file_path not in self.selected_files and 
                (file_path.lower().endswith('.pcap') or 
                 re.search(r'\.pcap\d*$', file_path.lower()))):
                self.selected_files.append(file_path)
                self.file_listbox.insert(tk.END, os.path.basename(file_path))
                count_added += 1
        
        if count_added > 0:
            self.update_ui_state()
            self.status_var.set(f"Added {count_added} file(s)")
        return count_added > 0
    
    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_indices = list(self.file_listbox.curselection())
        if not selected_indices:
            return
            
        # Remove from the end to avoid index shifting issues
        for i in sorted(selected_indices, reverse=True):
            if 0 <= i < len(self.selected_files):
                del self.selected_files[i]
                self.file_listbox.delete(i)
        
        self.update_ui_state()
        self.status_var.set(f"Removed {len(selected_indices)} file(s)")
    
    def clear_files(self):
        """Clear all files from the list"""
        if not self.selected_files:
            return
            
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_ui_state()
        self.status_var.set("Cleared all files")
    
    def on_drop(self, event):
        """Handle file drop event"""
        # Get the file paths from the drop event
        data = event.data.strip()
        
        # Debug: Print raw drop data
        print(f"Raw drop data: {data}")
        
        # tkinterdnd2 provides paths in format: {path1} {path2} {path3}
        # Extract all paths between { and }
        file_paths = []
        
        # Split the data by spaces that are outside of curly braces
        parts = []
        current = []
        in_braces = 0
        
        for char in data:
            if char == '{':
                in_braces += 1
                current.append(char)
            elif char == '}':
                in_braces -= 1
                current.append(char)
            elif char.isspace() and in_braces == 0:
                if current:
                    parts.append(''.join(current))
                    current = []
            else:
                current.append(char)
        
        if current:  # Add the last part if exists
            parts.append(''.join(current))
        
        # Process each part to extract the path
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # Remove surrounding {}
            if part.startswith('{') and part.endswith('}'):
                path = part[1:-1].strip()
                # Convert to Windows path if it's using forward slashes
                path = path.replace('/', '\\')
                
                # Convert to absolute path and check if it exists
                try:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        file_paths.append(abs_path)
                    else:
                        print(f"Warning: Path does not exist: {abs_path}")
                except Exception as e:
                    print(f"Error processing path '{path}': {e}")
        
        # Add the processed files to the UI
        if file_paths:
            self.add_files(file_paths)
        
        # Add the files and update UI
        if file_paths:
            if self.add_files(file_paths):
                self.dnd_hint.config(text=f"Added {len(file_paths)} file(s)! Drag and drop more or click 'Decrypt PCAP' when ready.", 
                                   foreground="green")
                self.root.after(3000, lambda: self.dnd_hint.config(
                    text="Drag and drop PCAP files here or click 'Add Files' below",
                    foreground="gray"
                ))
    
    def update_ui_state(self):
        """Update the UI based on current state"""
        has_files = len(self.selected_files) > 0
        self.process_btn.config(state=tk.NORMAL if has_files else tk.DISABLED)
        
        if has_files:
            count = len(self.selected_files)
            self.status_var.set(f"Ready to decrypt {count} file{'s' if count > 1 else ''}")
        else:
            self.status_var.set("No files selected")
    
    def extract_f5_keylog(self, input_file, key_file):
        """Extract F5 keylog data and format it properly"""
        try:
            # Run tshark to extract F5 keylog data
            # Ensure input_file is properly passed as an argument
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

    def browse_output_dir(self):
        """Open a dialog to select output directory"""
        initial_dir = self.output_path.get() or os.path.expanduser('~')
        selected_dir = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=initial_dir
        )
        if selected_dir:
            self.output_path.set(selected_dir)
    
    def toggle_output_dir(self):
        """Toggle between custom and default output directory"""
        if not self.use_custom_output.get():
            # When unchecking, clear the output path
            self.output_path.set("")
    
    def get_output_dir(self, input_file):
        """Get the output directory based on user preference"""
        if self.use_custom_output.get() and self.output_path.get():
            return self.output_path.get()
        return os.path.dirname(os.path.abspath(input_file))
    
    def process_file(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected")
            return
            
        success_count = 0
        failed_files = []
        last_successful_output = None
        
        # Debug: Print current working directory
        print(f"Current working directory: {os.getcwd()}")
        print("Selected files:")
        for i, f in enumerate(self.selected_files, 1):
            exists = "EXISTS" if os.path.exists(f) else "NOT FOUND"
            print(f"  {i}. {f} ({exists})")
        
        # Check if tshark is available before starting
        if not self.check_tshark_available():
            messagebox.showerror("Error", "tshark is not available. Please download Wireshark from https://www.wireshark.org/ and make sure tshark is in your system PATH.")
            return
        
        # Process each file
        for i, input_file in enumerate(self.selected_files, 1):
            # Debug: Print full path being checked
            print(f"\nProcessing file: {input_file}")
            print(f"Absolute path: {os.path.abspath(input_file)}")
            print(f"File exists: {os.path.exists(input_file)}")
            print(f"Is file: {os.path.isfile(input_file)}")
            
            if not os.path.isfile(input_file):
                error_msg = f"File not found: {input_file} (Absolute: {os.path.abspath(input_file)})"
                print(error_msg)
                failed_files.append((input_file, error_msg))
                continue
                
            try:
                # Update progress
                progress = (i / len(self.selected_files)) * 100
                self.progress['value'] = progress
                self.status_var.set(f"Processing {i} of {len(self.selected_files)}: {os.path.basename(input_file)}")
                self.root.update_idletasks()
                
                # Get output directory based on user preference
                output_dir = self.get_output_dir(input_file)
                os.makedirs(output_dir, exist_ok=True)
                
                output_file = os.path.join(
                    output_dir,
                    f"decrypted_{os.path.basename(input_file)}"
                )
                
                key_file = os.path.join(tempfile.gettempdir(), 'ssl-keys.txt')
                
                # Extract F5 keylog data
                success, message = self.extract_f5_keylog(input_file, key_file)
                
                if not success:
                    failed_files.append((input_file, f"Keylog extraction failed: {message}"))
                    continue
                    
                # Check if key file is not empty
                if os.path.getsize(key_file) == 0:
                    failed_files.append((input_file, "No F5 keylog data found"))
                    continue
                
                # Create decrypted pcap using editcap
                # Using shell=False and passing arguments as a list to avoid shell injection
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
                failed_files.append((input_file, f"Decryption failed: {str(e)}"))
            except Exception as e:
                failed_files.append((input_file, f"Error: {str(e)}"))
        
        # Update UI after processing
        self.progress['value'] = 100
        self.status_var.set("Processing completed")
        self.root.update_idletasks()
        
        # Build result message
        result_message = []
        
        if success_count > 0:
            result_message.append(f"✅ Successfully processed {success_count} file{'s' if success_count > 1 else ''}.")
            self.output_path.set(os.path.dirname(last_successful_output))
            self.open_btn.config(state=tk.NORMAL)
        
        if failed_files:
            result_message.append(f"❌ Failed to process {len(failed_files)} file{'s' if len(failed_files) > 1 else ''}:")
            max_errors = 5  # Show max 5 errors in the dialog
            for i, (file, error) in enumerate(failed_files[:max_errors], 1):
                result_message.append(f"   {i}. {os.path.basename(file)}: {error}")
            
            if len(failed_files) > max_errors:
                result_message.append(f"   ... and {len(failed_files) - max_errors} more errors (see console for details)")
                
            # Log all errors to console
            print("\nDetailed error log:")
            for file, error in failed_files:
                print(f"Failed to process {file}: {error}")
        
        # Show result dialog
        if success_count > 0 or failed_files:
            messagebox.showinfo(
                "Processing Complete",
                "\n".join(result_message)
            )
        
        # Ask to open output folder if any files were successfully processed
        if success_count > 0 and messagebox.askyesno(
            "Success",
            "Would you like to open the output folder?"
        ):
            self.open_output_folder()
        
        # Reset progress
        self.progress['value'] = 0
    
    def open_output_folder(self):
        output_path = self.output_path.get()
        if output_path:
            # Check if the path is a file or directory and open its parent directory
            if os.path.isfile(output_path):
                folder_path = os.path.dirname(output_path)
            else:
                folder_path = output_path
                
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {str(e)}")

if __name__ == '__main__':
    # Create the appropriate root window based on available modules
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
        print("tkinterdnd2 not available. Drag and drop will be disabled.")
    
    app = PcapDecrypterApp(root)
    root.mainloop()