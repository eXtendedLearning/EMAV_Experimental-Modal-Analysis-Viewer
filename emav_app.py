# EMAV - Experimental Modal Analysis Viewer
# Version: 0.4.0 (with Dual-Tree View and Multiple Reconstructed Files)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import scipy.io as sio
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyuff
import traceback
import tempfile
import os
from scipy.interpolate import interp1d
from scipy.signal import find_peaks
from sklearn.metrics import r2_score

class EMAVApp:
    """
    A GUI application for viewing, comparing, and analyzing data from .mat or .unv files
    containing experimental modal analysis records. Version 0.4.0 introduces dual-tree view
    for simultaneous testlab and reconstructed signal management.
    """
    def __init__(self, root):
        """
        Initializes the main application window and its widgets.
        """
        self.root = root
        self.root.title("EMAV - v0.4.0")
        self.root.geometry("1400x950")

        # --- Member variables ---
        self.testlab_data = None
        self.testlab_record_map = {}
        self.selected_testlab_iid = None
        self.current_testlab_filepath = ""
        self.testlab_file_type = None
        
        # Multiple reconstructed files support
        self.reconstructed_files = {}  # {file_iid: {'filepath': str, 'data': dict, 'records': {iid: record}}}
        self.selected_reconstructed_iid = None
        self.reconstructed_file_counter = 0

        # --- Main layout ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Top frame for buttons and version
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.open_testlab_button = ttk.Button(top_frame, text="Load Testlab File", command=self.load_testlab_file)
        self.open_testlab_button.pack(side=tk.LEFT, padx=(0,10))

        self.open_recon_button = ttk.Button(top_frame, text="Load Reconstructed Files", command=self.load_reconstructed_files)
        self.open_recon_button.pack(side=tk.LEFT, padx=(0,10))

        self.clear_recon_button = ttk.Button(top_frame, text="Clear Reconstructed", command=self.clear_reconstructed_files)
        self.clear_recon_button.pack(side=tk.LEFT)

        self.file_label = ttk.Label(top_frame, text="No files loaded.")
        self.file_label.pack(side=tk.LEFT, padx=10)

        self.version_label = ttk.Label(top_frame, text="v0.4.0")
        self.version_label.pack(side=tk.RIGHT)

        # Paned window for resizable left/right panes
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH)

        # --- Left Pane: Dual Tree Views (Testlab and Reconstructed) ---
        left_pane = ttk.Frame(paned_window, padding="5")
        paned_window.add(left_pane, weight=3) 

        # Testlab Tree
        testlab_label = ttk.Label(left_pane, text="Testlab Signals", font=('TkDefaultFont', 9, 'bold'))
        testlab_label.pack(fill=tk.X, pady=(0,5))

        testlab_tree_frame = ttk.Frame(left_pane)
        testlab_tree_frame.pack(expand=True, fill=tk.BOTH, pady=(0,10))

        self.testlab_tree = ttk.Treeview(testlab_tree_frame, columns=("info",), show="tree headings", height=12)
        self.testlab_tree.heading("#0", text="File / Record")
        self.testlab_tree.column("#0", width=180)
        self.testlab_tree.heading("info", text="Info")
        self.testlab_tree.column("info", width=100)
        self.testlab_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        testlab_scrollbar = ttk.Scrollbar(testlab_tree_frame, orient="vertical", command=self.testlab_tree.yview)
        self.testlab_tree.configure(yscrollcommand=testlab_scrollbar.set)
        testlab_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.testlab_tree.bind("<<TreeviewSelect>>", self.on_testlab_select)

        # Separator
        ttk.Separator(left_pane, orient='horizontal').pack(fill=tk.X, pady=5)

        # Reconstructed Tree
        recon_label = ttk.Label(left_pane, text="Reconstructed Signals", font=('TkDefaultFont', 9, 'bold'))
        recon_label.pack(fill=tk.X, pady=(0,5))

        recon_tree_frame = ttk.Frame(left_pane)
        recon_tree_frame.pack(expand=True, fill=tk.BOTH)

        self.recon_tree = ttk.Treeview(recon_tree_frame, columns=("info",), show="tree headings", height=12)
        self.recon_tree.heading("#0", text="File / Record")
        self.recon_tree.column("#0", width=180)
        self.recon_tree.heading("info", text="Info")
        self.recon_tree.column("info", width=100)
        self.recon_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        recon_scrollbar = ttk.Scrollbar(recon_tree_frame, orient="vertical", command=self.recon_tree.yview)
        self.recon_tree.configure(yscrollcommand=recon_scrollbar.set)
        recon_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.recon_tree.bind("<<TreeviewSelect>>", self.on_recon_select)

        # --- Right Pane: Plots and controls ---
        right_pane = ttk.Frame(paned_window, padding="5")
        paned_window.add(right_pane, weight=5)
        right_pane.grid_rowconfigure(0, weight=4) # Reconstructed plot area
        right_pane.grid_rowconfigure(1, weight=0) # Reconstructed controls
        right_pane.grid_rowconfigure(2, weight=5) # Testlab plot area
        right_pane.grid_rowconfigure(3, weight=0) # Testlab controls
        right_pane.grid_rowconfigure(4, weight=0) # Validation metrics panel
        right_pane.grid_columnconfigure(0, weight=1)

        # Reconstructed FRF Plot
        self.fig_recon = Figure(figsize=(7, 2.5), dpi=100)
        self.ax_recon = self.fig_recon.add_subplot(111)
        self.ax_recon.set_title("Reconstructed FRF (Linear Scale)")
        self.canvas_recon = FigureCanvasTkAgg(self.fig_recon, master=right_pane)
        self.canvas_recon_widget = self.canvas_recon.get_tk_widget()
        self.canvas_recon_widget.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        # --- Reconstructed Plot Controls ---
        recon_controls_frame = ttk.Frame(right_pane)
        recon_controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.recon_xmin_var = tk.StringVar()
        self.recon_xmax_var = tk.StringVar()
        self.recon_ymin_var = tk.StringVar()
        self.recon_ymax_var = tk.StringVar()

        ttk.Label(recon_controls_frame, text="X Min:").pack(side=tk.LEFT, padx=(0,2))
        self.recon_xmin_entry = ttk.Entry(recon_controls_frame, textvariable=self.recon_xmin_var, width=8, state=tk.DISABLED)
        self.recon_xmin_entry.pack(side=tk.LEFT)
        ttk.Label(recon_controls_frame, text="X Max:").pack(side=tk.LEFT, padx=(5,2))
        self.recon_xmax_entry = ttk.Entry(recon_controls_frame, textvariable=self.recon_xmax_var, width=8, state=tk.DISABLED)
        self.recon_xmax_entry.pack(side=tk.LEFT)
        
        ttk.Label(recon_controls_frame, text="Y Min:").pack(side=tk.LEFT, padx=(15,2))
        self.recon_ymin_entry = ttk.Entry(recon_controls_frame, textvariable=self.recon_ymin_var, width=8, state=tk.DISABLED)
        self.recon_ymin_entry.pack(side=tk.LEFT)
        ttk.Label(recon_controls_frame, text="Y Max:").pack(side=tk.LEFT, padx=(5,2))
        self.recon_ymax_entry = ttk.Entry(recon_controls_frame, textvariable=self.recon_ymax_var, width=8, state=tk.DISABLED)
        self.recon_ymax_entry.pack(side=tk.LEFT)
        
        self.apply_scale_button = ttk.Button(recon_controls_frame, text="Apply Scale", command=self.apply_recon_scale, state=tk.DISABLED)
        self.apply_scale_button.pack(side=tk.LEFT, padx=10)
        self.reset_scale_button = ttk.Button(recon_controls_frame, text="Reset Scale", command=self.reset_recon_scale, state=tk.DISABLED)
        self.reset_scale_button.pack(side=tk.LEFT)

        # Testlab FRF Plot (with optional phase)
        self.fig_testlab = Figure(figsize=(7, 3.5), dpi=100)
        self.axes_testlab = self.fig_testlab.subplots(2, 1, sharex=True)
        self.fig_testlab.tight_layout(pad=3.0)
        self.canvas_testlab = FigureCanvasTkAgg(self.fig_testlab, master=right_pane)
        self.canvas_testlab_widget = self.canvas_testlab.get_tk_widget()
        self.canvas_testlab_widget.grid(row=2, column=0, sticky="nsew", pady=(10, 5))
        
        # Controls for Testlab plot
        controls_frame_testlab = ttk.Frame(right_pane)
        controls_frame_testlab.grid(row=3, column=0, sticky="ew", pady=(5,0))
        
        self.show_phase_var = tk.BooleanVar(value=True)
        self.show_phase_check = ttk.Checkbutton(controls_frame_testlab, text="Show Phase", 
                                                variable=self.show_phase_var, command=self.update_testlab_plots)
        self.show_phase_check.pack(side=tk.LEFT, padx=(0,10))

        self.log_scale_var = tk.BooleanVar(value=True)
        self.log_scale_check = ttk.Checkbutton(controls_frame_testlab, text="Log Scale", 
                                               variable=self.log_scale_var, command=self.update_testlab_plots)
        self.log_scale_check.pack(side=tk.LEFT)

        self.save_button = ttk.Button(controls_frame_testlab, text="Save Selected Testlab Record", 
                                      command=self.save_selected_record, state=tk.DISABLED)
        self.save_button.pack(side=tk.RIGHT)

        # --- Validation Metrics Panel ---
        validation_frame = ttk.LabelFrame(right_pane, text="Quantitative Validation Metrics", padding="10")
        validation_frame.grid(row=4, column=0, sticky="nsew", pady=(10,0))
        right_pane.grid_rowconfigure(4, weight=2)

        metrics_scroll_frame = ttk.Frame(validation_frame)
        metrics_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.metrics_text = tk.Text(metrics_scroll_frame, height=10, width=70, state=tk.DISABLED, 
                                    font=('Courier', 9), wrap=tk.NONE)
        self.metrics_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        metrics_scrollbar = ttk.Scrollbar(metrics_scroll_frame, orient="vertical", command=self.metrics_text.yview)
        self.metrics_text.configure(yscrollcommand=metrics_scrollbar.set)
        metrics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.calculate_metrics_button = ttk.Button(validation_frame, 
                                                   text="Calculate Validation Metrics", 
                                                   command=self.calculate_validation_metrics,
                                                   state=tk.DISABLED)
        self.calculate_metrics_button.pack(pady=(5,0))

    def reset_ui_testlab(self):
        """Clears the testlab tree and plot."""
        for i in self.testlab_tree.get_children():
            self.testlab_tree.delete(i)
        self.testlab_record_map.clear()
        for ax in self.axes_testlab:
            ax.clear()
        self.axes_testlab[0].set_title("Select a Testlab record to display")
        self.canvas_testlab.draw()
        self.save_button.config(state=tk.DISABLED)
        self.selected_testlab_iid = None
        self.testlab_file_type = None
        self.update_metrics_button_state()

    def clear_reconstructed_files(self):
        """Clears all loaded reconstructed files."""
        for i in self.recon_tree.get_children():
            self.recon_tree.delete(i)
        self.reconstructed_files.clear()
        self.selected_reconstructed_iid = None
        self.ax_recon.clear()
        self.ax_recon.set_title("No reconstructed signal loaded")
        self.canvas_recon.draw()
        
        for widget in [self.recon_xmin_entry, self.recon_xmax_entry, 
                      self.recon_ymin_entry, self.recon_ymax_entry, 
                      self.apply_scale_button, self.reset_scale_button]:
            widget.config(state=tk.DISABLED)
        
        self.update_metrics_button_state()
        self.file_label.config(text="Reconstructed files cleared.")

    def load_testlab_file(self):
        """Opens a file dialog to select a .mat or .unv file and loads its contents."""
        filepath = filedialog.askopenfilename(
            title="Select Testlab data file",
            filetypes=(("Supported Files", "*.mat *.unv"), ("All files", "*.*"))
        )
        if not filepath: return

        self.reset_ui_testlab()
        self.current_testlab_filepath = filepath
        filename = filepath.split('/')[-1]
        self.file_label.config(text=f"Loading: {filename}...")
        self.root.update_idletasks() 

        try:
            print(f"--- Loading Testlab File: {filepath} ---")
            if filepath.lower().endswith('.mat'):
                self.testlab_file_type = 'mat'
                print("File type detected: .mat")
                self.testlab_data = sio.loadmat(filepath, struct_as_record=False, squeeze_me=True)
                print("Raw .mat data loaded.")
                self.populate_testlab_tree_mat()
            elif filepath.lower().endswith('.unv'):
                self.testlab_file_type = 'unv'
                print("File type detected: .unv")
                uff_file = pyuff.UFF(filepath)
                self.testlab_data = uff_file.read_sets()
                print(f"pyuff read_sets result type: {type(self.testlab_data)}")
                self.populate_testlab_tree_unv()
            else:
                raise ValueError("Unsupported file type.")
            
            self.file_label.config(text=f"Testlab loaded: {filename}")
            print("--- Testlab file loading successful ---")

        except Exception as e:
            print("--- ERROR DETAILS (Testlab File) ---")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            traceback.print_exc()
            print("---------------------------------")
            messagebox.showerror("Error", f"Failed to load Testlab file.\n{e}")
            self.reset_ui_testlab()
            self.file_label.config(text="File loading failed.")
        
        self.canvas_testlab.draw()

    def load_reconstructed_files(self):
        """Opens a file dialog to select multiple reconstructed .unv files."""
        filepaths = filedialog.askopenfilenames(
            title="Select Reconstructed FRF files (multiple selection allowed)",
            filetypes=(("Universal files", "*.unv"), ("All files", "*.*"))
        )
        if not filepaths: return
        
        self.file_label.config(text=f"Loading {len(filepaths)} reconstructed files...")
        self.root.update_idletasks()
        
        successful = 0
        failed = 0
        
        for filepath in filepaths:
            try:
                print(f"\n--- Loading Reconstructed File: {filepath} ---")
                
                # Try custom parser first
                try:
                    print("Attempting custom parser...")
                    data_dict = self._parse_reconstructed_unv(filepath)
                    if data_dict is not None:
                        print("Successfully parsed using custom parser.")
                    else:
                        raise ValueError("Custom parser returned None")
                except Exception as custom_err:
                    print(f"Custom parser failed: {custom_err}")
                    print("Falling back to pyuff library...")
                    
                    temp_filepath = None
                    try:
                        with open(filepath, 'r') as f:
                            lines = f.readlines()
                        
                        output_lines = []
                        i = 0
                        while i < len(lines):
                            line = lines[i].strip()
                            if line == '151' and i > 0 and lines[i-1].strip() == '-1':
                                i += 1
                                while i < len(lines):
                                    if lines[i].strip() == '-1':
                                        break
                                    i += 1
                            else:
                                output_lines.append(lines[i])
                            i += 1

                        filtered_content = "".join(output_lines)
                        
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.unv', encoding='utf-8') as temp_f:
                            temp_f.write(filtered_content)
                            temp_filepath = temp_f.name

                        uff_file = pyuff.UFF(temp_filepath)
                        data = uff_file.read_sets()
                        
                        if isinstance(data, dict):
                            data = [data]
                        
                        if not data or not isinstance(data, list) or len(data) == 0:
                            raise ValueError("No valid data sets found in the file.")

                        data_dict = data[0]
                        print("Successfully extracted using pyuff.")
                    finally:
                        if temp_filepath and os.path.exists(temp_filepath):
                            os.remove(temp_filepath)
                
                # Add to reconstructed files collection
                file_iid = f"recon_file_{self.reconstructed_file_counter}"
                self.reconstructed_file_counter += 1
                
                filename = os.path.basename(filepath)
                self.reconstructed_files[file_iid] = {
                    'filepath': filepath,
                    'filename': filename,
                    'data': data_dict,
                    'records': {file_iid: data_dict}  # Single record for now
                }
                
                # Add to tree
                file_node = self.recon_tree.insert("", "end", iid=file_iid, text=filename, open=True)
                
                # For simplicity, treat each file as having one record
                # (Could be extended to handle multi-record reconstructed files)
                info_text = f"{data_dict.get('num_points', len(data_dict['x']))} pts"
                self.recon_tree.insert(file_node, "end", iid=file_iid, text="Record 1", values=(info_text,))
                
                successful += 1
                print(f"Successfully loaded: {filename}")
                
            except Exception as e:
                failed += 1
                print(f"--- ERROR loading {filepath} ---")
                print(f"Error: {e}")
                traceback.print_exc()
        
        # Update status
        status_msg = f"Loaded {successful} reconstructed file(s)"
        if failed > 0:
            status_msg += f" ({failed} failed)"
        self.file_label.config(text=status_msg)
        
        if successful > 0:
            self.update_metrics_button_state()
        
        print(f"\n--- Batch loading complete: {successful} successful, {failed} failed ---")

    def populate_testlab_tree_mat(self):
        filename = self.current_testlab_filepath.split('/')[-1]
        file_node = self.testlab_tree.insert("", "end", text=filename, open=True)
        if not self.testlab_data: return
        for key, value in self.testlab_data.items():
            if key.startswith('__'): continue
            def process_record(record, iid, parent):
                if hasattr(record, 'Name') and hasattr(record, 'X_Data') and hasattr(record, 'Y_Data'):
                    record_name = getattr(record, 'Name', f'Record {iid}')
                    self.testlab_record_map[iid] = record
                    self.testlab_tree.insert(parent, "end", text=record_name, iid=iid)
                    return True
                return False
            if isinstance(value, np.ndarray) and value.dtype.kind == 'O':
                parent_node = self.testlab_tree.insert(file_node, "end", text=key, open=True)
                for i, record in enumerate(value):
                    process_record(record, f"{key}_{i}", parent_node)
            elif hasattr(value, '_fieldnames'):
                parent_node = file_node
                process_record(value, key, parent_node)

    def populate_testlab_tree_unv(self):
        filename = self.current_testlab_filepath.split('/')[-1]
        file_node = self.testlab_tree.insert("", "end", text=filename, open=True)
        type_nodes = {}
        
        data_to_process = self.testlab_data
        if isinstance(data_to_process, dict):
            data_to_process = [data_to_process]
            
        for i, dataset in enumerate(data_to_process):
            if dataset.get('type') == 58:
                node_key = 58
                node_text = "Functions (Type 58)"
                try:
                    record_name = f"Resp:{dataset.get('rsp_node',0)}:{dataset.get('rsp_dir',0)}/Ref:{dataset.get('ref_node',0)}:{dataset.get('ref_dir',0)}"
                except:
                    record_name = f"Record {i+1}"
                if node_key not in type_nodes:
                    type_nodes[node_key] = self.testlab_tree.insert(file_node, "end", text=node_text, open=True)
                iid = f"testlab_{i}"
                self.testlab_record_map[iid] = dataset
                self.testlab_tree.insert(type_nodes[node_key], "end", text=record_name, iid=iid)

    def on_testlab_select(self, event=None):
        selected_iid = self.testlab_tree.focus()
        if not selected_iid or selected_iid not in self.testlab_record_map:
            self.save_button.config(state=tk.DISABLED)
            self.selected_testlab_iid = None
            self.update_metrics_button_state()
            return
        self.selected_testlab_iid = selected_iid
        self.update_testlab_plots()
        self.save_button.config(state=tk.NORMAL)
        self.update_metrics_button_state()

    def on_recon_select(self, event=None):
        selected_iid = self.recon_tree.focus()
        
        # Find the actual record data
        record_data = None
        for file_iid, file_info in self.reconstructed_files.items():
            if selected_iid == file_iid or selected_iid in file_info['records']:
                record_data = file_info['data']
                break
        
        if record_data is None:
            self.selected_reconstructed_iid = None
            self.update_metrics_button_state()
            return
        
        self.selected_reconstructed_iid = selected_iid
        
        # Plot the selected reconstructed signal
        try:
            x_data = record_data['x']
            y_data_raw = record_data['data']
            
            if y_data_raw.ndim == 2:
                y_data = y_data_raw[:, 0]
            else:
                y_data = y_data_raw
            
            self.ax_recon.clear()
            self.ax_recon.plot(x_data, y_data)
            
            # Get filename for title
            filename = "Reconstructed FRF"
            for file_iid, file_info in self.reconstructed_files.items():
                if selected_iid == file_iid or selected_iid in file_info['records']:
                    filename = file_info['filename']
                    break
            
            self.ax_recon.set_title(f"Reconstructed: {filename}")
            self.ax_recon.set_xlabel("Frequency (Hz)")
            self.ax_recon.set_ylabel("Amplitude")
            self.ax_recon.grid(True, linestyle='--')
            self.fig_recon.tight_layout()
            self.canvas_recon.draw()
            
            # Update scale controls
            xmin, xmax = self.ax_recon.get_xlim()
            ymin, ymax = self.ax_recon.get_ylim()
            self.recon_xmin_var.set(f"{xmin:.2f}")
            self.recon_xmax_var.set(f"{xmax:.2f}")
            self.recon_ymin_var.set(f"{ymin:.2f}")
            self.recon_ymax_var.set(f"{ymax:.2f}")

            for widget in [self.recon_xmin_entry, self.recon_xmax_entry, 
                          self.recon_ymin_entry, self.recon_ymax_entry, 
                          self.apply_scale_button, self.reset_scale_button]:
                widget.config(state=tk.NORMAL)
            
            self.update_metrics_button_state()
            
        except Exception as e:
            print(f"Error plotting reconstructed signal: {e}")
            traceback.print_exc()

    def update_metrics_button_state(self):
        """Enable metrics button only if both testlab and reconstructed signals are selected."""
        if self.selected_testlab_iid and self.selected_reconstructed_iid:
            self.calculate_metrics_button.config(state=tk.NORMAL)
        else:
            self.calculate_metrics_button.config(state=tk.DISABLED)

    def apply_recon_scale(self):
        """Applies the manual axis limits from the entry boxes to the reconstructed plot."""
        try:
            xmin = float(self.recon_xmin_var.get())
            xmax = float(self.recon_xmax_var.get())
            ymin = float(self.recon_ymin_var.get())
            ymax = float(self.recon_ymax_var.get())
            
            self.ax_recon.set_xlim(xmin, xmax)
            self.ax_recon.set_ylim(ymin, ymax)
            self.canvas_recon.draw()
        except (ValueError, TypeError):
            messagebox.showerror("Input Error", "Please enter valid numbers for all axis limits.")

    def reset_recon_scale(self):
        """Resets the reconstructed plot to its default auto-scale."""
        if self.selected_reconstructed_iid:
            self.on_recon_select()  # Re-plot to auto-scale

    def update_testlab_plots(self):
        if not self.selected_testlab_iid: return
            
        record = self.testlab_record_map[self.selected_testlab_iid]
        name = self.testlab_tree.item(self.selected_testlab_iid, 'text')
        
        for ax in self.axes_testlab:
            ax.clear()

        try:
            raw_y_data = None
            if self.testlab_file_type == 'mat':
                x_data = record.X_Data
                raw_y_data = record.Y_Data
                x_label = f"{getattr(record, 'X_Label', 'Freq')} ({getattr(record, 'X_Units', 'Hz')})"
            elif self.testlab_file_type == 'unv':
                x_data = record['x']
                raw_y_data = record['data']
                x_label = f"{record.get('xlabel', 'Abscissa')} ({record.get('xunits_description', '')})"

            is_complex = np.iscomplexobj(raw_y_data)
            is_unv_frf = (self.testlab_file_type == 'unv' and raw_y_data.ndim == 2 and raw_y_data.shape[1] >= 2)

            if is_complex or is_unv_frf:
                if is_unv_frf:
                    complex_y_data = raw_y_data[:, 0] + 1j * raw_y_data[:, 1]
                else:
                    complex_y_data = raw_y_data
                
                mag = np.abs(complex_y_data)
                phase = np.angle(complex_y_data, deg=True)
                self.plot_frf(x_data, mag, phase, name, x_label)
            else:
                self.plot_real(x_data, raw_y_data, name, x_label)

        except Exception as e:
            messagebox.showwarning("Plot Error", f"Could not plot selected record.\nDetails: {e}")
            for ax in self.axes_testlab:
                ax.clear()
            self.axes_testlab[0].set_title(f"Could not plot record: {name}")
            self.canvas_testlab.draw()
            self.save_button.config(state=tk.DISABLED)

    def plot_frf(self, x, mag, phase, name, xlabel):
        """Plot FRF with optional phase display."""
        show_phase = self.show_phase_var.get()
        
        if show_phase:
            # Show both magnitude and phase
            self.axes_testlab[0].set_visible(True)
            self.axes_testlab[1].set_visible(True)
            
            self.axes_testlab[0].plot(x, mag)
            self.axes_testlab[0].set_title(f"Testlab: {name}")
            self.axes_testlab[0].set_ylabel("Amplitude")
            
            if self.log_scale_var.get():
                self.axes_testlab[0].set_yscale('log')
                self.axes_testlab[0].set_ylim(1e-3, 1e2)
                self.axes_testlab[0].grid(True, which='both', linestyle='--')
            else:
                self.axes_testlab[0].set_yscale('linear')
                self.axes_testlab[0].grid(True, linestyle='--')

            self.axes_testlab[1].plot(x, phase)
            self.axes_testlab[1].set_ylabel("Phase (deg)")
            self.axes_testlab[1].set_xlabel(xlabel)
            self.axes_testlab[1].grid(True, linestyle='--')
            
            self.fig_testlab.tight_layout(h_pad=0.5)
        else:
            # Show magnitude only
            self.axes_testlab[0].set_visible(True)
            self.axes_testlab[1].set_visible(False)
            
            self.axes_testlab[0].plot(x, mag)
            self.axes_testlab[0].set_title(f"Testlab: {name}")
            self.axes_testlab[0].set_ylabel("Amplitude")
            self.axes_testlab[0].set_xlabel(xlabel)
            
            if self.log_scale_var.get():
                self.axes_testlab[0].set_yscale('log')
                self.axes_testlab[0].set_ylim(1e-3, 1e2)
                self.axes_testlab[0].grid(True, which='both', linestyle='--')
            else:
                self.axes_testlab[0].set_yscale('linear')
                self.axes_testlab[0].grid(True, linestyle='--')
            
            self.fig_testlab.tight_layout()
        
        self.canvas_testlab.draw()

    def plot_real(self, x, y, name, xlabel):
        """Plot real-valued data (PSD, Coherence, etc.)."""
        self.axes_testlab[0].set_visible(True)
        self.axes_testlab[1].set_visible(False)
        
        self.axes_testlab[0].plot(x, y)
        self.axes_testlab[0].set_title(f"Testlab: {name}")
        self.axes_testlab[0].set_ylabel("Value")
        self.axes_testlab[0].set_xlabel(xlabel)
        self.axes_testlab[0].set_yscale('linear')
        self.axes_testlab[0].grid(True, linestyle='--')
        
        self.fig_testlab.tight_layout()
        self.canvas_testlab.draw()

    def save_selected_record(self):
        if not self.selected_testlab_iid:
            messagebox.showwarning("Save Error", "No record selected.")
            return

        original_record = self.testlab_record_map.get(self.selected_testlab_iid)
        
        initial_filename = self.testlab_tree.item(self.selected_testlab_iid, 'text').replace(":","_").replace("/","-").strip()
        save_path = filedialog.asksaveasfilename(
            title="Save Transformed Record as .unv",
            defaultextension=".unv", filetypes=(("Universal files", "*.unv"),),
            initialfile=f"Linear_{initial_filename}.unv"
        )
        if not save_path: return

        try:
            if self.testlab_file_type == 'unv' and original_record.get('type') == 58:
                y_data_raw = original_record['data']
                
                if y_data_raw.ndim == 2 and y_data_raw.shape[1] >= 2:
                    complex_y = y_data_raw[:, 0] + 1j * y_data_raw[:, 1]
                    linear_magnitude = np.abs(complex_y)

                    new_record = original_record.copy()
                    
                    save_data = np.zeros((len(linear_magnitude), 2))
                    save_data[:, 0] = linear_magnitude

                    new_record['data'] = save_data
                    new_record['data_type'] = 2
                    new_record['z_def_type'] = 0
                    new_record['num_values_per_point'] = 2
                    new_record['ylabel'] = 'AMPLITUDE'
                    
                    uff_out = pyuff.UFF(save_path, 'w')
                    uff_out.write_sets(new_record)
                    messagebox.showinfo("Success", f"Successfully saved transformed record to:\n{save_path}")

                else:
                     uff_out = pyuff.UFF(save_path, 'w')
                     uff_out.write_sets(original_record)
                     messagebox.showinfo("Success", f"Record was not a complex FRF. Saved original data to:\n{save_path}")

            elif self.testlab_file_type == 'mat':
                messagebox.showwarning("Not Implemented", "Saving transformed FRF from .mat is not yet supported. Please use .unv files for this feature.")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save to .unv file.\n{e}")

    # ==================== CUSTOM UNV PARSER ====================

    def _parse_reconstructed_unv(self, filepath):
        """
        Custom parser for simplified reconstructed FRF .unv files.
        Handles Dataset 58 files with simplified headers that pyuff cannot parse.
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.rstrip('\r\n') for line in f.readlines()]
        
        i = 0
        dataset_found = False
        
        while i < len(lines):
            if lines[i].strip() == '-1' and i + 1 < len(lines) and lines[i+1].strip() == '58':
                dataset_found = True
                i += 2
                break
            i += 1
        
        if not dataset_found:
            raise ValueError("No Dataset 58 found in file")
        
        header_line1 = lines[i].split()
        i += 1
        
        data_char_line = lines[i].split()
        i += 1
        
        if len(data_char_line) >= 3:
            data_type = int(data_char_line[0])
            num_points = int(data_char_line[1])
            spacing_type = int(data_char_line[2])
        else:
            raise ValueError(f"Invalid data characteristic line: {data_char_line}")
        
        if len(data_char_line) >= 6:
            x_min = float(data_char_line[3])
            x_increment_or_max = float(data_char_line[4])
        else:
            x_min = 0.0
            x_increment_or_max = 1.0
        
        axis_lines_to_skip = 4
        i += axis_lines_to_skip
        
        print(f"Scanning for data start from line {i}...")
        data_start_found = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            if 'E' in line or 'e' in line:
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        f1 = float(parts[0])
                        f2 = float(parts[1])
                        print(f"Found data starting at line {i}: {line[:50]}")
                        data_start_found = True
                        break
                except:
                    pass
            
            i += 1
            
            if i > 100:
                raise ValueError("Could not find data section in first 100 lines")
        
        if not data_start_found:
            raise ValueError("Could not locate data section")
        
        print(f"Parsing data starting at line {i}, expecting {num_points} points")
        data_values = []
        lines_parsed = 0
        
        while i < len(lines) and len(data_values) < num_points * 2:
            line = lines[i].strip()
            
            if line == '-1':
                break
            
            if not line:
                i += 1
                continue
            
            try:
                parts = line.split()
                for part in parts:
                    try:
                        val = float(part)
                        data_values.append(val)
                    except ValueError:
                        pass
            except:
                pass
            
            i += 1
            lines_parsed += 1
            
            if lines_parsed > num_points * 3:
                print(f"Warning: Parsed more lines than expected. Breaking.")
                break
        
        print(f"Collected {len(data_values)} values for {num_points} points (need {num_points*2} values)")
        
        if len(data_values) < num_points * 2:
            print(f"Warning: Only found {len(data_values)} values, expected {num_points * 2}")
            while len(data_values) < num_points * 2:
                data_values.append(0.0)
        
        data_array = np.array(data_values[:num_points * 2]).reshape(num_points, 2)
        
        if spacing_type == 1:
            if x_increment_or_max > x_min + 1:
                x_data = np.linspace(x_min, x_increment_or_max, num_points)
            else:
                x_data = np.arange(num_points) * x_increment_or_max + x_min
        else:
            x_data = np.arange(num_points) * x_increment_or_max + x_min
        
        result = {
            'type': 58,
            'x': x_data,
            'data': data_array,
            'data_type': data_type,
            'num_points': num_points
        }
        
        print(f"Successfully parsed: {num_points} points, x range: [{x_data[0]:.2f}, {x_data[-1]:.2f}]")
        print(f"Data range: [{np.min(data_array):.6e}, {np.max(data_array):.6e}]")
        return result
    
    def _is_float(self, value):
        """Helper to check if a string can be converted to float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    # ==================== VALIDATION METRICS METHODS ====================

    def calculate_validation_metrics(self):
        """
        Compute all validation metrics between reconstructed and selected Testlab FRF.
        """
        if not self.selected_reconstructed_iid:
            messagebox.showwarning("Validation Error", "Select a reconstructed signal first.")
            return
        
        if not self.selected_testlab_iid:
            messagebox.showwarning("Validation Error", "Select a Testlab record to compare.")
            return
        
        try:
            print("\n--- Starting Validation Calculation ---")
            
            # Get testlab data
            testlab_record = self.testlab_record_map[self.selected_testlab_iid]
            if self.testlab_file_type == 'mat':
                x_testlab = testlab_record.X_Data
                y_testlab_raw = testlab_record.Y_Data
            elif self.testlab_file_type == 'unv':
                x_testlab = testlab_record['x']
                y_testlab_raw = testlab_record['data']
            
            # Convert to complex
            if np.iscomplexobj(y_testlab_raw):
                y_testlab_complex = y_testlab_raw
            elif y_testlab_raw.ndim == 2 and y_testlab_raw.shape[1] >= 2:
                y_testlab_complex = y_testlab_raw[:, 0] + 1j * y_testlab_raw[:, 1]
            else:
                messagebox.showerror("Validation Error", 
                                   "Selected testlab record is not a complex FRF.")
                return
            
            # Get reconstructed data
            recon_record = None
            for file_iid, file_info in self.reconstructed_files.items():
                if self.selected_reconstructed_iid == file_iid or self.selected_reconstructed_iid in file_info['records']:
                    recon_record = file_info['data']
                    break
            
            if recon_record is None:
                messagebox.showerror("Validation Error", "Could not find reconstructed record data.")
                return
            
            x_recon = recon_record['x']
            y_recon_raw = recon_record['data']
            
            if y_recon_raw.ndim == 2:
                y_recon_amplitude = y_recon_raw[:, 0]
            else:
                y_recon_amplitude = y_recon_raw
            
            # Interpolate testlab to reconstructed grid
            print(f"Interpolating Testlab data to reconstructed frequency grid...")
            y_testlab_interp = self._interpolate_to_common_grid(
                x_testlab, y_testlab_complex, x_recon
            )
            
            # Convert reconstructed to complex (zero phase assumption)
            y_recon_complex = y_recon_amplitude + 0j
            
            # Compute metrics
            print("Computing validation metrics...")
            results = self._compute_all_metrics(
                x_recon, y_recon_complex, y_testlab_interp
            )
            
            # Display results
            self._display_validation_results(results)
            print("--- Validation Calculation Complete ---\n")
            
        except Exception as e:
            print("--- ERROR in Validation Calculation ---")
            traceback.print_exc()
            messagebox.showerror("Validation Error", f"Failed to calculate metrics.\n{e}")

    def _interpolate_to_common_grid(self, x_source, y_source_complex, x_target):
        """Interpolate complex data to a common frequency grid."""
        real_interp = interp1d(x_source, y_source_complex.real, 
                              kind='linear', bounds_error=False, fill_value=0)
        imag_interp = interp1d(x_source, y_source_complex.imag, 
                              kind='linear', bounds_error=False, fill_value=0)
        
        return real_interp(x_target) + 1j * imag_interp(x_target)

    def _compute_all_metrics(self, freq, y_original, y_reconstructed):
        """Compute all validation metrics."""
        mag_orig = np.abs(y_original)
        mag_recon = np.abs(y_reconstructed)
        
        results = {}
        
        # RMSE
        error = mag_orig - mag_recon
        rmse = np.sqrt(np.mean(error**2))
        results['RMSE'] = rmse
        
        # R²
        r2 = r2_score(mag_orig, mag_recon)
        results['R2'] = r2
        
        # MAE
        mae = np.mean(np.abs(error))
        results['MAE'] = mae
        
        # FRAC
        numerator = np.abs(np.vdot(y_original, y_reconstructed))**2
        denom_a = np.vdot(y_original, y_original).real
        denom_b = np.vdot(y_reconstructed, y_reconstructed).real
        
        if denom_a > 0 and denom_b > 0:
            frac = numerator / (denom_a * denom_b)
            results['FRAC'] = frac
        else:
            results['FRAC'] = None
        
        # Peak Analysis
        prominence_threshold = 0.1 * np.max(mag_orig)
        peaks_orig, _ = find_peaks(mag_orig, prominence=prominence_threshold)
        peaks_recon, _ = find_peaks(mag_recon, prominence=prominence_threshold)
        
        freq_tolerance = 0.05 * (freq[-1] - freq[0])
        peak_comparisons = []
        
        for pk_idx in peaks_orig:
            f_orig = freq[pk_idx]
            mag_orig_pk = mag_orig[pk_idx]
            
            if len(peaks_recon) > 0:
                freq_diffs = np.abs(freq[peaks_recon] - f_orig)
                nearest_idx = np.argmin(freq_diffs)
                
                if freq_diffs[nearest_idx] < freq_tolerance:
                    pk_recon_idx = peaks_recon[nearest_idx]
                    f_recon = freq[pk_recon_idx]
                    mag_recon_pk = mag_recon[pk_recon_idx]
                    
                    peak_comparisons.append({
                        'freq_original': f_orig,
                        'freq_reconstructed': f_recon,
                        'freq_error': f_recon - f_orig,
                        'freq_error_pct': 100 * (f_recon - f_orig) / f_orig if f_orig != 0 else 0,
                        'mag_original': mag_orig_pk,
                        'mag_reconstructed': mag_recon_pk,
                        'mag_error': mag_recon_pk - mag_orig_pk,
                        'mag_error_pct': 100 * (mag_recon_pk - mag_orig_pk) / mag_orig_pk if mag_orig_pk != 0 else 0
                    })
        
        results['peak_analysis'] = peak_comparisons
        results['n_peaks_original'] = len(peaks_orig)
        results['n_peaks_reconstructed'] = len(peaks_recon)
        results['n_peaks_matched'] = len(peak_comparisons)
        
        return results

    def _display_validation_results(self, results):
        """Format and display validation results."""
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 75)
        output.append("              QUANTITATIVE VALIDATION METRICS REPORT")
        output.append("=" * 75)
        output.append("Reference: Scientific Validation Guide (Oct 2025)")
        output.append("")
        
        # Global Metrics
        output.append("[1] GLOBAL ERROR METRICS")
        output.append("    " + "-" * 71)
        output.append(f"    Root Mean Squared Error (RMSE):    {results['RMSE']:.6e}")
        output.append(f"    Mean Absolute Error (MAE):         {results['MAE']:.6e}")
        output.append(f"    Coefficient of Determination (R²): {results['R2']:.6f}")
        
        if results['R2'] > 0.95:
            output.append("        → Excellent linear correlation")
        elif results['R2'] > 0.85:
            output.append("        → Good linear correlation")
        elif results['R2'] > 0.70:
            output.append("        → Moderate linear correlation")
        else:
            output.append("        → Poor linear correlation")
        
        output.append("")
        
        # Advanced Metrics
        output.append("[2] ADVANCED SHAPE METRICS")
        output.append("    " + "-" * 71)
        if results['FRAC'] is not None:
            output.append(f"    Frequency Response Assurance")
            output.append(f"    Criterion (FRAC):                  {results['FRAC']:.6f}")
            
            if results['FRAC'] > 0.95:
                output.append("        → Excellent shape consistency (>0.95)")
            elif results['FRAC'] > 0.85:
                output.append("        → Good shape consistency (0.85-0.95)")
            elif results['FRAC'] > 0.70:
                output.append("        → Moderate shape consistency (0.70-0.85)")
            else:
                output.append("        → Poor shape consistency (<0.70)")
        else:
            output.append("    FRAC: Unable to calculate (denominator error)")
        
        output.append("")
        
        # Peak Analysis
        output.append("[3] FEATURE-SPECIFIC ANALYSIS: RESONANT PEAKS")
        output.append("    " + "-" * 71)
        output.append(f"    Peaks Detected in Original Signal:      {results['n_peaks_original']}")
        output.append(f"    Peaks Detected in Reconstructed Signal: {results['n_peaks_reconstructed']}")
        output.append(f"    Successfully Matched Peak Pairs:        {results['n_peaks_matched']}")
        output.append("")
        
        if len(results['peak_analysis']) > 0:
            output.append("    Peak-by-Peak Comparison:")
            output.append("    " + "-" * 71)
            
            for i, peak in enumerate(results['peak_analysis'], 1):
                output.append(f"    Peak #{i}:")
                output.append(f"      Frequency (Original):    {peak['freq_original']:10.2f} Hz")
                output.append(f"      Frequency (Reconstruct): {peak['freq_reconstructed']:10.2f} Hz")
                output.append(f"      Frequency Error:         {peak['freq_error']:+10.2f} Hz "
                            f"({peak['freq_error_pct']:+6.2f}%)")
                output.append(f"      Magnitude (Original):    {peak['mag_original']:.4e}")
                output.append(f"      Magnitude (Reconstruct): {peak['mag_reconstructed']:.4e}")
                output.append(f"      Magnitude Error:         {peak['mag_error']:+.4e} "
                            f"({peak['mag_error_pct']:+6.2f}%)")
                if i < len(results['peak_analysis']):
                    output.append("")
        else:
            output.append("    No resonant peaks could be matched between the two signals.")
        
        output.append("")
        output.append("=" * 75)
        output.append("Note: FRAC values near 1.0 indicate excellent shape similarity.")
        output.append("      Peak matching uses 5% frequency tolerance.")
        output.append("=" * 75)
        
        self.metrics_text.insert(1.0, "\n".join(output))
        self.metrics_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = EMAVApp(root)
    root.mainloop()