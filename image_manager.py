#!/usr/bin/env python3
"""
Image Reference Manager
Handles PhotoImage objects properly to prevent reference errors
"""

import tkinter as tk
from PIL import Image, ImageTk
import weakref

class ImageManager:
    """Manages PhotoImage references to prevent errors"""
    _instance = None
    _images = {}
    _counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_photo_image(self, pil_image):
        """Create a PhotoImage with proper reference management"""
        try:
            self._counter += 1
            image_id = f"img_{self._counter}"
            
            # Create PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Store reference
            self._images[image_id] = photo
            
            # Clean up old images (keep only last 10)
            if len(self._images) > 10:
                oldest_key = list(self._images.keys())[0]
                del self._images[oldest_key]
            
            return photo
            
        except Exception as e:
            print(f"Error creating PhotoImage: {e}")
            return None
    
    def clear_all(self):
        """Clear all image references"""
        self._images.clear()
        self._counter = 0

# Global image manager instance
image_manager = ImageManager()
