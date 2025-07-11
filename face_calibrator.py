#!/usr/bin/env python3
"""
Face Recognition Calibration Tool
Helps tune face recognition parameters for better accuracy
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import json
import numpy as np
from PIL import Image, ImageTk
import face_recognition
import os

class FaceRecognitionCalibrator:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Calibrator")
        self.root.geometry("900x700")
        
        # Variables
        self.camera = None
        self.is_running = False
        self.current_frame = None
        self.results_text = None  # Initialize results_text first
        
        # Calibration parameters
        self.tolerance = tk.DoubleVar(value=0.4)
        self.confidence_threshold = tk.DoubleVar(value=0.7)
        self.face_detection_model = tk.StringVar(value="hog")
        
        # Load test data
        self.load_test_encodings()
        
        # Create GUI
        self.create_widgets()
    
    def create_widgets(self):
        """Create calibration interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        ttk.Label(main_frame, text="Face Recognition Calibration Tool", 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Left panel - Camera
        camera_frame = ttk.LabelFrame(main_frame, text="Live Camera Feed", padding="10")
        camera_frame.grid(row=1, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.camera_label = ttk.Label(camera_frame, text="Camera Feed", width=50, relief='sunken')
        self.camera_label.grid(row=0, column=0, pady=10)
        
        # Camera controls
        cam_btn_frame = ttk.Frame(camera_frame)
        cam_btn_frame.grid(row=1, column=0, pady=10)
        
        self.start_btn = ttk.Button(cam_btn_frame, text="Start Camera", command=self.start_camera)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(cam_btn_frame, text="Stop Camera", command=self.stop_camera, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Test button
        self.test_btn = ttk.Button(cam_btn_frame, text="Test Recognition", command=self.test_recognition, state='disabled')
        self.test_btn.grid(row=0, column=2, padx=5)
        
        # Right panel - Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Calibration Settings", padding="10")
        settings_frame.grid(row=1, column=1, padx=(10, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tolerance setting
        ttk.Label(settings_frame, text="Face Matching Tolerance:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tolerance_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.tolerance, orient='horizontal')
        tolerance_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(settings_frame, textvariable=self.tolerance).grid(row=0, column=2, pady=5)
        
        # Confidence threshold
        ttk.Label(settings_frame, text="Confidence Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
        confidence_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.confidence_threshold, orient='horizontal')
        confidence_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(settings_frame, textvariable=self.confidence_threshold).grid(row=1, column=2, pady=5)
        
        # Face detection model
        ttk.Label(settings_frame, text="Face Detection Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_combo = ttk.Combobox(settings_frame, textvariable=self.face_detection_model, 
                                  values=['hog', 'cnn'], state='readonly')
        model_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Apply settings button
        ttk.Button(settings_frame, text="Apply Settings", command=self.apply_settings).grid(row=3, column=0, columnspan=3, pady=20)
        
        # Results area
        results_frame = ttk.LabelFrame(settings_frame, text="Test Results", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.results_text = tk.Text(results_frame, height=10, width=40, font=('Courier', 9))
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Configure weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        camera_frame.rowconfigure(0, weight=1)
        settings_frame.rowconfigure(4, weight=1)
    
    def load_test_encodings(self):
        """Load existing face encodings for testing"""
        try:
            with open('json_data/students.json', 'r') as f:
                self.students_data = json.load(f)
            
            with open('json_data/encodings.json', 'r') as f:
                encodings_data = json.load(f)
            
            self.known_encodings = []
            self.known_names = []
            self.known_rolls = []
            
            for roll_number, encodings_list in encodings_data.items():
                if roll_number in self.students_data:
                    student_info = self.students_data[roll_number]
                    student_name = student_info['name']
                    
                    for encoding in encodings_list:
                        self.known_encodings.append(np.array(encoding))
                        self.known_names.append(student_name)
                        self.known_rolls.append(roll_number)
            
            self.log_result(f"Loaded {len(self.known_encodings)} face encodings for testing")
            
        except Exception as e:
            self.log_result(f"Error loading encodings: {e}")
            self.known_encodings = []
            self.known_names = []
            self.known_rolls = []
    
    def log_result(self, message):
        """Add message to results log"""
        try:
            if self.results_text and hasattr(self.results_text, 'insert'):
                self.results_text.insert(tk.END, f"{message}\n")
                self.results_text.see(tk.END)
                self.results_text.update()
            else:
                print(f"Calibrator: {message}")  # Fallback to console
        except Exception as e:
            print(f"Calibrator: {message}")  # Fallback to console
    
    def start_camera(self):
        """Start camera for testing"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Failed to open camera")
                return
            
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.test_btn.config(state='normal')
            
            self.update_camera_feed()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {e}")
    
    def update_camera_feed(self):
        """Update camera feed"""
        if self.is_running and self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.current_frame = frame
                
                # Convert and display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (480, 360))
                
                pil_image = Image.fromarray(frame_resized)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
            
            self.root.after(30, self.update_camera_feed)
    
    def test_recognition(self):
        """Test face recognition with current settings"""
        if not self.current_frame is not None:
            messagebox.showerror("Error", "No camera frame available")
            return
        
        if not self.known_encodings:
            messagebox.showerror("Error", "No face encodings loaded for testing")
            return
        
        try:
            # Find faces
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model=self.face_detection_model.get())
            
            self.log_result(f"\n--- Test Results (Tolerance: {self.tolerance.get():.2f}, Confidence: {self.confidence_threshold.get():.2f}) ---")
            self.log_result(f"Faces detected: {len(face_locations)}")
            
            if len(face_locations) == 0:
                self.log_result("No faces detected in current frame")
                return
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for i, face_encoding in enumerate(face_encodings):
                # Test recognition
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, 
                                                       tolerance=self.tolerance.get())
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    confidence = 1.0 - face_distances[best_match_index]
                    
                    if matches[best_match_index] and confidence >= self.confidence_threshold.get():
                        name = self.known_names[best_match_index]
                        roll = self.known_rolls[best_match_index]
                        self.log_result(f"Face {i+1}: ✅ RECOGNIZED - {name} ({roll}) - Confidence: {confidence:.3f}")
                    else:
                        self.log_result(f"Face {i+1}: ❌ NOT RECOGNIZED - Best confidence: {confidence:.3f}")
                        if len(face_distances) > 0:
                            best_name = self.known_names[best_match_index]
                            self.log_result(f"          Closest match: {best_name} (distance: {face_distances[best_match_index]:.3f})")
                else:
                    self.log_result(f"Face {i+1}: ❌ NO ENCODINGS TO COMPARE")
            
        except Exception as e:
            self.log_result(f"Error during recognition test: {e}")
    
    def apply_settings(self):
        """Apply current settings to the main recognition system"""
        try:
            # Update recognize.py with new settings
            tolerance = self.tolerance.get()
            confidence = self.confidence_threshold.get()
            
            self.log_result(f"\n--- Applying Settings ---")
            self.log_result(f"Tolerance: {tolerance:.2f}")
            self.log_result(f"Confidence: {confidence:.2f}")
            self.log_result(f"Model: {self.face_detection_model.get()}")
            
            # Save settings to a config file
            settings = {
                "recognition_threshold": tolerance,
                "min_face_confidence": confidence,
                "face_detection_model": self.face_detection_model.get()
            }
            
            with open('json_data/recognition_config.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.log_result("✅ Settings saved to json_data/recognition_config.json")
            self.log_result("Restart the recognition module to apply changes")
            
            messagebox.showinfo("Success", "Settings applied successfully!\nRestart the recognition module to use new settings.")
            
        except Exception as e:
            self.log_result(f"Error applying settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def stop_camera(self):
        """Stop camera"""
        self.is_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.test_btn.config(state='disabled')
        
        self.camera_label.configure(image='', text="Camera Stopped")

def main():
    root = tk.Tk()
    app = FaceRecognitionCalibrator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
