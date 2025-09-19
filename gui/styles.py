"""
Enhanced styling system for Picture Finder GUI with teal/white theme,
accessibility features, and polished visual design.
"""

from ttkthemes import ThemedStyle
import tkinter as tk
from tkinter import ttk


class PictureFinderTheme:
    """Custom theme manager for Picture Finder with teal/white color scheme."""
    
    # Color palette
    COLORS = {
        'primary_bg': '#ADD8E6',      # Light blue background
        'secondary_bg': '#E0F6FF',    # Very light blue
        'primary_accent': '#008080',   # Teal accent
        'secondary_accent': '#006666', # Darker teal
        'text_primary': '#FFFFFF',     # White text
        'text_secondary': '#008080',   # Teal text
        'text_dark': '#333333',        # Dark text
        'success': '#28A745',          # Green for success
        'warning': '#FFC107',          # Orange for warnings
        'error': '#DC3545',            # Red for errors
        'disabled': '#6C757D',         # Gray for disabled elements
        'border': '#B0B0B0',           # Light gray borders
        'hover': '#20B2AA'             # Light sea green for hover
    }
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the theme manager.
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.style = ThemedStyle(root)
        
        # Try to use a modern theme as base
        try:
            self.style.set_theme('equilux')
        except:
            try:
                self.style.set_theme('arc')
            except:
                pass  # Fall back to default
    
    def apply_theme(self):
        """Apply the complete Picture Finder theme."""
        self._configure_window()
        self._configure_frames()
        self._configure_buttons()
        self._configure_labels()
        self._configure_entries()
        self._configure_checkboxes_radios()
        self._configure_scales()
        self._configure_progressbars()
        self._configure_notebooks()
        self._configure_treeviews()
        self._configure_scrollbars()
        self._configure_tooltips()
    
    def _configure_window(self):
        """Configure main window appearance."""
        self.root.configure(bg=self.COLORS['primary_bg'])
    
    def _configure_frames(self):
        """Configure frame styles."""
        # Main frame style
        self.style.configure(
            'PF.TFrame',
            background=self.COLORS['primary_bg'],
            borderwidth=0
        )
        
        # Card-like frames for sections
        self.style.configure(
            'Card.TFrame',
            background=self.COLORS['secondary_bg'],
            relief='raised',
            borderwidth=1
        )
        
        # Header frames
        self.style.configure(
            'Header.TFrame',
            background=self.COLORS['primary_accent'],
            borderwidth=0
        )
    
    def _configure_buttons(self):
        """Configure button styles with hover effects."""
        # Primary buttons
        self.style.configure(
            'PF.TButton',
            background=self.COLORS['primary_accent'],
            foreground=self.COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5),
            font=('Helvetica', 10, 'bold')
        )
        
        self.style.map(
            'PF.TButton',
            background=[
                ('active', self.COLORS['hover']),
                ('pressed', self.COLORS['secondary_accent']),
                ('disabled', self.COLORS['disabled'])
            ],
            foreground=[
                ('disabled', self.COLORS['text_primary'])
            ]
        )
        
        # Secondary buttons
        self.style.configure(
            'Secondary.TButton',
            background=self.COLORS['secondary_bg'],
            foreground=self.COLORS['text_secondary'],
            borderwidth=1,
            bordercolor=self.COLORS['primary_accent'],
            focuscolor='none',
            padding=(8, 4),
            font=('Helvetica', 9)
        )
        
        self.style.map(
            'Secondary.TButton',
            background=[
                ('active', self.COLORS['primary_bg']),
                ('pressed', self.COLORS['primary_accent'])
            ],
            foreground=[
                ('pressed', self.COLORS['text_primary'])
            ]
        )
        
        # Success button
        self.style.configure(
            'Success.TButton',
            background=self.COLORS['success'],
            foreground=self.COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5),
            font=('Helvetica', 10, 'bold')
        )
        
        # Warning button
        self.style.configure(
            'Warning.TButton',
            background=self.COLORS['warning'],
            foreground=self.COLORS['text_dark'],
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5),
            font=('Helvetica', 10, 'bold')
        )
        
        # Error button
        self.style.configure(
            'Error.TButton',
            background=self.COLORS['error'],
            foreground=self.COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5),
            font=('Helvetica', 10, 'bold')
        )
    
    def _configure_labels(self):
        """Configure label styles."""
        # Standard labels
        self.style.configure(
            'PF.TLabel',
            background=self.COLORS['primary_bg'],
            foreground=self.COLORS['text_secondary'],
            font=('Helvetica', 10)
        )
        
        # Header labels
        self.style.configure(
            'Header.TLabel',
            background=self.COLORS['primary_accent'],
            foreground=self.COLORS['text_primary'],
            font=('Helvetica', 12, 'bold'),
            padding=(10, 5)
        )
        
        # Status labels
        self.style.configure(
            'Status.TLabel',
            background=self.COLORS['primary_bg'],
            foreground=self.COLORS['text_dark'],
            font=('Helvetica', 9),
            padding=(5, 2)
        )
        
        # Success/Error labels
        self.style.configure(
            'Success.TLabel',
            background=self.COLORS['success'],
            foreground=self.COLORS['text_primary'],
            font=('Helvetica', 9, 'bold'),
            padding=(5, 2)
        )
        
        self.style.configure(
            'Error.TLabel',
            background=self.COLORS['error'],
            foreground=self.COLORS['text_primary'],
            font=('Helvetica', 9, 'bold'),
            padding=(5, 2)
        )
    
    def _configure_entries(self):
        """Configure entry field styles."""
        self.style.configure(
            'PF.TEntry',
            fieldbackground=self.COLORS['secondary_bg'],
            foreground=self.COLORS['text_dark'],
            borderwidth=1,
            insertcolor=self.COLORS['primary_accent'],
            font=('Helvetica', 10)
        )
        
        self.style.map(
            'PF.TEntry',
            focuscolor=[('focus', self.COLORS['primary_accent'])],
            bordercolor=[('focus', self.COLORS['primary_accent'])]
        )
    
    def _configure_checkboxes_radios(self):
        """Configure checkbox and radio button styles."""
        # Checkboxes
        self.style.configure(
            'PF.TCheckbutton',
            background=self.COLORS['primary_bg'],
            foreground=self.COLORS['text_secondary'],
            focuscolor='none',
            font=('Helvetica', 10)
        )
        
        self.style.map(
            'PF.TCheckbutton',
            background=[('active', self.COLORS['primary_bg'])],
            indicatorcolor=[
                ('selected', self.COLORS['primary_accent']),
                ('!selected', self.COLORS['secondary_bg'])
            ]
        )
        
        # Radio buttons
        self.style.configure(
            'PF.TRadiobutton',
            background=self.COLORS['primary_bg'],
            foreground=self.COLORS['text_secondary'],
            focuscolor='none',
            font=('Helvetica', 10)
        )
        
        self.style.map(
            'PF.TRadiobutton',
            background=[('active', self.COLORS['primary_bg'])],
            indicatorcolor=[
                ('selected', self.COLORS['primary_accent']),
                ('!selected', self.COLORS['secondary_bg'])
            ]
        )
    
    def _configure_scales(self):
        """Configure slider/scale styles."""
        self.style.configure(
            'PF.TScale',
            background=self.COLORS['primary_bg'],
            troughcolor=self.COLORS['secondary_bg'],
            slidercolor=self.COLORS['primary_accent'],
            borderwidth=0,
            lightcolor=self.COLORS['hover'],
            darkcolor=self.COLORS['secondary_accent']
        )
        
        self.style.map(
            'PF.TScale',
            slidercolor=[
                ('active', self.COLORS['hover']),
                ('pressed', self.COLORS['secondary_accent'])
            ]
        )
    
    def _configure_progressbars(self):
        """Configure progress bar styles."""
        self.style.configure(
            'PF.TProgressbar',
            background=self.COLORS['primary_accent'],
            troughcolor=self.COLORS['secondary_bg'],
            borderwidth=1,
            lightcolor=self.COLORS['hover'],
            darkcolor=self.COLORS['secondary_accent']
        )
    
    def _configure_notebooks(self):
        """Configure notebook (tab) styles."""
        self.style.configure(
            'PF.TNotebook',
            background=self.COLORS['primary_bg'],
            borderwidth=0
        )
        
        self.style.configure(
            'PF.TNotebook.Tab',
            background=self.COLORS['secondary_bg'],
            foreground=self.COLORS['text_secondary'],
            padding=[20, 10],
            font=('Helvetica', 10, 'bold'),
            borderwidth=1
        )
        
        self.style.map(
            'PF.TNotebook.Tab',
            background=[
                ('selected', self.COLORS['primary_accent']),
                ('active', self.COLORS['hover'])
            ],
            foreground=[
                ('selected', self.COLORS['text_primary']),
                ('active', self.COLORS['text_primary'])
            ]
        )
    
    def _configure_treeviews(self):
        """Configure treeview (list) styles."""
        self.style.configure(
            'PF.Treeview',
            background=self.COLORS['secondary_bg'],
            foreground=self.COLORS['text_dark'],
            fieldbackground=self.COLORS['secondary_bg'],
            borderwidth=1,
            font=('Helvetica', 9)
        )
        
        self.style.configure(
            'PF.Treeview.Heading',
            background=self.COLORS['primary_accent'],
            foreground=self.COLORS['text_primary'],
            borderwidth=1,
            font=('Helvetica', 10, 'bold')
        )
        
        self.style.map(
            'PF.Treeview',
            background=[
                ('selected', self.COLORS['primary_accent'])
            ],
            foreground=[
                ('selected', self.COLORS['text_primary'])
            ]
        )
    
    def _configure_scrollbars(self):
        """Configure scrollbar styles."""
        self.style.configure(
            'PF.TScrollbar',
            background=self.COLORS['secondary_bg'],
            troughcolor=self.COLORS['primary_bg'],
            borderwidth=0,
            arrowcolor=self.COLORS['primary_accent'],
            darkcolor=self.COLORS['secondary_accent'],
            lightcolor=self.COLORS['hover']
        )
    
    def _configure_tooltips(self):
        """Configure tooltip styles."""
        # Note: Tooltips are typically handled separately as they're not standard ttk widgets
        pass
    
    def get_color(self, color_name: str) -> str:
        """Get color value by name."""
        return self.COLORS.get(color_name, '#000000')
    
    def create_separator(self, parent, orientation='horizontal'):
        """Create a styled separator."""
        separator = ttk.Separator(parent, orient=orientation)
        if orientation == 'horizontal':
            separator.configure(style='HSeparator.TSeparator')
        else:
            separator.configure(style='VSeparator.TSeparator')
        
        # Configure separator styles
        self.style.configure(
            'HSeparator.TSeparator',
            background=self.COLORS['border']
        )
        self.style.configure(
            'VSeparator.TSeparator',
            background=self.COLORS['border']
        )
        
        return separator


