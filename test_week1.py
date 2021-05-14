import os
import pymssql
from sql_connection_manager import SqlConnectionManager
import unittest
from COVID19_vaccine import COVID19Vaccine as covid
from enums import *
from utils import *

class TestCOVID19_vaccine(unittest.TestCase):

    def setUp(self):
        with SqlConnectionManager(Server=os.getenv("Server"),
                                  DBname=os.getenv("DBName"),
                                  UserId=os.getenv("UserID"),
                                  Password=os.getenv("Password")) as sqlClient:
              clear_tables(sqlClient)
              self.sqltext = "INSERT INTO Caregivers(CaregiverName) VALUES ('Preston'); INSERT INTO Patients(Name, dob, gender, sideeffects) VALUES ('Andreia', '10-11-2000', 'Female', 'No side effects'); INSERT INTO VaccineAppointment (PatientId, firstshot, VaccineId) VALUES (1, 1, 1); INSERT INTO CareGiverSchedule(CaregiverId, WorkDay, SlotHour, SlotMinute, SlotStatus, VaccineAppointmentId) VALUES (1, '12-12-2021', 12, 15, 0, 2);"
              dbcursor = sqlClient.cursor(as_dict=True)
              dbcursor.execute(self.sqltext)
              dbcursor.connection.commit()
              vaccines = {'Moderna': {'inventory': 100, 'shotsnecessary': 2}, 'Pfizer': {'inventory': 100, 'shotsnecessary': 2}, 'JohnsonJohnson': {'inventory': 100, 'shotsnecessary': 1}}
              vaccinedb = covid(dbcursor, vaccines)
    
    def tearDown(self):
        with SqlConnectionManager(Server=os.getenv("Server"),
                            DBname=os.getenv("DBName"),
                            UserId=os.getenv("UserID"),
                            Password=os.getenv("Password")) as sqlClient:
            
            self.sqltext = "DROP TABLE CareGiverSchedule; DROP TABLE AppointmentStatusCodes; DROP TABLE Caregivers; DROP TABLE  VaccineAppointment; DROP TABLE  Patients; DROP TABLE Vaccines "   
            dbcursor = sqlClient.cursor(as_dict=True)
            dbcursor.execute(self.sqltext)
            dbcursor.connection.commit()

    def test_AddDoses(self):
        test_value = 0
        updated_inventory = 0
        doses_to_add = 30
        with SqlConnectionManager(Server=os.getenv("Server"),
                                   DBname=os.getenv("DBName"),
                                   UserId=os.getenv("UserID"),
                                   Password=os.getenv("Password")) as sqlClient:
            dbcursor = sqlClient.cursor(as_dict=True)
            self.sqltext = "SELECT inventory FROM Vaccines WHERE vaccineid=1"
            dbcursor.execute(self.sqltext)
            rows = dbcursor.fetchone()
            current_inventory = rows['inventory']
            test_value = current_inventory + doses_to_add
            covid.AddDoses(dbcursor, 1, doses_to_add)
            self.sqltext = "SELECT inventory FROM Vaccines WHERE vaccineid=1"
            dbcursor.execute(self.sqltext)
            rows = dbcursor.fetchone()
            updated_inventory = rows['inventory']
        self.assertEqual(test_value, updated_inventory)

    def test_ReserveDoses(self):
        with SqlConnectionManager(Server=os.getenv("Server"),
                                   DBname=os.getenv("DBName"),
                                   UserId=os.getenv("UserID"),
                                   Password=os.getenv("Password")) as sqlClient:
            dbcursor = sqlClient.cursor(as_dict=True)
            # Initial data
            self.sqltext = "SELECT inventory, reserved, shotsnecessary FROM Vaccines WHERE vaccineid=1"
            dbcursor.execute(self.sqltext)
            rows = dbcursor.fetchone()
            current_inventory = rows['inventory']
            current_reserved = rows['reserved']
            shots_necessary= rows['shotsnecessary']
            # Expected Results 
            test_inventory = current_inventory - shots_necessary
            test_reserved = current_reserved + shots_necessary
            # Reserving Doses
            covid.ReserveDoses(dbcursor, 1)
            self.sqltext = "SELECT inventory, reserved FROM Vaccines WHERE vaccineid=1"
            dbcursor.execute(self.sqltext)
            rows = dbcursor.fetchone()
            # Actual Results
            updated_inventory = rows['inventory']
            updated_inventory = rows['reserved']
        # Test
        self.assertEqual(test_inventory, updated_inventory)
        self.assertEqual(test_reserved, updated_reserved)

    def test_ReserveDosesLowInventory(self):
        with SqlConnectionManager(Server=os.getenv("Server"),
                                   DBname=os.getenv("DBName"),
                                   UserId=os.getenv("UserID"),
                                   Password=os.getenv("Password")) as sqlClient:
            dbcursor = sqlClient.cursor(as_dict=True)
            # Setting inventory to zero
            sqltext = "UPDATE Vaccines SET inventory=%s WHERE vaccineid=1"
            cursor.execute(sqltext, 0)
            cursor.connection.commit()
            
            # Test
            self.assertRaisesRegex(ValueError, "Not enough vaccines. Please try a different vaccine or another vaccine!",
                       covid.ReserveDoses, 'dbcursor', 1)


if __name__ == '__main__':
    unittest.main()
