
import pymongo
import time

class Database:
    def __init__(self, string):
        self.client = pymongo.MongoClient(string)
        self.db = self.client['internship_db']
        self.collection = self.db['attendance']
        self.salrryy = self.db['salary']


    def save_data(self, attendance, modified, salary_per_session, salary_modified, salary_is_modified, database_type= "main"):
        start_time = time.time()
        mainp = True if database_type == "main" else False

        #save the attendance for each day
        for date, days in attendance.items():
            if mainp:
                modified[date]['is_modified'] = False
            # delete the records are useless
                if  not days['morning'] and not days['afternoon']:
                    self.collection.delete_one({'date': date})
                    continue
            self.collection.update_one(
                {'date': date},
                {'$set': {'attendance': days,
                            'is_modified': modified[date]['is_modified'],
                            'last_modified': modified[date]['last_modified'],
                            'modified_by': modified[date]['modified_by']}
                },
                upsert=True
            )

        #save the salary each session for each month
        for salary in salary_per_session:
            if mainp:
                salary_is_modified[salary] = False
                # delete the records are useless
                if not salary_per_session[salary]:
                    self.salrryy.delete_one({'month': f"{salary.split('/')[0]}/{salary.split('/')[1]}"})
                    continue

            self.salrryy.update_one(
                {'month': f"{salary.split('/')[0]}/{salary.split('/')[1]}"},
                {'$set': {'salary': salary_per_session[salary],
                            'last_modified': salary_modified[salary],
                            'is_modified': salary_is_modified[salary]
                            }
                },
                upsert=True
            )
        end_time = time.time()
        if mainp:
            print(f"Saved to MongoDB in {end_time - start_time} seconds")
        else:
            print(f"Saved to Backup MongoDB in {end_time - start_time} seconds")

    #restore data from backup database to main database
    def merge_data(self, backup_database):
        if(not backup_database) :
            return "You are in backup database"
        
        #tìm ra document có last_modified muộn nhất trong main database, ghi vào last_modified_main
        last_modified_main = self.collection.find_one(sort=[("last_modified", pymongo.DESCENDING)])
        last_modified_main = last_modified_main['last_modified'] if last_modified_main else 0

        #lấy ra tất cả các document có last_modified > last_modified_main trong backup database
        backup_data = backup_database.collection.find({'last_modified': {'$gt': last_modified_main}})

        #kiểm tra cursor có dữ liệu hay không
        if backup_database.collection.count_documents({'last_modified': {'$gt': last_modified_main}}) == 0:
            return "No new data to merge"
        else:
            for data in backup_data:
                #nếu document đã tồn tại trong main database thì update, ngược lại thì insert
                self.collection.update_one(
                    {'date': data['date']},
                    {'$set': {'attendance': data['attendance'],
                                'is_modified': data['is_modified'],
                                'last_modified': data['last_modified'],
                                'modified_by': data['modified_by']}
                    },
                    upsert=True
                )

            return "Merge successfully"
        

    
            
