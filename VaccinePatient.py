from VaccineReservationScheduler import VaccineReservationScheduler as scheduler
from COVID19_vaccine import COVID19Vaccine as covid
class VaccinePatient:
	def __init__(self, cursor, patientid):
		self.covid = covid()
		self.patientid = patientid
		self.getPatientInfo = "SELECT V.DosesPerPatient, VA.DoseNumber FROM Vaccines AS V, VaccineAppointments AS VA WHERE VA.VaccineAppointmentId=%s AND VA.VaccineName = V.VaccineName"

class VaccinePatient:
	def __init__(self, cursor, patientid):
		self.covid = covid()
		self.patientid = patientid
		self.getPatientInfo = "SELECT V.DosesPerPatient, VA.DoseNumber FROM Vaccines AS V, VaccineAppointments AS VA WHERE VA.VaccineAppointmentId=%s AND VA.VaccineName = V.VaccineName"

	def ReserveAppointment(CaregiverSlotSchedulingId, Vaccine, PatientId, cursor):
		'''
		Check if slot is on hold.
		Create a vaccine appointment.
		Update status of Patient. 
		'''
		# From CareGiverSchedule
		self.getScheduleInfo('SELECT SlotStatus, CaregiverId, WorkDay, SlotTime, SlotHour, SlotMinute FROM CareGiverSchedule WHERE CaregiverSlotSchedulingId=%s')
		cursor.execute(self.getScheduleInfo, CaregiverSlotSchedulingId)
		row = cursor.fetchone()
		slot_id = row['SlotStaus']
		
		# Check if appointment is OnHold, 1
		if slot_id != 1:
			raise Exception('Slot on CaregiverSchedule is not OnHold!')

		# get CareGiverId, WorkDay, SlotHour, SlotMinute
		caregiver_id = row['CaregiverId']
		date = row['WorkDay']
		slothour = row['SlotHour']
		slotminute = row['SlotMinute']

		# from Patient
		self.getPatientInfo('SELECT * FROM Patients WHERE PatientId=%s')
		cursor.execute(self.getPatientInfo, PatientId)
		row_patient = cursor.fetchone()
		vaccinestatus = row_patient['VaccineStatus']

		if vaccinestatus >= 3: # check if 1s dose already administered
			dose_number = 2
			new_vaccinestatus = 4 # (4, 'Queued for 2nd Dose')
		else:
			dose_number = 1
			new_vaccinestatus = 1 # (1, 'Queued for 1st Dose');

		# create vaccine appointment 
		self.createVaccineAppointment = "INSERT INTO VaccineAppointments (VaccineName, PatientId,  CaregiverId, ReservationDate, ReservationStartHour, ReservationStartMinute, AppointmentDuration, DoseNumber) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
		cursor.execute(self.createVaccineAppointment, Vaccine, PatientId, caregiver_id, date, slothour, slotminute, 15, dose_number)

		# change status of patient
		self.updatePatients = "UPDATE Patients SET VaccineStatus=%s WHERE PatientId=%s"
		cursor.execute(self.updatePatients, new_vaccinestatus, PatientId )

		# return vaccineAppointmentId
		self.getVaccineAppointment = "SELECT VaccineAppointmentId FROM VaccineAppointments WHERE PatientId=%s AND CaregiverId=%s AND ReservationDate=%s AND DoseNumber=%s) VALUES(%s, %s, %s, %s)"
		cursor.execute(self.getVaccineAppointment, PatientId, caregiver_id, date, dose_number)
		row_appointment = cursor.fetchone()
		appointment_id = row_patient['VaccineAppointmentId']

		return appointment_id

	def ScheduleAppointment(cursor, slotid):
		self.getPatientInfo = "SELECT V.DosesPerPatient AS DosesPerPatient, VA.DoseNumber AS DoseNumber FROM Vaccines AS V, VaccineAppointments AS VA WHERE VA.VaccineAppointmentId=%s AND VA.VaccineName = V.VaccineName"
		cursor.execute(self.getPatientInfo)
		row = cursor.fetchone()
		dose_number = row['DoseNumber']
		doses_per_patient = row['DosesPerPatient']
		if does_number > doses_per_patient:
			raise Exception('Patient dose number exceeds maxiumum number of doses per patient for this vaccine.')
		if dose_number = 1:
			covid.ReserveDoses(slotid)
		scheduler.ScheduleAppointmentSlot(slotid, cursor)
		print('Appointment successfully scheduled.')
		return None