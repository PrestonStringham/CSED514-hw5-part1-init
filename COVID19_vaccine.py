import pymssql

class COVID19Vaccine:
    def __init__(self, cursor, init_vaccines):
        vaccine_names = list(init_vaccines.keys())
        vaccine_inv = list(init_vaccines.values())
        vaccine_suppliers = [x['Supplier'] for x in vaccine_inv]
        vaccine_inventory = [x['inventory'] for x in vaccine_inv]
        vaccine_shotsnecessary = [x['shotsnecessary'] for x in vaccine_inv]
        vaccine_dayslower = [x['DaysBetweenDosesLower'] for x in vaccine_inv]
        vaccine_daysupper = [x['DaysBetweenDosesUpper'] for x in vaccine_inv]

        def __init__(self, cursor):
            self.cursor = cursor

        try:
            for i in range(len(vaccine_names)):
                self.sqltext = "INSERT INTO Vaccines (VaccineName, VaccineSupplier, AvailableDoses, ReservedDoses, TotalDoses, DosesPerPatient, DaysBetweenDosesLower, DaysBetweenDosesUpper) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(self.sqltext, ((vaccine_suppliers[i]), (vaccine_names[i]), (str(vaccine_inventory[i])), (str(0)), (str(vaccine_inventory[i])), (str(vaccine_shotsnecessary[i])), (str(vaccine_dayslower[i])), (str(vaccine_daysupper[i]))))
                cursor.connection.commit()
        except pymssql.Error as db_err:
          print("Database Programming Error in SQL Query processing for Vaccines! ")
          print("Exception code: " + str(db_err.args[0]))
          if len(db_err.args) > 1:
              print("Exception message: " + db_err.args[1])
          print("SQL text that resulted in an Error: " + self.sqltext)

    def AddDoses(cursor, vaccinename, new_inventory):
        if new_inventory < 0:
            raise Exception('New inventory must be greater than zero.')
        try:
            sqltext = "UPDATE Vaccines SET AvailableDoses = AvailableDoses + %s WHERE VaccineName=%s"
            cursor.execute(sqltext, ((new_inventory), (vaccinename)))
            sqltext = "UPDATE Vaccines SET TotalDoses = TotalDoses + %s WHERE VaccineName=%s"
            cursor.execute(sqltext, ((new_inventory), (vaccinename)))
            cursor.connection.commit()
            print("Successfully added %s doses to vaccineid %s", new_inventory, vaccinename)
        except pymssql.Error as db_err:
            print("ERROR: Could not add new doses. Pymssql error: " + db_err.args[1])
        return None

    def ReserveDoses(cursor, VaccineAppointmentId):
        try:
            sqltext = "SELECT va.VaccineName AS vaccinename, va.DoseNumber as DoseNumber, v.DosesPerPatient AS shotsnecessary, v.AvailableDoses AS inventory, v.ReservedDoses AS reserved FROM VaccineAppointments as va, Vaccines as v, CareGiverSchedule as cgs WHERE va.VaccineName=v.VaccineName AND cgs.VaccineAppointmentId=va.VaccineAppointmentId  AND cgs.VaccineAppointmentId=1 '"
            cursor.execute(sqltext, (VaccineAppointmentId))
            row = cursor.fetchone()
            current_inventory = row['inventory']
            print(current_inventory)
            shots_necessary = row['shotsnecessary']
            print(shots_necessary)
            is_first_shot = row['DoseNumber']
            current_reserved = row['reserved'] 
            vaccineid = row['vaccinename']

            if shots_necessary > current_inventory: 
                raise Exception( "Not enough vaccines. Please try a different vaccine or another vaccine!")
            else:
                sqltext = "UPDATE Vaccines SET AvailableDoses=%s, ReservedDoses=%s WHERE VaccineName=%s"
                if is_first_shot==1: 
                    cursor.execute(sqltext, ((current_inventory - shots_necessary), (current_reserved + shots_necessary), (vaccineid)))
                    cursor.connection.commit()
                    new_reserved = current_reserved + shots_necessary
                    print("Successfully reserved %s doses from vaccineid %s. Current reserved doses: %s", shots_necessary, vaccineid, new_reserved)
        except pymssql.Error as db_err:
            print("ERROR: Could not reserve new doses. Pymssql error: " + db_err.args[1])
        return None

