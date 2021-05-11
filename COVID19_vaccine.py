import pymssql

class COVID19Vaccine:
    def __init__(self, cursor, init_vaccines):
        vaccine_names = list(init_vaccines.keys())
        vaccine_inv = list(init_vaccines.values())
        try:
            for i in range(len(vaccine_names)):
                self.sqltext = "INSERT INTO Vaccines (Name, inventory, reserved) VALUES (%s, %s, %s)"
                cursor.execute(self.sqltext, ((vaccine_names[i]), (str(vaccine_inv[i])), (0)))
                cursor.connection.commit()
        except pymssql.Error as db_err:
          print("Database Programming Error in SQL Query processing for Vaccines! ")
          print("Exception code: " + str(db_err.args[0]))
          if len(db_err.args) > 1:
              print("Exception message: " + db_err.args[1])
          print("SQL text that resulted in an Error: " + self.sqltext)

    def AddDoses(cursor, vaccineid, new_inventory):
        try:
            sqltext = "SELECT inventory FROM Vaccines WHERE vaccineid=%s"
            cursor.execute(sqltext, (vaccineid))
            row = cursor.fetchone()
            current_inventory = row['inventory']
            sqltext = "UPDATE Vaccines SET inventory=%s WHERE vaccineid=%s"
            cursor.execute(sqltext, ((current_inventory + new_inventory), (vaccineid)))
            cursor.connection.commit()
            print("Successfully added %s doses to vaccineid %s", new_inventory, vaccineid)
        except pymssql.Error as db_err:
            print("ERROR: Could not add new doses. Pymssql error: " + db_err.args[1])
        return None

    def ReserveDoeses(cursor, VaccineAppointmentId):
        try:
            sqltext = ''' SELECT va.vaccineid AS vaccineid, va.firstshot as firstshot, v.shotsnecessary AS shotsnecessary, v.inventory AS inventory, v.reserved AS reserved
            FROM VaccineAppointment as va, Vaccines as v, CareGiverSchedule as cgs, AppointmentStatusCodes as statuscode 
            WHERE va.vaccineid=v.vaccine_id AND cgs.VaccineAppoinmentid=va.VaccineAppointmentId AND statuscode.StatusCodeId=cgs.SlotStatus
            AND VaccineAppointmentId=%s AND statuscode.StatusCode=''Open'' 
            '''


            cursor.execute(sqltext, (VaccineAppointmentId))
            row = cursor.fetchone()
            current_inventory = row['inventory']
            shots_necessary = row['shotsnecessary']
            is_first_shot = row['firstshot']
            current_reserved = row['reserved'] 

            if shots_necessary < current_inventory: 
                raise Exception( "Not enough vaccines. Please try a different vaccine or another vaccine!")
            else:
                sqltext = "UPDATE Vaccines SET inventory=%s, reserved=%s WHERE vaccineid=%s"
                if is_first_shot==1: 
                    cursor.execute(sqltext, ((current_inventory - shots_ncessary), (current_reserved + shots_necessary), (vaccineid)))
                    cursor.connection.commit()
                    new_reserved = current_reserved + shots_necessary
                    print("Successfully reserved %s doses from vaccineid %s. Current reserved doses: %s", shots_necessary, vaccineid, new_reserved)
        except pymssql.Error as db_err:
            print("ERROR: Could not reserve new doses. Pymssql error: " + db_err.args[1])
        return None 

