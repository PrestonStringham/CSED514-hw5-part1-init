from COVID19_vaccine import COVID19Vaccine as covid
class VaccinePatient:
	def __init__(self):
		return None

	def ReserveAppointment(self, CaregiverSlotSchedulingId, Vaccine, PatientId, read_cursor, action_cursor):
		'''
		Check if slot is on hold.
		Create a vaccine appointment.
		Update status of Patient. 
		'''
		# From CareGiverSchedule
		getScheduleInfo = 'SELECT SlotStatus, CaregiverId, WorkDay, SlotTime, SlotHour, SlotMinute FROM CareGiverSchedule WHERE CaregiverSlotSchedulingId=%s'
		read_cursor.execute(getScheduleInfo, CaregiverSlotSchedulingId)
		row = read_cursor.fetchone()
		slot_id = row['SlotStatus']
		
		# Check if appointment is OnHold, 1
		if slot_id != 1:
			raise Exception('Slot on CaregiverSchedule is not OnHold!')

		# get CareGiverId, WorkDay, SlotHour, SlotMinute
		caregiver_id = row['CaregiverId']
		date = row['WorkDay']
		slothour = row['SlotHour']
		slotminute = row['SlotMinute']

		# from Patient
		getPatientInfo = 'SELECT * FROM Patients WHERE PatientId=%s'
		read_cursor.execute(getPatientInfo, PatientId)
		row_patient = read_cursor.fetchone()
		vaccinestatus = row_patient['VaccineStatus']

		if vaccinestatus == 7:
			raise Exception('Patient is fully vaccinated.')
		
		if vaccinestatus >= 3: # check if 1s dose already administered
			dose_number = 2
			new_vaccinestatus = 4 # (4, 'Queued for 2nd Dose')
		else:
			dose_number = 1
			new_vaccinestatus = 1 # (1, 'Queued for 1st Dose');

		# check if vaccine appointment already exists
		getVaccineAppointment = "SELECT VaccineAppointmentId FROM VaccineAppointments WHERE PatientId=%s AND CaregiverId=%s AND ReservationDate=%s AND DoseNumber=%s"
		read_cursor.execute(getVaccineAppointment, ((PatientId), (caregiver_id), (date), (dose_number)))
		row = read_cursor.fetchone()
		if row is None:
			# create vaccine appointment 
			createVaccineAppointment = "INSERT INTO VaccineAppointments (VaccineName, PatientId,  CaregiverId, ReservationDate, ReservationStartHour, ReservationStartMinute, AppointmentDuration, DoseNumber, SlotStatus) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
			action_cursor.execute(createVaccineAppointment, ((Vaccine), (PatientId), (caregiver_id), (date), (slothour), (slotminute), (15), (dose_number), (1)))
		else:
			raise Exception('Patient is already scheduled for this time slot.')

		# change status of patient
		updatePatients = "UPDATE Patients SET VaccineStatus=%s WHERE PatientId=%s"
		action_cursor.execute(updatePatients, ((new_vaccinestatus), (PatientId)))

		# return vaccineAppointmentId
		getVaccineAppointment = "SELECT VaccineAppointmentId FROM VaccineAppointments WHERE PatientId=%s AND CaregiverId=%s AND ReservationDate=%s AND DoseNumber=%s"
		read_cursor.execute(getVaccineAppointment, ((PatientId), (caregiver_id), (date), (dose_number)))
		row_appointment = read_cursor.fetchone()
		appointment_id = row_appointment['VaccineAppointmentId']
		return appointment_id

	def ScheduleAppointment(read_cursor, action_cursor, slotid, vaccineappointmentid):
		'''
		Insert vaccineappointmentid into caregiver schedule
		Reserve doses
		Update patient status code
		'''
		updateCGS = "UPDATE CareGiverSchedule SET VaccineAppointmentId=%s WHERE CaregiverSlotSchedulingId=%s"
		getPatientId = "SELECT PatientId FROM VaccineAppointments WHERE VaccineAppointmentId=%s"
		updatePatientStatus = "UPDATE Patients SET VaccineStatus=VaccineStatus+1 WHERE PatientId=%s"
		try:
			action_cursor.execute(updateCGS, ((vaccineappointmentid), (slotid)))
			read_cursor.execute(getPatientId, (vaccineappointmentid))
			row = read_cursor.fetchone()
			patientid = row['PatientId']
			print('patientid: ', patientid)
			action_cursor.execute(updatePatientStatus, (patientid))
			covid.ReserveDoses(read_cursor, action_cursor, vaccineappointmentid)
			print('Patient successfully scheduled.')
		except:
			action_cursor.connection.rollback()
			raise Exception('Could not schedule appointment.')