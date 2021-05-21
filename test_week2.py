import unittest
import os

from sql_connection_manager import SqlConnectionManager
from vaccine_caregiver import VaccineCaregiver
from enums import *
from utils import *
from COVID19_vaccine import COVID19Vaccine as covid
from VaccinePatient import VaccinePatient as patient
from vaccine_reservation_scheduler import VaccineReservationScheduler as schedule
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
          vaccines = {'Pfizer': {'Supplier': 'Pfizer', 'inventory': 5, 'shotsnecessary': 2, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 42}}
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

  # Initial test of ReserveAppointment. Checks that status codes get updated properly.
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
          # check that slot statuses are correct
          self.assertEqual([1, 1], [patientstatus, vaccinestatus])
        except Exception:
            # clear the tables if an exception occurred
          clear_tables(sqlClient)
          self.fail("Reserve Appointment Failed")

  def test_FivePatientScenario(self):
    with SqlConnectionManager(Server=os.getenv("Server"),
                              DBname=os.getenv("DBName"),
                              UserId=os.getenv("UserID"),
                              Password=os.getenv("Password")) as sqlClient:
      with sqlClient.cursor(as_dict=True) as cursor:
        addFivePatients = "INSERT INTO Patients(PatientName, VaccineStatus) VALUES ('Andreia1', 0), ('Andreia2', 0), ('Andreia3', 0), ('Andreia4', 0), ('Andreia5', 0);"
        addSchedules = "INSERT INTO CareGiverSchedule(CaregiverId, WorkDay, SlotTime, SlotHour, SlotMinute, SlotStatus) VALUES (1, '12-12-2021', '11:15:00', 11, 15, 0), (2, '01-12-2022', '12:35:00', 12, 35, 0), (1, '12-13-2021', '11:15:00', 11, 15, 0), (2, '01-13-2022', '12:35:00', 12, 35, 0), (1, '12-14-2021', '11:15:00', 11, 15, 0), (2, '01-14-2022', '12:35:00', 12, 35, 0), (1, '12-15-2021', '11:15:00', 11, 15, 0), (2, '01-15-2022', '12:35:00', 12, 35, 0), (1, '12-16-2021', '11:15:00', 11, 15, 0), (2, '01-16-2022', '12:35:00', 12, 35, 0)"
        cursor.execute(addFivePatients)
        cursor.execute(addSchedules)
        scheduler = schedule()
        # Scheduling the first patient runs fine
        scheduler.FullScheduler(cursor, cursor, 1, '12-12-2021', '1-12-2022', 'Pfizer', '10:00:00', '14:00:00')
        # Scheduling the second patient runs fine
        scheduler.FullScheduler(cursor, cursor, 2, '12-13-2021', '1-13-2022', 'Pfizer', '10:00:00', '14:00:00')
        # Scheduling the third patient fails due to the lack of pfizer inventory
        self.assertRaisesRegex(Exception, 'Could not schedule appointment.', scheduler.FullScheduler, cursor, cursor, 3, '12-14-2021', '1-14-2022', 'Pfizer', '10:00:00', '14:00:00')
        # Scheduling the fourth patient fails due to the lack of pfizer inventory
        self.assertRaisesRegex(Exception, 'Could not schedule appointment.', scheduler.FullScheduler, cursor, cursor, 4, '12-15-2021', '1-15-2022', 'Pfizer', '10:00:00', '14:00:00')
        # Scheduling the fifth patient fails due to the lack of pfizer inventory
        self.assertRaisesRegex(Exception, 'Could not schedule appointment.', scheduler.FullScheduler, cursor, cursor, 5, '12-16-2021', '1-16-2022', 'Pfizer', '10:00:00', '14:00:00')
        sql = "SELECT COUNT(DISTINCT PatientId) as patientcount FROM VaccineAppointments WHERE SlotStatus=2"
        cursor.execute(sql)
        row = cursor.fetchone()
        count = row['patientcount']
        # Check that only 2 patients were actually scheduled
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
