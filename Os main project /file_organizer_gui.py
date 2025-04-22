import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import ctypes  

import datetime


lib = ctypes.CDLL('./file_organizer_backend.so')


lib.get_directory_contents.argtypes = [ctypes.c_char_p]
lib.get_directory_contents.restype = ctypes.POINTER(ctypes.c_char_p)

lib.copy_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.copy_file.restype = ctypes.c_bool

lib.move_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.move_file.restype = ctypes.c_bool

lib.delete_file.argtypes = [ctypes.c_char_p]
lib.delete_file.restype = ctypes.c_bool

lib.organize_by_date.argtypes = [ctypes.c_char_p]
lib.organize_by_date.restype = ctypes.c_bool

lib.organize_by_type.argtypes = [ctypes.c_char_p]
lib.organize_by_type.restype = ctypes.c_bool

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)

        

    
    def _load_directory_thread(self, directory):
        try:
            result = lib.get_directory_contents(directory.encode('utf-8'))
            if not result:
                raise Exception("Failed to load directory contents")

            files = []
            i = 0
            while result[i]:
                file_path = result[i].decode('utf-8')
                stats = os.stat(file_path)
                is_dir = os.path.isdir(file_path)
                file_info = {
                    "name": os.path.basename(file_path),
                    "path": file_path,
                    "size": stats.st_size if not is_dir else 0,
                    "created": stats.st_ctime,
                    "modified": stats.st_mtime,
                    "is_dir": is_dir
                }
                files.append(file_info)
                i += 1

            self.files = files
            self.filter_and_sort_files()
            self.root.after(0, self.display_files)
            self.root.after(0, lambda: self.update_status(f"Loaded {len(self.files)} items"))
            self.root.after(0, lambda: self.file_count_label.config(text=f"{len(self.filtered_files)} items"))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}"))

    def copy_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
        file_info = self.selected_file
        destination = filedialog.askdirectory(title="Select Destination Folder")
        if not destination:
            return
        try:
            src = file_info["path"].encode('utf-8')
            dest = os.path.join(destination, file_info["name"]).encode('utf-8')
            success = lib.copy_file(src, dest)
            if success:
                self.update_status(f"Copied {file_info['name']} to {destination}")
                messagebox.showinfo("Success", f"File copied successfully to {destination}")
            else:
                messagebox.showerror("Error", "Failed to copy file")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy file: {str(e)}")

    def move_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
        file_info = self.selected_file
        destination = filedialog.askdirectory(title="Select Destination Folder")
        if not destination:
            return
        try:
            src = file_info["path"].encode('utf-8')
            dest = os.path.join(destination, file_info["name"]).encode('utf-8')
            success = lib.move_file(src, dest)
            if success:
                self.update_status(f"Moved {file_info['name']} to {destination}")
                messagebox.showinfo("Success", f"File moved successfully to {destination}")
                self.load_directory(self.current_dir)
            else:
                messagebox.showerror("Error", "Failed to move file")
        except Exception as e:
            messagebox.showerror("Error", f"Could not move file: {str(e)}")

    def delete_file(self):
        if self.selected_file is None:
            messagebox.showinfo("Info", "No file selected")
            return
        file_info = self.selected_file
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {file_info['name']}?"):
            return
        try:
            path = file_info["path"].encode('utf-8')
            success = lib.delete_file(path)
            if success:
                self.update_status(f"Deleted {file_info['name']}")
                self.load_directory(self.current_dir)
            else:
                messagebox.showerror("Error", "Failed to delete file")
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file: {str(e)}")

    def organize_by_date(self):
        destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
        if destination == "":
            destination = self.current_dir
        if not messagebox.askyesno("Confirm Organization",
                                  f"Are you sure you want to organize files by date in {destination}?"):
            return
        try:
            success = lib.organize_by_date(destination.encode('utf-8'))
            if success:
                messagebox.showinfo("Success", f"Files organized by date in {destination}")
                if destination == self.current_dir:
                    self.load_directory(self.current_dir)
                self.update_status(f"Organized files by date in {destination}")
            else:
                messagebox.showerror("Error", "Failed to organize files by date")
        except Exception as e:
            messagebox.showerror("Error", f"Could not organize files: {str(e)}")

    def organize_by_type(self):
        destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
        if destination == "":
            destination = self.current_dir
        if not messagebox.askyesno("Confirm Organization",
                                  f"Are you sure you want to organize files by type in {destination}?"):
            return
        try:
            success = lib.organize_by_type(destination.encode('utf-8'))
            if success:
                messagebox.showinfo("Success", f"Files organized by type in {destination}")
                if destination == self.current_dir:
                    self.load_directory(self.current_dir)
                self.update_status(f"Organized files by type in {destination}")
            else:
                messagebox.showerror("Error", "Failed to organize files by type")
        except Exception as e:
            messagebox.showerror("Error", f"Could not organize files: {str(e)}")


