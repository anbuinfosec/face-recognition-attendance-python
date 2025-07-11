#!/usr/bin/env python3
"""
Real-time Face Recognition Attendance Module
Handles live face recognition and attendance marking
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import json
import numpy as np
from datetime import datetime, date
from PIL import Image, ImageTk
import threading
import os
from image_manager import image_manager

# Try to import face_recognition, handle gracefully if not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️  face_recognition not available - recognition will be simulated")

class AttendanceRecognition:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance")
        self.root.geometry("1000x700")
        self.root.configure(bg='#ecf0f1')
        
        # Variables
        self.camera = None
        self.is_running = False
        self.known_encodings = []
        self.known_names = []
        self.known_rolls = []
        self.students_data = {}
        self.today_attendance = {}
        self.camera_label = None  # Initialize camera label
        
        # Recognition settings
        self.load_recognition_settings()
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        
        # Bind cleanup to window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load data
        self.load_encodings()
        self.load_today_attendance()
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Real-time Face Recognition Attendance", 
                               font=('Arial', 18, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Left panel - Camera and controls
        left_frame = ttk.LabelFrame(main_frame, text="Camera Feed", padding="10")
        left_frame.grid(row=1, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel - Attendance info
        right_frame = ttk.LabelFrame(main_frame, text="Attendance Information", padding="10")
        right_frame.grid(row=1, column=1, padx=(10, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_camera_section(left_frame)
        self.create_info_section(right_frame)
        
    def create_camera_section(self, parent):
        """Create camera preview and controls"""
        # Camera display
        self.camera_label = ttk.Label(parent, text="Camera Feed", 
                                    relief='sunken', width=50, font=('Arial', 12))
        self.camera_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Status display
        self.status_var = tk.StringVar(value="System ready - Click Start to begin")
        status_label = ttk.Label(parent, textvariable=self.status_var, 
                               font=('Arial', 11, 'bold'), foreground='#27ae60')
        status_label.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Recognition", 
                                  command=self.start_recognition, style='Large.TButton')
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Recognition", 
                                 command=self.stop_recognition, style='Large.TButton', 
                                 state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(btn_frame, text="Refresh Data", command=self.refresh_data, 
                  style='Large.TButton').grid(row=0, column=2, padx=5)
        
        # Style
        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 10), padding=6)
        
    def create_info_section(self, parent):
        """Create attendance information section"""
        # Today's stats
        stats_frame = ttk.LabelFrame(parent, text="Today's Statistics", padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.total_students_var = tk.StringVar(value="Total Students: 0")
        self.present_today_var = tk.StringVar(value="Present Today: 0")
        self.last_recognition_var = tk.StringVar(value="Last Recognition: None")
        
        ttk.Label(stats_frame, textvariable=self.total_students_var, 
                 font=('Arial', 11)).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.present_today_var, 
                 font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.last_recognition_var, 
                 font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W)
        
        # Recent attendance list
        list_frame = ttk.LabelFrame(parent, text="Today's Attendance", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Treeview for attendance list
        columns = ('Roll', 'Name', 'Time')
        self.attendance_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.attendance_tree.heading('Roll', text='Roll No.')
        self.attendance_tree.heading('Name', text='Name')
        self.attendance_tree.heading('Time', text='Time')
        
        # Configure column widths
        self.attendance_tree.column('Roll', width=80)
        self.attendance_tree.column('Name', width=150)
        self.attendance_tree.column('Time', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        self.attendance_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # Update initial stats
        self.update_stats()
        self.refresh_attendance_list()
        
    def load_encodings(self):
        """Load face encodings and student data"""
        try:
            # Load students data
            with open('json_data/students.json', 'r') as f:
                self.students_data = json.load(f)
            
            # Load encodings
            with open('json_data/encodings.json', 'r') as f:
                encodings_data = json.load(f)
            
            # Prepare arrays for face recognition
            self.known_encodings = []
            self.known_names = []
            self.known_rolls = []
            
            for roll_number, encodings_list in encodings_data.items():
                if roll_number in self.students_data:
                    student_info = self.students_data[roll_number]
                    student_name = student_info['name']
                    student_role = student_info.get('role', 'Student')
                    
                    for encoding in encodings_list:
                        self.known_encodings.append(np.array(encoding))
                        self.known_names.append(f"{student_name} ({student_role})")
                        self.known_rolls.append(roll_number)
            
            print(f"Loaded {len(self.known_encodings)} face encodings for {len(self.students_data)} students")
            
            if not FACE_RECOGNITION_AVAILABLE:
                print("⚠️  Running in demo mode - face recognition will be simulated")
            
        except FileNotFoundError as e:
            messagebox.showerror("Error", 
                               f"Required data files not found: {str(e)}\n"
                               "Please register students and train the model first.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load encodings: {str(e)}")
    
    def load_today_attendance(self):
        """Load today's attendance data"""
        today = date.today().strftime("%Y-%m-%d")
        attendance_file = f"attendance/{today}.json"
        
        try:
            with open(attendance_file, 'r') as f:
                self.today_attendance = json.load(f)
        except FileNotFoundError:
            self.today_attendance = {}
        except Exception as e:
            print(f"Error loading attendance: {e}")
            self.today_attendance = {}
    
    def save_attendance(self, roll_number, student_name):
        """Save attendance for a student"""
        today = date.today().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Create attendance directory if it doesn't exist
        os.makedirs("attendance", exist_ok=True)
        
        attendance_file = f"attendance/{today}.json"
        
        # Add to today's attendance
        self.today_attendance[roll_number] = {
            "name": student_name,
            "time": current_time,
            "date": today
        }
        
        # Save to file
        try:
            with open(attendance_file, 'w') as f:
                json.dump(self.today_attendance, f, indent=2)
            
            print(f"Attendance saved for {student_name} ({roll_number}) at {current_time}")
            return True
            
        except Exception as e:
            print(f"Error saving attendance: {e}")
            return False
    
    def load_recognition_settings(self):
        """Load face recognition settings from config file"""
        try:
            with open('json_data/recognition_config.json', 'r') as f:
                settings = json.load(f)
            
            self.recognition_threshold = settings.get('recognition_threshold', 0.4)
            self.min_face_confidence = settings.get('min_face_confidence', 0.7)
            self.face_detection_model = settings.get('face_detection_model', 'hog')
            
            print(f"✅ Loaded recognition settings: tolerance={self.recognition_threshold}, confidence={self.min_face_confidence}, model={self.face_detection_model}")
            
        except FileNotFoundError:
            # Use default settings
            self.recognition_threshold = 0.4
            self.min_face_confidence = 0.7
            self.face_detection_model = 'hog'
            print("📝 Using default recognition settings")
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Use default settings
            self.recognition_threshold = 0.4
            self.min_face_confidence = 0.7
            self.face_detection_model = 'hog'
    
    def start_recognition(self):
        """Start face recognition"""
        if len(self.known_encodings) == 0:
            messagebox.showerror("Error", "No trained data found. Please train the model first.")
            return
        
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Failed to open camera")
                return
            
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
            self.status_var.set("Recognition started - Show your face to camera")
            
            # Start recognition in separate thread
            thread = threading.Thread(target=self.recognition_loop)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recognition: {str(e)}")
    
    def recognition_loop(self):
        """Main recognition loop"""
        demo_counter = 0  # Counter for demo mode
        
        while self.is_running and self.camera is not None:
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            if not FACE_RECOGNITION_AVAILABLE:
                # Demo mode - simulate recognition every 5 seconds
                demo_counter += 1
                if demo_counter % 150 == 0:  # Every ~5 seconds at 30fps
                    self.simulate_recognition()
                
                # Just display the frame without face detection
                self.display_frame_with_recognition(frame)
                continue
            
            # Real face recognition mode
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in current frame using calibrated settings
            self.face_locations = face_recognition.face_locations(rgb_small_frame, model=self.face_detection_model)
            
            # Only process if faces are found
            if len(self.face_locations) > 0:
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
            else:
                self.face_encodings = []
            
            self.face_names = []
            
            for face_encoding in self.face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, 
                                                       tolerance=self.recognition_threshold)
                name = "Unknown"
                roll = "Unknown"
                
                # Use the known face with the smallest distance
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    # Additional validation: check if the best match is good enough
                    if matches[best_match_index] and face_distances[best_match_index] < self.recognition_threshold:
                        # Extract name without role for matching
                        full_name = self.known_names[best_match_index]
                        if "(" in full_name and ")" in full_name:
                            name = full_name.split(" (")[0]  # Get name without role
                        else:
                            name = full_name
                        roll = self.known_rolls[best_match_index]
                        
                        # Double-check: ensure this is a confident match
                        confidence = 1.0 - face_distances[best_match_index]
                        if confidence < self.min_face_confidence:
                            name = "Unknown (Low Confidence)"
                            roll = "Unknown"
                        else:
                            # Mark attendance if not already marked today
                            if roll not in self.today_attendance:
                                if self.save_attendance(roll, name):
                                    self.status_var.set(f"✅ Attendance marked for {name} ({roll}) - Confidence: {confidence:.2f}")
                                    self.last_recognition_var.set(f"Last Recognition: {name}")
                                    # Update GUI in main thread
                                    self.root.after(0, self.refresh_attendance_list)
                                    self.root.after(0, self.update_stats)
                                else:
                                    self.status_var.set(f"Failed to save attendance for {name}")
                            else:
                                self.status_var.set(f"Already marked: {name} ({roll})")
                                self.last_recognition_var.set(f"Last Recognition: {name} (Already marked)")
                    else:
                        name = "Unknown (Poor Match)"
                        roll = "Unknown"
                
                self.face_names.append(f"{name} ({roll})")
            
            # Display the results
            self.display_frame_with_recognition(frame)
    
    def simulate_recognition(self):
        """Simulate face recognition for demo purposes"""
        if not self.students_data:
            return
        
        # Pick a random student from the registered students
        import random
        roll_number = random.choice(list(self.students_data.keys()))
        student_name = self.students_data[roll_number]['name']
        
        # Check if already marked today
        if roll_number not in self.today_attendance:
            if self.save_attendance(roll_number, student_name):
                self.status_var.set(f"[DEMO] Attendance marked for {student_name} ({roll_number})")
                self.last_recognition_var.set(f"Last Recognition: {student_name} (Demo)")
                # Update GUI in main thread
                self.root.after(0, self.refresh_attendance_list)
                self.root.after(0, self.update_stats)
            else:
                self.status_var.set(f"[DEMO] Failed to save attendance for {student_name}")
        else:
            self.status_var.set(f"[DEMO] Already marked: {student_name} ({roll_number})")
            self.last_recognition_var.set(f"Last Recognition: {student_name} (Already marked)")
    
    def display_frame_with_recognition(self, frame):
        """Display frame with recognition results"""
        try:
            # Scale back up face locations
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Choose color based on recognition
                if "Unknown" in name:
                    color = (0, 0, 255)  # Red for unknown
                elif "Already marked" in self.status_var.get():
                    color = (255, 165, 0)  # Orange for already marked
                else:
                    color = (0, 255, 0)  # Green for newly recognized
                
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
            # Convert to display format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (640, 480))
            
            # Convert to PhotoImage using image manager
            pil_image = Image.fromarray(frame_resized)
            photo = image_manager.create_photo_image(pil_image)
            
            if photo:
                # Update label in main thread
                self.root.after(0, self.update_camera_display, photo)
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
            # Continue without crashing
    
    def update_camera_display(self, photo):
        """Update camera display with new frame"""
        try:
            if self.camera_label and photo:
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo  # Keep a reference
        except tk.TclError:
            # Handle case where window was closed
            pass
    
    def stop_recognition(self):
        """Stop face recognition"""
        self.is_running = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        # Clear camera display
        self.camera_label.configure(image='', text="Recognition Stopped")
        self.status_var.set("Recognition stopped")
    
    def refresh_data(self):
        """Refresh encodings and attendance data"""
        self.load_encodings()
        self.load_today_attendance()
        self.update_stats()
        self.refresh_attendance_list()
        self.status_var.set("Data refreshed successfully")
    
    def update_stats(self):
        """Update statistics display"""
        total_students = len(self.students_data)
        present_today = len(self.today_attendance)
        
        self.total_students_var.set(f"Total Students: {total_students}")
        self.present_today_var.set(f"Present Today: {present_today}")
    
    def refresh_attendance_list(self):
        """Refresh the attendance list display"""
        # Clear existing items
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        # Add today's attendance
        for roll, info in self.today_attendance.items():
            self.attendance_tree.insert('', tk.END, values=(roll, info['name'], info['time']))
    
    def on_closing(self):
        """Handle window closing properly"""
        try:
            self.stop_recognition()
            if self.camera:
                self.camera.release()
            image_manager.clear_all()  # Clear image references
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.root.destroy()

def main():
    root = tk.Tk()
    app = AttendanceRecognition(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
