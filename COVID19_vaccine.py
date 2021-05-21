import pymssql

class COVID19Vaccine:
    def __init__(self, action_cursor, init_vaccines):
        vaccine_names = list(init_vaccines.keys())
        vaccine_inv = list(init_vaccines.values())
        vaccine_suppliers = [x['Supplier'] for x in vaccine_inv]
        vaccine_inventory = [x['inventory'] for x in vaccine_inv]
        vaccine_shotsnecessary = [x['shotsnecessary'] for x in vaccine_inv]
        vaccine_dayslower = [x['DaysBetweenDosesLower'] for x in vaccine_inv]
        vaccine_daysupper = [x['DaysBetweenDosesUpper'] for x in vaccine_inv]
        try:
            for i in range(len(vaccine_names)):
                self.sqltext = "INSERT INTO Vaccines (VaccineName, VaccineSupplier, AvailableDoses, ReservedDoses, TotalDoses, DosesPerPatient, DaysBetweenDosesLower, DaysBetweenDosesUpper) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                action_cursor.execute(self.sqltext, ((vaccine_suppliers[i]), (vaccine_names[i]), (str(vaccine_inventory[i])), (str(0)), (str(vaccine_inventory[i])), (str(vaccine_shotsnecessary[i])), (str(vaccine_dayslower[i])), (str(vaccine_daysupper[i]))))
                action_cursor.connection.commit()
        except pymssql.Error as db_err:
          print("Database Programming Error in SQL Query processing for Vaccines! ")
          print("Exception code: " + str(db_err.args[0]))
          if len(db_err.args) > 1:
              print("Exception message: " + db_err.args[1])
          print("SQL text that resulted in an Error: " + self.sqltext)

    def AddDoses(action_cursor, vaccinename, new_inventory):
        if new_inventory < 0:
            raise Exception('New inventory must be greater than zero.')
        try:
            sqltext = "UPDATE Vaccines SET AvailableDoses = AvailableDoses + %s WHERE VaccineName=%s"
            action_cursor.execute(sqltext, ((new_inventory), (vaccinename)))
            sqltext = "UPDATE Vaccines SET TotalDoses = TotalDoses + %s WHERE VaccineName=%s"
            action_cursor.execute(sqltext, ((new_inventory), (vaccinename)))
            print("Successfully added %s doses to vaccineid %s", new_inventory, vaccinename)
        except pymssql.Error as db_err:
            print("ERROR: Could not add new doses. Pymssql error: " + db_err.args[1])
        return None

    def ReserveDoses(read_cursor, action_cursor, VaccineAppointmentId):
        try:
            sqltext = "SELECT va.VaccineName AS vaccinename, va.DoseNumber as DoseNumber, v.DosesPerPatient AS shotsnecessary, v.AvailableDoses AS inventory, v.ReservedDoses AS reserved FROM VaccineAppointments as va, Vaccines as v WHERE va.VaccineName=v.VaccineName AND va.VaccineAppointmentId=%s"
            read_cursor.execute(sqltext, (VaccineAppointmentId))
            row = read_cursor.fetchone()
            current_inventory = row['inventory']
            shots_necessary = row['shotsnecessary']
            is_first_shot = row['DoseNumber']
            current_reserved = row['reserved'] 
            vaccineid = row['vaccinename']
            if is_first_shot == 2:
                return None
            if shots_necessary > current_inventory: 
                raise Exception( "Not enough vaccines. Please try a different vaccine or another vaccine!")
            else:
                sqltext = "UPDATE Vaccines SET AvailableDoses=%s, ReservedDoses=%s WHERE VaccineName=%s"
                if is_first_shot==1: 
                    action_cursor.execute(sqltext, ((current_inventory - shots_necessary), (current_reserved + shots_necessary), (vaccineid)))
                    new_reserved = current_reserved + shots_necessary
                    print("Successfully reserved doses.")
        except pymssql.Error as db_err:
            print("ERROR: Could not reserve new doses. Pymssql error: " + db_err.args[1])
        return None

