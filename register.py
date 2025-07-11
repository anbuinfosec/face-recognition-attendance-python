#!/usr/bin/env python3
"""
Student Registration Module
Handles student registration with face capture and data storage
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
import threading
from image_manager import image_manager

class StudentRegistration:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Registration")
        self.root.geometry("900x700")
        self.root.configure(bg='#ecf0f1')
        
        # Variables
        self.camera = None
        self.is_capturing = False
        self.captured_images = []
        self.preview_label = None
        self.auto_capture_active = False
        self.capture_count = 0
        self.max_images = 20  # Increased to 20 images
        self.capture_delay = 400  # Reduced delay for faster capture
        self.auto_workflow_active = False
        
        # Bind cleanup to window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        self.create_widgets(main_frame)
        
    def create_widgets(self, parent):
        """Create and arrange widgets"""
        # Title
        title_label = ttk.Label(parent, text="Student Registration", 
                               font=('Arial', 20, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left frame for form
        form_frame = ttk.LabelFrame(parent, text="Student Information", padding="15")
        form_frame.grid(row=1, column=0, padx=(0, 10), pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right frame for camera
        camera_frame = ttk.LabelFrame(parent, text="Face Capture", padding="15")
        camera_frame.grid(row=1, column=1, padx=(10, 0), pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Form fields
        self.create_form_fields(form_frame)
        
        # Camera section
        self.create_camera_section(camera_frame)
        
        # Configure column weights
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)
        
    def create_form_fields(self, parent):
        """Create form input fields"""
        # Name field
        ttk.Label(parent, text="Full Name:", font=('Arial', 12)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(parent, textvariable=self.name_var, font=('Arial', 12), width=25)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Roll Number field
        ttk.Label(parent, text="Roll Number:", font=('Arial', 12)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.roll_var = tk.StringVar()
        roll_entry = ttk.Entry(parent, textvariable=self.roll_var, font=('Arial', 12), width=25)
        roll_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Department field
        ttk.Label(parent, text="Department:", font=('Arial', 12)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dept_var = tk.StringVar()
        dept_combo = ttk.Combobox(parent, textvariable=self.dept_var, font=('Arial', 12), width=22)
        dept_combo['values'] = ('CSE', 'ECE', 'EEE', 'MECH', 'CIVIL', 'IT', 'OTHER')
        dept_combo.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Role field (NEW)
        ttk.Label(parent, text="Role:", font=('Arial', 12)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value="Student")
        role_combo = ttk.Combobox(parent, textvariable=self.role_var, font=('Arial', 12), width=22)
        role_combo['values'] = ('Student', 'Teacher', 'Staff', 'Admin')
        role_combo.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to capture images")
        status_label = ttk.Label(parent, textvariable=self.status_var, 
                               font=('Arial', 10), foreground='#27ae60')
        status_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Images captured label
        self.images_var = tk.StringVar(value="Images captured: 0/20")
        images_label = ttk.Label(parent, textvariable=self.images_var, font=('Arial', 10))
        images_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Automatic workflow progress
        self.workflow_var = tk.StringVar(value="Ready for automatic registration")
        workflow_label = ttk.Label(parent, textvariable=self.workflow_var, font=('Arial', 10), 
                                  foreground='#3498db')
        workflow_label.grid(row=6, column=0, columnspan=2, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        self.register_btn = ttk.Button(btn_frame, text="🚀 Auto Register & Train", 
                                     command=self.start_auto_registration, style='Large.TButton')
        self.register_btn.grid(row=0, column=0, padx=5)
        
        self.manual_register_btn = ttk.Button(btn_frame, text="📝 Manual Registration", 
                                            command=self.register_student, style='Large.TButton')
        self.manual_register_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Clear Form", command=self.clear_form, 
                  style='Large.TButton').grid(row=0, column=2, padx=5)
        
        # Style
        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 11), padding=8)
        
    def create_camera_section(self, parent):
        """Create camera preview and capture controls"""
        # Camera preview
        self.preview_label = ttk.Label(parent, text="Camera will start automatically during registration", 
                                     font=('Arial', 12), relief='sunken', width=40)
        self.preview_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Workflow status
        self.camera_status_var = tk.StringVar(value="Ready - Click 'Auto Register & Train' to begin")
        status_label = ttk.Label(parent, textvariable=self.camera_status_var, 
                               font=('Arial', 11, 'bold'), foreground='#27ae60')
        status_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Manual controls (hidden by default)
        self.manual_controls_frame = ttk.Frame(parent)
        
        self.start_btn = ttk.Button(self.manual_controls_frame, text="Start Camera", 
                                  command=self.start_camera)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.capture_btn = ttk.Button(self.manual_controls_frame, text="Auto Capture (20 Images)", 
                                    command=self.start_auto_capture, state='disabled')
        self.capture_btn.grid(row=0, column=1, padx=5)
        
        self.manual_capture_btn = ttk.Button(self.manual_controls_frame, text="Manual Capture", 
                                           command=self.manual_capture, state='disabled')
        self.manual_capture_btn.grid(row=0, column=2, padx=5)
        
        self.stop_btn = ttk.Button(self.manual_controls_frame, text="Stop Camera", 
                                 command=self.stop_camera, state='disabled')
        self.stop_btn.grid(row=0, column=3, padx=5)
        
        # Show manual controls button
        self.show_manual_btn = ttk.Button(parent, text="🔧 Show Manual Controls", 
                                        command=self.toggle_manual_controls)
        self.show_manual_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
    def start_camera(self):
        """Start camera preview"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Failed to open camera")
                return
                
            self.is_capturing = True
            self.start_btn.config(state='disabled')
            self.capture_btn.config(state='normal')
            self.manual_capture_btn.config(state='normal')
            self.stop_btn.config(state='normal')
            
            self.update_camera_preview()
            self.status_var.set("Camera started - Ready to capture")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
    
    def update_camera_preview(self):
        """Update camera preview continuously"""
        if self.is_capturing and self.camera is not None:
            try:
                ret, frame = self.camera.read()
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Resize for preview
                    frame_resized = cv2.resize(frame_rgb, (400, 300))
                    
                    # Convert to PIL Image and then to PhotoImage using image manager
                    pil_image = Image.fromarray(frame_resized)
                    photo = image_manager.create_photo_image(pil_image)
                    
                    # Update label
                    if self.preview_label and photo:
                        self.preview_label.configure(image=photo)
                        self.preview_label.image = photo  # Keep a reference
                        
                # Schedule next update
                self.root.after(10, self.update_camera_preview)
            except Exception as e:
                print(f"Error updating camera preview: {e}")
                # Continue without crashing
    
    def create_role_based_directory(self, roll_number, role):
        """Create role-based directory structure for student images"""
        # Create base dataset directory
        base_dir = "dataset"
        os.makedirs(base_dir, exist_ok=True)
        
        # Create role-based subdirectory
        role_dir = os.path.join(base_dir, role.lower())
        os.makedirs(role_dir, exist_ok=True)
        
        # Create student-specific directory
        student_dir = os.path.join(role_dir, roll_number)
        os.makedirs(student_dir, exist_ok=True)
        
        return student_dir
    
    def start_auto_capture(self):
        """Start automatic image capture"""
        if not self.camera or not self.is_capturing:
            messagebox.showerror("Error", "Camera not started")
            return
            
        if not self.name_var.get() or not self.roll_var.get() or not self.role_var.get():
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        # Reset capture variables
        self.auto_capture_active = True
        self.capture_count = 0
        self.captured_images = []
        
        # Disable capture button during auto capture
        self.capture_btn.config(state='disabled', text="Capturing...")
        self.manual_capture_btn.config(state='disabled')
        
        self.status_var.set("Auto capture started - Please look at camera and change poses")
        
        # Start auto capture process
        self.auto_capture_next_image()
    
    def auto_capture_next_image(self):
        """Capture next image in auto capture sequence"""
        if not self.auto_capture_active or self.capture_count >= self.max_images:
            self.finish_auto_capture()
            return
        
        if not self.camera or not self.is_capturing:
            self.finish_auto_capture()
            return
        
        try:
            # Get current frame
            ret, frame = self.camera.read()
            if ret:
                # Create role-based directory
                roll_number = self.roll_var.get().strip()
                role = self.role_var.get().strip()
                student_dir = self.create_role_based_directory(roll_number, role)
                
                # Save image with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(student_dir, f"image_{self.capture_count + 1:02d}_{timestamp}.jpg")
                cv2.imwrite(image_path, frame)
                self.captured_images.append(image_path)
                
                # Update progress
                self.capture_count += 1
                self.images_var.set(f"Images captured: {self.capture_count}/{self.max_images}")
                self.status_var.set(f"Capturing image {self.capture_count}/{self.max_images}...")
                
                print(f"✅ Captured image {self.capture_count}: {image_path}")
                
                # Schedule next capture
                self.root.after(self.capture_delay, self.auto_capture_next_image)
            else:
                self.status_var.set("Failed to capture frame")
                self.finish_auto_capture()
                
        except Exception as e:
            print(f"Error during auto capture: {e}")
            self.status_var.set(f"Capture error: {str(e)}")
            self.finish_auto_capture()
    
    def finish_auto_capture(self):
        """Finish auto capture process"""
        self.auto_capture_active = False
        
        # Re-enable buttons
        if self.is_capturing:
            self.capture_btn.config(state='normal', text="Auto Capture (15 Images)")
            self.manual_capture_btn.config(state='normal')
        
        if self.capture_count >= self.max_images:
            self.status_var.set(f"Auto capture completed! {self.capture_count} images saved")
            messagebox.showinfo("Success", f"Auto capture completed!\n{self.capture_count} images captured successfully")
        else:
            self.status_var.set(f"Auto capture stopped. {self.capture_count} images captured")
    
    def manual_capture(self):
        """Manual single image capture"""
        if not self.camera or not self.is_capturing:
            messagebox.showerror("Error", "Camera not started")
            return
            
        if not self.name_var.get() or not self.roll_var.get() or not self.role_var.get():
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        if len(self.captured_images) >= self.max_images:
            messagebox.showwarning("Warning", f"Maximum {self.max_images} images already captured")
            return
        
        try:
            # Get current frame
            ret, frame = self.camera.read()
            if ret:
                # Create role-based directory
                roll_number = self.roll_var.get().strip()
                role = self.role_var.get().strip()
                student_dir = self.create_role_based_directory(roll_number, role)
                
                # Save image with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_count = len(self.captured_images) + 1
                image_path = os.path.join(student_dir, f"image_{image_count:02d}_{timestamp}.jpg")
                cv2.imwrite(image_path, frame)
                self.captured_images.append(image_path)
                
                # Update progress
                self.images_var.set(f"Images captured: {len(self.captured_images)}/{self.max_images}")
                self.status_var.set(f"Manual capture: {len(self.captured_images)} images saved")
                
                print(f"✅ Manual capture: {image_path}")
            else:
                messagebox.showerror("Error", "Failed to capture frame from camera")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture image: {str(e)}")
    
    def capture_images(self):
        """Legacy capture method - replaced by auto capture"""
        # This method is kept for compatibility but redirects to auto capture
        self.start_auto_capture()
    
    def stop_camera(self):
        """Stop camera and clean up"""
        # Stop auto capture if active
        self.auto_capture_active = False
        
        self.is_capturing = False
        if self.camera:
            self.camera.release()
            self.camera = None
            
        self.start_btn.config(state='normal')
        self.capture_btn.config(state='disabled', text="Auto Capture (15 Images)")
        self.manual_capture_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        
        # Clear preview
        self.preview_label.configure(image='', text="Camera Stopped")
        self.status_var.set("Camera stopped")
    
    def register_student(self):
        """Register student with captured data"""
        # Validate input
        if not self.name_var.get() or not self.roll_var.get() or not self.dept_var.get() or not self.role_var.get():
            messagebox.showerror("Error", "Please fill in all required fields")
            return
            
        if len(self.captured_images) < 5:
            messagebox.showerror("Error", "Please capture at least 5 images before registration")
            return
        
        try:
            # Load existing students data
            try:
                with open('json_data/students.json', 'r') as f:
                    students_data = json.load(f)
            except FileNotFoundError:
                students_data = {}
            
            # Check if roll number already exists
            roll_number = self.roll_var.get().strip()
            if roll_number in students_data:
                messagebox.showerror("Error", "Student with this roll number already exists")
                return
            
            # Add new student with role information
            students_data[roll_number] = {
                "name": self.name_var.get().strip(),
                "roll": roll_number,
                "department": self.dept_var.get().strip(),
                "role": self.role_var.get().strip(),
                "registered_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "images_count": len(self.captured_images),
                "image_folder": f"dataset/{self.role_var.get().strip().lower()}/{roll_number}"
            }
            
            # Save updated data
            with open('json_data/students.json', 'w') as f:
                json.dump(students_data, f, indent=2)
            
            # Show success message with role information
            role = self.role_var.get().strip()
            messagebox.showinfo("Success", 
                              f"{role} {self.name_var.get()} registered successfully!\n"
                              f"Roll: {roll_number}\n"
                              f"Department: {self.dept_var.get()}\n"
                              f"Images saved: {len(self.captured_images)}\n"
                              f"Folder: dataset/{role.lower()}/{roll_number}")
            
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register student: {str(e)}")
    
    def clear_form(self):
        """Clear all form fields"""
        self.stop_camera()
        self.name_var.set("")
        self.roll_var.set("")
        self.dept_var.set("")
        self.role_var.set("Student")  # Reset to default
        self.captured_images = []
        self.capture_count = 0
        self.auto_capture_active = False
        self.images_var.set("Images captured: 0/15")
        self.status_var.set("Form cleared - Ready for new registration")
    
    def on_closing(self):
        """Handle window closing"""
        try:
            self.stop_camera()
            image_manager.clear_all()  # Clear image references
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.root.destroy()
    
    def toggle_manual_controls(self):
        """Toggle manual controls visibility"""
        if self.manual_controls_frame.winfo_viewable():
            self.manual_controls_frame.grid_remove()
            self.show_manual_btn.config(text="🔧 Show Manual Controls")
        else:
            self.manual_controls_frame.grid(row=3, column=0, columnspan=2, pady=10)
            self.show_manual_btn.config(text="🔧 Hide Manual Controls")
    
    def start_auto_registration(self):
        """Start the complete automatic registration workflow"""
        # Validate input first
        if not self.name_var.get() or not self.roll_var.get() or not self.dept_var.get() or not self.role_var.get():
            messagebox.showerror("Error", "Please fill in all required fields before starting automatic registration")
            return
        
        # Check if student already exists
        try:
            with open('json_data/students.json', 'r') as f:
                students_data = json.load(f)
            
            roll_number = self.roll_var.get().strip()
            if roll_number in students_data:
                messagebox.showerror("Error", "Student with this roll number already exists")
                return
        except FileNotFoundError:
            pass  # File doesn't exist yet, which is fine
        
        # Start the automatic workflow
        self.auto_workflow_active = True
        self.workflow_var.set("🚀 Starting automatic registration workflow...")
        
        # Disable form during process
        self.disable_form()
        
        # Start camera automatically
        self.auto_start_camera()
    
    def auto_start_camera(self):
        """Automatically start camera for the workflow"""
        try:
            self.workflow_var.set("📷 Starting camera...")
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Failed to open camera")
                self.auto_workflow_active = False
                self.enable_form()
                return
            
            self.is_capturing = True
            self.camera_status_var.set("📹 Camera started - Preparing for capture...")
            
            self.update_camera_preview()
            
            # Wait 2 seconds for camera to stabilize, then start auto capture
            self.root.after(2000, self.auto_start_capture)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
            self.auto_workflow_active = False
            self.enable_form()
    
    def auto_start_capture(self):
        """Automatically start the capture process"""
        if not self.auto_workflow_active:
            return
        
        self.workflow_var.set("📸 Starting automatic image capture (20 images)...")
        self.camera_status_var.set("📸 Capturing images - Please look at camera and change poses")
        
        # Reset capture variables
        self.auto_capture_active = True
        self.capture_count = 0
        self.captured_images = []
        
        # Start auto capture process
        self.auto_capture_next_image()
    
    def disable_form(self):
        """Disable form inputs during automatic process"""
        # Note: We'll keep the form enabled but change button states
        self.register_btn.config(state='disabled', text="🔄 Processing...")
        self.manual_register_btn.config(state='disabled')
    
    def enable_form(self):
        """Re-enable form inputs"""
        self.register_btn.config(state='normal', text="🚀 Auto Register & Train")
        self.manual_register_btn.config(state='normal')
    
def main():
    root = tk.Tk()
    app = StudentRegistration(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
