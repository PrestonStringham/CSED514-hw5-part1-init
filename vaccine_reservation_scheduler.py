import datetime
from enum import IntEnum
import os
import pymssql
import traceback

from sql_connection_manager import SqlConnectionManager
from vaccine_caregiver import VaccineCaregiver
from enums import *
from utils import *
from COVID19_vaccine import COVID19Vaccine as covid
from vaccine_patient import VaccinePatient as patient


class VaccineReservationScheduler:

    def __init__(self):
        return

    def PutHoldOnAppointmentSlot(self, cursor, Date, TimeLower, TimeUpper):
        ''' Method that reserves a CareGiver appointment slot &
        returns the unique scheduling slotid
        Should return 0 if no slot is available  or -1 if there is a database error'''
        # Note to students: this is a stub that needs to replaced with your code
        with SqlConnectionManager(Server=os.getenv("Server"),
                                   DBname=os.getenv("DBName"),
                                   UserId=os.getenv("UserID"),
                                   Password=os.getenv("Password")) as sqlClient:
            dbcursor = sqlClient.cursor(as_dict=True)
            # Setting inventory to zero
            self.sqltext = "SELECT TOP 1 CaregiverSlotSchedulingId FROM CareGiverSchedule WHERE WorkDay=%s AND  SlotTime BETWEEN  %$ AND %s ORDER BY SlotTime ASC"
            try:
                dbcursor.execute(self.sqltext, ((Date), (TimeLower), (TimeUpper)))
                rows = dbcursor.fetchone()
                slot_id = rows['CaregiverSlotSchedulingId']

                # No appointments available
                if slot_id is None:
                    return 0

                # Update status CaregiverSchedule to OnHold (statusCodeId=1, StatusCode='OnHold')
                self.updateCaregiverSQL = "UPDATE CareGiverSchedule SET SlotStatus=1 WHERE CaregiverSlotSchedulingId=%s"
                cursor.execute(self.updateCaregiverSQL, (str(slotid)))

                cursor.connection.commit()
                return slot_id
            
            except pymssql.Error as db_err:
                print("Database Programming Error in SQL Query processing! ")
                print("Exception code: " + str(db_err.args[0]))
                if len(db_err.args) > 1:
                    print("Exception message: " + db_err.args[1])           
                print("SQL text that resulted in an Error: " + self.sqltext)
                cursor.connection.rollback()
                return -1

    #FOR VACCINEAPPOINTMENT
    #MARK PATIENT SCHEDULED
    #MARK CAREGIVER SCHEDULED
    #RESERVE DOSES
    def ScheduleAppointmentSlot(self, slotid, cursor):
        '''method that marks a slot on Hold with a definite reservation  
        slotid is the slot that is currently on Hold and whose status will be updated 
        returns the same slotid when the database update succeeds 
        returns 0 is there if the database update dails 
        returns -1 the same slotid when the database command fails
        returns 21 if the slotid parm is invalid '''
        # Note to students: this is a stub that needs to replaced with your code
        if slotid < 1:
            return -2
        self.slotSchedulingId = slotid
        self.getSlotStatuses = "SELECT VA.PatientId as PatientId, VA.SlotStatus as VASlotStatus, CGS.SlotStatus as CGSSlotStatus, P.VaccineStatus as PVaccineStatus FROM VaccineAppointments as VA, CareGiverSchedule as CGS, Patients as P WHERE VA.VaccineAppointmentId=%s AND CGS.VaccineAppointmentId=%s AND P.PatientId = VA.PatientId"
        self.updateAppointmentSQL = "UPDATE VaccineAppointments SET SlotStatus=SlotStatus+1 WHERE VaccineAppointmentId=%s"
        self.updatePatientsSQL = "UPDATE Patients SET VaccineStatus=VaccineStatus+1 WHERE PatientId=%s"
        self.updateCaregiverSQL = "UPDATE CareGiverSchedule SET SlotStatus=SlotStatus+1 WHERE VaccineAppointmentId=%s"
        try:
            cursor.execute(self.getSlotStatuses, (str(slotid), (str(slotid))))
            row = cursor.fetchone()
            patientid = row['PatientId']
            vaslotstatus = row['VASlotStatus']
            cgsslotstatus = row['CGSSlotStatus']
            pslotstatus = row['PVaccineStatus']
            if vaslotstatus == 1 and cgsslotstatus == 1 and (pslotstatus==1 or pslotstatus==4):
                cursor.execute(self.updateAppointmentSQL, (str(slotid)))
                cursor.execute(self.getPatientId, (str(slotid)))
                cursor.execute(self.updatePatientsSQL, (str(patientid)))
                cursor.execute(self.updateCaregiverSQL, (str(slotid)))
                cursor.connection.commit()
                print('Sucessfully scheduled slotid.')
                return self.slotSchedulingId
            else:
                raise Exception('One slot status was not marked as reserved.')
        except pymssql.Error as db_err:
            cursor.connection.rollback()    
            print("Database Programming Error in SQL Query processing! ")
            print("Exception code: " + db_err.args[0])
            if len(db_err.args) > 1:
                print("Exception message: " + str(db_err.args[1]))  
            print("SQL text that resulted in an Error: " + self.getAppointmentSQL)
            return -1

if __name__ == '__main__':
        with SqlConnectionManager(Server=os.getenv("Server"),
                                  DBname=os.getenv("DBName"),
                                  UserId=os.getenv("UserID"),
                                  Password=os.getenv("Password")) as sqlClient:
            vrs = VaccineReservationScheduler()

            # get a cursor from the SQL connection
            dbcursor = sqlClient.cursor(as_dict=True)

            # Iniialize the caregivers, patients & vaccine supply
            # caregiversList = []
            # caregiversList.append(VaccineCaregiver('Carrie Nation', dbcursor))
            # caregiversList.append(VaccineCaregiver('Clare Barton', dbcursor))
            # caregivers = {}
            # for cg in caregiversList:
            #     cgid = cg.caregiverId
            #     caregivers[cgid] = cg

            # Add a vaccine and Add doses to inventory of the vaccine
            #vaccines = {'Moderna': {'Supplier': 'Moderna', 'inventory': 100, 'shotsnecessary': 2, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 28}, 'Pfizer': {'Supplier': 'Pfizer', 'inventory': 100, 'shotsnecessary': 2, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 28}, 'JohnsonJohnson': {'Supplier': 'JJ', 'inventory': 100, 'shotsnecessary': 1, 'DaysBetweenDosesLower': 21, 'DaysBetweenDosesUpper': 28}}
            #vaccinedb = covid(dbcursor, vaccines)
            # Ass patients
            # Schedule the patients
            #covid.AddDoses(dbcursor, 'Moderna', 30)
            vrs.ScheduleAppointmentSlot(1, dbcursor)
            # Test cases done!
            #covid.ReserveDoses(dbcursor, 2)
            # clear_tables(sqlClient)
