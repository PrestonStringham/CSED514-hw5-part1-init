# import os
# import pymssql
# from sql_connection_manager import SqlConnectionManager
# import unittest
# from COVID19_vaccine import COVID19Vaccine as covid
# from vaccine_reservation_scheduler import VaccineReservationScheduler as scheduler
# from enums import *
# from utils import *

# # NOTE: RUN THE TESTS AFTER DROPPING ALL TABLES AND PROCEDURES. TESTS EXECUTE STORED PROCEDURE AND DROP TABLES AUTOMATICALLY.
# # PLEASE COMMENT OUT THE 'EXECUTE InitDataModel' IN OUR SQL FILE AS WELL. dbcursor EXECUTES THE PROCEDURE.

# class TestCOVID19_vaccine(unittest.TestCase):

#   def setUp(self):
#       with SqlConnectionManager(Server=os.getenv("Server"),
#                                 DBname=os.getenv("DBName"),
#                                 UserId=os.getenv("UserID"),
#                                 Password=os.getenv("Password")) as sqlClient:
#           dbcursor = sqlClient.cursor(as_dict=True)

#           # with open('hw5_week1_sql.sql') as f: 
#           #   sql = f.read() # Don't do that with untrusted inputs
#           #   dbcursor.execute(sql)
#           #   dbcursor.connection.commit()

#           # dbcursor.callproc('InitDataModel')

#           addTwoCaregivers = "INSERT INTO Caregivers(CaregiverName) VALUES ('Preston1'), ('Preston2');"
#           vaccines = {'Pfizer': {'Pfizer': 'Moderna', 'inventory': 5, 'shotsnecessary': 2, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 28}}
#           vaccinedb = covid(dbcursor, vaccines)
#           dbcursor.connection.commit()
#           dbcursor.close()

#   def tearDown(self):
#       with SqlConnectionManager(Server=os.getenv("Server"),
#                           DBname=os.getenv("DBName"),
#                           UserId=os.getenv("UserID"),
#                           Password=os.getenv("Password")) as sqlClient:
          
#           self.sqltext = "DROP TABLE CareGiverSchedule; DROP TABLE AppointmentStatusCodes; DROP TABLE Caregivers; DROP TABLE VaccineAppointment; DROP TABLE Patients; DROP TABLE Vaccines; DROP PROCEDURE InitDataModel; "   
#           dbcursor = sqlClient.cursor(as_dict=True)
#           dbcursor.execute(self.sqltext)
#           dbcursor.connection.commit()

#   def test_AddDoses(self):
#     addFivePatients = "INSERT INTO Pateints(PatientName, VaccineStatus) VALUES ('Andreia1', 0), ('Andreia2', 0), ('Andreia3', 0) ('Andreia4', 0), ('Andreia5', 0);"
#     addSchedules = "INSERT INTO CareGiverSchedule(CaregiverId, WorkDay, SlotTime, SlotHour, SlotMinute, SlotStatus) VALUES (1, '12-12-2021', 11:15:00, 11, 15, 0), (2, '01-12-2022', 12:35:00, 12, 35, 0), (1, '12-13-2021', 11:15:00, 11, 15, 0), (2, '01-13-2022', 12:35:00, 12, 35, 0),"


import unittest
import os

