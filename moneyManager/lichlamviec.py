import tkinter as tk
from pathlib import Path
from tkcalendar import Calendar
from datetime import datetime, timedelta
from Database import Database
from export import TextHandler
""" #TODO list:
`           0. multiple users // priority: low
            1. send data to mentor app to manage your work schedule
            2. one person can work 2 or more different jobs, make CRUD for jobs
            3. Each job has a different salary type, make CRUD for salary type (per session, per month, per year, per hour)
"""



current_directory = Path(__file__).parent
database_string_path = current_directory /'mongo.txt'
with database_string_path.open('r') as file:
    #file includes a list of database urls, prioritize from top to bottom
    mongo_url = file.read().splitlines()
    
class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Ứng dụng chấm công thực tập")
        self.root.geometry("400x600")

        self.root.geometry("+%d+%d" % (root.winfo_screenwidth()-500, root.winfo_screenheight()//2 -350))

        self.root.bind("<Escape>", self.on_closing)
        self.root.bind("<BackSpace>", self.clear_day)
        self.root.bind("<A>", self.toggle_morning)
        self.root.bind("<a>", self.toggle_morning)
        self.root.bind("<d>" , self.toggle_afternoon)
        self.root.bind("<D>" , self.toggle_afternoon)

        #Button when click the window will alway on top, set this button to bottom right
        self.always_on_top_button = tk.Button(root, text="onTop", font=("Arial", 14), command=self.always_on_top)
        self.always_on_top_button.pack(side=tk.BOTTOM, anchor=tk.SE)
        self.root.update()

        #Create a calendar to select the date
        self.calendar = Calendar(root, selectmode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, font=("Arial", 14))
        self.calendar.pack(pady=20, padx=20)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_change)
        self.calendar.bind("<<CalendarMonthChanged>>", self.on_month_change)  #Change month event
        self.time_label = tk.Label(root, text="", font=("Arial", 14))
        self.time_label.pack(pady=5)

        #Morning button
        self.morning_button = tk.Button(root, text="Buổi sáng", font=("Arial", 14), command=self.toggle_morning)
        self.morning_button.pack(pady=5)

        #Afternoon button
        self.afternoon_button = tk.Button(root, text="Buổi chiều", font=("Arial", 14), command=self.toggle_afternoon)
        self.afternoon_button.pack(pady=5)

        # Where the user can enter the salary each session for each month
        self.salary_label = tk.Label(root, text="", font=("Arial", 14))
        self.salary_label.pack(pady=5)
        self.salary_entry = tk.Entry(root, font=("Arial", 14))
        self.salary_entry.pack(pady=5)
        self.root.update()
        # try to connect to the database, prioritize the first url in the list
        try:
            for i in (0, len(mongo_url)):
                self.db = Database(mongo_url[i])
                self.db.client.server_info()
                print(f"Connected to the database at {mongo_url[i]}")
                break
            #when main data is connected, connect to the backup database is the next url in the list
            self.backup = Database(mongo_url[i+1])
        except:
            print(f"Failed to connect to clouds database")
            #create a connection to local database as a backup, this database is the last one in the list
            self.db = Database(mongo_url[-1])
            print("Connected to the local database instead")
            self.backup = None
        #merge the data from the backup database to the main database (if any)
        print (self.db.merge_data(self.backup))

        #load the salary from the database
        self.salary_per_session = {}
        self.salary_modified = {}
        self.salary_is_modified = {}
        for record in self.db.salrryy.find():
            self.salary_per_session[record['month']] = record['salary']
            self.salary_modified[record['month']] = record.get('last_modified', datetime.now())
            self.salary_is_modified[record['month']] = record.get('is_modified', False)
        #when the user press enter, save the salary
        self.salary_entry.bind("<Return>", self.save_salary)
        
        # Show the result
        self.result_label = tk.Label(root, text="", font=("Arial", 14))
        self.result_label.pack(pady=5)
        self.root.update()

        # Load the attendance from the database
        # Dictionary to store the attendance of each day in the format {date: {morning: True/False, afternoon: True/False}}
        self.attendance = {}
        self.modified = {}
        for record in self.db.collection.find():
            self.attendance[record['date']] = record['attendance']
            self.modified.setdefault(record['date'], {})['is_modified'] = record.get('is_modified', False)
            self.modified[record['date']]['last_modified'] = record.get('last_modified', datetime.now())
            self.modified[record['date']]['modified_by'] = record.get('modified_by', self.db.client.server_info())
            self.update_calendar(record['date'], 0)
            self.root.update()
        self.on_date_change(None)

        # Export the data for the mentor
        self.export_Button = tk.Button(root, text="Export Week data", font=("Time", 14), command=self.export_data_for_mentor)
        self.export_Button.pack(side=tk.BOTTOM, anchor=tk.SE)
        self.root.update()
        
    # Handle the closing event
    def on_closing(self,event=None):
        self.save_salary(None)
        self.root.withdraw()
        if self.backup is not None:
            self.db.save_data(self.attendance, self.modified, self.salary_per_session, self.salary_modified, self.salary_is_modified)
            self.backup.save_data(self.attendance, self.modified, self.salary_per_session, self.salary_modified, self.salary_is_modified)
        else:
            self.db.save_data(self.attendance, self.modified, self.salary_per_session, self.salary_modified, self.salary_is_modified, "backup")
        self.root.destroy()

    # Set the window to always on top
    def always_on_top(self):
        self.root.attributes("-topmost", not self.root.attributes("-topmost"))

    #Change month event
    def on_month_change(self, event):
        #Change month event by get_displayed_month(). it returns a tuple (month, year)
        month= self.calendar.get_displayed_month()
        #Set the selected date to the first day of the month
        today = datetime.now()
        if month[1] == today.year and month[0] == today.month:
            self.calendar.selection_set(today)
        else:
            self.calendar.selection_set(datetime(month[1], month[0], 1))
        #Call the on_date_change event to update the calendar
        self.on_date_change(event)

    # Update the calendar when the user selects a date
    def on_date_change(self, event):
        date = self.calendar.get_date()
        self.update_calendar(date, 0)
        self.time_label.config(text=f"Ngày chọn: {date}")
        month = self.calendar.get_displayed_month()
        #Only show the salary of the selected month
        salary_keys = date.split('/')[0] + '/' + date.split('/')[2]
        if self.salary_per_session.get(salary_keys) is None:
            self.salary_per_session[salary_keys] = 0
        self.salary_label.config(text=f"Lương mỗi buổi trong tháng {month[0]}/{month[1]}")
        self.salary_entry.delete(0, tk.END)
        self.salary_entry.insert(0, self.salary_per_session[salary_keys])

        self.caculate_each_month()

    #When the user works in the morning
    def toggle_morning(self,event=None):
        date = self.calendar.get_date()
        if date not in self.attendance:
            self.attendance[date] = {'morning': False, 'afternoon': False}
        self.attendance[date]['morning'] = not self.attendance[date]['morning']
        self.modified[date] = {'is_modified': True, 'last_modified': datetime.now(), 'modified_by': self.db.client.server_info()}
        self.update_calendar(date, 1)
        self.caculate_each_month()

    #When the user works in the afternoon
    def toggle_afternoon(self,event=None):
        date = self.calendar.get_date()
        if date not in self.attendance:
            self.attendance[date] = {'morning': False, 'afternoon': False}
        self.attendance[date]['afternoon'] = not self.attendance[date]['afternoon']
        self.modified[date] = {'is_modified': True, 'last_modified': datetime.now(), 'modified_by': self.db.client.server_info()}
        self.update_calendar(date, 1)
        self.caculate_each_month()

    #Clear the attendance of the selected day
    def clear_day(self, event):
        date = self.calendar.get_date()
        if date in self.attendance:
            self.attendance[date] = {'morning': False, 'afternoon': False}
            self.modified[date] = {'is_modified': True, 'last_modified': datetime.now(), 'modified_by': self.db.client.server_info()}
            self.update_calendar(date, 1)
            self.caculate_each_month()

    
    def update_calendar(self, date, type):
        """Update the calendar based on the attendance dictionary"""
        morning = self.attendance.get(date, {}).get('morning', False)
        afternoon = self.attendance.get(date, {}).get('afternoon', False)
        self.calendar.calevent_remove('morning', datetime.strptime(date, "%m/%d/%y"))
        self.calendar.calevent_remove('afternoon', datetime.strptime(date, "%m/%d/%y"))
        self.calendar.calevent_remove('full_day', datetime.strptime(date, "%m/%d/%y"))

        if morning and afternoon:
            self.morning_button.config(bg='#FFA27D')
            self.afternoon_button.config(bg='#00BABD')
            self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Full Day', 'full_day')
            self.calendar.tag_config('full_day', background='#2AD587', foreground='black')
        elif morning:
            self.morning_button.config(bg='#FFA27D')
            self.afternoon_button.config(bg='SystemButtonFace')
            self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Morning', 'morning')
            self.calendar.tag_config('morning', background='#FFA27D', foreground='black')
        elif afternoon:
            self.morning_button.config(bg='SystemButtonFace')
            self.afternoon_button.config(bg='#00BABD')
            self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Afternoon', 'afternoon')
            self.calendar.tag_config('afternoon', background='#00BABD', foreground='black')
        else:
            # different type 1 and 0
            # type = 0: When the user selects a date form the calendar
            if type == 0:
                self.morning_button.config(bg='SystemButtonFace')
                self.afternoon_button.config(bg='SystemButtonFace')
            # type = 1: When the user clicks the morning or afternoon button
            elif type == 1:
                self.morning_button.config(bg='SystemButtonFace')
                self.afternoon_button.config(bg='SystemButtonFace')
                
                #If weekend, change the color of the date to gray, otherwise, change it to white
                #TODO: little bug here, Color is affected by same day in different month:
                if datetime.strptime(date, "%m/%d/%y").weekday() in [5, 6]:
                    self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Weekend', 'weekend')
                    self.calendar.tag_config('weekend', background='#cccccc', foreground='black')
                else:
                    self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Normal', 'normal')
                    self.calendar.tag_config('normal', background='white', foreground='black')


    def save_salary(self, event):
        try:
            print("Saving salary")
            salary_per_session = int(self.salary_entry.get())
            month = self.calendar.get_date().split('/')[0]
            year = self.calendar.get_date().split('/')[2]
            self.salary_per_session[f"{month}/{year}"] = salary_per_session
            self.salary_modified[f"{month}/{year}"] = datetime.now()
            self.salary_is_modified[f"{month}/{year}"] = True
            self.caculate_each_month()
        except ValueError:
            pass

    # Calculate the total salary of the month is displayed on the calendar
    def caculate_each_month(self):
        month = self.calendar.get_date().split('/')[0]
        year = self.calendar.get_date().split('/')[2]
        #number of sessions that month
        total_sessions = 0
        for date, days in self.attendance.items():
            if date.split('/')[0] == month and date.split('/')[2] == year:
                if days['morning']:
                    total_sessions += 1
                if days['afternoon']:
                    total_sessions += 1
        
        try:
            salary_this_month = int(self.salary_entry.get())
            self.salary_per_session[f"{month}/{year}"] = salary_this_month
            total_salary = total_sessions * salary_this_month
            formatted_salary = "{:,.0f}".format(total_salary)
            self.result_label.config(text=f"Tổng lương tháng {month}/{year}: {formatted_salary} VNĐ")
        except ValueError:
            self.result_label.config(text="Vui lòng nhập số lương hợp lệ")

    
    def export_data_for_mentor(self, time=7):
        """make function to export the data of the week when day is selected"""
        today = self.calendar.selection_get()
        #get the first day of the week
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        week = {day: {'sáng': False, 'chiều': False} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
        for i in range(7):
            date = start_date + timedelta(days=i)
            self.calendar.selection_set(date)
            #lấy thứ tuoong ứng với ngày
            day = date.strftime("%A")

            if day in week:
                #key in attendance in the format of 'mm/dd/yy', and some key is not in the attendance, so we need to check if the key is in the attendance
                key = self.calendar.get_date()
                if key in self.attendance:
                    week[day]['sáng'] = self.attendance[key].get('morning', False)
                    week[day]['chiều'] = self.attendance[key].get('afternoon', False)
                else:
                    week[day]['sáng'] = False
                    week[day]['chiều'] = False

        self.calendar.selection_set(today)
        week_string = f"Lịch làm tuần {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}:\n"
        for day, sessions in week.items():
            if sessions['sáng'] and sessions['chiều']:
                week_string += f"• {TextHandler.replace_day_names(day)}: sáng, chiều\n"
            elif sessions['sáng']:
                week_string += f"• {TextHandler.replace_day_names(day)}: sáng\n"
            elif sessions['chiều']:
                week_string += f"• {TextHandler.replace_day_names(day)}: chiều\n"

        TextHandler.save_to_clipboard(self.root, week_string)

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()

