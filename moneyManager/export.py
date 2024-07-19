

from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog

class TextHandler:
    def __init__(self, data):
        self.data = data

    def replace_day_names(text):
        # Dictionary to map English day names to Vietnamese day names
        day_map = {
            "Monday": "Thứ 2",
            "Tuesday": "Thứ 3",
            "Wednesday": "Thứ 4",
            "Thursday": "Thứ 5",
            "Friday": "Thứ 6",
            "Saturday": "Thứ 7",
            "Sunday": "Chủ nhật"
        }
        # Replace each English day name with its Vietnamese counterpart
        for english_day, vietnamese_day in day_map.items():
            text = text.replace(english_day, vietnamese_day)
        return text

    #save the data to a clipboard
    @staticmethod
    def save_to_clipboard( root, text):
        root.clipboard_clear()
        root.clipboard_append(text)
        text = text.split("\n")[0]
        TextHandler.show_notification(text, root)
    

    @staticmethod
    def show_notification(message, root):
        notification = tk.Toplevel(root)
        notification.title("Notification")
        notification.geometry("300x50")
        #Set the notification window to be in the center of the main window
        notification.geometry(f"+{root.winfo_x() + root.winfo_width() // 2 - 150}+{root.winfo_y() + root.winfo_height() // 2 - 50}")
        notification.resizable(False, False)

        # Create a label to display the message
        label = tk.Label(notification, text=message, font=("Arial", 12))
        label.pack(expand=True)

        # Function to close the notification window
        def close_notification():
            notification.destroy()
        #Auto close after 1 second
        notification.after(1000, close_notification)