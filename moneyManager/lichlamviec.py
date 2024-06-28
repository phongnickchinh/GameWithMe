import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime
from pymongo import MongoClient

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Ứng dụng chấm công thực tập")
        self.root.geometry("600x600")  # Set the window size to 600x600
        self.client = MongoClient('mongodb+srv://phamphong300111:phamvanphong@phongpham300111.rqyu2st.mongodb.net/')
        # self.client = MongoClient('localhost', 27017)
        self.db = self.client['internship_db']
        self.collection = self.db['attendance']
        self.salrryy = self.db['salary']

        # Tạo lịch với font chữ lớn hơn
        self.calendar = Calendar(root, selectmode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, font=("Arial", 14))
        self.calendar.pack(pady=20, padx=20)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_change)
        self.calendar.bind("<<CalendarMonthChanged>>", self.change_month)  #tạo sự kiện cho nút chuyển tháng
        #tạo sự kiện cho nút chuyển tháng

        # Hiển thị thời gian
        self.time_label = tk.Label(root, text="", font=("Arial", 14))
        self.time_label.pack(pady=5)

        # Nút buổi sáng
        self.morning_button = tk.Button(root, text="Buổi sáng", font=("Arial", 14), command=self.toggle_morning)
        self.morning_button.pack(pady=5)

        # Nút buổi chiều
        self.afternoon_button = tk.Button(root, text="Buổi chiều", font=("Arial", 14), command=self.toggle_afternoon)
        self.afternoon_button.pack(pady=5)

        # Nhãn và ô nhập lương cho mỗi buổi
        self.salary_label = tk.Label(root, text="Nhập lương 1 buổi:", font=("Arial", 14))
        self.salary_label.pack(pady=5)

        self.salary_entry = tk.Entry(root, font=("Arial", 14))
        self.salary_entry.pack(pady=5)
        #nhận giá trị mặc định từ mongod
        salary_per_session = self.salrryy.find_one()
        if salary_per_session:
            self.salary_entry.insert(0, salary_per_session['salary'])

        # Nhãn hiển thị kết quả
        self.result_label = tk.Label(root, text="", font=("Arial", 14))
        self.result_label.pack(pady=5)

        # Dictionary chứa thông tin chấm công của nhân viên bao gồm ngày và buổi làm việc lấy từ MongoDB
        self.attendance = {}
        for record in self.collection.find():
            self.attendance[record['date']] = record['attendance']
            self.update_calendar(record['date'], 0)
        self.caculate_each_month()


    def on_closing(self):
        # Ẩn giao diện ngay lập tức
        self.root.withdraw()
        # Thực hiện các phương thức cần thiết
        self.save_to_mongodb()
        # Sau khi các phương thức đã hoàn tất, đóng ứng dụng
        self.root.destroy()

    def change_month(self, event):
        #thay đổi ngày lựa chọn thành đầu tháng khi chuyển tháng
        date = self.calendar.get_date()
        self.update_calendar(date, 0)
        self.time_label.config(text=f"Ngày chọn: {date}")
        self.caculate_each_month()
    def on_date_change(self, event):
        date = self.calendar.get_date()
        self.update_calendar(date, 0)
        self.time_label.config(text=f"Ngày chọn: {date}")
        self.caculate_each_month()

    def toggle_morning(self):
        date = self.calendar.get_date()
        if date not in self.attendance:
            self.attendance[date] = {'morning': False, 'afternoon': False}
        self.attendance[date]['morning'] = not self.attendance[date]['morning']
        self.update_calendar(date, 1)
        self.caculate_each_month()
        # self.save_to_mongodb(date, self.salary_entry.get())

    def toggle_afternoon(self):
        date = self.calendar.get_date()
        if date not in self.attendance:
            self.attendance[date] = {'morning': False, 'afternoon': False}
        self.attendance[date]['afternoon'] = not self.attendance[date]['afternoon']
        self.update_calendar(date, 1)
        self.caculate_each_month()
        # self.save_to_mongodb(date, self.salary_entry.get())

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
            #xử lí khác khi type = 0 và type = 1
            # type = 0: khi chọn ngày trên lịch
            if type == 0:
                self.morning_button.config(bg='SystemButtonFace')
                self.afternoon_button.config(bg='SystemButtonFace')
            # type = 1: khi click vào nút buổi sáng hoặc buổi chiều
            elif type == 1:
                self.morning_button.config(bg='SystemButtonFace')
                self.afternoon_button.config(bg='SystemButtonFace')
                self.calendar.calevent_create(datetime.strptime(date, "%m/%d/%y"), 'Normal', 'normal')
                self.calendar.tag_config('normal', background='white', foreground='black')


    
    # Tính lương cho từng tháng
    def caculate_each_month(self):
        month = self.calendar.get_date().split('/')[0]
        year = self.calendar.get_date().split('/')[2]

        # Tính số buổi làm việc trong tháng
        total_sessions = 0
        for date, days in self.attendance.items():
            if date.split('/')[0] == month:
                if days['morning']:
                    total_sessions += 1
                if days['afternoon']:
                    total_sessions += 1
        
        try:
            salary_per_session = int(self.salary_entry.get())
            total_salary = total_sessions * salary_per_session
            formatted_salary = "{:,.0f}".format(total_salary)
            self.result_label.config(text=f"Tổng lương tháng {month}/{year}: {formatted_salary} VNĐ")
        except ValueError:
            self.result_label.config(text="Vui lòng nhập số lương hợp lệ")

    def save_to_mongodb(self):
        
        for date, days in self.attendance.items():
            # Lưu thông tin chấm công vào MongoDB, các ngày chỉ false thì không lưu
            if not days['morning'] and not days['afternoon']:
                self.collection.delete_one({'date': date})
            else:
                self.collection.update_one(
                    {'date': date},
                    {'$set': {'attendance': days}},
                    upsert=True
                )
        
        if self.salary_entry.get():
            # Lưu lương vào MongoDB, chỉ có 1 bản ghi duy nhất
            self.salrryy.update_one(
                {},
                {'$set': {'salary': int(self.salary_entry.get())}},
                upsert=True
            )
        print("Saving to MongoDB")
if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()

