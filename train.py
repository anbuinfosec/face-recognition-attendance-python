#!/usr/bin/env python3
"""
Face Recognition Model Training Module
Processes student images and creates face encodings
"""

import os
import json
import cv2
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Try to import face_recognition, handle gracefully if not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️  face_recognition not available - training will be simulated")

class ModelTrainer:
    def __init__(self, root=None):
        self.root = root
        self.progress_var = None
        self.status_var = None
        self.progress_bar = None
        
        if root:
            self.setup_gui()
    
    def setup_gui(self):
        """Setup training progress GUI"""
        self.root.title("Model Training")
        self.root.geometry("500x300")
        self.root.configure(bg='#ecf0f1')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Face Recognition Model Training", 
                               font=('Arial', 16, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to start training...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               font=('Arial', 11), foreground='#7f8c8d')
        status_label.grid(row=1, column=0, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=2, column=0, pady=20, sticky=(tk.W, tk.E))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, pady=20)
        
        self.train_btn = ttk.Button(btn_frame, text="Start Training", 
                                  command=self.start_training_thread, 
                                  style='Large.TButton')
        self.train_btn.grid(row=0, column=0, padx=5)
        
        ttk.Button(btn_frame, text="Close", command=self.root.destroy, 
                  style='Large.TButton').grid(row=0, column=1, padx=5)
        
        # Style
        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 11), padding=8)
        
        # Log text widget
        log_frame = ttk.LabelFrame(main_frame, text="Training Log", padding="10")
        log_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=8, width=60, font=('Courier', 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
    
    def log_message(self, message):
        """Add message to log"""
        if self.log_text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.root.update()
    
    def update_status(self, message):
        """Update status label"""
        if self.status_var:
            self.status_var.set(message)
            self.root.update()
    
    def update_progress(self, value):
        """Update progress bar"""
        if self.progress_var:
            self.progress_var.set(value)
            self.root.update()
    
    def start_training_thread(self):
        """Start training in a separate thread"""
        self.train_btn.config(state='disabled')
        thread = threading.Thread(target=self.train_model)
        thread.daemon = True
        thread.start()
    
    def train_model(self):
        """Train the face recognition model"""
        try:
            self.log_message("Starting face recognition model training...")
            self.update_status("Initializing training process...")
            
            # Check if face_recognition is available
            if not FACE_RECOGNITION_AVAILABLE:
                self.log_message("WARNING: face_recognition library not available!")
                self.log_message("Creating dummy encodings for demonstration...")
                self.create_dummy_encodings()
                return
            
            # Check if dataset directory exists
            if not os.path.exists('dataset'):
                self.log_message("ERROR: Dataset directory not found!")
                messagebox.showerror("Error", "Dataset directory not found. Please register students first.")
                return
            
            # Load students data
            try:
                with open('json_data/students.json', 'r') as f:
                    students_data = json.load(f)
            except FileNotFoundError:
                self.log_message("ERROR: No students data found!")
                messagebox.showerror("Error", "No students data found. Please register students first.")
                return
            
            if not students_data:
                self.log_message("ERROR: No students registered!")
                messagebox.showerror("Error", "No students registered. Please register students first.")
                return
            
            self.log_message(f"Found {len(students_data)} registered students")
            
            # Initialize encodings dictionary
            encodings_data = {}
            total_students = len(students_data)
            processed_students = 0
            
            # Process each student
            for roll_number, student_info in students_data.items():
                student_name = student_info['name']
                
                # Check for role-based directory structure first
                role = student_info.get('role', 'student').lower()
                role_based_dir = f"dataset/{role}/{roll_number}"
                legacy_dir = f"dataset/{roll_number}"
                
                # Determine which directory to use
                if os.path.exists(role_based_dir):
                    student_dir = role_based_dir
                    self.log_message(f"Using role-based directory: {role_based_dir}")
                elif os.path.exists(legacy_dir):
                    student_dir = legacy_dir
                    self.log_message(f"Using legacy directory: {legacy_dir}")
                else:
                    self.log_message(f"WARNING: No directory found for {student_name}")
                    continue
                
                self.log_message(f"Processing {role.title()}: {student_name} ({roll_number})")
                self.update_status(f"Processing {student_name}...")
                
                # Get all image files
                image_files = [f for f in os.listdir(student_dir) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                if not image_files:
                    self.log_message(f"WARNING: No images found for {student_name}")
                    continue
                
                self.log_message(f"Found {len(image_files)} images for {student_name}")
                
                # Process images and extract encodings
                student_encodings = []
                
                for i, image_file in enumerate(image_files):
                    image_path = os.path.join(student_dir, image_file)
                    
                    try:
                        # Load image
                        image = face_recognition.load_image_file(image_path)
                        
                        # Find face locations
                        face_locations = face_recognition.face_locations(image)
                        
                        if len(face_locations) == 0:
                            self.log_message(f"WARNING: No face found in {image_file}")
                            continue
                        
                        if len(face_locations) > 1:
                            self.log_message(f"WARNING: Multiple faces in {image_file}, using first one")
                        
                        # Get face encodings
                        face_encodings = face_recognition.face_encodings(image, face_locations)
                        
                        if face_encodings:
                            student_encodings.append(face_encodings[0].tolist())
                            self.log_message(f"Successfully processed {image_file}")
                        
                    except Exception as e:
                        self.log_message(f"ERROR processing {image_file}: {str(e)}")
                        continue
                
                if student_encodings:
                    encodings_data[roll_number] = student_encodings
                    self.log_message(f"Generated {len(student_encodings)} encodings for {student_name}")
                else:
                    self.log_message(f"ERROR: No valid encodings generated for {student_name}")
                
                # Update progress
                processed_students += 1
                progress = (processed_students / total_students) * 100
                self.update_progress(progress)
            
            # Save encodings to JSON file
            self.log_message("Saving encodings to file...")
            self.update_status("Saving encodings...")
            
            with open('json_data/encodings.json', 'w') as f:
                json.dump(encodings_data, f, indent=2)
            
            # Add metadata
            metadata = {
                'total_students': len(encodings_data),
                'training_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_encodings': sum(len(encodings) for encodings in encodings_data.values())
            }
            
            # Save metadata
            with open('json_data/model_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.log_message(f"Training completed successfully!")
            self.log_message(f"Total students trained: {len(encodings_data)}")
            self.log_message(f"Total encodings generated: {metadata['total_encodings']}")
            
            self.update_status("Training completed successfully!")
            self.update_progress(100)
            
            if self.root:
                messagebox.showinfo("Success", 
                                  f"Model training completed!\n"
                                  f"Students trained: {len(encodings_data)}\n"
                                  f"Encodings generated: {metadata['total_encodings']}")
            
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            self.log_message(f"ERROR: {error_msg}")
            self.update_status("Training failed!")
            
            if self.root:
                messagebox.showerror("Error", error_msg)
        
        finally:
            if self.train_btn:
                self.train_btn.config(state='normal')
    
    def create_dummy_encodings(self):
        """Create dummy face encodings for demonstration purposes"""
        try:
            # Load students data
            with open('json_data/students.json', 'r') as f:
                students_data = json.load(f)
            
            if not students_data:
                self.log_message("ERROR: No students registered!")
                messagebox.showerror("Error", "No students registered. Please register students first.")
                return
            
            self.log_message(f"Creating dummy encodings for {len(students_data)} students...")
            
            # Create dummy encodings
            encodings_data = {}
            total_students = len(students_data)
            processed_students = 0
            
            for roll_number, student_info in students_data.items():
                student_name = student_info['name']
                self.log_message(f"Creating dummy encoding for: {student_name} ({roll_number})")
                
                # Create random 128-dimensional encodings (dummy data)
                dummy_encodings = []
                for i in range(5):  # Create 5 dummy encodings per student
                    dummy_encoding = np.random.random(128).tolist()
                    dummy_encodings.append(dummy_encoding)
                
                encodings_data[roll_number] = dummy_encodings
                
                # Update progress
                processed_students += 1
                progress = (processed_students / total_students) * 100
                self.update_progress(progress)
                self.update_status(f"Processing {student_name}...")
            
            # Save encodings
            with open('json_data/encodings.json', 'w') as f:
                json.dump(encodings_data, f, indent=2)
            
            # Save metadata
            metadata = {
                'total_students': len(encodings_data),
                'training_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_encodings': sum(len(encodings) for encodings in encodings_data.values()),
                'training_type': 'dummy_demo'
            }
            
            with open('json_data/model_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.log_message("Dummy training completed successfully!")
            self.log_message("NOTE: This is demo data - install face_recognition for real training")
            self.update_status("Demo training completed!")
            self.update_progress(100)
            
            if self.root:
                messagebox.showinfo("Demo Training Complete", 
                                  f"Demo training completed!\n"
                                  f"Students: {len(encodings_data)}\n"
                                  f"Dummy encodings: {metadata['total_encodings']}\n\n"
                                  f"Install face_recognition library for real training.")
                                  
        except Exception as e:
            error_msg = f"Demo training failed: {str(e)}"
            self.log_message(f"ERROR: {error_msg}")
            self.update_status("Demo training failed!")
            
            if self.root:
                messagebox.showerror("Error", error_msg)

def main():
    """Main function for GUI mode"""
    root = tk.Tk()
    trainer = ModelTrainer(root)
    root.mainloop()

def train_without_gui():
    """Train model without GUI (for command line use)"""
    trainer = ModelTrainer()
    trainer.train_model()

if __name__ == "__main__":
    main()
