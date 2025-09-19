"""
Enhanced GUI interface for Picture Finder with responsive design, accessibility,
internationalization support, and comprehensive user experience features.
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import asyncio
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
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            variable=self.progress_var,
            maximum=100,
            length=350
        )
        self.progress_bar.pack(pady=20, padx=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(
            self.dialog,
            textvariable=self.status_var,
            font=('Helvetica', 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Cancel button
        self.cancel_button = ttk.Button(
            self.dialog,
            text="Cancel",
            command=self._on_cancel
        )
        self.cancel_button.pack(pady=(0, 20))
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        if self.cancelled:
            return
            
        if total > 0:
            percentage = (current / total) * 100
            self.progress_var.set(percentage)
            status_msg = f"{message} ({current}/{total})"
        else:
            status_msg = message
        
        self.status_var.set(status_msg)
        self.dialog.update_idletasks()
    
    def set_cancel_callback(self, callback: Callable):
        """Set callback for cancel button."""
        self.cancel_callback = callback
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        if self.cancel_callback:
            self.cancel_callback()
        self.close()
    
    def close(self):
        """Close the dialog."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()


class SettingsTab:
    """Settings tab with advanced configuration options."""
    
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
        self.use_async = tk.BooleanVar(value=True)  # Enable async by default
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create settings tab widgets."""
        # Main scrollable frame
        canvas = tk.Canvas(self.frame, bg=self.theme.get_color('primary_bg'))
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='PF.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header_label = ttk.Label(
            scrollable_frame,
            text=f"{ICONS['settings']} Advanced Settings",
            style='Header.TLabel',
            font=('Helvetica', 14, 'bold')
        )
        header_label.pack(pady=(20, 15))
        
        # Detection Settings Section
        detection_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['image']} Detection Settings",
            style='Card.TFrame'
        )
        detection_frame.pack(fill='x', padx=10, pady=5)
        
        # Similarity threshold
        ttk.Label(
            detection_frame,
            text=f"Similarity Threshold: {self.similarity_threshold.get()}",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        ttk.Label(
            detection_frame,
            text="Lower = stricter (1-20, default: 10)",
            style='Status.TLabel'
        ).pack(anchor='w', padx=10)
        
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
            "Lower values = stricter duplicate detection. "
            "Higher values = more lenient (may include similar but different photos)."
        )
        
        # Hash algorithm selection
        ttk.Label(
            detection_frame,
            text="Hash Algorithm:",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(0, 5))
        
        hash_combo = ttk.Combobox(
            detection_frame,
            textvariable=self.hash_algorithm,
            values=['average', 'perceptual', 'difference', 'wavelet'],
            state='readonly',
            width=30
        )
        hash_combo.pack(anchor='w', padx=10, pady=(0, 10))
        
        add_tooltip(
            hash_combo,
            "Algorithm for generating image fingerprints. "
            "Average: Fast, good for most cases. "
            "Perceptual: Better for rotated/scaled images. "
            "Difference: Good for cropped images. "
            "Wavelet: Best accuracy but slower."
        )
        
        # Performance Settings Section
        performance_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['cpu']} Performance Settings",
            style='Card.TFrame'
        )
        performance_frame.pack(fill='x', padx=10, pady=5)
        
        # Batch size
        ttk.Label(
            performance_frame,
            text=f"Batch Size: {self.chunk_size.get()}",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        ttk.Label(
            performance_frame,
            text="Files processed per batch (100-2000)",
            style='Status.TLabel'
        ).pack(anchor='w', padx=10)
        
        self.chunk_scale = ttk.Scale(
            performance_frame,
            from_=100, to=2000,
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
        )
        
        # Scan Options Section
        scan_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['folder']} Scan Options",
            style='Card.TFrame'
        )
        scan_frame.pack(fill='x', padx=10, pady=5)
        
        # Recursive scanning
        ttk.Checkbutton(
            scan_frame,
            text="Scan subfolders recursively",
            variable=self.recursive_scan,
            style='PF.TCheckbutton'
        ).pack(anchor='w', padx=10, pady=5)
        
        # Export Settings Section
        export_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['zip']} Export Settings",
            style='Card.TFrame'
        )
        export_frame.pack(fill='x', padx=10, pady=5)
        
        # Auto export checkbox
        ttk.Checkbutton(
            export_frame,
            text="Automatically export unique photos to ZIP",
            variable=self.auto_export,
            style='PF.TCheckbutton'
        ).pack(anchor='w', padx=10, pady=5)
        
        # Compression level
        ttk.Label(
            export_frame,
            text=f"Compression Level: {self.compression_level.get()}",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(5, 0))
        
        ttk.Label(
            export_frame,
            text="0 = No compression, 9 = Maximum compression",
            style='Status.TLabel'
        ).pack(anchor='w', padx=10)
        
        self.compression_scale = ttk.Scale(
            export_frame,
            from_=0, to=9,
            orient='horizontal',
            variable=self.compression_level,
            style='PF.TScale',
            command=self._on_compression_change
        )
        self.compression_scale.pack(fill='x', padx=10, pady=(0, 10))
        
        # Language Settings Section
        lang_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['settings']} Language Settings",
            style='Card.TFrame'
        )
        lang_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(
            lang_frame,
            text="Language:",
            style='PF.TLabel'
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language,
            values=['en', 'es', 'fr'],
            state='readonly',
            width=20
        )
        language_combo.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Performance Settings Section
        perf_frame = ttk.LabelFrame(
            scrollable_frame,
            text=f"{ICONS['settings']} Performance Settings",
            style='Card.TFrame'
        )
        perf_frame.pack(fill='x', padx=10, pady=5)
        
        # Async processing checkbox
        async_check = ttk.Checkbutton(
            perf_frame,
            text="Enable Async Processing (Recommended)",
            variable=self.use_async,
            style='PF.TCheckbutton'
        )
        async_check.pack(anchor='w', padx=10, pady=10)
        
        ttk.Label(
            perf_frame,
            text="Async processing provides better performance and responsiveness",
            style='Status.TLabel'
        ).pack(anchor='w', padx=10, pady=(0, 10))
        
        # Reset Settings Button
        reset_button = create_icon_button(
            scrollable_frame,
            "Reset to Defaults",
            command=self._reset_settings,
            icon_char=ICONS['refresh'],
            style='Secondary.TButton'
        )
        reset_button.pack(pady=10)
        
        add_tooltip(reset_button, "Reset all settings to their default values")
    
    def _on_threshold_change(self, value):
        """Handle similarity threshold change."""
        val = int(float(value))
        self.similarity_threshold.set(val)
        
        # Update label in parent
        parent = self.threshold_scale.master
        for child in parent.winfo_children():
            if isinstance(child, ttk.Label) and "Similarity Threshold" in str(child.cget('text')):
                child.configure(text=f"Similarity Threshold: {val}")
                break
    
    def _on_chunk_change(self, value):
        """Handle chunk size change."""
        val = int(float(value))
        self.chunk_size.set(val)
        
        # Update label
        parent = self.chunk_scale.master
        for child in parent.winfo_children():
            if isinstance(child, ttk.Label) and "Batch Size" in str(child.cget('text')):
                child.configure(text=f"Batch Size: {val}")
                break
    
    def _on_compression_change(self, value):
        """Handle compression level change."""
        val = int(float(value))
        self.compression_level.set(val)
        
        # Update label
        parent = self.compression_scale.master
        for child in parent.winfo_children():
            if isinstance(child, ttk.Label) and "Compression Level" in str(child.cget('text')):
                child.configure(text=f"Compression Level: {val}")
                break
    
    def _reset_settings(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            self.similarity_threshold.set(10)
            self.chunk_size.set(500)
            self.hash_algorithm.set('average')
            self.language.set('en')
            self.recursive_scan.set(False)
            self.auto_export.set(False)
            self.compression_level.set(6)
            self.use_async.set(True)  # Reset async to enabled
            
            # Update scale labels
            self._on_threshold_change(10)
            self._on_chunk_change(500)
            self._on_compression_change(6)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            'similarity_threshold': self.similarity_threshold.get(),
            'chunk_size': self.chunk_size.get(),
            'hash_algorithm': self.hash_algorithm.get(),
            'language': self.language.get(),
            'recursive_scan': self.recursive_scan.get(),
            'auto_export': self.auto_export.get(),
            'compression_level': self.compression_level.get(),
            'use_async': self.use_async.get()
        }


class MainTab:
    """Main tab with folder selection and processing controls."""
    
    def __init__(self, parent_frame, theme: PictureFinderTheme, settings_tab: SettingsTab):
        """
        Initialize main tab.
        
        Args:
            parent_frame: Parent notebook frame
            theme: Theme manager
            settings_tab: Settings tab reference
        """
        self.frame = parent_frame
        self.theme = theme
        self.settings_tab = settings_tab
        self.logger = get_logger()
        
        # State variables
        self.folder_path = tk.StringVar()
        self.operation_mode = tk.StringVar(value='copy')
        self.performance_mode = tk.StringVar(value='high')
        self.status_text = tk.StringVar(value="Ready to process photos")
        
        # Processing state
        self.processor: Optional[ImageProcessor] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.progress_dialog: Optional[ProgressDialog] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create main tab widgets."""
        # Main container with padding
        main_container = ttk.Frame(self.frame, style='PF.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_container, style='Header.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_label = ttk.Label(
            header_frame,
            text=f"{ICONS['image']} Picture Finder",
            style='Header.TLabel',
            font=('Helvetica', 16, 'bold')
        )
        header_label.pack(pady=10)
        
        # Folder selection section
        folder_frame = ttk.LabelFrame(
            main_container,
            text=f"{ICONS['folder']} Select Photo Folder",
            style='Card.TFrame'
        )
        folder_frame.pack(fill='x', pady=(0, 15))
        
        # Folder path entry and browse button
        folder_input_frame = ttk.Frame(folder_frame, style='PF.TFrame')
        folder_input_frame.pack(fill='x', padx=10, pady=10)
        
        self.folder_entry = ttk.Entry(
            folder_input_frame,
            textvariable=self.folder_path,
            font=('Helvetica', 10),
            style='PF.TEntry'
        )
        self.folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        browse_button = create_icon_button(
            folder_input_frame,
            "Browse",
            command=self._browse_folder,
            icon_char=ICONS['folder'],
            style='PF.TButton'
        )
        browse_button.pack(side='right')
        
        add_tooltip(self.folder_entry, "Path to the folder containing your photos")
        add_tooltip(browse_button, "Select folder to scan for duplicate photos")
        
        # Operation mode section
        mode_frame = ttk.LabelFrame(
            main_container,
            text=f"{ICONS['settings']} Processing Options",
            style='Card.TFrame'
        )
        mode_frame.pack(fill='x', pady=(0, 15))
        
        # Operation mode (copy/move)
        operation_frame = ttk.Frame(mode_frame, style='PF.TFrame')
        operation_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(
            operation_frame,
            text="Action for unique photos:",
            style='PF.TLabel',
            font=('Helvetica', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        # Radio buttons for copy/move
        radio_frame = ttk.Frame(operation_frame, style='PF.TFrame')
        radio_frame.pack(fill='x')
        
        copy_radio = ttk.Radiobutton(
            radio_frame,
            text=f"{ICONS['copy']} Copy (Keep originals)",
            variable=self.operation_mode,
            value='copy',
            style='PF.TRadiobutton'
        )
        copy_radio.pack(anchor='w', pady=2)
        
        move_radio = ttk.Radiobutton(
            radio_frame,
            text=f"{ICONS['move']} Move (Remove originals)",
            variable=self.operation_mode,
            value='move',
            style='PF.TRadiobutton'
        )
        move_radio.pack(anchor='w', pady=2)
        
        add_tooltip(copy_radio, "Copy unique photos to 'unique_photos' folder (original files remain)")
        add_tooltip(move_radio, "Move unique photos to 'unique_photos' folder (original files are moved)")
        
        # Performance mode selection
        perf_frame = ttk.Frame(mode_frame, style='PF.TFrame')
        perf_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(
            perf_frame,
            text="Performance Mode:",
            style='PF.TLabel',
            font=('Helvetica', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        perf_combo = ttk.Combobox(
            perf_frame,
            textvariable=self.performance_mode,
            values=['low', 'medium', 'high'],
            state='readonly',
            width=30
        )
        perf_combo.pack(anchor='w')
        
        # Set combobox display values
        perf_combo.configure(values=[
            'Low (1 core, minimal RAM)',
            'Medium (2 cores, moderate RAM)',
            'High (4 cores, high RAM)'
        ])
        perf_combo.set('High (4 cores, high RAM)')
        
        add_tooltip(
            perf_combo,
            "Choose performance mode based on your computer's capabilities. "
            "Higher modes are faster but use more system resources."
        )
        
        # Action buttons section
        action_frame = ttk.Frame(main_container, style='PF.TFrame')
        action_frame.pack(fill='x', pady=(0, 15))
        
        # Main action buttons
        button_frame = ttk.Frame(action_frame, style='PF.TFrame')
        button_frame.pack()
        
        self.run_button = create_icon_button(
            button_frame,
            "Start Processing",
            command=self._start_processing,
            icon_char=ICONS['play'],
            style='Success.TButton'
        )
        self.run_button.pack(side='left', padx=(0, 10))
        
        self.export_button = create_icon_button(
            button_frame,
            "Export ZIP",
            command=self._export_zip,
            icon_char=ICONS['zip'],
            style='PF.TButton'
        )
        self.export_button.pack(side='left', padx=(0, 10))
        self.export_button.configure(state='disabled')
        
        self.view_logs_button = create_icon_button(
            button_frame,
            "View Logs",
            command=self._view_logs,
            icon_char=ICONS['file'],
            style='Secondary.TButton'
        )
        self.view_logs_button.pack(side='left')
        
        add_tooltip(self.run_button, "Start scanning for duplicate photos")
        add_tooltip(self.export_button, "Export unique photos to a ZIP file")
        add_tooltip(self.view_logs_button, "Open the log file to see processing details")
        
        # Progress section
        progress_frame = ttk.LabelFrame(
            main_container,
            text=f"{ICONS['info']} Status",
            style='Card.TFrame'
        )
        progress_frame.pack(fill='x', pady=(0, 15))
        
        # Status label
        self.status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_text,
            style='Status.TLabel',
            font=('Helvetica', 10)
        )
        self.status_label.pack(padx=10, pady=10)
        
        # Quick stats display
        stats_frame = ttk.Frame(progress_frame, style='PF.TFrame')
        stats_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.stats_text = tk.Text(
            stats_frame,
            height=4,
            width=50,
            wrap='word',
            background=self.theme.get_color('secondary_bg'),
            foreground=self.theme.get_color('text_dark'),
            font=('Courier', 9),
            state='disabled'
        )
        self.stats_text.pack(fill='x')
        
        # Help section
        help_frame = ttk.Frame(main_container, style='PF.TFrame')
        help_frame.pack(fill='x')
        
        help_button = create_icon_button(
            help_frame,
            "Help & Documentation",
            command=self._show_help,
            icon_char=ICONS['info'],
            style='Secondary.TButton'
        )
        help_button.pack()
        
        add_tooltip(help_button, "Open help documentation and user guide")
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(
            title="Select folder containing photos",
            initialdir=self.folder_path.get() or os.path.expanduser("~")
        )
        
        if folder:
            self.folder_path.set(folder)
            self.status_text.set(f"Selected: {folder}")
            self.logger.log_info(f"User selected folder: {folder}")
    
    def _start_processing(self):
        """Start the photo processing in a separate thread."""
        folder = self.folder_path.get().strip()
        
        if not folder:
            messagebox.showerror("Error", "Please select a folder first!")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("Error", "Selected folder does not exist!")
            return
        
        # Get settings
        settings = self.settings_tab.get_settings()
        
        # Extract performance mode
        perf_mode_text = self.performance_mode.get()
        if 'Low' in perf_mode_text:
            perf_mode = 'low'
        elif 'Medium' in perf_mode_text:
            perf_mode = 'medium'
        else:
            perf_mode = 'high'
        
        # Confirm action
        mode_text = "copy" if self.operation_mode.get() == 'copy' else "move"
        message = (
            f"Start processing photos in:\n{folder}\n\n"
            f"Action: {mode_text.title()} unique photos\n"
            f"Performance: {perf_mode.title()}\n"
            f"Recursive: {'Yes' if settings['recursive_scan'] else 'No'}\n\n"
            "Continue?"
        )
        
        if not messagebox.askyesno("Confirm Processing", message):
            return
        
        # Disable buttons during processing
        self.run_button.configure(state='disabled')
        self.export_button.configure(state='disabled')
        
        # Create processor
        self.processor = ImageProcessor(
            output_dir=os.getcwd(),
            performance_mode=perf_mode,
            hash_algorithm=settings['hash_algorithm'],
            similarity_threshold=settings['similarity_threshold']
        )
        
        # Show progress dialog
        self.progress_dialog = ProgressDialog(self.frame.winfo_toplevel(), "Processing Photos")
        self.progress_dialog.set_cancel_callback(self._cancel_processing)
        
        # Set up progress callback
        self.processor.set_progress_callback(self._update_progress)
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_photos,
            args=(folder, settings),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_photos(self, folder: str, settings: Dict[str, Any]):
        """Process photos in background thread with async support."""
        try:
            self.status_text.set("Processing photos...")

            # Check if async processing is available and enabled
            use_async = hasattr(self.processor, 'async_process_folder') and settings.get('use_async', True)

            if use_async:
                # Use asyncio for non-blocking processing
                asyncio.run(self._async_process_photos(folder, settings))
            else:
                # Fallback to synchronous processing
                results = self.processor.process_folder(
                    folder_path=folder,
                    mode=self.operation_mode.get(),
                    chunk_size=settings['chunk_size'],
                    recursive=settings['recursive_scan'],
                    export_zip=settings['auto_export']
                )
                # Update UI on main thread
                self.frame.after(0, self._processing_completed, results)

        except Exception as e:
            self.logger.log_error(f"Processing failed: {str(e)}")
            self.frame.after(0, self._processing_failed, str(e))

    async def _async_process_photos(self, folder: str, settings: Dict[str, Any]):
        """Async version of photo processing."""
        try:
            # Process folder asynchronously
            results = await self.processor.async_process_folder(
                folder_path=folder,
                mode=self.operation_mode.get(),
                chunk_size=settings['chunk_size'],
                recursive=settings['recursive_scan'],
                export_zip=settings['auto_export']
            )

            # Update UI on main thread
            self.frame.after(0, self._processing_completed, results)

        except Exception as e:
            self.logger.log_error(f"Async processing failed: {str(e)}")
            self.frame.after(0, self._processing_failed, str(e))
    
    def _update_progress(self, current: int, total: int, message: str):
        """Update progress dialog from processing thread."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, message)
    
    def _processing_completed(self, results: Dict[str, Any]):
        """Handle processing completion on main thread."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Update statistics display
        stats_text = (
            f"Processing completed in {results['processing_time']:.1f} seconds\n"
            f"Files scanned: {results['detection_stats']['total_files']:,}\n"
            f"Duplicate groups: {results['duplicate_groups']:,}\n"
            f"Total duplicates: {results['total_duplicates']:,}\n"
            f"Unique files processed: {results['unique_files_processed']:,}\n"
            f"Videos separated: {results['detection_stats']['videos_separated']:,}"
        )
        
        self._update_stats_display(stats_text)
        
        # Enable export button if unique photos were processed
        if results['unique_files_processed'] > 0:
            self.export_button.configure(state='normal')
        
        # Show completion message
        message = (
            f"Processing completed successfully!\n\n"
            f"• {results['total_duplicates']:,} duplicates found\n"
            f"• {results['unique_files_processed']:,} unique photos processed\n"
            f"• {results['detection_stats']['videos_separated']:,} videos separated\n\n"
            "Check the output folders for results."
        )
        
        if results.get('zip_export_path'):
            message += f"\n\nZIP export: {results['zip_export_path']}"
        
        messagebox.showinfo("Processing Complete", message)
        
        # Re-enable buttons
        self.run_button.configure(state='normal')
        
        self.status_text.set("Processing completed successfully")
        self.logger.log_info("Processing completed successfully")
    
    def _processing_failed(self, error_msg: str):
        """Handle processing failure on main thread."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Re-enable buttons
        self.run_button.configure(state='normal')
        
        self.status_text.set(f"Processing failed: {error_msg}")
        
        messagebox.showerror(
            "Processing Failed",
            f"An error occurred during processing:\n\n{error_msg}\n\nCheck the log file for details."
        )
    
    def _cancel_processing(self):
        """Cancel current processing operation."""
        if self.processor:
            self.processor.cancel_processing()
        
        self.status_text.set("Processing cancelled")
        self.run_button.configure(state='normal')
    
    def _export_zip(self):
        """Export unique photos to ZIP file."""
        unique_folder = Path("unique_photos")
        
        if not unique_folder.exists() or not any(unique_folder.iterdir()):
            messagebox.showwarning(
                "No Files to Export",
                "No unique photos found to export. Process photos first."
            )
            return
        
        # Ask for ZIP file location
        zip_path = filedialog.asksaveasfilename(
            title="Save ZIP file as",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not zip_path:
            return
        
        # Get compression settings
        settings = self.settings_tab.get_settings()
        
        try:
            from core.file_manager import FileManager
            file_manager = FileManager()
            
            result = file_manager.export_to_zip(
                str(unique_folder),
                zip_path,
                compression_level=settings['compression_level']
            )
            
            if result:
                messagebox.showinfo(
                    "Export Complete",
                    f"Unique photos exported to:\n{zip_path}"
                )
                self.logger.log_info(f"ZIP export completed: {zip_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to create ZIP file.")
                
        except Exception as e:
            self.logger.log_error(f"ZIP export failed: {str(e)}")
            messagebox.showerror("Export Failed", f"Error creating ZIP file:\n{str(e)}")
    
    def _view_logs(self):
        """Open the log file."""
        try:
            log_path = self.logger.get_log_file_path()
            
            if os.path.exists(log_path):
                # Try to open with default application
                if os.name == 'nt':  # Windows
                    os.startfile(log_path)
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'open "{log_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{log_path}"')
            else:
                messagebox.showwarning("No Log File", "No log file found. Start processing to generate logs.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file:\n{str(e)}")
    
    def _show_help(self):
        """Show help documentation."""
        help_text = """
Picture Finder - Help

1. SELECT FOLDER: Choose the folder containing your photos

2. CHOOSE ACTION:
   • Copy: Keep original files, copy unique photos to 'unique_photos' folder
   • Move: Move unique photos to 'unique_photos' folder (originals are removed)

3. PERFORMANCE MODE:
   • Low: Uses 1 CPU core and minimal RAM (slower, but system-friendly)
   • Medium: Uses 2 CPU cores and moderate RAM (balanced)
   • High: Uses 4 CPU cores and high RAM (fastest, but resource-intensive)

4. SETTINGS TAB:
   • Similarity Threshold: How similar images must be (1=strict, 20=lenient)
   • Batch Size: Number of files processed at once
   • Hash Algorithm: Method for detecting duplicates
   • Recursive Scan: Include subfolders

5. OUTPUT:
   • Duplicates are moved to 'duplicates' folder
   • Unique photos go to 'unique_photos' folder
   • Videos are moved to 'videos' folder
   • Detailed logs are created for each run

Tips:
• Start with default settings for most use cases
• Use lower similarity threshold for stricter duplicate detection
• Enable recursive scan to process subfolders
• Check logs for detailed processing information
        """
        
        # Create help window
        help_window = tk.Toplevel(self.frame.winfo_toplevel())
        help_window.title("Picture Finder - Help")
        help_window.geometry("600x500")
        help_window.transient(self.frame.winfo_toplevel())
        
        # Help text widget with scrollbar
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        text_widget = tk.Text(
            text_frame,
            wrap='word',
            font=('Helvetica', 10),
            background='white',
            foreground='black'
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert('1.0', help_text)
        text_widget.configure(state='disabled')
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Close button
        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy
        )
        close_button.pack(pady=(0, 20))
    
    def _update_stats_display(self, stats_text: str):
        """Update the statistics display."""
        self.stats_text.configure(state='normal')
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats_text)
        self.stats_text.configure(state='disabled')


class PictureFinderGUI:
    """Main GUI application class."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the Picture Finder GUI.
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.logger = get_logger()
        
        self._setup_window()
        self.theme = PictureFinderTheme(root)
        self.theme.apply_theme()
        
        self._create_gui()
        
        # Keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        self.logger.log_info("Picture Finder GUI initialized")
    
    def _setup_window(self):
        """Configure the main window."""
        self.root.title("Picture Finder - Duplicate Photo Detection")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # Set icon if available
        try:
            icon_path = Path("assets/icon.ico")
            if icon_path.exists():
                if os.name == 'nt':  # Windows
                    self.root.iconbitmap(str(icon_path))
                else:  # macOS/Linux
                    # For cross-platform compatibility
                    pass
        except Exception:
            pass  # Icon not critical
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_gui(self):
        """Create the main GUI components."""
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root, style='PF.TNotebook')
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Main tab frame
        main_frame = ttk.Frame(self.notebook, style='PF.TFrame')
        self.notebook.add(main_frame, text=f"{ICONS['image']} Main")
        
        # Settings tab frame
        settings_frame = ttk.Frame(self.notebook, style='PF.TFrame')
        self.notebook.add(settings_frame, text=f"{ICONS['settings']} Settings")
        
        # Create tab instances
        self.settings_tab = SettingsTab(settings_frame, self.theme)
        self.main_tab = MainTab(main_frame, self.theme, self.settings_tab)
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            style='Status.TLabel',
            relief='sunken',
            anchor='w'
        )
        self.status_bar.pack(side='bottom', fill='x')
        
        # Add tooltips to tabs
        add_tooltip(main_frame, "Main processing interface")
        add_tooltip(settings_frame, "Configure detection and processing settings")
    
    def _setup_keyboard_shortcuts(self):
        """Set up enhanced keyboard shortcuts for accessibility."""
        # File operations
        self.root.bind('<Control-o>', lambda e: self.main_tab._browse_folder())
        self.root.bind('<Control-s>', lambda e: self._save_settings())
        self.root.bind('<Control-e>', lambda e: self.main_tab._export_zip())
        
        # Processing controls
        self.root.bind('<F5>', lambda e: self.main_tab._start_processing())
        self.root.bind('<Escape>', lambda e: self._cancel_processing())
        
        # Navigation and help
        self.root.bind('<F1>', lambda e: self.main_tab._show_help())
        self.root.bind('<Control-h>', lambda e: self._show_accessibility_help())
        self.root.bind('<Control-l>', lambda e: self.main_tab._view_logs())
        
        # Tab navigation
        self.root.bind('<Control-Tab>', lambda e: self._next_tab())
        self.root.bind('<Control-Shift-Tab>', lambda e: self._previous_tab())
        
        # Accessibility toggles
        self.root.bind('<Control-Alt-h>', lambda e: self._toggle_high_contrast())
        self.root.bind('<Control-Alt-t>', lambda e: self._toggle_tooltips())
        
        # Quick actions
        self.root.bind('<Control-r>', lambda e: self._refresh_folder())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
    
    def _save_settings(self):
        """Save current settings."""
        if hasattr(self, 'settings_tab'):
            self.settings_tab._save_settings()
    
    def _cancel_processing(self):
        """Cancel current processing."""
        if hasattr(self.main_tab, 'processor') and self.main_tab.processor:
            self.main_tab.processor.cancel_processing()
    
    def _show_accessibility_help(self):
        """Show accessibility help dialog."""
        help_text = """
Accessibility Keyboard Shortcuts:

File Operations:
• Ctrl+O: Browse for folder
• Ctrl+S: Save settings
• Ctrl+E: Export results to ZIP

Processing:
• F5: Start processing
• Escape: Cancel processing

Navigation:
• F1: Show help
• Ctrl+H: Show this accessibility help
• Ctrl+L: View logs
• Ctrl+Tab: Next tab
• Ctrl+Shift+Tab: Previous tab

Accessibility:
• Ctrl+Alt+H: Toggle high contrast mode
• Ctrl+Alt+T: Toggle enhanced tooltips

Quick Actions:
• Ctrl+R: Refresh folder
• Ctrl+Q: Quit application

All buttons and controls are keyboard accessible using Tab/Shift+Tab navigation.
"""
        messagebox.showinfo("Accessibility Help", help_text)
    
    def _next_tab(self):
        """Navigate to next tab."""
        if hasattr(self, 'notebook'):
            current = self.notebook.index('current')
            total = self.notebook.index('end')
            next_tab = (current + 1) % total
            self.notebook.select(next_tab)
    
    def _previous_tab(self):
        """Navigate to previous tab."""
        if hasattr(self, 'notebook'):
            current = self.notebook.index('current')
            total = self.notebook.index('end')
            prev_tab = (current - 1) % total
            self.notebook.select(prev_tab)
    
    def _toggle_high_contrast(self):
        """Toggle high contrast mode."""
        if hasattr(self, 'theme'):
            self.theme.toggle_high_contrast()
    
    def _toggle_tooltips(self):
        """Toggle enhanced tooltips."""
        if hasattr(self, 'theme'):
            self.theme.toggle_enhanced_tooltips()
    
    def _refresh_folder(self):
        """Refresh current folder selection."""
        if hasattr(self.main_tab, '_browse_folder'):
            self.main_tab._browse_folder()
    
    def _on_closing(self):
        """Handle application closing."""
        # Cancel any ongoing processing
        if hasattr(self.main_tab, 'processor') and self.main_tab.processor:
            self.main_tab.processor.cancel_processing()
        
        # Close progress dialog if open
        if hasattr(self.main_tab, 'progress_dialog') and self.main_tab.progress_dialog:
            self.main_tab.progress_dialog.close()
        
        self.logger.log_info("Picture Finder GUI closing")
        self.root.destroy()


# Legacy compatibility function
def create_gui(root: tk.Tk) -> PictureFinderGUI:
    """
    Create the Picture Finder GUI (legacy compatibility function).
    
    Args:
        root: Root Tkinter window
        
    Returns:
        PictureFinderGUI instance
    """
    return PictureFinderGUI(root)