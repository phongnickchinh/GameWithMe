import tkinter as tk
from pathlib import Path
from tkcalendar import Calendar
from datetime import datetime
from Database import Database
""" #TODO list:
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
        self.root.geometry("600x600")
        self.root.bind("<Escape>", self.on_closing)
        self.root.bind("<BackSpace>", self.clear_day)
        self.root.bind("<A>", self.toggle_morning)
        self.root.bind("<a>", self.toggle_morning)
        self.root.bind("<d>" , self.toggle_afternoon)
        self.root.bind("<D>" , self.toggle_afternoon)

        
        

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

    # Update the calendar based on the attendance dictionary
    def update_calendar(self, date, type):
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


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()

