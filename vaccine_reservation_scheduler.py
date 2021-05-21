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
from VaccinePatient import VaccinePatient as pat


class VaccineReservationScheduler:

    def __init__(self):
        return
    
    def ScheduleProcess(self, read_cursor, action_cursor, PatientId, Date, DateUpper='99-99-9999', Vaccine='Pfizer', TimeLower='00:00:00', TimeUpper='23:59:59'):
        '''
        Full process for scheduling a vaccine appointment. 
        '''
        # put hold on slot of Caregiver Scheduler  
        slotid = self.PutHoldOnAppointmentSlot(read_cursor, action_cursor, Date, DateUpper, TimeLower, TimeUpper) 
        patient = pat()
        #check for invalid output 0, -1 or -2  
        if slotid <= 0:
            raise Exception('Error finding slot in Caregiver Schedule.')
        
        # creates vaccine appointment def ReserveAppointment(self, CaregiverSlotSchedulingId, Vaccine, PatientId, read_cursor, action_cursor):
        vaccineappointmentid = patient.ReserveAppointment(slotid, Vaccine, PatientId, read_cursor, action_cursor)
        
        # change status to scheduled
        scheduleslot = self.ScheduleAppointmentSlot(vaccineappointmentid, slotid, read_cursor, action_cursor)
        # check for invalid -1 or -2
        if scheduleslot <= 0:
            raise Exception('Error scheduling slot in Caregiver Schedule.')
        
        # update tables in database post scheduling
        patient.ScheduleAppointment(read_cursor, action_cursor, slotid, vaccineappointmentid)
        return None

    def FullScheduler(self, read_cursor, action_cursor, PatientId, Date, DateUpper='99-99-9999', Vaccine='Pfizer', TimeLower='00:00:00', TimeUpper='23:59:59'):
        '''
        Reserves appointment(s) for patient.
        '''
        # schedule first appointment
        self.ScheduleProcess(read_cursor, action_cursor, PatientId, Date, DateUpper, Vaccine, TimeLower, TimeUpper)
        
        # get vaccine number of doses and TimeBetweenLower/TimeBetweenUpper
        getVaccineInfo = 'SELECT * FROM Vaccines WHERE VaccineName=%s'
        read_cursor.execute(getVaccineInfo, Vaccine)
        row = read_cursor.fetchone()
        number_doses = row['DosesPerPatient']
        BetweenLower = row['DaysBetweenDosesLower']
        BetweenUpper = row['DaysBetweenDosesUpper']

        # check if needs 2nd appointment
        if number_doses == 2:
            NewDate = (datetime.datetime.strptime(Date, '%m-%d-%Y') + datetime.timedelta(days=BetweenLower)).strftime('%m-%d-%Y')
            NewDateUpper = (datetime.datetime.strptime(Date, '%m-%d-%Y') + datetime.timedelta(days=BetweenUpper)).strftime('%m-%d-%Y')
            self.ScheduleProcess (read_cursor, action_cursor, PatientId, NewDate, NewDateUpper, Vaccine, TimeLower, TimeUpper)

            return 'Your appointments for your 2 (two) doses are scheduled!'

        return 'Your appointment is scheduled!' 

        



    def PutHoldOnAppointmentSlot(self, read_cursor, action_cursor, Date, DateUpper='99-99-9999', TimeLower='00:00:00', TimeUpper='23:59:59'):
        ''' Method that reserves a CareGiver appointment slot &
        returns the unique scheduling slotid
        Should return 0 if no slot is available  or -1 if there is a database error'''
        # Note to students: this is a stub that needs to replaced with your code
        # Setting inventory to zero
        if DateUpper == '99-99-9999':
            DateUpper = Date
        self.sqltext = "SELECT TOP 1 CaregiverSlotSchedulingId FROM CareGiverSchedule WHERE SlotStatus=0 AND WorkDay>= %s AND WorkDay <= %s AND SlotTime BETWEEN %s AND %s ORDER BY WorkDay, SlotTime ASC"
        try:
            read_cursor.execute(self.sqltext, ((Date), (DateUpper), (TimeLower), (TimeUpper)))
            rows = read_cursor.fetchone()
            # No appointments available
            if rows is None:
                return 0
            slot_id = rows['CaregiverSlotSchedulingId']

            # Update status CaregiverSchedule to OnHold (statusCodeId=1, StatusCode='OnHold')
            self.updateCaregiverSQL = "UPDATE CareGiverSchedule SET SlotStatus=1 WHERE CaregiverSlotSchedulingId=%s"
            action_cursor.execute(self.updateCaregiverSQL, (str(slot_id)))

            action_cursor.connection.commit()
            return slot_id
        
        except pymssql.Error as db_err:
            print("Database Programming Error in SQL Query processing! ")
            print("Exception code: " + str(db_err.args[0]))
            if len(db_err.args) > 1:
                print("Exception message: " + db_err.args[1])           
            print("SQL text that resulted in an Error: " + self.sqltext)
            action_cursor.connection.rollback()
            return -1

    #FOR VACCINEAPPOINTMENT
    #MARK PATIENT SCHEDULED
    #MARK CAREGIVER SCHEDULED
    #RESERVE DOSES
    def ScheduleAppointmentSlot(self, vaccineappointmentid, slotid, read_cursor, action_cursor):
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
        self.getCGStatus = "SELECT SlotStatus FROM CareGiverSchedule WHERE CaregiverSlotSchedulingId=%s"
        self.getVAStatus = "SELECT SlotStatus FROM VaccineAppointments WHERE VaccineAppointmentId=%s"
        # Update caregiver slot status
        self.updateCaregiverSchedule = "UPDATE CareGiverSchedule SET SlotStatus=SlotStatus+1 WHERE CaregiverSlotSchedulingId=%s"
        # Update vaccine appointment status
        self.updateVaccineAppStatus = "UPDATE VaccineAppointments SET SlotStatus=SlotStatus+1 WHERE VaccineAppointmentId=%s"
        try:
            # Get cgsstatus
            read_cursor.execute(self.getCGStatus, (str(slotid)))
            row = read_cursor.fetchone()
            cgstatus = row['SlotStatus']
            # Get vastatus
            read_cursor.execute(self.getVAStatus, (str(vaccineappointmentid)))
            row = read_cursor.fetchone()
            vastatus = row['SlotStatus']
            # Check to make sure statuses are in correct position
            if cgstatus == 1 and vastatus == 1:
                action_cursor.execute(self.updateCaregiverSchedule, (str(slotid)))
                action_cursor.execute(self.updateVaccineAppStatus, (str(vaccineappointmentid)))
                print('Sucessfully scheduled slotid.')
                return self.slotSchedulingId
            else:
                raise Exception('One slot status was not marked as reserved.')
        except pymssql.Error as db_err:
            action_cursor.connection.rollback()    
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
            read_cursor = sqlClient.cursor(as_dict=True)
            action_cursor = sqlClient.cursor(as_dict=True)

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
            # patientid = 1
            # slotid = vrs.PutHoldOnAppointmentSlot(read_cursor, action_cursor, '12-12-2021')
            # vaccinepatient = patient()
            # vaccineappointmentid = vaccinepatient.ReserveAppointment(slotid, 'Pfizer', patientid, read_cursor, action_cursor)
            # print(slotid)
            # print(vaccineappointmentid)
            # slotid = vrs.ScheduleAppointmentSlot(vaccineappointmentid, slotid, read_cursor, action_cursor)
            # patient.ScheduleAppointment(read_cursor, action_cursor, slotid, vaccineappointmentid)
            #FullScheduler(self, read_cursor, action_cursor, PatientId, Date, DateUpper='99-99-9999', Vaccine='Pfizer', TimeLower='00:00:00', TimeUpper='23:59:59'):
            #vrs.FullScheduler(read_cursor, action_cursor, 1, '12-12-2021', '12-12-2022', 'Pfizer', '10:00:00', '14:00:00')
            # Test cases done!
            #covid.ReserveDoses(dbcursor, 2)
            # clear_tables(sqlClient)


#Call it 2x here
