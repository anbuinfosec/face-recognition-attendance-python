#!/usr/bin/env python3
"""
Face Recognition-Based Attendance System with GUI and JSON Storage
Main Application Launcher
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
import subprocess
import sys

class FaceAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 Face Recognition Attendance System")
        self.root.geometry("900x650")
        self.root.configure(bg='#f8f9fa')
        
        # Set window icon (if available)
        try:
            # You can add an icon file later
            pass
        except:
            pass
        
        # Check face_recognition availability
        self.check_face_recognition_status()
        
        # Configure style
        self.setup_styles()
        
        # Create main frame with gradient effect
        self.create_main_interface()
        
    def check_face_recognition_status(self):
        """Check if face_recognition is available"""
        try:
            import face_recognition
            self.face_recognition_available = True
            print("✅ Face recognition library is available")
        except Exception as e:
            self.face_recognition_available = False
            print(f"⚠️  Face recognition library not available: {e}")
            print("📝 System will run in demo mode")
    
    def initialize_data_files(self):
        """Initialize JSON data files if they don't exist"""
        try:
            # Create json_data/students.json if it doesn't exist
            if not os.path.exists('json_data/students.json'):
                with open('json_data/students.json', 'w') as f:
                    json.dump({}, f, indent=2)
            
            # Create json_data/encodings.json if it doesn't exist
            if not os.path.exists('json_data/encodings.json'):
                with open('json_data/encodings.json', 'w') as f:
                    json.dump({}, f, indent=2)
                    
            self.update_status("Data files initialized successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize data files: {str(e)}")
    
    def update_status(self, message):
        """Update status label"""
        try:
            if self.status_label and hasattr(self.status_label, 'config'):
                self.status_label.config(text=f"Status: {message}")
                if hasattr(self.root, 'update'):
                    self.root.update()
        except tk.TclError:
            # Handle case where widget was destroyed
            print(f"Status update: {message}")
        except Exception as e:
            print(f"Error updating status: {e} - Message: {message}")
    
    def open_register(self):
        """Open student registration window"""
        try:
            self.update_status("Opening registration window...")
            # Create new window instead of importing module
            reg_window = tk.Toplevel(self.root)
            import register
            app = register.StudentRegistration(reg_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open registration: {str(e)}")
    
    def train_model(self):
        """Train the face recognition model"""
        try:
            self.update_status("Training model...")
            import train
            train.main()
            self.update_status("Model training completed")
            messagebox.showinfo("Success", "Model training completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to train model: {str(e)}")
            self.update_status("Model training failed")
    
    def open_attendance(self):
        """Open attendance taking window"""
        try:
            self.update_status("Opening attendance window...")
            # Create new window instead of importing module
            att_window = tk.Toplevel(self.root)
            import recognize
            app = recognize.AttendanceRecognition(att_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open attendance: {str(e)}")
    
    def open_reports(self):
        """Open reports viewing window"""
        try:
            self.update_status("Opening reports window...")
            # Create new window instead of importing module
            rep_window = tk.Toplevel(self.root)
            import view_report
            app = view_report.AttendanceReportViewer(rep_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open reports: {str(e)}")
    
    def open_calibrator(self):
        """Open face recognition calibrator"""
        try:
            self.update_status("Opening calibration tool...")
            # Create new window instead of importing module
            cal_window = tk.Toplevel(self.root)
            import face_calibrator
            app = face_calibrator.FaceRecognitionCalibrator(cal_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open calibrator: {str(e)}")
    
    def setup_styles(self):
        """Configure modern UI styles"""
        style = ttk.Style()
        
        # Configure modern button styles
        style.configure('ModernButton.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 15))
        
        style.configure('HeaderLabel.TLabel',
                       font=('Segoe UI', 28, 'bold'),
                       foreground='#2c3e50')
        
        style.configure('SubheaderLabel.TLabel',
                       font=('Segoe UI', 12),
                       foreground='#7f8c8d')
        
        style.configure('StatusLabel.TLabel',
                       font=('Segoe UI', 10),
                       foreground='#27ae60')
    
    def create_main_interface(self):
        """Create the main interface with modern design"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Header section
        header_frame = tk.Frame(main_container, bg='#f8f9fa')
        header_frame.pack(fill='x', pady=(0, 30))
        
        # Title with modern styling
        title_label = tk.Label(header_frame, 
                              text="🎓 Face Recognition Attendance System",
                              font=('Segoe UI', 26, 'bold'),
                              fg='#2c3e50',
                              bg='#f8f9fa')
        title_label.pack()
        
        # Subtitle with mode indicator
        mode = "🤖 Demo Mode" if not getattr(self, 'face_recognition_available', False) else "🔴 Live Mode"
        subtitle_label = tk.Label(header_frame,
                                 text=f"Smart Attendance Management System - {mode}",
                                 font=('Segoe UI', 12),
                                 fg='#7f8c8d',
                                 bg='#f8f9fa')
        subtitle_label.pack(pady=(5, 0))
        
        # Main content area
        content_frame = tk.Frame(main_container, bg='#f8f9fa')
        content_frame.pack(fill='both', expand=True)
        
        # Create button grid
        self.create_modern_buttons(content_frame)
        
        # Status section
        self.create_status_section(main_container)
        
        # Initialize data files
        self.initialize_data_files()
    
    def create_modern_buttons(self, parent):
        """Create modern-styled navigation buttons"""
        # Button container with grid layout
        button_container = tk.Frame(parent, bg='#f8f9fa')
        button_container.pack(expand=True)
        
        # Button definitions with modern icons and colors
        buttons = [
            {
                'text': '👤 Register\nStudent',
                'command': self.open_register,
                'bg': '#3498db',
                'hover': '#2980b9',
                'desc': 'Register new students with face capture'
            },
            {
                'text': '🧠 Train\nModel',
                'command': self.train_model,
                'bg': '#e74c3c',
                'hover': '#c0392b',
                'desc': 'Train face recognition model'
            },
            {
                'text': '📹 Take\nAttendance',
                'command': self.open_attendance,
                'bg': '#2ecc71',
                'hover': '#27ae60',
                'desc': 'Mark attendance with face recognition'
            },
            {
                'text': '📊 View\nReports',
                'command': self.open_reports,
                'bg': '#f39c12',
                'hover': '#e67e22',
                'desc': 'View and export attendance reports'
            },
            {
                'text': '⚙️ Calibrate\nRecognition',
                'command': self.open_calibrator,
                'bg': '#9b59b6',
                'hover': '#8e44ad',
                'desc': 'Fine-tune face recognition accuracy'
            },
            {
                'text': '🔧 System\nStatus',
                'command': self.show_system_status,
                'bg': '#34495e',
                'hover': '#2c3e50',
                'desc': 'Check system health and diagnostics'
            }
        ]
        
        # Create buttons in a 3x2 grid
        for i, btn_info in enumerate(buttons):
            row = i // 3
            col = i % 3
            
            # Button frame for hover effects
            btn_frame = tk.Frame(button_container, bg='#f8f9fa')
            btn_frame.grid(row=row, column=col, padx=15, pady=15)
            
            # Main button
            btn = tk.Button(btn_frame,
                           text=btn_info['text'],
                           command=btn_info['command'],
                           font=('Segoe UI', 11, 'bold'),
                           bg=btn_info['bg'],
                           fg='white',
                           width=15,
                           height=4,
                           relief='flat',
                           cursor='hand2',
                           activebackground=btn_info['hover'],
                           activeforeground='white')
            btn.pack()
            
            # Description label
            desc_label = tk.Label(btn_frame,
                                 text=btn_info['desc'],
                                 font=('Segoe UI', 8),
                                 fg='#7f8c8d',
                                 bg='#f8f9fa')
            desc_label.pack(pady=(5, 0))
            
            # Add hover effects
            self.add_hover_effect(btn, btn_info['bg'], btn_info['hover'])
    
    def add_hover_effect(self, button, normal_color, hover_color):
        """Add hover effect to buttons"""
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def create_status_section(self, parent):
        """Create modern status section"""
        status_container = tk.Frame(parent, bg='#ecf0f1', relief='solid', bd=1)
        status_container.pack(fill='x', pady=(20, 0))
        
        status_inner = tk.Frame(status_container, bg='#ecf0f1')
        status_inner.pack(fill='x', padx=20, pady=10)
        
        # Status icon and text
        status_frame = tk.Frame(status_inner, bg='#ecf0f1')
        status_frame.pack(side='left')
        
        status_icon = tk.Label(status_frame, text="ℹ️", font=('Segoe UI', 12), bg='#ecf0f1')
        status_icon.pack(side='left', padx=(0, 10))
        
        self.status_label = tk.Label(status_frame,
                                   text="System Ready - All components loaded",
                                   font=('Segoe UI', 10),
                                   fg='#27ae60',
                                   bg='#ecf0f1')
        self.status_label.pack(side='left')
        
        # System info on the right
        info_frame = tk.Frame(status_inner, bg='#ecf0f1')
        info_frame.pack(side='right')
        
        mode_text = "Live Mode" if getattr(self, 'face_recognition_available', False) else "Demo Mode"
        mode_color = '#27ae60' if getattr(self, 'face_recognition_available', False) else '#f39c12'
        
        mode_label = tk.Label(info_frame,
                             text=f"Mode: {mode_text}",
                             font=('Segoe UI', 9, 'bold'),
                             fg=mode_color,
                             bg='#ecf0f1')
        mode_label.pack()
    
    def show_system_status(self):
        """Show system status window"""
        try:
            self.update_status("Opening system status...")
            # Create new window instead of subprocess
            status_window = tk.Toplevel(self.root)
            import system_check # type: ignore
            app = system_check.SystemHealthChecker(status_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open system status: {str(e)}")

def main():
    root = tk.Tk()
    app = FaceAttendanceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
