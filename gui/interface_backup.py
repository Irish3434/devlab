"""
Enhanced GUI interface for Picture Finder with responsive design, accessibility,
internationalization support, and comprehensive user experience features.
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import webbrowser

from gui.styles import PictureFinderTheme, add_tooltip, create_icon_button, ICONS, make_accessible
from core.image_processor import ImageProcessor
from core.log_writer import get_logger, create_log_file


class ProgressDialog:
    """Modal progress dialog with cancel functionality."""
    
    def __init__(self, parent, title: str = "Processing..."):
        """
        Initialize progress dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
        """
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.cancelled = False
        self.cancel_callback: Optional[Callable] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='PF.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Initializing...",
            style='PF.TLabel',
            font=('Helvetica', 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            style='PF.TProgressbar'
        )
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # Details label (smaller text)
        self.details_label = ttk.Label(
            main_frame,
            text="",
            style='Status.TLabel',
            font=('Helvetica', 8)
        )
        self.details_label.pack(pady=(0, 10))
        
        # Cancel button
        self.cancel_button = create_icon_button(
            main_frame,
            "Cancel",
            command=self._on_cancel,
            icon_char=ICONS['cancel'],
            style='Error.TButton'
        )
        self.cancel_button.pack()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_var.set(percentage)
            self.status_label.configure(text=f"{current:,} / {total:,} files processed")
        else:
            self.progress_bar.configure(mode='indeterminate')
            self.progress_bar.start()
            self.status_label.configure(text="Processing...")
        
        if message:
            self.details_label.configure(text=message)
        
        self.dialog.update()
    
    def set_cancel_callback(self, callback: Callable):
        """Set callback to call when cancel is pressed."""
        self.cancel_callback = callback
    
    def _on_cancel(self):
        """Handle cancel button/close."""
        if messagebox.askyesno("Cancel", "Cancel processing?", parent=self.dialog):
            self.cancelled = True
            if self.cancel_callback:
                self.cancel_callback()
            self.close()
    
    def close(self):
        """Close the dialog."""
        self.progress_bar.stop()
        self.dialog.grab_release()
        self.dialog.destroy()


class SettingsTab:
    """Settings tab with sliders and configuration options."""
    
    def __init__(self, parent_frame, theme: PictureFinderTheme):
        """
        Initialize settings tab.
        
        Args:
            parent_frame: Parent notebook frame
            theme: Theme manager
        """
        self.frame = parent_frame
        self.theme = theme
        self.logger = get_logger()
        
        # Settings variables
        self.similarity_threshold = tk.IntVar(value=10)
        self.chunk_size = tk.IntVar(value=500)
        self.hash_algorithm = tk.StringVar(value='average')
        self.language = tk.StringVar(value='en')
        self.recursive_scan = tk.BooleanVar(value=False)
        self.auto_export = tk.BooleanVar(value=False)
        self.compression_level = tk.IntVar(value=6)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create settings tab widgets."""
        # Main scrollable frame
        canvas = tk.Canvas(self.frame, bg=self.theme.get_color('primary_bg'))
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview, style='PF.TScrollbar')
        scrollable_frame = ttk.Frame(canvas, style='PF.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Detection Settings Section
        detection_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['search']} Detection Settings",
            style='Card.TFrame'
        )
        detection_frame.pack(fill='x', padx=10, pady=5)
        
        # Similarity threshold slider
        ttk.Label(
            detection_frame,
            text=f"Similarity Threshold: {self.similarity_threshold.get()}",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(10, 0))
        
        self.threshold_label = ttk.Label(
            detection_frame,
            text="Lower = More strict, Higher = More lenient",
            style='Status.TLabel'
        )
        self.threshold_label.pack(anchor='w', padx=10)
        
        self.threshold_scale = ttk.Scale(
            detection_frame,
            from_=1, to=20,
            orient='horizontal',
            variable=self.similarity_threshold,
            style='PF.TScale',
            command=self._on_threshold_change
        )
        self.threshold_scale.pack(fill='x', padx=10, pady=(0, 10))
        
        add_tooltip(
            self.threshold_scale,
            "Adjust how similar images must be to be considered duplicates. "
            "Lower values = stricter matching, Higher values = more lenient matching."
        )
        
        # Hash algorithm selection
        ttk.Label(
            detection_frame,
            text="Hash Algorithm:",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(5, 0))
        
        algorithm_frame = ttk.Frame(detection_frame, style='PF.TFrame')
        algorithm_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        algorithms = [
            ('average', 'Average Hash (Recommended)'),
            ('perceptual', 'Perceptual Hash (More accurate)'),
            ('difference', 'Difference Hash (Fast)'),
            ('wavelet', 'Wavelet Hash (Advanced)')
        ]
        
        for value, text in algorithms:
            ttk.Radiobutton(
                algorithm_frame,
                text=text,
                variable=self.hash_algorithm,
                value=value,
                style='PF.TRadiobutton'
            ).pack(anchor='w', pady=2)
        
        # Performance Settings Section
        performance_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['settings']} Performance Settings",
            style='Card.TFrame'
        )
        performance_frame.pack(fill='x', padx=10, pady=5)
        
        # Batch size slider
        ttk.Label(
            performance_frame,
            text=f"Batch Size: {self.chunk_size.get()}",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(10, 0))
        
        ttk.Label(
            performance_frame,
            text="Number of files processed at once",
            style='Status.TLabel'
        ).pack(anchor='w', padx=10)
        
        self.chunk_scale = ttk.Scale(
            performance_frame,
            from_=50, to=1000,
            orient='horizontal',
            variable=self.chunk_size,
            style='PF.TScale',
            command=self._on_chunk_change
        )
        self.chunk_scale.pack(fill='x', padx=10, pady=(0, 10))
        
        add_tooltip(
            self.chunk_scale,
            "Higher values = faster processing but more memory usage. "
            "Lower values = slower but more memory efficient."
        )\n        \n        # Scan Options Section\n        scan_frame = ttk.LabelFrame(\n            scrollable_frame,\n            text=f\"{ICONS['folder']} Scan Options\",\n            style='Card.TFrame'\n        )\n        scan_frame.pack(fill='x', padx=10, pady=5)\n        \n        # Recursive scanning\n        ttk.Checkbutton(\n            scan_frame,\n            text=\"Scan subfolders recursively\",\n            variable=self.recursive_scan,\n            style='PF.TCheckbutton'\n        ).pack(anchor='w', padx=10, pady=5)\n        \n        # Export Settings Section\n        export_frame = ttk.LabelFrame(\n            scrollable_frame,\n            text=f\"{ICONS['zip']} Export Settings\",\n            style='Card.TFrame'\n        )\n        export_frame.pack(fill='x', padx=10, pady=5)\n        \n        # Auto export checkbox\n        ttk.Checkbutton(\n            export_frame,\n            text=\"Automatically export unique photos to ZIP\",\n            variable=self.auto_export,\n            style='PF.TCheckbutton'\n        ).pack(anchor='w', padx=10, pady=5)\n        \n        # Compression level\n        ttk.Label(\n            export_frame,\n            text=f\"Compression Level: {self.compression_level.get()}\",\n            style='PF.TLabel'\n        ).pack(anchor='w', padx=10, pady=(5, 0))\n        \n        ttk.Label(\n            export_frame,\n            text=\"0 = No compression, 9 = Maximum compression\",\n            style='Status.TLabel'\n        ).pack(anchor='w', padx=10)\n        \n        self.compression_scale = ttk.Scale(\n            export_frame,\n            from_=0, to=9,\n            orient='horizontal',\n            variable=self.compression_level,\n            style='PF.TScale',\n            command=self._on_compression_change\n        )\n        self.compression_scale.pack(fill='x', padx=10, pady=(0, 10))\n        \n        # Language Settings Section\n        lang_frame = ttk.LabelFrame(\n            scrollable_frame,\n            text=f\"{ICONS['settings']} Language Settings\",\n            style='Card.TFrame'\n        )\n        lang_frame.pack(fill='x', padx=10, pady=5)\n        \n        ttk.Label(\n            lang_frame,\n            text=\"Language:\",\n            style='PF.TLabel'\n        ).pack(anchor='w', padx=10, pady=(10, 5))\n        \n        language_combo = ttk.Combobox(\n            lang_frame,\n            textvariable=self.language,\n            values=['en', 'es', 'fr'],\n            state='readonly',\n            width=20\n        )\n        language_combo.pack(anchor='w', padx=10, pady=(0, 10))\n        \n        # Reset Settings Button\n        reset_button = create_icon_button(\n            scrollable_frame,\n            \"Reset to Defaults\",\n            command=self._reset_settings,\n            icon_char=ICONS['refresh'],\n            style='Secondary.TButton'\n        )\n        reset_button.pack(pady=10)\n        \n        add_tooltip(reset_button, \"Reset all settings to their default values\")\n    \n    def _on_threshold_change(self, value):\n        \"\"\"Handle similarity threshold change.\"\"\"\n        val = int(float(value))\n        self.similarity_threshold.set(val)\n        \n        # Update label in parent\n        parent = self.threshold_scale.master\n        for child in parent.winfo_children():\n            if isinstance(child, ttk.Label) and \"Similarity Threshold\" in str(child.cget('text')):\n                child.configure(text=f\"Similarity Threshold: {val}\")\n                break\n    \n    def _on_chunk_change(self, value):\n        \"\"\"Handle chunk size change.\"\"\"\n        val = int(float(value))\n        self.chunk_size.set(val)\n        \n        # Update label\n        parent = self.chunk_scale.master\n        for child in parent.winfo_children():\n            if isinstance(child, ttk.Label) and \"Batch Size\" in str(child.cget('text')):\n                child.configure(text=f\"Batch Size: {val}\")\n                break\n    \n    def _on_compression_change(self, value):\n        \"\"\"Handle compression level change.\"\"\"\n        val = int(float(value))\n        self.compression_level.set(val)\n        \n        # Update label\n        parent = self.compression_scale.master\n        for child in parent.winfo_children():\n            if isinstance(child, ttk.Label) and \"Compression Level\" in str(child.cget('text')):\n                child.configure(text=f\"Compression Level: {val}\")\n                break\n    \n    def _reset_settings(self):\n        \"\"\"Reset all settings to defaults.\"\"\"\n        if messagebox.askyesno(\"Reset Settings\", \"Reset all settings to default values?\"):\n            self.similarity_threshold.set(10)\n            self.chunk_size.set(500)\n            self.hash_algorithm.set('average')\n            self.language.set('en')\n            self.recursive_scan.set(False)\n            self.auto_export.set(False)\n            self.compression_level.set(6)\n            \n            # Update scale labels\n            self._on_threshold_change(10)\n            self._on_chunk_change(500)\n            self._on_compression_change(6)\n    \n    def get_settings(self) -> Dict[str, Any]:\n        \"\"\"Get current settings as dictionary.\"\"\"\n        return {\n            'similarity_threshold': self.similarity_threshold.get(),\n            'chunk_size': self.chunk_size.get(),\n            'hash_algorithm': self.hash_algorithm.get(),\n            'language': self.language.get(),\n            'recursive_scan': self.recursive_scan.get(),\n            'auto_export': self.auto_export.get(),\n            'compression_level': self.compression_level.get()\n        }\n\n\nclass MainTab:\n    \"\"\"Main tab with folder selection and processing controls.\"\"\"\n    \n    def __init__(self, parent_frame, theme: PictureFinderTheme, settings_tab: SettingsTab):\n        \"\"\"\n        Initialize main tab.\n        \n        Args:\n            parent_frame: Parent notebook frame\n            theme: Theme manager\n            settings_tab: Settings tab reference\n        \"\"\"\n        self.frame = parent_frame\n        self.theme = theme\n        self.settings_tab = settings_tab\n        self.logger = get_logger()\n        \n        # State variables\n        self.folder_path = tk.StringVar()\n        self.operation_mode = tk.StringVar(value='copy')\n        self.performance_mode = tk.StringVar(value='high')\n        self.status_text = tk.StringVar(value=\"Ready to process photos\")\n        \n        # Processing state\n        self.processor: Optional[ImageProcessor] = None\n        self.processing_thread: Optional[threading.Thread] = None\n        self.progress_dialog: Optional[ProgressDialog] = None\n        \n        self._create_widgets()\n    \n    def _create_widgets(self):\n        \"\"\"Create main tab widgets.\"\"\"\n        # Main container with padding\n        main_container = ttk.Frame(self.frame, style='PF.TFrame')\n        main_container.pack(fill='both', expand=True, padx=20, pady=20)\n        \n        # Header\n        header_frame = ttk.Frame(main_container, style='Header.TFrame')\n        header_frame.pack(fill='x', pady=(0, 20))\n        \n        header_label = ttk.Label(\n            header_frame,\n            text=f\"{ICONS['image']} Picture Finder\",\n            style='Header.TLabel',\n            font=('Helvetica', 16, 'bold')\n        )\n        header_label.pack(pady=10)\n        \n        # Folder selection section\n        folder_frame = ttk.LabelFrame(\n            main_container,\n            text=f\"{ICONS['folder']} Select Photo Folder\",\n            style='Card.TFrame'\n        )\n        folder_frame.pack(fill='x', pady=(0, 15))\n        \n        # Folder path entry and browse button\n        folder_input_frame = ttk.Frame(folder_frame, style='PF.TFrame')\n        folder_input_frame.pack(fill='x', padx=10, pady=10)\n        \n        self.folder_entry = ttk.Entry(\n            folder_input_frame,\n            textvariable=self.folder_path,\n            font=('Helvetica', 10),\n            style='PF.TEntry'\n        )\n        self.folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))\n        \n        browse_button = create_icon_button(\n            folder_input_frame,\n            \"Browse\",\n            command=self._browse_folder,\n            icon_char=ICONS['folder'],\n            style='PF.TButton'\n        )\n        browse_button.pack(side='right')\n        \n        add_tooltip(self.folder_entry, \"Path to the folder containing your photos\")\n        add_tooltip(browse_button, \"Select folder to scan for duplicate photos\")\n        \n        # Operation mode section\n        mode_frame = ttk.LabelFrame(\n            main_container,\n            text=f\"{ICONS['settings']} Processing Options\",\n            style='Card.TFrame'\n        )\n        mode_frame.pack(fill='x', pady=(0, 15))\n        \n        # Operation mode (copy/move)\n        operation_frame = ttk.Frame(mode_frame, style='PF.TFrame')\n        operation_frame.pack(fill='x', padx=10, pady=10)\n        \n        ttk.Label(\n            operation_frame,\n            text=\"Action for unique photos:\",\n            style='PF.TLabel',\n            font=('Helvetica', 10, 'bold')\n        ).pack(anchor='w', pady=(0, 5))\n        \n        # Radio buttons for copy/move\n        radio_frame = ttk.Frame(operation_frame, style='PF.TFrame')\n        radio_frame.pack(fill='x')\n        \n        copy_radio = ttk.Radiobutton(\n            radio_frame,\n            text=f\"{ICONS['copy']} Copy (Keep originals)\",\n            variable=self.operation_mode,\n            value='copy',\n            style='PF.TRadiobutton'\n        )\n        copy_radio.pack(anchor='w', pady=2)\n        \n        move_radio = ttk.Radiobutton(\n            radio_frame,\n            text=f\"{ICONS['move']} Move (Remove originals)\",\n            variable=self.operation_mode,\n            value='move',\n            style='PF.TRadiobutton'\n        )\n        move_radio.pack(anchor='w', pady=2)\n        \n        add_tooltip(copy_radio, \"Copy unique photos to 'unique_photos' folder (original files remain)\")\n        add_tooltip(move_radio, \"Move unique photos to 'unique_photos' folder (original files are moved)\")\n        \n        # Performance mode selection\n        perf_frame = ttk.Frame(mode_frame, style='PF.TFrame')\n        perf_frame.pack(fill='x', padx=10, pady=(0, 10))\n        \n        ttk.Label(\n            perf_frame,\n            text=\"Performance Mode:\",\n            style='PF.TLabel',\n            font=('Helvetica', 10, 'bold')\n        ).pack(anchor='w', pady=(0, 5))\n        \n        perf_combo = ttk.Combobox(\n            perf_frame,\n            textvariable=self.performance_mode,\n            values=['low', 'medium', 'high'],\n            state='readonly',\n            width=30\n        )\n        perf_combo.pack(anchor='w')\n        \n        # Set combobox display values\n        perf_combo.configure(values=[\n            'Low (1 core, minimal RAM)',\n            'Medium (2 cores, moderate RAM)',\n            'High (4 cores, high RAM)'\n        ])\n        perf_combo.set('High (4 cores, high RAM)')\n        \n        add_tooltip(\n            perf_combo,\n            \"Choose performance mode based on your computer's capabilities. \"\n            \"Higher modes are faster but use more system resources.\"\n        )\n        \n        # Action buttons section\n        action_frame = ttk.Frame(main_container, style='PF.TFrame')\n        action_frame.pack(fill='x', pady=(0, 15))\n        \n        # Main action buttons\n        button_frame = ttk.Frame(action_frame, style='PF.TFrame')\n        button_frame.pack()\n        \n        self.run_button = create_icon_button(\n            button_frame,\n            \"Start Processing\",\n            command=self._start_processing,\n            icon_char=ICONS['play'],\n            style='Success.TButton'\n        )\n        self.run_button.pack(side='left', padx=(0, 10))\n        \n        self.export_button = create_icon_button(\n            button_frame,\n            \"Export ZIP\",\n            command=self._export_zip,\n            icon_char=ICONS['zip'],\n            style='PF.TButton'\n        )\n        self.export_button.pack(side='left', padx=(0, 10))\n        self.export_button.configure(state='disabled')\n        \n        self.view_logs_button = create_icon_button(\n            button_frame,\n            \"View Logs\",\n            command=self._view_logs,\n            icon_char=ICONS['file'],\n            style='Secondary.TButton'\n        )\n        self.view_logs_button.pack(side='left')\n        \n        add_tooltip(self.run_button, \"Start scanning for duplicate photos\")\n        add_tooltip(self.export_button, \"Export unique photos to a ZIP file\")\n        add_tooltip(self.view_logs_button, \"Open the log file to see processing details\")\n        \n        # Progress section\n        progress_frame = ttk.LabelFrame(\n            main_container,\n            text=f\"{ICONS['info']} Status\",\n            style='Card.TFrame'\n        )\n        progress_frame.pack(fill='x', pady=(0, 15))\n        \n        # Status label\n        self.status_label = ttk.Label(\n            progress_frame,\n            textvariable=self.status_text,\n            style='Status.TLabel',\n            font=('Helvetica', 10)\n        )\n        self.status_label.pack(padx=10, pady=10)\n        \n        # Quick stats display\n        stats_frame = ttk.Frame(progress_frame, style='PF.TFrame')\n        stats_frame.pack(fill='x', padx=10, pady=(0, 10))\n        \n        self.stats_text = tk.Text(\n            stats_frame,\n            height=4,\n            width=50,\n            wrap='word',\n            background=self.theme.get_color('secondary_bg'),\n            foreground=self.theme.get_color('text_dark'),\n            font=('Courier', 9),\n            state='disabled'\n        )\n        self.stats_text.pack(fill='x')\n        \n        # Help section\n        help_frame = ttk.Frame(main_container, style='PF.TFrame')\n        help_frame.pack(fill='x')\n        \n        help_button = create_icon_button(\n            help_frame,\n            \"Help & Documentation\",\n            command=self._show_help,\n            icon_char=ICONS['info'],\n            style='Secondary.TButton'\n        )\n        help_button.pack()\n        \n        add_tooltip(help_button, \"Open help documentation and user guide\")\n    \n    def _browse_folder(self):\n        \"\"\"Open folder browser dialog.\"\"\"\n        folder = filedialog.askdirectory(\n            title=\"Select folder containing photos\",\n            initialdir=self.folder_path.get() or os.path.expanduser(\"~\")\n        )\n        \n        if folder:\n            self.folder_path.set(folder)\n            self.status_text.set(f\"Selected: {folder}\")\n            self.logger.log_info(f\"User selected folder: {folder}\")\n    \n    def _start_processing(self):\n        \"\"\"Start the photo processing in a separate thread.\"\"\"\n        folder = self.folder_path.get().strip()\n        \n        if not folder:\n            messagebox.showerror(\"Error\", \"Please select a folder first!\")\n            return\n        \n        if not os.path.exists(folder):\n            messagebox.showerror(\"Error\", \"Selected folder does not exist!\")\n            return\n        \n        # Get settings\n        settings = self.settings_tab.get_settings()\n        \n        # Extract performance mode\n        perf_mode_text = self.performance_mode.get()\n        if 'Low' in perf_mode_text:\n            perf_mode = 'low'\n        elif 'Medium' in perf_mode_text:\n            perf_mode = 'medium'\n        else:\n            perf_mode = 'high'\n        \n        # Confirm action\n        mode_text = \"copy\" if self.operation_mode.get() == 'copy' else \"move\"\n        message = (\n            f\"Start processing photos in:\\n{folder}\\n\\n\"\n            f\"Action: {mode_text.title()} unique photos\\n\"\n            f\"Performance: {perf_mode.title()}\\n\"\n            f\"Recursive: {'Yes' if settings['recursive_scan'] else 'No'}\\n\\n\"\n            \"Continue?\"\n        )\n        \n        if not messagebox.askyesno(\"Confirm Processing\", message):\n            return\n        \n        # Disable buttons during processing\n        self.run_button.configure(state='disabled')\n        self.export_button.configure(state='disabled')\n        \n        # Create processor\n        self.processor = ImageProcessor(\n            output_dir=os.getcwd(),\n            performance_mode=perf_mode,\n            hash_algorithm=settings['hash_algorithm'],\n            similarity_threshold=settings['similarity_threshold']\n        )\n        \n        # Show progress dialog\n        self.progress_dialog = ProgressDialog(self.frame.winfo_toplevel(), \"Processing Photos\")\n        self.progress_dialog.set_cancel_callback(self._cancel_processing)\n        \n        # Set up progress callback\n        self.processor.set_progress_callback(self._update_progress)\n        \n        # Start processing thread\n        self.processing_thread = threading.Thread(\n            target=self._process_photos,\n            args=(folder, settings),\n            daemon=True\n        )\n        self.processing_thread.start()\n    \n    def _process_photos(self, folder: str, settings: Dict[str, Any]):\n        \"\"\"Process photos in background thread.\"\"\"\n        try:\n            self.status_text.set(\"Processing photos...\")\n            \n            # Process folder\n            results = self.processor.process_folder(\n                folder_path=folder,\n                mode=self.operation_mode.get(),\n                chunk_size=settings['chunk_size'],\n                recursive=settings['recursive_scan'],\n                export_zip=settings['auto_export']\n            )\n            \n            # Update UI on main thread\n            self.frame.after(0, self._processing_completed, results)\n            \n        except Exception as e:\n            self.logger.log_error(f\"Processing failed: {str(e)}\")\n            self.frame.after(0, self._processing_failed, str(e))\n    \n    def _update_progress(self, current: int, total: int, message: str):\n        \"\"\"Update progress dialog from processing thread.\"\"\"\n        if self.progress_dialog:\n            self.progress_dialog.update_progress(current, total, message)\n    \n    def _processing_completed(self, results: Dict[str, Any]):\n        \"\"\"Handle processing completion on main thread.\"\"\"\n        if self.progress_dialog:\n            self.progress_dialog.close()\n            self.progress_dialog = None\n        \n        # Update statistics display\n        stats_text = (\n            f\"Processing completed in {results['processing_time']:.1f} seconds\\n\"\n            f\"Files scanned: {results['detection_stats']['total_files']:,}\\n\"\n            f\"Duplicate groups: {results['duplicate_groups']:,}\\n\"\n            f\"Total duplicates: {results['total_duplicates']:,}\\n\"\n            f\"Unique files processed: {results['unique_files_processed']:,}\\n\"\n            f\"Videos separated: {results['detection_stats']['videos_separated']:,}\"\n        )\n        \n        self._update_stats_display(stats_text)\n        \n        # Enable export button if unique photos were processed\n        if results['unique_files_processed'] > 0:\n            self.export_button.configure(state='normal')\n        \n        # Show completion message\n        message = (\n            f\"Processing completed successfully!\\n\\n\"\n            f\"• {results['total_duplicates']:,} duplicates found\\n\"\n            f\"• {results['unique_files_processed']:,} unique photos processed\\n\"\n            f\"• {results['detection_stats']['videos_separated']:,} videos separated\\n\\n\"\n            \"Check the output folders for results.\"\n        )\n        \n        if results.get('zip_export_path'):\n            message += f\"\\n\\nZIP export: {results['zip_export_path']}\"\n        \n        messagebox.showinfo(\"Processing Complete\", message)\n        \n        # Re-enable buttons\n        self.run_button.configure(state='normal')\n        \n        self.status_text.set(\"Processing completed successfully\")\n        self.logger.log_info(\"Processing completed successfully\")\n    \n    def _processing_failed(self, error_msg: str):\n        \"\"\"Handle processing failure on main thread.\"\"\"\n        if self.progress_dialog:\n            self.progress_dialog.close()\n            self.progress_dialog = None\n        \n        # Re-enable buttons\n        self.run_button.configure(state='normal')\n        \n        self.status_text.set(f\"Processing failed: {error_msg}\")\n        \n        messagebox.showerror(\n            \"Processing Failed\",\n            f\"An error occurred during processing:\\n\\n{error_msg}\\n\\nCheck the log file for details.\"\n        )\n    \n    def _cancel_processing(self):\n        \"\"\"Cancel current processing operation.\"\"\"\n        if self.processor:\n            self.processor.cancel_processing()\n        \n        self.status_text.set(\"Processing cancelled\")\n        self.run_button.configure(state='normal')\n    \n    def _export_zip(self):\n        \"\"\"Export unique photos to ZIP file.\"\"\"\n        unique_folder = Path(\"unique_photos\")\n        \n        if not unique_folder.exists() or not any(unique_folder.iterdir()):\n            messagebox.showwarning(\n                \"No Files to Export\",\n                \"No unique photos found to export. Process photos first.\"\n            )\n            return\n        \n        # Ask for ZIP file location\n        zip_path = filedialog.asksaveasfilename(\n            title=\"Save ZIP file as\",\n            defaultextension=\".zip\",\n            filetypes=[(\"ZIP files\", \"*.zip\"), (\"All files\", \"*.*\")]\n        )\n        \n        if not zip_path:\n            return\n        \n        # Get compression settings\n        settings = self.settings_tab.get_settings()\n        \n        try:\n            from core.file_manager import FileManager\n            file_manager = FileManager()\n            \n            result = file_manager.export_to_zip(\n                str(unique_folder),\n                zip_path,\n                compression_level=settings['compression_level']\n            )\n            \n            if result:\n                messagebox.showinfo(\n                    \"Export Complete\",\n                    f\"Unique photos exported to:\\n{zip_path}\"\n                )\n                self.logger.log_info(f\"ZIP export completed: {zip_path}\")\n            else:\n                messagebox.showerror(\"Export Failed\", \"Failed to create ZIP file.\")\n                \n        except Exception as e:\n            self.logger.log_error(f\"ZIP export failed: {str(e)}\")\n            messagebox.showerror(\"Export Failed\", f\"Error creating ZIP file:\\n{str(e)}\")\n    \n    def _view_logs(self):\n        \"\"\"Open the log file.\"\"\"\n        try:\n            log_path = self.logger.get_log_file_path()\n            \n            if os.path.exists(log_path):\n                # Try to open with default application\n                if os.name == 'nt':  # Windows\n                    os.startfile(log_path)\n                elif os.name == 'posix':  # macOS/Linux\n                    os.system(f'open \"{log_path}\"' if os.uname().sysname == 'Darwin' else f'xdg-open \"{log_path}\"')\n            else:\n                messagebox.showwarning(\"No Log File\", \"No log file found. Start processing to generate logs.\")\n                \n        except Exception as e:\n            messagebox.showerror(\"Error\", f\"Failed to open log file:\\n{str(e)}\")\n    \n    def _show_help(self):\n        \"\"\"Show help documentation.\"\"\"\n        help_text = \"\"\"\nPicture Finder - Help\n\n1. SELECT FOLDER: Choose the folder containing your photos\n\n2. CHOOSE ACTION:\n   • Copy: Keep original files, copy unique photos to 'unique_photos' folder\n   • Move: Move unique photos to 'unique_photos' folder (originals are removed)\n\n3. PERFORMANCE MODE:\n   • Low: Uses 1 CPU core and minimal RAM (slower, but system-friendly)\n   • Medium: Uses 2 CPU cores and moderate RAM (balanced)\n   • High: Uses 4 CPU cores and high RAM (fastest, but resource-intensive)\n\n4. SETTINGS TAB:\n   • Similarity Threshold: How similar images must be (1=strict, 20=lenient)\n   • Batch Size: Number of files processed at once\n   • Hash Algorithm: Method for detecting duplicates\n   • Recursive Scan: Include subfolders\n\n5. OUTPUT:\n   • Duplicates are moved to 'duplicates' folder\n   • Unique photos go to 'unique_photos' folder\n   • Videos are moved to 'videos' folder\n   • Detailed logs are created for each run\n\nTips:\n• Start with default settings for most use cases\n• Use lower similarity threshold for stricter duplicate detection\n• Enable recursive scan to process subfolders\n• Check logs for detailed processing information\n        \"\"\"\n        \n        # Create help window\n        help_window = tk.Toplevel(self.frame.winfo_toplevel())\n        help_window.title(\"Picture Finder - Help\")\n        help_window.geometry(\"600x500\")\n        help_window.transient(self.frame.winfo_toplevel())\n        \n        # Help text widget with scrollbar\n        text_frame = ttk.Frame(help_window)\n        text_frame.pack(fill='both', expand=True, padx=20, pady=20)\n        \n        text_widget = tk.Text(\n            text_frame,\n            wrap='word',\n            font=('Helvetica', 10),\n            background='white',\n            foreground='black'\n        )\n        \n        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)\n        text_widget.configure(yscrollcommand=scrollbar.set)\n        \n        text_widget.insert('1.0', help_text)\n        text_widget.configure(state='disabled')\n        \n        text_widget.pack(side='left', fill='both', expand=True)\n        scrollbar.pack(side='right', fill='y')\n        \n        # Close button\n        close_button = ttk.Button(\n            help_window,\n            text=\"Close\",\n            command=help_window.destroy\n        )\n        close_button.pack(pady=(0, 20))\n    \n    def _update_stats_display(self, stats_text: str):\n        \"\"\"Update the statistics display.\"\"\"\n        self.stats_text.configure(state='normal')\n        self.stats_text.delete('1.0', tk.END)\n        self.stats_text.insert('1.0', stats_text)\n        self.stats_text.configure(state='disabled')\n\n\nclass PictureFinderGUI:\n    \"\"\"Main GUI application class.\"\"\"\n    \n    def __init__(self, root: tk.Tk):\n        \"\"\"\n        Initialize the Picture Finder GUI.\n        \n        Args:\n            root: Root Tkinter window\n        \"\"\"\n        self.root = root\n        self.logger = get_logger()\n        \n        self._setup_window()\n        self.theme = PictureFinderTheme(root)\n        self.theme.apply_theme()\n        \n        self._create_gui()\n        \n        # Keyboard shortcuts\n        self._setup_keyboard_shortcuts()\n        \n        self.logger.log_info(\"Picture Finder GUI initialized\")\n    \n    def _setup_window(self):\n        \"\"\"Configure the main window.\"\"\"\n        self.root.title(\"Picture Finder - Duplicate Photo Detection\")\n        self.root.geometry(\"800x700\")\n        self.root.minsize(600, 500)\n        \n        # Set icon if available\n        try:\n            icon_path = Path(\"assets/icon.ico\")\n            if icon_path.exists():\n                if os.name == 'nt':  # Windows\n                    self.root.iconbitmap(str(icon_path))\n                else:  # macOS/Linux\n                    # For cross-platform compatibility\n                    pass\n        except Exception:\n            pass  # Icon not critical\n        \n        # Handle window close\n        self.root.protocol(\"WM_DELETE_WINDOW\", self._on_closing)\n    \n    def _create_gui(self):\n        \"\"\"Create the main GUI components.\"\"\"\n        # Main notebook for tabs\n        self.notebook = ttk.Notebook(self.root, style='PF.TNotebook')\n        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)\n        \n        # Main tab frame\n        main_frame = ttk.Frame(self.notebook, style='PF.TFrame')\n        self.notebook.add(main_frame, text=f\"{ICONS['image']} Main\")\n        \n        # Settings tab frame\n        settings_frame = ttk.Frame(self.notebook, style='PF.TFrame')\n        self.notebook.add(settings_frame, text=f\"{ICONS['settings']} Settings\")\n        \n        # Create tab instances\n        self.settings_tab = SettingsTab(settings_frame, self.theme)\n        self.main_tab = MainTab(main_frame, self.theme, self.settings_tab)\n        \n        # Status bar\n        self.status_bar = ttk.Label(\n            self.root,\n            text=\"Ready\",\n            style='Status.TLabel',\n            relief='sunken',\n            anchor='w'\n        )\n        self.status_bar.pack(side='bottom', fill='x')\n        \n        # Add tooltips to tabs\n        add_tooltip(main_frame, \"Main processing interface\")\n        add_tooltip(settings_frame, \"Configure detection and processing settings\")\n    \n    def _setup_keyboard_shortcuts(self):\n        \"\"\"Set up keyboard shortcuts for accessibility.\"\"\"\n        # Ctrl+O: Browse for folder\n        self.root.bind('<Control-o>', lambda e: self.main_tab._browse_folder())\n        \n        # F5: Start processing\n        self.root.bind('<F5>', lambda e: self.main_tab._start_processing())\n        \n        # F1: Show help\n        self.root.bind('<F1>', lambda e: self.main_tab._show_help())\n        \n        # Ctrl+L: View logs\n        self.root.bind('<Control-l>', lambda e: self.main_tab._view_logs())\n        \n        # Ctrl+E: Export ZIP\n        self.root.bind('<Control-e>', lambda e: self.main_tab._export_zip())\n    \n    def _on_closing(self):\n        \"\"\"Handle application closing.\"\"\"\n        # Cancel any ongoing processing\n        if hasattr(self.main_tab, 'processor') and self.main_tab.processor:\n            self.main_tab.processor.cancel_processing()\n        \n        # Close progress dialog if open\n        if hasattr(self.main_tab, 'progress_dialog') and self.main_tab.progress_dialog:\n            self.main_tab.progress_dialog.close()\n        \n        self.logger.log_info(\"Picture Finder GUI closing\")\n        self.root.destroy()\n\n\n# Legacy compatibility function\ndef create_gui(root: tk.Tk) -> PictureFinderGUI:\n    \"\"\"\n    Create the Picture Finder GUI (legacy compatibility function).\n    \n    Args:\n        root: Root Tkinter window\n        \n    Returns:\n        PictureFinderGUI instance\n    \"\"\"\n    return PictureFinderGUI(root)