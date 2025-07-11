#!/usr/bin/env python3
"""
Attendance Report Viewer Module
View and export attendance reports from JSON files
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

class AttendanceReportViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Attendance Reports")
        self.root.geometry("1000x700")
        self.root.configure(bg='#ecf0f1')
        
        # Variables
        self.students_data = {}
        self.current_date = date.today()
        self.attendance_data = {}
        
        # Load students data
        self.load_students_data()
        
        # Create GUI
        self.create_widgets()
        
        # Load today's attendance by default
        self.load_attendance_for_date(self.current_date)
        
    def create_widgets(self):
        """Create and arrange widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Attendance Reports", 
                               font=('Arial', 18, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Report Controls", padding="15")
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Report display frame
        report_frame = ttk.LabelFrame(main_frame, text="Attendance Data", padding="15")
        report_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_controls(controls_frame)
        self.create_report_display(report_frame)
        
    def create_controls(self, parent):
        """Create control widgets"""
        # Date selection frame
        date_frame = ttk.Frame(parent)
        date_frame.grid(row=0, column=0, columnspan=4, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # Date selection
        ttk.Label(date_frame, text="Select Date:", font=('Arial', 12, 'bold')).grid(row=0, column=0, padx=(0, 10))
        
        # Date entry
        self.date_var = tk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, font=('Arial', 11), width=12)
        date_entry.grid(row=0, column=1, padx=5)
        
        # Date buttons
        ttk.Button(date_frame, text="Today", command=self.load_today).grid(row=0, column=2, padx=5)
        ttk.Button(date_frame, text="Yesterday", command=self.load_yesterday).grid(row=0, column=3, padx=5)
        ttk.Button(date_frame, text="Load Date", command=self.load_selected_date).grid(row=0, column=4, padx=5)
        
        # Statistics frame
        stats_frame = ttk.Frame(parent)
        stats_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        # Statistics labels
        self.total_students_var = tk.StringVar(value="Total Students: 0")
        self.present_count_var = tk.StringVar(value="Present: 0")
        self.absent_count_var = tk.StringVar(value="Absent: 0")
        self.attendance_rate_var = tk.StringVar(value="Attendance Rate: 0%")
        
        ttk.Label(stats_frame, textvariable=self.total_students_var, 
                 font=('Arial', 11)).grid(row=0, column=0, padx=15, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.present_count_var, 
                 font=('Arial', 11), foreground='#27ae60').grid(row=0, column=1, padx=15, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.absent_count_var, 
                 font=('Arial', 11), foreground='#e74c3c').grid(row=0, column=2, padx=15, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.attendance_rate_var, 
                 font=('Arial', 11, 'bold'), foreground='#3498db').grid(row=0, column=3, padx=15, sticky=tk.W)
        
        # Action buttons frame
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=2, column=0, columnspan=4, pady=(15, 0))
        
        # Buttons
        ttk.Button(action_frame, text="📊 Export to CSV", command=self.export_to_csv, 
                  style='Action.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="📈 Monthly Report", command=self.show_monthly_report, 
                  style='Action.TButton').grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="🔄 Refresh", command=self.refresh_data, 
                  style='Action.TButton').grid(row=0, column=2, padx=5)
        ttk.Button(action_frame, text="📁 Open Attendance Folder", command=self.open_attendance_folder, 
                  style='Action.TButton').grid(row=0, column=3, padx=5)
        
        # Style for action buttons
        style = ttk.Style()
        style.configure('Action.TButton', font=('Arial', 10), padding=8)
        
    def create_report_display(self, parent):
        """Create report display area"""
        # Create notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # Present students tab
        present_frame = ttk.Frame(notebook, padding="10")
        notebook.add(present_frame, text="Present Students")
        
        # Absent students tab
        absent_frame = ttk.Frame(notebook, padding="10")
        notebook.add(absent_frame, text="Absent Students")
        
        # All students tab
        all_frame = ttk.Frame(notebook, padding="10")
        notebook.add(all_frame, text="All Students")
        
        # Create treeviews for each tab
        self.create_present_view(present_frame)
        self.create_absent_view(absent_frame)
        self.create_all_students_view(all_frame)
        
    def create_present_view(self, parent):
        """Create present students view"""
        # Treeview for present students
        columns = ('Roll', 'Name', 'Department', 'Time')
        self.present_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        # Define headings
        self.present_tree.heading('Roll', text='Roll Number')
        self.present_tree.heading('Name', text='Name')
        self.present_tree.heading('Department', text='Department')
        self.present_tree.heading('Time', text='Attendance Time')
        
        # Configure column widths
        self.present_tree.column('Roll', width=100)
        self.present_tree.column('Name', width=200)
        self.present_tree.column('Department', width=100)
        self.present_tree.column('Time', width=120)
        
        # Scrollbars
        present_v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.present_tree.yview)
        present_h_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.present_tree.xview)
        self.present_tree.configure(yscrollcommand=present_v_scrollbar.set, 
                                  xscrollcommand=present_h_scrollbar.set)
        
        # Grid layout
        self.present_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        present_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        present_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def create_absent_view(self, parent):
        """Create absent students view"""
        # Treeview for absent students
        columns = ('Roll', 'Name', 'Department', 'Status')
        self.absent_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        # Define headings
        self.absent_tree.heading('Roll', text='Roll Number')
        self.absent_tree.heading('Name', text='Name')
        self.absent_tree.heading('Department', text='Department')
        self.absent_tree.heading('Status', text='Status')
        
        # Configure column widths
        self.absent_tree.column('Roll', width=100)
        self.absent_tree.column('Name', width=200)
        self.absent_tree.column('Department', width=100)
        self.absent_tree.column('Status', width=120)
        
        # Scrollbars
        absent_v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.absent_tree.yview)
        absent_h_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.absent_tree.xview)
        self.absent_tree.configure(yscrollcommand=absent_v_scrollbar.set, 
                                 xscrollcommand=absent_h_scrollbar.set)
        
        # Grid layout
        self.absent_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        absent_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        absent_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def create_all_students_view(self, parent):
        """Create all students view"""
        # Treeview for all students
        columns = ('Roll', 'Name', 'Department', 'Status', 'Time')
        self.all_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        # Define headings
        self.all_tree.heading('Roll', text='Roll Number')
        self.all_tree.heading('Name', text='Name')
        self.all_tree.heading('Department', text='Department')
        self.all_tree.heading('Status', text='Status')
        self.all_tree.heading('Time', text='Time')
        
        # Configure column widths
        self.all_tree.column('Roll', width=100)
        self.all_tree.column('Name', width=200)
        self.all_tree.column('Department', width=100)
        self.all_tree.column('Status', width=100)
        self.all_tree.column('Time', width=120)
        
        # Scrollbars
        all_v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.all_tree.yview)
        all_h_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.all_tree.xview)
        self.all_tree.configure(yscrollcommand=all_v_scrollbar.set, 
                              xscrollcommand=all_h_scrollbar.set)
        
        # Grid layout
        self.all_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        all_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        all_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def load_students_data(self):
        """Load students data from JSON"""
        try:
            with open('json_data/students.json', 'r') as f:
                self.students_data = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "Students data not found. Please register students first.")
            self.students_data = {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students data: {str(e)}")
            self.students_data = {}
    
    def load_attendance_for_date(self, target_date):
        """Load attendance data for specific date"""
        date_str = target_date.strftime("%Y-%m-%d")
        attendance_file = f"attendance/{date_str}.json"
        
        try:
            with open(attendance_file, 'r') as f:
                self.attendance_data = json.load(f)
        except FileNotFoundError:
            self.attendance_data = {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load attendance data: {str(e)}")
            self.attendance_data = {}
        
        # Update displays
        self.update_statistics()
        self.update_report_displays()
        
    def load_today(self):
        """Load today's attendance"""
        self.current_date = date.today()
        self.date_var.set(self.current_date.strftime("%Y-%m-%d"))
        self.load_attendance_for_date(self.current_date)
        
    def load_yesterday(self):
        """Load yesterday's attendance"""
        yesterday = date.today() - timedelta(days=1)
        self.current_date = yesterday
        self.date_var.set(self.current_date.strftime("%Y-%m-%d"))
        self.load_attendance_for_date(self.current_date)
        
    def load_selected_date(self):
        """Load attendance for selected date"""
        try:
            selected_date = datetime.strptime(self.date_var.get(), "%Y-%m-%d").date()
            self.current_date = selected_date
            self.load_attendance_for_date(self.current_date)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
            
    def update_statistics(self):
        """Update statistics display"""
        total_students = len(self.students_data)
        present_count = len(self.attendance_data)
        absent_count = total_students - present_count
        
        if total_students > 0:
            attendance_rate = (present_count / total_students) * 100
        else:
            attendance_rate = 0
        
        self.total_students_var.set(f"Total Students: {total_students}")
        self.present_count_var.set(f"Present: {present_count}")
        self.absent_count_var.set(f"Absent: {absent_count}")
        self.attendance_rate_var.set(f"Attendance Rate: {attendance_rate:.1f}%")
        
    def update_report_displays(self):
        """Update all report displays"""
        # Clear existing data
        for tree in [self.present_tree, self.absent_tree, self.all_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # Present students
        for roll, attendance_info in self.attendance_data.items():
            if roll in self.students_data:
                student = self.students_data[roll]
                self.present_tree.insert('', tk.END, values=(
                    roll, student['name'], student['department'], attendance_info['time']
                ))
                
                # Add to all students view
                self.all_tree.insert('', tk.END, values=(
                    roll, student['name'], student['department'], 'Present', attendance_info['time']
                ))
        
        # Absent students
        for roll, student in self.students_data.items():
            if roll not in self.attendance_data:
                self.absent_tree.insert('', tk.END, values=(
                    roll, student['name'], student['department'], 'Absent'
                ))
                
                # Add to all students view
                self.all_tree.insert('', tk.END, values=(
                    roll, student['name'], student['department'], 'Absent', '--'
                ))
    
    def export_to_csv(self):
        """Export attendance data to CSV"""
        if not self.students_data:
            messagebox.showerror("Error", "No students data available")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"attendance_{self.current_date.strftime('%Y-%m-%d')}.csv"
        )
        
        if not filename:
            return
        
        try:
            # Prepare data for export
            export_data = []
            
            for roll, student in self.students_data.items():
                if roll in self.attendance_data:
                    # Present student
                    export_data.append({
                        'Roll Number': roll,
                        'Name': student['name'],
                        'Department': student['department'],
                        'Status': 'Present',
                        'Time': self.attendance_data[roll]['time'],
                        'Date': self.current_date.strftime("%Y-%m-%d")
                    })
                else:
                    # Absent student
                    export_data.append({
                        'Roll Number': roll,
                        'Name': student['name'],
                        'Department': student['department'],
                        'Status': 'Absent',
                        'Time': '--',
                        'Date': self.current_date.strftime("%Y-%m-%d")
                    })
            
            # Create DataFrame and save
            df = pd.DataFrame(export_data)
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("Success", f"Attendance data exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def show_monthly_report(self):
        """Show monthly attendance report"""
        # This would open a new window with monthly statistics
        # For now, just show a simple summary
        try:
            current_month = self.current_date.replace(day=1)
            month_name = calendar.month_name[current_month.month]
            year = current_month.year
            
            # Count attendance files for the month
            attendance_days = 0
            total_present = 0
            
            for day in range(1, 32):
                try:
                    check_date = current_month.replace(day=day)
                    if check_date.month != current_month.month:
                        break
                        
                    attendance_file = f"attendance/{check_date.strftime('%Y-%m-%d')}.json"
                    if os.path.exists(attendance_file):
                        attendance_days += 1
                        with open(attendance_file, 'r') as f:
                            day_attendance = json.load(f)
                            total_present += len(day_attendance)
                            
                except ValueError:
                    break  # Invalid date (e.g., Feb 30)
                except Exception:
                    continue
            
            avg_attendance = total_present / attendance_days if attendance_days > 0 else 0
            
            messagebox.showinfo("Monthly Report", 
                              f"Monthly Report for {month_name} {year}\n\n"
                              f"Days with attendance records: {attendance_days}\n"
                              f"Total attendance marks: {total_present}\n"
                              f"Average daily attendance: {avg_attendance:.1f}\n"
                              f"Total registered students: {len(self.students_data)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate monthly report: {str(e)}")
    
    def open_attendance_folder(self):
        """Open attendance folder in file explorer"""
        try:
            import subprocess
            import platform
            
            attendance_path = os.path.abspath("attendance")
            
            if platform.system() == "Darwin":  # macOS
                subprocess.call(["open", attendance_path])
            elif platform.system() == "Windows":
                subprocess.call(["explorer", attendance_path])
            else:  # Linux
                subprocess.call(["xdg-open", attendance_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_students_data()
        self.load_attendance_for_date(self.current_date)

def main():
    root = tk.Tk()
    app = AttendanceReportViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