def apply_styles(style: ThemedStyle, root: tk.Tk = None) -> PictureFinderTheme:
    """
    Legacy function for backward compatibility.
    
    Args:
        style: TTK Style object (ignored in new implementation)
        root: Root window (optional)
        
    Returns:
        PictureFinderTheme instance
    """
    if root is None:
        # Try to get root from style
        try:
            root = style.master
        except:
            root = tk._default_root
    
    theme_manager = PictureFinderTheme(root)
    theme_manager.apply_theme()
    return theme_manager


class ToolTip:
    """Enhanced tooltip widget for accessibility."""
    
    def __init__(self, widget, text='', delay=500, wraplength=180):
        """
        Create a tooltip for a widget.
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
            delay: Delay before showing (ms)
            wraplength: Text wrap length
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.tooltip_window = None
        self.id = None
        
        # Bind events
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<ButtonPress>', self.on_leave)
    
    def on_enter(self, event=None):
        """Handle mouse enter event."""
        self.schedule_tooltip()
    
    def on_leave(self, event=None):
        """Handle mouse leave event."""
        self.cancel_tooltip()
        self.hide_tooltip()
    
    def schedule_tooltip(self):
        """Schedule tooltip to appear after delay."""
        self.cancel_tooltip()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def cancel_tooltip(self):
        """Cancel scheduled tooltip."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show_tooltip(self, event=None):
        """Show the tooltip."""
        if self.tooltip_window or not self.text:
            return
        
        # Get widget position
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Configure tooltip appearance
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify='left',
            background='#FFFFE0',
            foreground='#000000',
            relief='solid',
            borderwidth=1,
            font=('Helvetica', 9),
            wraplength=self.wraplength
        )
        label.pack(ipadx=5, ipady=3)
    
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def update_text(self, new_text: str):
        """Update tooltip text."""
        self.text = new_text


