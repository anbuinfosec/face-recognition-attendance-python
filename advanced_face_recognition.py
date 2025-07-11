#!/usr/bin/env python3
"""
Advanced Face Recognition Engine
Enhanced face recognition with automatic calibration, quality assessment, and comprehensive logging
"""

import cv2
import numpy as np
import face_recognition
import json
import os
import logging
import sys
import traceback
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import math
from collections import defaultdict
import statistics
import threading
import time

class AdvancedFaceRecognition:
    def __init__(self, json_folder="json_data"):
        """Initialize advanced face recognition system"""
        self.json_folder = json_folder
        self.setup_logging()
        self.setup_directories()
        
        # Enhanced parameters
        self.face_detection_models = ["hog", "cnn"]
        self.current_model = "hog"  # Start with faster model
        
        # Dynamic thresholds (will be auto-calibrated)
        self.face_distance_threshold = 0.4
        self.confidence_threshold = 0.65
        self.quality_threshold = 0.7
        
        # Quality assessment parameters
        self.min_face_size = (50, 50)
        self.max_face_size = (500, 500)
        self.blur_threshold = 100
        self.brightness_range = (50, 200)
        
        # Performance tracking
        self.recognition_stats = {
            'total_attempts': 0,
            'successful_recognitions': 0,
            'false_positives': 0,
            'processing_times': [],
            'confidence_scores': []
        }
        
        self.load_encodings()
        self.logger.info("🚀 Advanced Face Recognition System Initialized")
        
    def setup_logging(self):
        """Setup comprehensive logging with terminal output"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        terminal_format = '%(levelname)s: %(message)s'
        detailed_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure main logger
        self.logger = logging.getLogger('AdvancedFaceRecognition')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(f'logs/advanced_face_recognition_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(detailed_format)
        file_handler.setFormatter(file_formatter)
        
        # Console handler for real-time terminal feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(terminal_format)
        console_handler.setFormatter(console_formatter)
        
        # Error handler for terminal errors
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter('🚨 ERROR: %(message)s')
        error_handler.setFormatter(error_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        
        # Set up root logger to catch all messages
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.INFO)
        
    def setup_directories(self):
        """Setup directory structure"""
        os.makedirs(self.json_folder, exist_ok=True)
        os.makedirs("dataset", exist_ok=True)
        os.makedirs("attendance", exist_ok=True)
        os.makedirs("calibration_data", exist_ok=True)
        
    def load_encodings(self):
        """Load face encodings with enhanced error handling"""
        try:
            encodings_file = os.path.join(self.json_folder, 'encodings.json')
            students_file = os.path.join(self.json_folder, 'students.json')
            
            self.known_encodings = []
            self.known_names = []
            self.known_rolls = []
            self.known_metadata = []
            
            if os.path.exists(encodings_file) and os.path.exists(students_file):
                with open(encodings_file, 'r') as f:
                    encodings_data = json.load(f)
                
                with open(students_file, 'r') as f:
                    students_data = json.load(f)
                
                total_encodings = 0
                for roll_number, encodings_list in encodings_data.items():
                    if roll_number in students_data:
                        student_info = students_data[roll_number]
                        
                        for i, encoding in enumerate(encodings_list):
                            self.known_encodings.append(np.array(encoding))
                            self.known_names.append(student_info['name'])
                            self.known_rolls.append(roll_number)
                            self.known_metadata.append({
                                'registration_date': student_info.get('registration_date', 'unknown'),
                                'role': student_info.get('role', 'student'),
                                'encoding_index': i
                            })
                            total_encodings += 1
                
                self.logger.info(f"✅ Loaded {total_encodings} face encodings for {len(students_data)} students")
                
                # Auto-calibrate if we have enough data
                if total_encodings >= 10:
                    self.auto_calibrate()
                    
            else:
                self.logger.warning("⚠️ No existing encodings found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading encodings: {e}")
            self.known_encodings = []
            self.known_names = []
            self.known_rolls = []
            self.known_metadata = []
    
    def auto_calibrate(self):
        """Automatically calibrate recognition parameters based on existing data"""
        self.logger.info("🔧 Starting automatic calibration...")
        
        if len(self.known_encodings) < 5:
            self.logger.warning("⚠️ Insufficient data for auto-calibration")
            return
        
        try:
            # Calculate inter-class distances (different people)
            inter_class_distances = []
            intra_class_distances = []
            
            # Group encodings by person
            person_encodings = defaultdict(list)
            for i, roll in enumerate(self.known_rolls):
                person_encodings[roll].append(self.known_encodings[i])
            
            # Calculate intra-class distances (same person)
            for roll, encodings in person_encodings.items():
                if len(encodings) > 1:
                    for i in range(len(encodings)):
                        for j in range(i + 1, len(encodings)):
                            distance = face_recognition.face_distance([encodings[i]], encodings[j])[0]
                            intra_class_distances.append(distance)
            
            # Calculate inter-class distances (different people)
            rolls = list(person_encodings.keys())
            for i in range(len(rolls)):
                for j in range(i + 1, len(rolls)):
                    for enc1 in person_encodings[rolls[i]][:2]:  # Limit to prevent too many comparisons
                        for enc2 in person_encodings[rolls[j]][:2]:
                            distance = face_recognition.face_distance([enc1], enc2)[0]
                            inter_class_distances.append(distance)
            
            if intra_class_distances and inter_class_distances:
                # Calculate optimal threshold
                avg_intra = statistics.mean(intra_class_distances)
                avg_inter = statistics.mean(inter_class_distances)
                std_intra = statistics.stdev(intra_class_distances) if len(intra_class_distances) > 1 else 0.1
                
                # Set threshold between the distributions
                optimal_threshold = avg_intra + 2 * std_intra
                
                # Ensure reasonable bounds
                self.face_distance_threshold = max(0.3, min(0.6, optimal_threshold))
                
                # Adjust confidence threshold accordingly
                self.confidence_threshold = 1.0 - self.face_distance_threshold - 0.1
                
                self.logger.info(f"🎯 Auto-calibration complete:")
                self.logger.info(f"   Face distance threshold: {self.face_distance_threshold:.3f}")
                self.logger.info(f"   Confidence threshold: {self.confidence_threshold:.3f}")
                self.logger.info(f"   Avg intra-class distance: {avg_intra:.3f}")
                self.logger.info(f"   Avg inter-class distance: {avg_inter:.3f}")
                
                # Save calibration results
                self.save_calibration_results()
                
        except Exception as e:
            self.logger.error(f"❌ Auto-calibration failed: {e}")
    
    def save_calibration_results(self):
        """Save calibration results for future use"""
        try:
            calibration_data = {
                'timestamp': datetime.now().isoformat(),
                'face_distance_threshold': self.face_distance_threshold,
                'confidence_threshold': self.confidence_threshold,
                'quality_threshold': self.quality_threshold,
                'face_detection_model': self.current_model,
                'calibration_stats': {
                    'encodings_used': len(self.known_encodings),
                    'unique_persons': len(set(self.known_rolls))
                }
            }
            
            calibration_file = os.path.join('calibration_data', 'auto_calibration.json')
            with open(calibration_file, 'w') as f:
                json.dump(calibration_data, f, indent=2)
                
            self.logger.info(f"💾 Calibration results saved to {calibration_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save calibration results: {e}")
    
    def assess_image_quality(self, image: np.ndarray, face_location: Tuple) -> Dict:
        """Assess the quality of a face image"""
        top, right, bottom, left = face_location
        face_img = image[top:bottom, left:right]
        
        if face_img.size == 0:
            return {'overall_score': 0.0, 'issues': ['Empty face region']}
        
        quality_metrics = {}
        issues = []
        
        # Size check
        face_height, face_width = face_img.shape[:2]
        quality_metrics['size_score'] = 1.0
        if face_width < self.min_face_size[0] or face_height < self.min_face_size[1]:
            quality_metrics['size_score'] = 0.3
            issues.append('Face too small')
        elif face_width > self.max_face_size[0] or face_height > self.max_face_size[1]:
            quality_metrics['size_score'] = 0.7
            issues.append('Face too large')
        
        # Blur detection using Laplacian variance
        gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY) if len(face_img.shape) == 3 else face_img
        blur_score = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        quality_metrics['blur_score'] = min(1.0, blur_score / self.blur_threshold)
        if blur_score < self.blur_threshold * 0.5:
            issues.append('Image too blurry')
        
        # Brightness check
        brightness = np.mean(gray_face)
        if brightness < self.brightness_range[0]:
            quality_metrics['brightness_score'] = 0.4
            issues.append('Image too dark')
        elif brightness > self.brightness_range[1]:
            quality_metrics['brightness_score'] = 0.6
            issues.append('Image too bright')
        else:
            quality_metrics['brightness_score'] = 1.0
        
        # Face orientation (basic check using face landmarks if available)
        quality_metrics['orientation_score'] = 1.0  # Simplified for now
        
        # Overall score
        overall_score = (
            quality_metrics['size_score'] * 0.3 +
            quality_metrics['blur_score'] * 0.4 +
            quality_metrics['brightness_score'] * 0.2 +
            quality_metrics['orientation_score'] * 0.1
        )
        
        return {
            'overall_score': overall_score,
            'metrics': quality_metrics,
            'issues': issues
        }
    
    def recognize_faces(self, frame: np.ndarray, return_quality=True) -> List[Dict]:
        """Enhanced face recognition with quality assessment and logging"""
        start_time = datetime.now()
        self.recognition_stats['total_attempts'] += 1
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces with current model
            face_locations = face_recognition.face_locations(rgb_frame, model=self.current_model)
            
            self.logger.debug(f"🔍 Detected {len(face_locations)} faces using {self.current_model} model")
            
            if not face_locations:
                return []
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            results = []
            
            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                result = {
                    'face_id': i,
                    'location': face_location,
                    'recognized': False,
                    'name': 'Unknown',
                    'roll_number': None,
                    'confidence': 0.0,
                    'distance': float('inf'),
                    'metadata': {}
                }
                
                # Quality assessment
                if return_quality:
                    quality_info = self.assess_image_quality(rgb_frame, face_location)
                    result['quality'] = quality_info
                    
                    if quality_info['overall_score'] < self.quality_threshold:
                        self.logger.warning(f"⚠️ Low quality face detected: {quality_info['issues']}")
                
                # Face recognition
                if len(self.known_encodings) > 0:
                    # Calculate distances to all known faces
                    face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                    
                    # Find best match
                    best_match_index = np.argmin(face_distances)
                    best_distance = face_distances[best_match_index]
                    confidence = 1.0 - best_distance
                    
                    # Log recognition attempt
                    self.logger.debug(f"🎯 Face {i}: Best distance={best_distance:.3f}, Confidence={confidence:.3f}")
                    
                    # Check if it's a valid match
                    if best_distance <= self.face_distance_threshold and confidence >= self.confidence_threshold:
                        result.update({
                            'recognized': True,
                            'name': self.known_names[best_match_index],
                            'roll_number': self.known_rolls[best_match_index],
                            'confidence': confidence,
                            'distance': best_distance,
                            'metadata': self.known_metadata[best_match_index]
                        })
                        
                        self.recognition_stats['successful_recognitions'] += 1
                        self.recognition_stats['confidence_scores'].append(confidence)
                        
                        self.logger.info(f"✅ Recognized: {result['name']} ({result['roll_number']}) - Confidence: {confidence:.3f}")
                    else:
                        self.logger.info(f"❌ Unknown face - Best match: {self.known_names[best_match_index]} (distance: {best_distance:.3f})")
                
                results.append(result)
            
            # Record processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            self.recognition_stats['processing_times'].append(processing_time)
            
            self.logger.debug(f"⏱️ Processing time: {processing_time:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Recognition error: {e}")
            return []
    
    def adaptive_model_selection(self, frame_count: int):
        """Adaptively select face detection model based on performance"""
        if frame_count % 100 == 0 and len(self.recognition_stats['processing_times']) > 10:
            avg_time = statistics.mean(self.recognition_stats['processing_times'][-10:])
            
            # Switch to faster model if processing is slow
            if avg_time > 0.5 and self.current_model == "cnn":
                self.current_model = "hog"
                self.logger.info("🔄 Switched to HOG model for better performance")
            # Switch to more accurate model if processing is fast
            elif avg_time < 0.2 and self.current_model == "hog":
                self.current_model = "cnn"
                self.logger.info("🔄 Switched to CNN model for better accuracy")
    
    def get_performance_stats(self) -> Dict:
        """Get detailed performance statistics"""
        stats = self.recognition_stats.copy()
        
        if stats['total_attempts'] > 0:
            stats['recognition_rate'] = stats['successful_recognitions'] / stats['total_attempts']
        else:
            stats['recognition_rate'] = 0.0
        
        if stats['processing_times']:
            stats['avg_processing_time'] = statistics.mean(stats['processing_times'])
            stats['max_processing_time'] = max(stats['processing_times'])
        
        if stats['confidence_scores']:
            stats['avg_confidence'] = statistics.mean(stats['confidence_scores'])
            stats['min_confidence'] = min(stats['confidence_scores'])
        
        return stats
    
    def log_performance_summary(self):
        """Log comprehensive performance summary"""
        stats = self.get_performance_stats()
        
        self.logger.info("📊 Performance Summary:")
        self.logger.info(f"   Total recognition attempts: {stats['total_attempts']}")
        self.logger.info(f"   Successful recognitions: {stats['successful_recognitions']}")
        self.logger.info(f"   Recognition rate: {stats.get('recognition_rate', 0):.2%}")
        
        if 'avg_processing_time' in stats:
            self.logger.info(f"   Average processing time: {stats['avg_processing_time']:.3f}s")
            
        if 'avg_confidence' in stats:
            self.logger.info(f"   Average confidence: {stats['avg_confidence']:.3f}")
        
        self.logger.info(f"   Current model: {self.current_model}")
        self.logger.info(f"   Distance threshold: {self.face_distance_threshold:.3f}")
        self.logger.info(f"   Confidence threshold: {self.confidence_threshold:.3f}")
    
    def process_student_images(self, student_roll: str, image_folder: str, callback=None) -> bool:
        """
        Process all images for a student and generate encodings automatically
        """
        try:
            self.logger.info(f"🔄 Starting automatic encoding generation for student {student_roll}")
            print(f"\n{'='*60}")
            print(f"🎯 PROCESSING STUDENT: {student_roll}")
            print(f"📁 Image folder: {image_folder}")
            print(f"{'='*60}")
            
            if not os.path.exists(image_folder):
                error_msg = f"Image folder not found: {image_folder}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
                return False
            
            # Get all image files
            image_files = []
            supported_formats = ('.jpg', '.jpeg', '.png', '.bmp')
            
            for file in os.listdir(image_folder):
                if file.lower().endswith(supported_formats):
                    image_files.append(os.path.join(image_folder, file))
            
            if not image_files:
                error_msg = f"No image files found in {image_folder}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
                return False
            
            print(f"📸 Found {len(image_files)} images to process")
            
            encodings = []
            processed_count = 0
            failed_count = 0
            
            for i, image_path in enumerate(image_files):
                try:
                    if callback:
                        callback(f"Processing image {i+1}/{len(image_files)}: {os.path.basename(image_path)}")
                    
                    print(f"🔍 Processing image {i+1}/{len(image_files)}: {os.path.basename(image_path)}")
                    
                    # Load image
                    image = cv2.imread(image_path)
                    if image is None:
                        self.logger.warning(f"⚠️ Could not load image: {image_path}")
                        print(f"⚠️ Skipping corrupted image: {os.path.basename(image_path)}")
                        failed_count += 1
                        continue
                    
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Detect faces
                    face_locations = face_recognition.face_locations(rgb_image, model="hog")
                    
                    if not face_locations:
                        self.logger.warning(f"⚠️ No face detected in {image_path}")
                        print(f"⚠️ No face found in: {os.path.basename(image_path)}")
                        failed_count += 1
                        continue
                    
                    if len(face_locations) > 1:
                        self.logger.warning(f"⚠️ Multiple faces detected in {image_path}, using largest")
                        print(f"⚠️ Multiple faces in {os.path.basename(image_path)}, using largest")
                        # Use the largest face
                        face_locations = [max(face_locations, key=lambda loc: (loc[2]-loc[0])*(loc[1]-loc[3]))]
                    
                    # Generate encoding
                    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                    
                    if face_encodings:
                        encodings.append(face_encodings[0].tolist())
                        processed_count += 1
                        print(f"✅ Successfully processed: {os.path.basename(image_path)}")
                    else:
                        self.logger.warning(f"⚠️ Could not generate encoding for {image_path}")
                        print(f"⚠️ Failed to encode: {os.path.basename(image_path)}")
                        failed_count += 1
                
                except Exception as e:
                    self.logger.error(f"❌ Error processing {image_path}: {str(e)}")
                    print(f"❌ Error in {os.path.basename(image_path)}: {str(e)}")
                    failed_count += 1
                    continue
            
            print(f"\n📊 PROCESSING SUMMARY:")
            print(f"✅ Successfully processed: {processed_count} images")
            print(f"❌ Failed to process: {failed_count} images")
            print(f"📈 Success rate: {(processed_count/(processed_count+failed_count)*100):.1f}%")
            
            if processed_count == 0:
                error_msg = f"No valid encodings generated for student {student_roll}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
                return False
            
            # Save encodings
            success = self.save_student_encodings(student_roll, encodings)
            
            if success:
                print(f"💾 Encodings saved successfully!")
                print(f"🎯 Generated {len(encodings)} face encodings for {student_roll}")
                self.logger.info(f"✅ Successfully generated {len(encodings)} encodings for {student_roll}")
                
                # Update model metadata
                self.update_model_metadata()
                
                # Reload encodings to include new data
                self.load_encodings()
                
                return True
            else:
                return False
                
        except Exception as e:
            error_msg = f"Critical error in process_student_images: {str(e)}"
            self.logger.error(error_msg)
            print(f"🚨 {error_msg}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def save_student_encodings(self, student_roll: str, encodings: List) -> bool:
        """Save encodings for a specific student"""
        try:
            encodings_file = os.path.join(self.json_folder, 'encodings.json')
            
            # Load existing encodings
            if os.path.exists(encodings_file):
                with open(encodings_file, 'r') as f:
                    all_encodings = json.load(f)
            else:
                all_encodings = {}
            
            # Add/update student encodings
            all_encodings[student_roll] = encodings
            
            # Save back to file
            with open(encodings_file, 'w') as f:
                json.dump(all_encodings, f, indent=2)
            
            self.logger.info(f"💾 Saved {len(encodings)} encodings for student {student_roll}")
            print(f"💾 Encodings saved to: {encodings_file}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save encodings: {str(e)}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def update_model_metadata(self):
        """Update model metadata file"""
        try:
            # Count total students and encodings
            encodings_file = os.path.join(self.json_folder, 'encodings.json')
            students_file = os.path.join(self.json_folder, 'students.json')
            
            total_students = 0
            total_encodings = 0
            
            if os.path.exists(encodings_file):
                with open(encodings_file, 'r') as f:
                    encodings_data = json.load(f)
                    total_students = len(encodings_data)
                    total_encodings = sum(len(encs) for encs in encodings_data.values())
            
            metadata = {
                "total_students": total_students,
                "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_encodings": total_encodings,
                "model_version": "2.0",
                "face_detection_model": self.current_model,
                "distance_threshold": self.face_distance_threshold,
                "confidence_threshold": self.confidence_threshold
            }
            
            with open('model_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"📊 Updated model metadata: {total_students} students, {total_encodings} encodings")
            print(f"📊 Model metadata updated")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update metadata: {str(e)}")
            print(f"❌ Metadata update failed: {str(e)}")
    
    def validate_student_data(self, student_roll: str, student_name: str) -> bool:
        """Validate student data before processing"""
        if not student_roll or not student_roll.strip():
            self.logger.error("❌ Invalid roll number: empty or None")
            print("❌ Roll number cannot be empty")
            return False
        
        if not student_name or not student_name.strip():
            self.logger.error("❌ Invalid student name: empty or None")
            print("❌ Student name cannot be empty")
            return False
        
        # Check if student already exists
        students_file = os.path.join(self.json_folder, 'students.json')
        if os.path.exists(students_file):
            try:
                with open(students_file, 'r') as f:
                    students_data = json.load(f)
                    if student_roll in students_data:
                        self.logger.warning(f"⚠️ Student {student_roll} already exists, will update")
                        print(f"⚠️ Student {student_roll} already exists - updating data")
            except Exception as e:
                self.logger.error(f"❌ Error checking existing students: {str(e)}")
        
        return True

# Global instance for easy access
advanced_face_recognition = None

def get_advanced_recognition_engine():
    """Get singleton instance of advanced face recognition"""
    global advanced_face_recognition
    if advanced_face_recognition is None:
        advanced_face_recognition = AdvancedFaceRecognition()
    return advanced_face_recognition
