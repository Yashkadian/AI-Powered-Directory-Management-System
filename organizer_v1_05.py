import os
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from PIL import Image, ImageTk, ImageFile
import io
import time

# Enable loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        # Theme colors - Updated with more modern colors
        self.themes = {
            "light": {
                "primary": "#4361ee",  # Modern blue
                "secondary": "#4cc9f0",  # Light blue
                "accent": "#f72585",  # Pink
                "success": "#06d6a0",  # Green
                "warning": "#ffd166",  # Yellow
                "danger": "#ef476f",  # Red
                "background": "#f8f9fa",  # Light grey
                "card": "#ffffff",  # White
                "text": "#212529",  # Dark grey
                "text_secondary": "#6c757d",  # Medium grey
                "border": "#dee2e6",  # Light grey
                "hover": "#e9ecef"  # Light grey hover
            },
            "dark": {
                "primary": "#4cc9f0",  # Light blue
                "secondary": "#4361ee",  # Modern blue
                "accent": "#f72585",  # Pink
                "success": "#06d6a0",  # Green
                "warning": "#ffd166",  # Yellow
                "danger": "#ef476f",  # Red
                "background": "#212529",  # Dark grey
                "card": "#343a40",  # Medium grey
                "text": "#f8f9fa",  # Light grey
                "text_secondary": "#adb5bd",  # Medium grey
                "border": "#495057",  # Medium grey
                "hover": "#495057"  # Medium grey hover
            }
        }
        
        self.current_theme = "light"
        self.selected_file = None  # Initialize selected_file
        self.cancel_operation = False  # Flag for cancelling operations
        self.thumbnail_cache = {}  # Cache for thumbnails
        
        # File categories with extensions
        self.file_categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "Videos": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm"],
            "Audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma"],
            "Documents": [".pdf", ".doc", ".docx", ".rtf", ".tex"],
            "Spreadsheets": [".xls", ".xlsx", ".csv"],
            "Presentations": [".ppt", ".pptx"],
            "Text": [".txt", ".md", ".log"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".iso"],
            "Executables": [".exe", ".msi", ".app"],
            "OneNote": [".one", ".onetoc2"],
            "Others": []
        }
        
        # Current directory and files
        self.current_dir = os.path.expanduser("~")
        self.files = []
        self.filtered_files = []
        self.current_category = "All"
        self.current_sort = "Name (A-Z)"
        
        # Apply theme
        self.apply_theme()
        
        # Create UI
        self.create_ui()
        
        # Load initial directory
        self.load_directory(self.current_dir)

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        self.root.configure(bg=theme["background"])
        
        # Create styles for ttk widgets
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure styles for different widgets
        style.configure("TFrame", background=theme["background"])
        
        style.configure("TButton", 
                        background=theme["primary"], 
                        foreground=theme["text"],
                        borderwidth=0)
        style.map("TButton",
                 background=[("active", theme["primary"])])
        
        style.configure("Secondary.TButton", 
                        background=theme["secondary"], 
                        foreground=theme["text"])
        style.map("Secondary.TButton",
                 background=[("active", theme["secondary"])])
        
        style.configure("Success.TButton", 
                        background=theme["success"], 
                        foreground=theme["text"])
        style.map("Success.TButton",
                 background=[("active", theme["success"])])
        
        style.configure("Danger.TButton", 
                        background=theme["danger"], 
                        foreground=theme["text"])
        style.map("Danger.TButton",
                 background=[("active", theme["danger"])])
        
        style.configure("TLabel", 
                        background=theme["background"], 
                        foreground=theme["text"])
        
        style.configure("Category.TLabel", 
                        background=theme["background"], 
                        foreground=theme["text"],
                        font=("Segoe UI", 11))
        
        style.configure("Title.TLabel", 
                        background=theme["background"], 
                        foreground=theme["text"],
                        font=("Segoe UI", 14, "bold"))
        
        style.configure("Path.TLabel", 
                        background=theme["background"], 
                        foreground=theme["primary"],
                        font=("Segoe UI", 10))
        
        style.configure("TCombobox", 
                        fieldbackground=theme["card"],
                        background=theme["primary"],
                        foreground=theme["text"])
        
        style.configure("Horizontal.TProgressbar", 
                        background=theme["primary"],
                        troughcolor=theme["background"])

    def create_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Top bar with path and controls
        self.top_bar = ttk.Frame(self.main_frame)
        self.top_bar.pack(fill=tk.X, pady=(0, 16))
        
        # Path navigation
        self.back_button = ttk.Button(self.top_bar, text="←", width=3, command=self.go_back)
        self.back_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.path_label = ttk.Label(self.top_bar, text=self.current_dir, style="Path.TLabel")
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))
        
        # Browse button
        self.browse_button = ttk.Button(self.top_bar, text="Browse", command=self.browse_directory)
        self.browse_button.pack(side=tk.LEFT, padx=(0, 16))
        
        # Theme toggle - Modern icon-only button
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_button = ttk.Button(self.top_bar, text=theme_icon, width=3, command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT)
        
        # Content area with sidebar and main content
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar with categories
        self.sidebar = ttk.Frame(self.content_frame, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        self.sidebar.pack_propagate(False)
        
        # Categories title
        ttk.Label(self.sidebar, text="Categories", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 16))
        
        # Add "All" category
        self.create_category_button("All", True)
        
        # Add file categories
        for category in self.file_categories:
            self.create_category_button(category)
        
        # Main content area
        self.content_area = ttk.Frame(self.content_frame)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Controls bar (sorting, organizing options)
        self.controls_bar = ttk.Frame(self.content_area)
        self.controls_bar.pack(fill=tk.X, pady=(0, 16))
        
        # Sort options
        ttk.Label(self.controls_bar, text="Sort by:").pack(side=tk.LEFT, padx=(0, 8))
        
        self.sort_options = ["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Size (Largest)", "Size (Smallest)"]
        self.sort_var = tk.StringVar(value=self.sort_options[0])
        self.sort_combo = ttk.Combobox(self.controls_bar, textvariable=self.sort_var, values=self.sort_options, state="readonly", width=15)
        self.sort_combo.pack(side=tk.LEFT, padx=(0, 16))
        self.sort_combo.bind("<<ComboboxSelected>>", self.on_sort_change)
        
        # Organize buttons
        self.organize_by_date_button = ttk.Button(self.controls_bar, text="Organize by Date", 
                                                 command=self.organize_by_date, style="Success.TButton")
        self.organize_by_date_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        self.organize_by_type_button = ttk.Button(self.controls_bar, text="Organize by Type", 
                                                 command=self.organize_by_type, style="Success.TButton")
        self.organize_by_type_button.pack(side=tk.RIGHT)
        
        # Files display area (scrollable)
        self.files_canvas = tk.Canvas(self.content_area, bg=self.themes[self.current_theme]["background"], 
                                     highlightthickness=0)
        self.files_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=self.files_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame for files inside canvas
        self.files_frame = ttk.Frame(self.files_canvas)
        self.files_canvas_window = self.files_canvas.create_window((0, 0), window=self.files_frame, anchor=tk.NW)
        
        # Configure canvas scrolling
        self.files_frame.bind("<Configure>", self.on_frame_configure)
        self.files_canvas.bind("<Configure>", self.on_canvas_configure)
        self.files_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Status bar
        self.status_bar = ttk.Frame(self.main_frame)
        self.status_bar.pack(fill=tk.X, pady=(16, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.file_count_label = ttk.Label(self.status_bar, text="0 items")
        self.file_count_label.pack(side=tk.RIGHT)
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open", command=lambda: self.open_file())
        self.context_menu.add_command(label="Details", command=self.show_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self.copy_file)
        self.context_menu.add_command(label="Move", command=self.move_file)
        self.context_menu.add_command(label="Delete", command=self.delete_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Locate in Explorer", command=self.locate_in_explorer)
        
        # Tooltip
        self.tooltip = tk.Label(self.root, text="", bg="#ffffcc", relief="solid", borderwidth=1)
        self.tooltip.place_forget()

    def create_category_button(self, category, is_all=False):
        theme = self.themes[self.current_theme]
        
        frame = ttk.Frame(self.sidebar)
        frame.pack(fill=tk.X, pady=4)
        
        # Use lambda to pass the category name to the click handler
        frame.bind("<Button-1>", lambda e, cat=category: self.select_category(cat))
        
        # Add category icon based on category name
        icon_text = "📁"  # Default folder icon
        if category == "Images":
            icon_text = "🖼️"
        elif category == "Videos":
            icon_text = "🎬"
        elif category == "Audio":
            icon_text = "🎵"
        elif category == "Documents":
            icon_text = "📝"
        elif category == "Spreadsheets":
            icon_text = "📊"
        elif category == "Presentations":
            icon_text = "📊"
        elif category == "Text":
            icon_text = "📄"
        elif category == "Archives":
            icon_text = "📦"
        elif category == "Executables":
            icon_text = "⚙️"
        elif category == "All":
            icon_text = "🏠"
        
        icon_label = tk.Label(frame, text=icon_text, bg=theme["background"], fg=theme["primary"])
        icon_label.pack(side=tk.LEFT, padx=(8, 4))
        icon_label.bind("<Button-1>", lambda e, cat=category: self.select_category(cat))
        
        label = ttk.Label(frame, text=category, style="Category.TLabel")
        label.pack(side=tk.LEFT, padx=(0, 8), pady=4)
        label.bind("<Button-1>", lambda e, cat=category: self.select_category(cat))
        
        # Store reference to highlight the selected category
        if is_all:
            self.selected_category_label = label
            self.selected_category_frame = frame

    def select_category(self, category):
        # Update selected category
        self.current_category = category
        
        # Filter files based on category
        self.filter_and_sort_files()
        
        # Update UI
        self.display_files()
        
        # Update status
        self.update_status(f"Category: {category}")

    def on_sort_change(self, event):
        # Get selected sort option
        self.current_sort = self.sort_var.get()
        
        # Re-sort files
        self.filter_and_sort_files()
        
        # Update UI
        self.display_files()
        
        # Update status
        self.update_status(f"Sorted by: {self.current_sort}")

    def filter_and_sort_files(self):
        # Filter files by category
        if self.current_category == "All":
            self.filtered_files = self.files.copy()
        else:
            extensions = self.file_categories.get(self.current_category, [])
            if extensions:  # If specific extensions are defined
                self.filtered_files = [f for f in self.files if os.path.splitext(f["name"])[1].lower() in extensions]
            else:  # For "Others" category or any without specific extensions
                all_extensions = []
                for exts in self.file_categories.values():
                    all_extensions.extend(exts)
                self.filtered_files = [f for f in self.files if os.path.splitext(f["name"])[1].lower() not in all_extensions]
        
        # Sort files
        if self.current_sort == "Name (A-Z)":
            self.filtered_files.sort(key=lambda x: x["name"].lower())
        elif self.current_sort == "Name (Z-A)":
            self.filtered_files.sort(key=lambda x: x["name"].lower(), reverse=True)
        elif self.current_sort == "Date (Newest)":
            self.filtered_files.sort(key=lambda x: x["modified"], reverse=True)
        elif self.current_sort == "Date (Oldest)":
            self.filtered_files.sort(key=lambda x: x["modified"])
        elif self.current_sort == "Size (Largest)":
            self.filtered_files.sort(key=lambda x: x["size"], reverse=True)
        elif self.current_sort == "Size (Smallest)":
            self.filtered_files.sort(key=lambda x: x["size"])

    def load_directory(self, directory):
        # Update current directory
        self.current_dir = directory
        self.path_label.config(text=directory)
        
        # Clear existing files
        self.files = []
        
        # Show loading status
        self.update_status("Loading files...")
        
        # Use threading to prevent UI freeze during loading
        threading.Thread(target=self._load_directory_thread, args=(directory,), daemon=True).start()

    def _load_directory_thread(self, directory):
        try:
            # Get all files in directory
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # Skip hidden files
                if item.startswith('.'):
                    continue
                
                # Get file info
                if os.path.isfile(item_path):
                    stats = os.stat(item_path)
                    file_info = {
                        "name": item,
                        "path": item_path,
                        "size": stats.st_size,
                        "created": stats.st_ctime,
                        "modified": stats.st_mtime,
                        "is_dir": False
                    }
                    self.files.append(file_info)
                else:  # Directory
                    stats = os.stat(item_path)
                    dir_info = {
                        "name": item,
                        "path": item_path,
                        "size": 0,  # Directories show as 0 size
                        "created": stats.st_ctime,
                        "modified": stats.st_mtime,
                        "is_dir": True
                    }
                    self.files.append(dir_info)
            
            # Filter and sort files
            self.filter_and_sort_files()
            
            # Update UI in main thread
            self.root.after(0, self.display_files)
            self.root.after(0, lambda: self.update_status(f"Loaded {len(self.files)} items"))
            self.root.after(0, lambda: self.file_count_label.config(text=f"{len(self.filtered_files)} items"))
            
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}"))

    def display_files(self):
        # Clear existing files display
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        
        # Calculate grid layout based on canvas width
        canvas_width = self.files_canvas.winfo_width()
        tile_width = 120
        padding = 16
        cols = max(1, (canvas_width - padding) // (tile_width + padding))
        
        theme = self.themes[self.current_theme]
        
        # Check if directory is empty
        if not self.filtered_files:
            # Create empty folder message
            empty_frame = tk.Frame(self.files_frame, bg=theme["background"])
            empty_frame.pack(expand=True, fill=tk.BOTH, pady=50)
            
            empty_icon = tk.Label(empty_frame, text="📂", font=("Segoe UI", 48), 
                                 bg=theme["background"], fg=theme["text_secondary"])
            empty_icon.pack(pady=(20, 10))
            
            empty_text = tk.Label(empty_frame, text="This folder is empty", font=("Segoe UI", 14),
                                 bg=theme["background"], fg=theme["text_secondary"])
            empty_text.pack()
            
            empty_subtext = tk.Label(empty_frame, text="Drag and drop files here or use the organize functions",
                                    bg=theme["background"], fg=theme["text_secondary"])
            empty_subtext.pack(pady=(5, 20))
            
            return
        
        # Create file tiles
        row, col = 0, 0
        
        for file_info in self.filtered_files:
            # Create file tile frame with border
            tile_frame = tk.Frame(self.files_frame, width=tile_width, height=150, 
                                 bg=theme["card"], bd=1, relief=tk.SOLID, 
                                 highlightbackground=theme["border"], highlightthickness=1)
            tile_frame.grid(row=row, column=col, padx=padding//2, pady=padding//2, sticky="nsew")
            tile_frame.pack_propagate(False)
            
            # Bind events
            tile_frame.bind("<Button-1>", lambda e, f=file_info: self.select_file(f))
            tile_frame.bind("<Double-Button-1>", lambda e, f=file_info: self.open_file(f))
            tile_frame.bind("<Button-3>", lambda e, f=file_info: self.show_context_menu(e, f))
            
            # Add hover effect
            tile_frame.bind("<Enter>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, f, True))
            tile_frame.bind("<Leave>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, False))
            
            # File icon or thumbnail
            if file_info["is_dir"]:
                icon_label = tk.Label(tile_frame, text="📁", font=("Segoe UI", 32), bg=theme["card"], fg=theme["primary"])
                icon_label.pack(pady=(16, 8))
            else:
                # Determine file type
                ext = os.path.splitext(file_info["name"])[1].lower()
                
                # Check if it's an image or video for thumbnail
                if ext in self.file_categories["Images"]:
                    # Create a frame for the thumbnail
                    thumb_frame = tk.Frame(tile_frame, width=80, height=80, bg=theme["card"])
                    thumb_frame.pack(pady=(16, 8))
                    thumb_frame.pack_propagate(False)
                    
                    # Try to load thumbnail
                    try:
                        # Check if thumbnail is in cache
                        if file_info["path"] in self.thumbnail_cache:
                            thumbnail = self.thumbnail_cache[file_info["path"]]
                        else:
                            # Generate thumbnail
                            img = Image.open(file_info["path"])
                            img.thumbnail((80, 80))
                            thumbnail = ImageTk.PhotoImage(img)
                            # Cache the thumbnail
                            self.thumbnail_cache[file_info["path"]] = thumbnail
                        
                        # Display thumbnail
                        thumb_label = tk.Label(thumb_frame, image=thumbnail, bg=theme["card"])
                        thumb_label.image = thumbnail  # Keep a reference
                        thumb_label.pack(fill=tk.BOTH, expand=True)
                        
                    except Exception:
                        # If thumbnail generation fails, show default icon
                        icon_label = tk.Label(thumb_frame, text="🖼️", font=("Segoe UI", 32), 
                                             bg=theme["card"], fg=theme["text"])
                        icon_label.pack(fill=tk.BOTH, expand=True)
                
                elif ext in self.file_categories["Videos"]:
                    # For videos, just show a video icon for now
                    # In a more advanced version, we could generate video thumbnails
                    icon_label = tk.Label(tile_frame, text="🎬", font=("Segoe UI", 32), 
                                         bg=theme["card"], fg=theme["text"])
                    icon_label.pack(pady=(16, 8))
                
                else:
                    # Set icon based on file type
                    icon_text = "📄"  # Default file icon
                    
                    if ext in self.file_categories["Audio"]:
                        icon_text = "🎵"
                    elif ext in self.file_categories["Documents"]:
                        icon_text = "📝"
                    elif ext in self.file_categories["Spreadsheets"]:
                        icon_text = "📊"
                    elif ext in self.file_categories["Presentations"]:
                        icon_text = "📊"
                    elif ext in self.file_categories["Archives"]:
                        icon_text = "📦"
                    elif ext in self.file_categories["Executables"]:
                        icon_text = "⚙️"
                    
                    icon_label = tk.Label(tile_frame, text=icon_text, font=("Segoe UI", 32), 
                                         bg=theme["card"], fg=theme["text"])
                    icon_label.pack(pady=(16, 8))
            
            # File name (truncated if too long)
            name = file_info["name"]
            display_name = name
            if len(name) > 15:
                display_name = name[:12] + "..."
            
            name_label = tk.Label(tile_frame, text=display_name, bg=theme["card"], fg=theme["text"], 
                                 font=("Segoe UI", 9), wraplength=tile_width-10)
            name_label.pack(pady=(0, 8))
            
            # Bind events to all elements
            for widget in tile_frame.winfo_children():
                widget.bind("<Button-1>", lambda e, f=file_info: self.select_file(f))
                widget.bind("<Double-Button-1>", lambda e, f=file_info: self.open_file(f))
                widget.bind("<Button-3>", lambda e, f=file_info: self.show_context_menu(e, f))
                widget.bind("<Enter>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, f, True))
                widget.bind("<Leave>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, False))
            
            # Update grid position
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        # Update canvas scroll region
        self.files_frame.update_idletasks()
        self.files_canvas.config(scrollregion=self.files_canvas.bbox("all"))

    def on_tile_hover(self, frame, file_info=None, is_hover=True):
        theme = self.themes[self.current_theme]
        
        # Update frame background
        frame.config(bg=theme["hover"] if is_hover else theme["card"])
        
        # Update all child widgets' background
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Frame):
                # If it's a frame (like thumbnail frame), update its children too
                for child in widget.winfo_children():
                    child.config(bg=theme["hover"] if is_hover else theme["card"])
            widget.config(bg=theme["hover"] if is_hover else theme["card"])
        
        # Show tooltip with full filename on hover
        if is_hover and file_info:
            # Position tooltip near the cursor
            x, y = self.root.winfo_pointerxy()
            x_rel = x - self.root.winfo_rootx() + 15
            y_rel = y - self.root.winfo_rooty() + 10
            
            # Set tooltip text and show it
            self.tooltip.config(text=file_info["name"])
            self.tooltip.place(x=x_rel, y=y_rel)
        else:
            # Hide tooltip when not hovering
            self.tooltip.place_forget()

    def on_frame_configure(self, event):
        # Update the scrollregion to encompass the inner frame
        self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        # Update the width of the window to fill the canvas
        self.files_canvas.itemconfig(self.files_canvas_window, width=event.width)
        
        # Redisplay files to adjust grid layout
        self.display_files()

    def on_mousewheel(self, event):
        # Scroll the canvas with the mousewheel
        self.files_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_status(self, message):
        self.status_label.config(text=message)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.current_dir)
        if directory:
            self.load_directory(directory)

    def go_back(self):
        parent_dir = os.path.dirname(self.current_dir)
        if parent_dir != self.current_dir:  # Avoid going back from root
            self.load_directory(parent_dir)

    def toggle_theme(self):
        # Toggle theme
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        
        # Update theme button icon
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_button.config(text=theme_icon)
        
        # Apply theme
        self.apply_theme()
        
        # Redisplay files with new theme
        self.display_files()

    def select_file(self, file_info):
        # Store selected file
        self.selected_file = file_info
        
        # Update status
        self.update_status(f"Selected: {file_info['name']}")

    def open_file(self, file_info=None):
        if file_info is None:
            if self.selected_file is None:
                messagebox.showinfo("Info", "No file selected")
                return
            file_info = self.selected_file
        
        try:
            if file_info["is_dir"]:
                # Open directory
                self.load_directory(file_info["path"])
            else:
                # Open file with default application
                if os.name == "nt":  # Windows
                    os.startfile(file_info["path"])
                elif os.name == "posix":  # macOS and Linux
                    os.system(f"xdg-open '{file_info['path']}'")
                self.update_status(f"Opened {file_info['name']}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def show_context_menu(self, event, file_info):
        # Store selected file
        self.selected_file = file_info
        
        # Show context menu at the position of the event
        self.context_menu.post(event.x_root, event.y_root)

    def show_details(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
            
        file_info = self.selected_file
        theme = self.themes[self.current_theme]
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Details: {file_info['name']}")
        details_window.geometry("450x350")
        details_window.resizable(False, False)
        details_window.configure(bg=theme["background"])
        
        # Add a modern header
        header_frame = tk.Frame(details_window, bg=theme["primary"], height=60)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(header_frame, text="File Details", font=("Segoe UI", 16, "bold"),
                              bg=theme["primary"], fg="white")
        header_label.pack(pady=15)
        
        # Details content
        content_frame = tk.Frame(details_window, bg=theme["background"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # File icon
        if file_info["is_dir"]:
            icon_text = "📁"
        else:
            ext = os.path.splitext(file_info["name"])[1].lower()
            icon_text = "📄"  # Default
            
            if ext in self.file_categories["Images"]:
                icon_text = "🖼️"
            elif ext in self.file_categories["Videos"]:
                icon_text = "🎬"
            elif ext in self.file_categories["Audio"]:
                icon_text = "🎵"
            elif ext in self.file_categories["Documents"]:
                icon_text = "📝"
            elif ext in self.file_categories["Spreadsheets"]:
                icon_text = "📊"
            elif ext in self.file_categories["Presentations"]:
                icon_text = "📊"
            elif ext in self.file_categories["Archives"]:
                icon_text = "📦"
            elif ext in self.file_categories["Executables"]:
                icon_text = "⚙️"
        
        icon_label = tk.Label(content_frame, text=icon_text, font=("Segoe UI", 48),
                            bg=theme["background"], fg=theme["primary"])
        icon_label.grid(row=0, column=0, rowspan=3, padx=(0, 20), sticky="n")
        
        # File name
        tk.Label(content_frame, text="Name:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=0, column=1, sticky=tk.W, pady=4)
        tk.Label(content_frame, text=file_info["name"], font=("Segoe UI", 10),
               bg=theme["background"], fg=theme["text"]).grid(row=0, column=2, sticky=tk.W, pady=4)
        
        # File path
        tk.Label(content_frame, text="Path:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=1, column=1, sticky=tk.W, pady=4)
        path_label = tk.Label(content_frame, text=file_info["path"], font=("Segoe UI", 10),
                            bg=theme["background"], fg=theme["text"], wraplength=250)
        path_label.grid(row=1, column=2, sticky=tk.W, pady=4)
        
        # File type
        file_type = "Folder" if file_info["is_dir"] else os.path.splitext(file_info["name"])[1].upper()[1:] + " File"
        tk.Label(content_frame, text="Type:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=2, column=1, sticky=tk.W, pady=4)
        tk.Label(content_frame, text=file_type, font=("Segoe UI", 10),
               bg=theme["background"], fg=theme["text"]).grid(row=2, column=2, sticky=tk.W, pady=4)
        
        # File size
        size_str = "N/A" if file_info["is_dir"] else self.format_size(file_info["size"])
        tk.Label(content_frame, text="Size:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=3, column=1, sticky=tk.W, pady=4)
        tk.Label(content_frame, text=size_str, font=("Segoe UI", 10),
               bg=theme["background"], fg=theme["text"]).grid(row=3, column=2, sticky=tk.W, pady=4)
        
        # Created date
        created_str = datetime.datetime.fromtimestamp(file_info["created"]).strftime("%Y-%m-%d %H:%M:%S")
        tk.Label(content_frame, text="Created:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=4, column=1, sticky=tk.W, pady=4)
        tk.Label(content_frame, text=created_str, font=("Segoe UI", 10),
               bg=theme["background"], fg=theme["text"]).grid(row=4, column=2, sticky=tk.W, pady=4)
        
        # Modified date
        modified_str = datetime.datetime.fromtimestamp(file_info["modified"]).strftime("%Y-%m-%d %H:%M:%S")
        tk.Label(content_frame, text="Modified:", font=("Segoe UI", 10, "bold"),
               bg=theme["background"], fg=theme["text"]).grid(row=5, column=1, sticky=tk.W, pady=4)
        tk.Label(content_frame, text=modified_str, font=("Segoe UI", 10),
               bg=theme["background"], fg=theme["text"]).grid(row=5, column=2, sticky=tk.W, pady=4)
        
        # Button frame
        button_frame = tk.Frame(details_window, bg=theme["background"], pady=15)
        button_frame.pack(fill=tk.X)
        
        # Close button
        close_button = tk.Button(button_frame, text="Close", font=("Segoe UI", 10),
                               bg=theme["primary"], fg="white", bd=0, padx=15, pady=8,
                               command=details_window.destroy)
        close_button.pack()

    def format_size(self, size_bytes):
        # Format file size in human-readable format
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def copy_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
            
        file_info = self.selected_file
        
        # Ask for destination
        destination = filedialog.askdirectory(title="Select Destination Folder")
        if not destination:
            return
        
        # Copy file
        try:
            dest_path = os.path.join(destination, file_info["name"])
            
            # Check if destination already exists
            if os.path.exists(dest_path):
                if not messagebox.askyesno("File Exists", f"{file_info['name']} already exists. Overwrite?"):
                    return
            
            if file_info["is_dir"]:
                shutil.copytree(file_info["path"], dest_path)
            else:
                shutil.copy2(file_info["path"], dest_path)
            
            self.update_status(f"Copied {file_info['name']} to {destination}")
            messagebox.showinfo("Success", f"File copied successfully to {destination}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy file: {str(e)}")

    def move_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
            
        file_info = self.selected_file
        
        # Ask for destination
        destination = filedialog.askdirectory(title="Select Destination Folder")
        if not destination:
            return
        
        # Move file
        try:
            dest_path = os.path.join(destination, file_info["name"])
            
            # Check if destination already exists
            if os.path.exists(dest_path):
                if not messagebox.askyesno("File Exists", f"{file_info['name']} already exists. Overwrite?"):
                    return
            
            if file_info["is_dir"]:
                shutil.move(file_info["path"], dest_path)
            else:
                shutil.move(file_info["path"], dest_path)
            
            self.update_status(f"Moved {file_info['name']} to {destination}")
            messagebox.showinfo("Success", f"File moved successfully to {destination}")
            
            # Refresh current directory
            self.load_directory(self.current_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Could not move file: {str(e)}")

    def delete_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
            
        file_info = self.selected_file
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {file_info['name']}?"):
            return
        
        # Delete file
        try:
            if file_info["is_dir"]:
                shutil.rmtree(file_info["path"])
            else:
                os.remove(file_info["path"])
            
            self.update_status(f"Deleted {file_info['name']}")
            
            # Refresh current directory
            self.load_directory(self.current_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file: {str(e)}")

    def locate_in_explorer(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
            
        file_info = self.selected_file
        
        # Open file location in explorer
        try:
            if os.name == "nt":  # Windows
                os.system(f'explorer /select,"{file_info["path"]}"')
            elif os.name == "posix":  # macOS and Linux
                os.system(f'open -R "{file_info["path"]}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not locate file: {str(e)}")

    def organize_by_date(self):
        # Ask for destination
        destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
        if destination == "":
            destination = self.current_dir
        
        # Confirm organization
        if not messagebox.askyesno("Confirm Organization", 
                                  f"Are you sure you want to organize files by date in {destination}?"):
            return
        
        # Organize files
        try:
            self.update_status("Organizing files by date...")
            self.cancel_operation = False
            
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Organizing Files")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            
            # Apply theme
            theme = self.themes[self.current_theme]
            progress_window.configure(bg=theme["background"])
            
            # Progress label
            progress_label = tk.Label(progress_window, text="Organizing files...", font=("Segoe UI", 11),
                                    bg=theme["background"], fg=theme["text"])
            progress_label.pack(pady=(20, 10))
            
            # Progress bar
            progress_frame = tk.Frame(progress_window, bg=theme["background"])
            progress_frame.pack(fill=tk.X, padx=20)
            
            progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=350, mode="determinate",
                                         style="Horizontal.TProgressbar")
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Button frame
            button_frame = tk.Frame(progress_window, bg=theme["background"], pady=15)
            button_frame.pack(fill=tk.X)
            
            # Cancel button
            cancel_button = tk.Button(button_frame, text="Cancel", font=("Segoe UI", 10),
                                    bg=theme["danger"], fg="white", bd=0, padx=15, pady=5,
                                    command=lambda: self.cancel_organization(progress_window))
            cancel_button.pack()
            
            # Start organizing in a separate thread
            threading.Thread(target=self._organize_by_date_thread, 
                            args=(destination, progress_window, progress_label, progress_bar), 
                            daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not organize files: {str(e)}")

    def cancel_organization(self, progress_window):
        self.cancel_operation = True
        self.update_status("Organization cancelled")
        progress_window.destroy()

    def _organize_by_date_thread(self, destination, progress_window, progress_label, progress_bar):
        try:
            # Get files to organize
            files_to_organize = [f for f in self.files if not f["is_dir"]]
            total_files = len(files_to_organize)
            
            # Update progress bar
            progress_bar["maximum"] = total_files
            
            # Organize files by date
            for i, file_info in enumerate(files_to_organize):
                # Check if operation was cancelled
                if self.cancel_operation:
                    return
                
                # Get file date
                file_date = datetime.datetime.fromtimestamp(file_info["modified"])
                date_folder = file_date.strftime("%Y-%m-%d")
                
                # Create date folder
                date_path = os.path.join(destination, date_folder)
                os.makedirs(date_path, exist_ok=True)
                
                # Copy file to date folder
                dest_path = os.path.join(date_path, file_info["name"])
                
                # Skip if destination already exists
                if os.path.exists(dest_path):
                    continue
                
                # Copy file
                shutil.copy2(file_info["path"], dest_path)
                
                # Update progress
                self.root.after(0, lambda i=i, name=file_info["name"]: 
                               progress_label.config(text=f"Organizing {i+1}/{total_files}: {name}"))
                self.root.after(0, lambda i=i: progress_bar.step(1))
                
                # Small delay to make cancellation more responsive
                time.sleep(0.01)
            
            # Close progress window
            self.root.after(0, progress_window.destroy)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Files organized by date in {destination}"))
            
            # Refresh if organizing in current directory
            if destination == self.current_dir:
                self.root.after(0, lambda: self.load_directory(self.current_dir))
            
            # Update status
            self.root.after(0, lambda: self.update_status(f"Organized {total_files} files by date"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Could not organize files: {str(e)}"))
            self.root.after(0, progress_window.destroy)

    def organize_by_type(self):
        # Ask for destination
        destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
        if destination == "":
            destination = self.current_dir
        
        # Confirm organization
        if not messagebox.askyesno("Confirm Organization", 
                                  f"Are you sure you want to organize files by type in {destination}?"):
            return
        
        # Organize files
        try:
            self.update_status("Organizing files by type...")
            self.cancel_operation = False
            
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Organizing Files")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            
            # Apply theme
            theme = self.themes[self.current_theme]
            progress_window.configure(bg=theme["background"])
            
            # Progress label
            progress_label = tk.Label(progress_window, text="Organizing files...", font=("Segoe UI", 11),
                                    bg=theme["background"], fg=theme["text"])
            progress_label.pack(pady=(20, 10))
            
            # Progress bar
            progress_frame = tk.Frame(progress_window, bg=theme["background"])
            progress_frame.pack(fill=tk.X, padx=20)
            
            progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=350, mode="determinate",
                                         style="Horizontal.TProgressbar")
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Button frame
            button_frame = tk.Frame(progress_window, bg=theme["background"], pady=15)
            button_frame.pack(fill=tk.X)
            
            # Cancel button
            cancel_button = tk.Button(button_frame, text="Cancel", font=("Segoe UI", 10),
                                    bg=theme["danger"], fg="white", bd=0, padx=15, pady=5,
                                    command=lambda: self.cancel_organization(progress_window))
            cancel_button.pack()
            
            # Start organizing in a separate thread
            threading.Thread(target=self._organize_by_type_thread, 
                            args=(destination, progress_window, progress_label, progress_bar), 
                            daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not organize files: {str(e)}")

    def _organize_by_type_thread(self, destination, progress_window, progress_label, progress_bar):
        try:
            # Get files to organize
            files_to_organize = [f for f in self.files if not f["is_dir"]]
            total_files = len(files_to_organize)
            
            # Update progress bar
            progress_bar["maximum"] = total_files
            
            # Organize files by type
            for i, file_info in enumerate(files_to_organize):
                # Check if operation was cancelled
                if self.cancel_operation:
                    return
                
                # Get file extension
                _, ext = os.path.splitext(file_info["name"])
                ext = ext.lower()
                
                # Determine category folder
                category = "Others"
                for cat, extensions in self.file_categories.items():
                    if ext in extensions:
                        category = cat
                        break
                
                # Create category folder
                category_path = os.path.join(destination, category)
                os.makedirs(category_path, exist_ok=True)
                
                # Copy file to category folder
                dest_path = os.path.join(category_path, file_info["name"])
                
                # Skip if destination already exists
                if os.path.exists(dest_path):
                    continue
                
                # Copy file
                shutil.copy2(file_info["path"], dest_path)
                
                # Update progress
                self.root.after(0, lambda i=i, name=file_info["name"]: 
                               progress_label.config(text=f"Organizing {i+1}/{total_files}: {name}"))
                self.root.after(0, lambda i=i: progress_bar.step(1))
                
                # Small delay to make cancellation more responsive
                time.sleep(0.01)
            
            # Close progress window
            self.root.after(0, progress_window.destroy)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Files organized by type in {destination}"))
            
            # Refresh if organizing in current directory
            if destination == self.current_dir:
                self.root.after(0, lambda: self.load_directory(self.current_dir))
            
            # Update status
            self.root.after(0, lambda: self.update_status(f"Organized {total_files} files by type"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Could not organize files: {str(e)}"))
            self.root.after(0, progress_window.destroy)


if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    root.title("File Organizer")
    
    # Create app
    app = FileOrganizerApp(root)
    
    # Run app
    root.mainloop()