def add_tooltip(widget, text: str, **kwargs) -> ToolTip:
    """
    Convenience function to add tooltip to a widget.
    
    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
        **kwargs: Additional ToolTip arguments
        
    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, **kwargs)


# Accessibility helpers
def make_accessible(widget, label_text: str = None, description: str = None):
    """
    Add accessibility features to a widget.
    
    Args:
        widget: Widget to make accessible
        label_text: Accessible label
        description: Accessible description
    """
    # Set accessible name if provided
    if label_text:
        try:
            widget.configure(text=label_text)  # For labels, buttons, etc.
        except:
            pass  # Widget doesn't support text attribute
    
    # Add description as tooltip if provided
    if description:
        add_tooltip(widget, description)
    
    # Ensure widget is keyboard accessible
    try:
        widget.configure(takefocus=True)
    except:
        pass  # Widget doesn't support takefocus


def create_icon_button(parent, text: str, command=None, icon_char: str = None, 
                      style: str = 'PF.TButton', **kwargs):
    """
    Create a button with optional icon character.
    
    Args:
        parent: Parent widget
        text: Button text
        command: Button command
        icon_char: Unicode icon character
        style: Button style
        **kwargs: Additional button arguments
        
    Returns:
        Button widget
    """
    button_text = text
    if icon_char:
        button_text = f"{icon_char} {text}"
    
    button = ttk.Button(
        parent,
        text=button_text,
        command=command,
        style=style,
        **kwargs
    )
    
    return button


# Common icons (Unicode characters)
ICONS = {
    'folder': '📁',
    'file': '📄',
    'image': '🖼️',
    'video': '🎬',
    'copy': '📋',
    'move': '➡️',
    'zip': '📦',
    'settings': '⚙️',
    'play': '▶️',
    'pause': '⏸️',
    'stop': '⏹️',
    'cancel': '❌',
    'check': '✅',
    'warning': '⚠️',
    'error': '❌',
    'info': 'ℹ️',
    'search': '🔍',
    'refresh': '🔄',
    'trash': '🗑️',
    'duplicate': '👥',
    'unique': '⭐'
}