from sql_connection_manager import SqlConnectionManager
from vaccine_caregiver import VaccineCaregiver
from enums import *
from utils import *
from COVID19_vaccine import COVID19Vaccine as covid
from VaccinePatient import VaccinePatient as patient
class TestVaccineCaregiver(unittest.TestCase):
  def setUp(self):
    with SqlConnectionManager(Server=os.getenv("Server"),
                              DBname=os.getenv("DBName"),
                              UserId=os.getenv("UserID"),
                              Password=os.getenv("Password")) as sqlClient:
      dbcursor = sqlClient.cursor(as_dict=True)
      with sqlClient.cursor(as_dict=True) as cursor:
        try:
          with open('setup_procedure.sql') as f: 
              sql = f.read() # Don't do that with untrusted inputs
              dbcursor.execute(sql)
              dbcursor.connection.commit()

          dbcursor.callproc('InitScheduerApp')

          
          addTwoCaregivers = "INSERT INTO Caregivers(CaregiverName) VALUES ('Preston1'), ('Preston2');"
          vaccines = {'Pfizer': {'Supplier': 'Pfizer', 'inventory': 5, 'shotsnecessary': 2, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 28}}
          vaccinedb = covid(dbcursor, vaccines)
          dbcursor.execute(addTwoCaregivers)
          dbcursor.connection.commit()
          dbcursor.close()
        except Exception:
          # clear the tables if an exception occurred
          clear_tables(sqlClient)
          self.fail("Setup Failed")


  def tearDown(self):
        with SqlConnectionManager(Server=os.getenv("Server"),
                            DBname=os.getenv("DBName"),
                            UserId=os.getenv("UserID"),
                            Password=os.getenv("Password")) as sqlClient:
            
            self.sqltext = "DROP TABLE VaccineAppointments; DROP TABLE CareGiverSchedule;"
            self.drops = "DROP TABLE Caregivers; DROP TABLE Patients; DROP TABLE PatientAppointmentStatusCodes; DROP TABLE Vaccines; DROP TABLE AppointmentStatusCodes;DROP PROCEDURE InitScheduerApp;"      
            dbcursor = sqlClient.cursor(as_dict=True)
            
            dbcursor.execute(self.sqltext)
            dbcursor.execute(self.drops)
            dbcursor.connection.commit()

  def test_ReserveAppointment(self):
    with SqlConnectionManager(Server=os.getenv("Server"),
                              DBname=os.getenv("DBName"),
                              UserId=os.getenv("UserID"),
                              Password=os.getenv("Password")) as sqlClient:
      with sqlClient.cursor(as_dict=True) as cursor:
        addFivePatients = "INSERT INTO Patients(PatientName, VaccineStatus) VALUES ('Andreia1', 0), ('Andreia2', 0), ('Andreia3', 0), ('Andreia4', 0), ('Andreia5', 0);"
        addSchedules = "INSERT INTO CareGiverSchedule(CaregiverId, WorkDay, SlotTime, SlotHour, SlotMinute, SlotStatus) VALUES (1, '12-12-2021', '11:15:00', 11, 15, 1), (2, '01-12-2022', '12:35:00', 12, 35, 1), (1, '12-13-2021', '11:15:00', 11, 15, 1), (2, '01-13-2022', '12:35:00', 12, 35, 1)"
        getPatientStatus = "SELECT VaccineStatus FROM Patients WHERE PatientId=1"
        getCareGiverStatus = "SELECT SlotStatus FROM CareGiverSchedule WHERE CaregiverSlotSchedulingId=1"
        getVaccineStatus = "SELECT SlotStatus FROM VaccineAppointments WHERE VaccineAppointmentId=1"
        getCaregivers = "SELECT * FROM Caregivers"
        try:
          cursor.execute(getCaregivers)
          row = cursor.fetchall()
          print(row)
          cursor.execute(addFivePatients)
          cursor.execute(addSchedules)
          vaccinepatient = patient()
          reserve = vaccinepatient.ReserveAppointment(1, 'Pfizer', 1, cursor, cursor)
          cursor.execute(getPatientStatus)
          row = cursor.fetchone()
          patientstatus = row['VaccineStatus']
          cursor.execute(getVaccineStatus)
          row = cursor.fetchone()
          vaccinestatus = row['SlotStatus']
          self.assertEqual([1, 1], [patientstatus, vaccinestatus])
        except Exception:
            # clear the tables if an exception occurred
          clear_tables(sqlClient)
          self.fail("Reserve Appointment Failed")
  
  # def test_verify_schedule(self):
  #     with SqlConnectionManager(Server=os.getenv("Server"),
  #                               DBname=os.getenv("DBName"),
  #                               UserId=os.getenv("UserID"),
  #                               Password=os.getenv("Password")) as sqlClient:
  #         with sqlClient.cursor(as_dict=True) as cursor:
  #             try:
  #                 # clear the tables before testing
  #                 clear_tables(sqlClient)
  #                 # create a new VaccineCaregiver object
  #                 self.caregiver_a = VaccineCaregiver(name="Steve Ma",
  #                                                 cursor=cursor)
  #                 # check if schedule has been correctly inserted into CareGiverSchedule
  #                 sqlQuery = '''
  #                            SELECT *
  #                            FROM Caregivers, CareGiverSchedule
  #                            WHERE Caregivers.CaregiverName = 'Steve Ma'
  #                                AND Caregivers.CaregiverId = CareGiverSchedule.CaregiverId
  #                            '''
  #                 cursor.execute(sqlQuery)
  #                 rows = cursor.fetchall()
  #                 hoursToSchedlue = [10,11]
  #                 minutesToSchedlue = [0, 15, 30, 45]
  #                 for row in rows:
  #                     slot_hour = row["SlotHour"]
  #                     slot_minute = row["SlotMinute"]
  #                     if slot_hour not in hoursToSchedlue or slot_minute not in minutesToSchedlue:
  #                         self.fail("CareGiverSchedule verification failed")
  #                 # clear the tables after testing, just in-case
  #                 clear_tables(sqlClient)
  #             except Exception:
  #                 # clear the tables if an exception occurred
  #                 clear_tables(sqlClient)
  #                 self.fail("CareGiverSchedule verification failed")


if __name__ == '__main__':
    unittest.main()
