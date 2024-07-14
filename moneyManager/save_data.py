
import pymongo

class Database:
    def __init__(self, string):
        self.client = pymongo.MongoClient(string)
        self.db = self.client['internship_db']
        self.collection = self.db['attendance']
        self.salrryy = self.db['salary']


    def save_to_mongodb(self, attendance, salary_per_session):
        for date, days in attendance.items():

            #delete the records are useless
            if not days['morning'] and not days['afternoon']:
                self.collection.delete_one({'date': date})
            else:
                self.collection.update_one(
                    {'date': date},
                    {'$set': {'attendance': days}},
                    upsert=True
                )

        #save the salary each session for each month
        for salary in salary_per_session:
            if not salary_per_session[salary]:
                #xoá bản ghi
                self.salrryy.delete_one({'month': f"{salary.split('/')[0]}/{salary.split('/')[1]}"})
            else:
                self.salrryy.update_one(
                    {'month': f"{salary.split('/')[0]}/{salary.split('/')[1]}"},
                    {'$set': {'salary': salary_per_session[salary]}},
                    upsert=True
                )
        print("Saving to MongoDB")

    def check_backupdata(self, backup_data):
        return True