class FileOrganizerApp:
        def __init__(self, root):
            self.root = root
            self.root.title("File Organizer")
            self.root.geometry("1200x700")
            self.root.minsize(800, 600)

           
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
            self.selected_file = None  
            self.cancel_operation = False 
            self.thumbnail_cache = {}  

            
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

            
            self.current_dir = os.path.expanduser("~")
            self.files = []
            self.filtered_files = []
            self.current_category = "All"
            self.current_sort = "Name (A-Z)"

            
            self.apply_theme()

           
            self.create_ui()

            
            self.load_directory(self.current_dir)

        def apply_theme(self):
            theme = self.themes[self.current_theme]
            self.root.configure(bg=theme["background"])

           
            style = ttk.Style()
            style.theme_use("clam")

            
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
           
            self.main_frame = ttk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

            
            self.top_bar = ttk.Frame(self.main_frame)
            self.top_bar.pack(fill=tk.X, pady=(0, 16))

            
            self.back_button = ttk.Button(self.top_bar, text="←", width=3, command=self.go_back)
            self.back_button.pack(side=tk.LEFT, padx=(0, 8))
            self.path_label = ttk.Label(self.top_bar, text=self.current_dir, style="Path.TLabel")
            self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

            
            self.browse_button = ttk.Button(self.top_bar, text="Browse", command=self.browse_directory)
            self.browse_button.pack(side=tk.LEFT, padx=(0, 16))

            
            theme_icon = "🌙" if self.current_theme == "light" else "☀️"
            self.theme_button = ttk.Button(self.top_bar, text=theme_icon, width=3, command=self.toggle_theme)
            self.theme_button.pack(side=tk.RIGHT)

          
            self.content_frame = ttk.Frame(self.main_frame)
            self.content_frame.pack(fill=tk.BOTH, expand=True)

            
            self.sidebar = ttk.Frame(self.content_frame, width=200)
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
            self.sidebar.pack_propagate(False)

            
            ttk.Label(self.sidebar, text="Categories", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 16))

            
            self.create_category_button("All", True)

            
            for category in self.file_categories:
                self.create_category_button(category)

           
            self.content_area = ttk.Frame(self.content_frame)
            self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            
            self.controls_bar = ttk.Frame(self.content_area)
            self.controls_bar.pack(fill=tk.X, pady=(0, 16))

           
            ttk.Label(self.controls_bar, text="Sort by:").pack(side=tk.LEFT, padx=(0, 8))
            self.sort_options = ["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Size (Largest)", "Size (Smallest)"]
            self.sort_var = tk.StringVar(value=self.sort_options[0])
            self.sort_combo = ttk.Combobox(self.controls_bar, textvariable=self.sort_var, values=self.sort_options, state="readonly", width=15)
            self.sort_combo.pack(side=tk.LEFT, padx=(0, 16))
            self.sort_combo.bind("<<ComboboxSelected>>", self.on_sort_change)

            
            self.organize_by_date_button = ttk.Button(self.controls_bar, text="Organize by Date", 
                                                    command=self.organize_by_date, style="Success.TButton")
            self.organize_by_date_button.pack(side=tk.RIGHT, padx=(8, 0))
            self.organize_by_type_button = ttk.Button(self.controls_bar, text="Organize by Type", 
                                                    command=self.organize_by_type, style="Success.TButton")
            self.organize_by_type_button.pack(side=tk.RIGHT)

           
            self.files_canvas = tk.Canvas(self.content_area, bg=self.themes[self.current_theme]["background"], 
                                        highlightthickness=0)
            self.files_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

           
            self.scrollbar = ttk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=self.files_canvas.yview)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.files_canvas.configure(yscrollcommand=self.scrollbar.set)

            
            self.files_frame = ttk.Frame(self.files_canvas)
            self.files_canvas_window = self.files_canvas.create_window((0, 0), window=self.files_frame, anchor=tk.NW)

           
            self.files_frame.bind("<Configure>", self.on_frame_configure)
            self.files_canvas.bind("<Configure>", self.on_canvas_configure)
            self.files_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

         
            self.status_bar = ttk.Frame(self.main_frame)
            self.status_bar.pack(fill=tk.X, pady=(16, 0))
            self.status_label = ttk.Label(self.status_bar, text="Ready")
            self.status_label.pack(side=tk.LEFT)
            self.file_count_label = ttk.Label(self.status_bar, text="0 items")
            self.file_count_label.pack(side=tk.RIGHT)

           
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="Open", command=lambda: self.open_file())
            self.context_menu.add_command(label="Details", command=self.show_details)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Copy", command=self.copy_file)
            self.context_menu.add_command(label="Move", command=self.move_file)
            self.context_menu.add_command(label="Delete", command=self.delete_file)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Locate in Explorer", command=self.locate_in_explorer)

            
            self.tooltip = tk.Label(self.root, text="", bg="#ffffcc", relief="solid", borderwidth=1)
            self.tooltip.place_forget()

        def create_category_button(self, category, is_all=False):
            theme = self.themes[self.current_theme]
            frame = ttk.Frame(self.sidebar)
            frame.pack(fill=tk.X, pady=4)

           
            frame.bind("<Button-1>", lambda e, cat=category: self.select_category(cat))

           
            icon_text = "📁"  
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

            
            if is_all:
                self.selected_category_label = label
                self.selected_category_frame = frame

        def select_category(self, category):
           
            self.current_category = category
           
            self.filter_and_sort_files()
            
            self.display_files()
           
            self.update_status(f"Category: {category}")

        def on_sort_change(self, event):
           
            self.current_sort = self.sort_var.get()
           
            self.filter_and_sort_files()
          
            self.display_files()
            
            self.update_status(f"Sorted by: {self.current_sort}")

        def filter_and_sort_files(self):
           
            if self.current_category == "All":
                self.filtered_files = self.files.copy()
            else:
                extensions = self.file_categories.get(self.current_category, [])
                if extensions:  
                    self.filtered_files = [f for f in self.files if os.path.splitext(f["name"])[1].lower() in extensions]
                else:  
                    all_extensions = []
                    for exts in self.file_categories.values():
                        all_extensions.extend(exts)
                    self.filtered_files = [f for f in self.files if os.path.splitext(f["name"])[1].lower() not in all_extensions]

           
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
            
            self.current_dir = directory
            self.path_label.config(text=directory)
            
            self.files = []

            
            self.update_status("Loading files...")

            
            threading.Thread(target=self._load_directory_backend, args=(directory,), daemon=True).start()

        def _load_directory_backend(self, directory):
            try:
                
                lib = ctypes.CDLL('./file_organizer_backend.so')  
                lib.get_directory_contents.argtypes = [ctypes.c_char_p]
                lib.get_directory_contents.restype = ctypes.POINTER(ctypes.c_char_p)

                result = lib.get_directory_contents(directory.encode('utf-8'))
                if not result:
                    raise Exception("Failed to load directory contents")

                
                files = []
                i = 0
                while result[i]:
                    file_path = result[i].decode('utf-8')
                    files.append(file_path)
                    i += 1

                
                self.files = self._process_backend_files(files)

               
                self.filter_and_sort_files()

                
                self.root.after(0, self.display_files)
                self.root.after(0, lambda: self.update_status(f"Loaded {len(self.files)} items"))
                self.root.after(0, lambda: self.file_count_label.config(text=f"{len(self.filtered_files)} items"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}"))

        def _process_backend_files(self, files):
            
            processed_files = []
            for file_path in files:
                stats = os.stat(file_path)
                is_dir = os.path.isdir(file_path)
                file_info = {
                    "name": os.path.basename(file_path),
                    "path": file_path,
                    "size": stats.st_size if not is_dir else 0,
                    "created": stats.st_ctime,
                    "modified": stats.st_mtime,
                    "is_dir": is_dir
                }
                processed_files.append(file_info)
            return processed_files

        def display_files(self):
            
            for widget in self.files_frame.winfo_children():
                widget.destroy()

            
            canvas_width = self.files_canvas.winfo_width()
            tile_width = 120
            padding = 16
            cols = max(1, (canvas_width - padding) // (tile_width + padding))
            theme = self.themes[self.current_theme]

            
            if not self.filtered_files:
                
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

           
            row, col = 0, 0
            for file_info in self.filtered_files:
               
                tile_frame = tk.Frame(self.files_frame, width=tile_width, height=150, 
                                    bg=theme["card"], bd=1, relief=tk.SOLID, 
                                    highlightbackground=theme["border"], highlightthickness=1)
                tile_frame.grid(row=row, column=col, padx=padding//2, pady=padding//2, sticky="nsew")
                tile_frame.pack_propagate(False)

               
                tile_frame.bind("<Button-1>", lambda e, f=file_info: self.select_file(f))
                tile_frame.bind("<Double-Button-1>", lambda e, f=file_info: self.open_file(f))
                tile_frame.bind("<Button-3>", lambda e, f=file_info: self.show_context_menu(e, f))
                tile_frame.bind("<Enter>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, f, True))
                tile_frame.bind("<Leave>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, False))

                
                if file_info["is_dir"]:
                    icon_label = tk.Label(tile_frame, text="📁", font=("Segoe UI", 32), bg=theme["card"], fg=theme["primary"])
                    icon_label.pack(pady=(16, 8))
                else:
                   
                    ext = os.path.splitext(file_info["name"])[1].lower()
                    
                    if ext in self.file_categories["Images"]:
                       
                        thumb_frame = tk.Frame(tile_frame, width=80, height=80, bg=theme["card"])
                        thumb_frame.pack(pady=(16, 8))
                        thumb_frame.pack_propagate(False)
                       
                        try:
                        
                            if file_info["path"] in self.thumbnail_cache:
                                thumbnail = self.thumbnail_cache[file_info["path"]]
                            else:
                               
                                img = Image.open(file_info["path"])
                                img.thumbnail((80, 80))
                                thumbnail = ImageTk.PhotoImage(img)
                                
                                self.thumbnail_cache[file_info["path"]] = thumbnail
                            
                            thumb_label = tk.Label(thumb_frame, image=thumbnail, bg=theme["card"])
                            thumb_label.image = thumbnail  
                            thumb_label.pack(fill=tk.BOTH, expand=True)
                        except Exception:
                         
                            icon_label = tk.Label(thumb_frame, text="🖼️", font=("Segoe UI", 32), 
                                                bg=theme["card"], fg=theme["text"])
                            icon_label.pack(fill=tk.BOTH, expand=True)
                    elif ext in self.file_categories["Videos"]:
                        
                        icon_label = tk.Label(tile_frame, text="🎬", font=("Segoe UI", 32), 
                                            bg=theme["card"], fg=theme["text"])
                        icon_label.pack(pady=(16, 8))
                    else:
                        
                        icon_text = "📄" 
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

                
                name = file_info["name"]
                display_name = name
                if len(name) > 15:
                    display_name = name[:12] + "..."
                name_label = tk.Label(tile_frame, text=display_name, bg=theme["card"], fg=theme["text"], 
                                    font=("Segoe UI", 9), wraplength=tile_width-10)
                name_label.pack(pady=(0, 8))

                
                for widget in tile_frame.winfo_children():
                    widget.bind("<Button-1>", lambda e, f=file_info: self.select_file(f))
                    widget.bind("<Double-Button-1>", lambda e, f=file_info: self.open_file(f))
                    widget.bind("<Button-3>", lambda e, f=file_info: self.show_context_menu(e, f))
                    widget.bind("<Enter>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, f, True))
                    widget.bind("<Leave>", lambda e, frame=tile_frame, f=file_info: self.on_tile_hover(frame, False))

                col += 1
                if col >= cols:
                    col = 0
                    row += 1

            self.files_frame.update_idletasks()
            self.files_canvas.config(scrollregion=self.files_canvas.bbox("all"))

        def on_tile_hover(self, frame, file_info=None, is_hover=True):
            theme = self.themes[self.current_theme]
            frame.config(bg=theme["hover"] if is_hover else theme["card"])
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        child.config(bg=theme["hover"] if is_hover else theme["card"])
                widget.config(bg=theme["hover"] if is_hover else theme["card"])
            if is_hover and file_info:
                x, y = self.root.winfo_pointerxy()
                x_rel = x - self.root.winfo_rootx() + 15
                y_rel = y - self.root.winfo_rooty() + 10
                self.tooltip.config(text=file_info["name"])
                self.tooltip.place(x=x_rel, y=y_rel)
            else:
                self.tooltip.place_forget()

        def on_frame_configure(self, event):
            self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))

        def on_canvas_configure(self, event):
            self.files_canvas.itemconfig(self.files_canvas_window, width=event.width)
            self.display_files()

        def on_mousewheel(self, event):
            self.files_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def update_status(self, message):
            self.status_label.config(text=message)

        def browse_directory(self):
            directory = filedialog.askdirectory(initialdir=self.current_dir)
            if directory:
                self.load_directory(directory)

        def go_back(self):
            parent_dir = os.path.dirname(self.current_dir)
            if parent_dir != self.current_dir:  
                self.load_directory(parent_dir)

        def toggle_theme(self):
            self.current_theme = "dark" if self.current_theme == "light" else "light"
            theme_icon = "🌙" if self.current_theme == "light" else "☀️"
            self.theme_button.config(text=theme_icon)
            self.apply_theme()
            self.display_files()

        def select_file(self, file_info):
            self.selected_file = file_info
            self.update_status(f"Selected: {file_info['name']}")

        def open_file(self, file_info=None):
            if file_info is None:
                if self.selected_file is None:
                    messagebox.showinfo("Info", "No file selected")
                    return
                file_info = self.selected_file
            try:
                if file_info["is_dir"]:
                    self.load_directory(file_info["path"])
                else:
                    if os.name == "nt":  
                        os.startfile(file_info["path"])
                    elif os.name == "posix":  
                        os.system(f"xdg-open '{file_info['path']}'")
                    self.update_status(f"Opened {file_info['name']}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

        def show_context_menu(self, event, file_info):
            self.selected_file = file_info
            self.context_menu.post(event.x_root, event.y_root)

        def show_details(self):
            if self.selected_file is None:
                messagebox.showinfo("Info", "No file selected")
                return
            file_info = self.selected_file
            theme = self.themes[self.current_theme]
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

            content_frame = tk.Frame(details_window, bg=theme["background"], padx=20, pady=20)
            content_frame.pack(fill=tk.BOTH, expand=True)

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

            tk.Label(content_frame, text="Name:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=0, column=1, sticky=tk.W, pady=4)
            tk.Label(content_frame, text=file_info["name"], font=("Segoe UI", 10),
                bg=theme["background"], fg=theme["text"]).grid(row=0, column=2, sticky=tk.W, pady=4)

            tk.Label(content_frame, text="Path:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=1, column=1, sticky=tk.W, pady=4)
            path_label = tk.Label(content_frame, text=file_info["path"], font=("Segoe UI", 10),
                                bg=theme["background"], fg=theme["text"], wraplength=250)
            path_label.grid(row=1, column=2, sticky=tk.W, pady=4)

            file_type = "Folder" if file_info["is_dir"] else os.path.splitext(file_info["name"])[1].upper()[1:] + " File"
            tk.Label(content_frame, text="Type:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=2, column=1, sticky=tk.W, pady=4)
            tk.Label(content_frame, text=file_type, font=("Segoe UI", 10),
                bg=theme["background"], fg=theme["text"]).grid(row=2, column=2, sticky=tk.W, pady=4)

            size_str = "N/A" if file_info["is_dir"] else self.format_size(file_info["size"])
            tk.Label(content_frame, text="Size:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=3, column=1, sticky=tk.W, pady=4)
            tk.Label(content_frame, text=size_str, font=("Segoe UI", 10),
                bg=theme["background"], fg=theme["text"]).grid(row=3, column=2, sticky=tk.W, pady=4)

            created_str = datetime.datetime.fromtimestamp(file_info["created"]).strftime("%Y-%m-%d %H:%M:%S")
            tk.Label(content_frame, text="Created:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=4, column=1, sticky=tk.W, pady=4)
            tk.Label(content_frame, text=created_str, font=("Segoe UI", 10),
                bg=theme["background"], fg=theme["text"]).grid(row=4, column=2, sticky=tk.W, pady=4)

            modified_str = datetime.datetime.fromtimestamp(file_info["modified"]).strftime("%Y-%m-%d %H:%M:%S")
            tk.Label(content_frame, text="Modified:", font=("Segoe UI", 10, "bold"),
                bg=theme["background"], fg=theme["text"]).grid(row=5, column=1, sticky=tk.W, pady=4)
            tk.Label(content_frame, text=modified_str, font=("Segoe UI", 10),
                bg=theme["background"], fg=theme["text"]).grid(row=5, column=2, sticky=tk.W, pady=4)

            button_frame = tk.Frame(details_window, bg=theme["background"], pady=15)
            button_frame.pack(fill=tk.X)

            close_button = tk.Button(button_frame, text="Close", font=("Segoe UI", 10),
                                bg=theme["primary"], fg="white", bd=0, padx=15, pady=8,
                                command=details_window.destroy)
            close_button.pack()

        def format_size(self, size_bytes):
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
            destination = filedialog.askdirectory(title="Select Destination Folder")
            if not destination:
                return
            threading.Thread(target=self._copy_file_backend, args=(file_info, destination), daemon=True).start()

        def _copy_file_backend(self, file_info, destination):
            try:
                lib = ctypes.CDLL('./file_organizer_backend.so')  
                lib.copy_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                lib.copy_file.restype = ctypes.c_bool

                src = file_info["path"].encode('utf-8')
                dest = os.path.join(destination, file_info["name"]).encode('utf-8')

                success = lib.copy_file(src, dest)
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"File copied successfully to {destination}"))
                    self.root.after(0, lambda: self.update_status(f"Copied {file_info['name']} to {destination}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to copy file"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not copy file: {str(e)}"))

        def move_file(self):
            if self.selected_file is None:
                messagebox.showinfo("Info", "No file selected")
                return
            file_info = self.selected_file
            destination = filedialog.askdirectory(title="Select Destination Folder")
            if not destination:
                return
            threading.Thread(target=self._move_file_backend, args=(file_info, destination), daemon=True).start()

        def _move_file_backend(self, file_info, destination):
            try:
                lib = ctypes.CDLL('./file_organizer_backend.so')  
                lib.move_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                lib.move_file.restype = ctypes.c_bool

                src = file_info["path"].encode('utf-8')
                dest = os.path.join(destination, file_info["name"]).encode('utf-8')

                success = lib.move_file(src, dest)
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"File moved successfully to {destination}"))
                    self.root.after(0, lambda: self.update_status(f"Moved {file_info['name']} to {destination}"))
                    self.root.after(0, lambda: self.load_directory(self.current_dir))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to move file"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not move file: {str(e)}"))

        def delete_file(self):
            if self.selected_file is None:
                messagebox.showinfo("Info", "No file selected")
                return
            file_info = self.selected_file
            if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {file_info['name']}?"):
                return
            threading.Thread(target=self._delete_file_backend, args=(file_info,), daemon=True).start()

        def _delete_file_backend(self, file_info):
            try:
                lib = ctypes.CDLL('./file_organizer_backend.so')  
                lib.delete_file.argtypes = [ctypes.c_char_p]
                lib.delete_file.restype = ctypes.c_bool

                path = file_info["path"].encode('utf-8')

                success = lib.delete_file(path)
                if success:
                    self.root.after(0, lambda: self.update_status(f"Deleted {file_info['name']}"))
                    self.root.after(0, lambda: self.load_directory(self.current_dir))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to delete file"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not delete file: {str(e)}"))

        def locate_in_explorer(self):
            if self.selected_file is None:
                messagebox.showinfo("Info", "No file selected")
                return
            file_info = self.selected_file
            try:
                if os.name == "nt":  
                    os.system(f'explorer /select,"{file_info["path"]}"')
                elif os.name == "posix":  
                    os.system(f'open -R "{file_info["path"]}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not locate file: {str(e)}")

        def organize_by_date(self):
            destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
            if destination == "":
                destination = self.current_dir
            if not messagebox.askyesno("Confirm Organization",
                                    f"Are you sure you want to organize files by date in {destination}?"):
                return
            threading.Thread(target=self._organize_by_date_backend, args=(destination,), daemon=True).start()

        def _organize_by_date_backend(self, destination):
            try:
                lib = ctypes.CDLL('./file_organizer_backend.so') 
                lib.organize_by_date.argtypes = [ctypes.c_char_p]
                lib.organize_by_date.restype = ctypes.c_bool

                success = lib.organize_by_date(destination.encode('utf-8'))
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Files organized by date in {destination}"))
                    if destination == self.current_dir:
                        self.root.after(0, lambda: self.load_directory(self.current_dir))
                    self.root.after(0, lambda: self.update_status(f"Organized files by date in {destination}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to organize files by date"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not organize files: {str(e)}"))

        def organize_by_type(self):
            destination = filedialog.askdirectory(title="Select Destination Folder (leave empty to organize in place)")
            if destination == "":
                destination = self.current_dir
            if not messagebox.askyesno("Confirm Organization",
                                    f"Are you sure you want to organize files by type in {destination}?"):
                return
            threading.Thread(target=self._organize_by_type_backend, args=(destination,), daemon=True).start()

        def _organize_by_type_backend(self, destination):
            try:
                lib = ctypes.CDLL('./file_organizer_backend.so')  
                lib.organize_by_type.argtypes = [ctypes.c_char_p]
                lib.organize_by_type.restype = ctypes.c_bool

                success = lib.organize_by_type(destination.encode('utf-8'))
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Files organized by type in {destination}"))
                    if destination == self.current_dir:
                        self.root.after(0, lambda: self.load_directory(self.current_dir))
                    self.root.after(0, lambda: self.update_status(f"Organized files by type in {destination}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to organize files by type"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not organize files: {str(e)}"))


if __name__ == "__main__":
    root = tk.Tk()
    
    app = FileOrganizerApp(root)
    
    # Start the main event loop
    root.mainloop()
