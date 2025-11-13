from oxychai_app.models import Appointment, Depth, HoodSizes, Layouts, Masks, PipeLength, Price, MaskSizes, Time, Calendar, TracheaSizes, appointmentLayout, patient, MoneyOwed, MoneyPayed, Extras, Notes
from django.db.models import Q, Sum
import traceback
import json 

class MyException(Exception):
    pass

class RetrieveApp():
    def patients_not_booked(date_id, session_id):
        """returns list of all those not at appointment"""
        try:
            booked_apps = Appointment.objects.filter(dateID = date_id).filter(sessionTime = session_id).filter(~Q(appointmentStatus = 'CANC'))
            booked_ids = []
            for app in booked_apps:
                booked_ids.append(app.patientID.personID)
            all_active = patient.objects.filter(active = True).order_by('last_name', 'first_name')
            not_booked = []
            for person in all_active:
                if person.personID not in booked_ids:
                    not_booked.append({'name':f"{person.first_name} {person.last_name}", 'id':person.personID})
            return not_booked
        except Exception as e:
            print(e)
            raise LookupError('couldnt find not booked patients')


    def get_appointment(appointment_id):
        try:
            appointment = Appointment.objects.get(id = appointment_id)
            return appointment
        except Exception as e:
            print(e)
            raise LookupError('couldnt find appointment')

    def find_existing(date_id, session_id, patient_id):
        try:
            existing_appointments = Appointment.objects.filter(dateID = date_id, sessionTime = session_id, patientID = patient_id)
            if existing_appointments:
                #get first
                first_id = existing_appointments.first().id
                first_existing  = Appointment.objects.get(id = first_id)
                return first_existing
            else:
                return False
        except Exception as e:
            print(e)
            raise LookupError('couldnt find existing appointment')
        
    def get_patients(date_id, time_id):
        """returns query set of all those at appointment"""
        try:
            app_q_set = Appointment.objects.filter(dateID= date_id, sessionTime = time_id).filter(~Q(appointmentStatus = 'CANC'))
        except Exception as e:
            print(e)
            raise LookupError('couldnt find appointment')
        patient_ids = []
        unq_app_ids = []
        #loop through set and add all unique app ids to list
        for app in app_q_set:
            p_id = app.patientID.personID
            a_id = app.id
            if p_id not in patient_ids:
                patient_ids.append(p_id)
                unq_app_ids.append(a_id)
        #run query
        try:
            filtered_q = Appointment.objects.filter(id__in = unq_app_ids)
        except Exception as e:
            print(e)
            raise LookupError('cldnt filter out unique people')
        return filtered_q        

    def next_app(date_id, time_id): 
        nextAppSess = None
        nextAppDate = None       
        try:
            session = Time.objects.get(id=time_id)
        except Exception as e:
            print(e)
            raise LookupError(e)
        
        all_sessions = Time.objects.filter(status = True).order_by('time')
        latest_t = all_sessions.last()
        #check if have to go to next day
        if session == latest_t:
            nextAppSess = all_sessions.first()
            nextAppDate = date_id + 1
        else:
            nextAppDate = date_id
            save_this = False
            for sess in all_sessions:
                if save_this:
                    nextAppSess = sess
                    break
                if sess.id == session.id:
                    #save next value
                    save_this = True

        try:
            day_obj = Calendar.objects.get(id=nextAppDate)
        except Exception as e:
            print(e)
            raise LookupError(e)
        try:
            appointments = Appointment.objects.filter(dateID = day_obj).filter(sessionTime = nextAppSess).filter(~Q(appointmentStatus = 'CANC'))
        except Exception as e:
            print(e)
            raise LookupError(e)

        return appointments
    
    def get_depths(queyset):
        """makes dict of depths (patient + depth)"""
        depths = []
        if not queyset:
            return depths
        
        for app in queyset:
            depth = app.patientID.depth
            p_id = app.patientID.personID
            if depth:
                depths.append({'id':p_id, 'depth':depth})

        return depths

    def get_equipment(query_Set):
        try:
            """returns dict of all equipment"""
            people_ids = set()
            for app in query_Set:
                people_ids.add(app.patientID)
            mask = 0
            hood = 0
            mouthpiece = 0
            xl_pipes = 0
            mask_size = []
            hood_size = []
            for p_id in people_ids:
                """try:
                    person =patient.objects.get(personID = p_id)
                except Exception as e:
                    print(e)
                    raise LookupError("couldn't find person")"""
                face_covering = p_id.face_covering
                size = p_id.size
                if xl_pipes:
                    xl_pipes += 1
                if face_covering:
                    if face_covering == 'Mask':
                        mask += 1
                        if mask_size:
                            mask_size.append(size)
                    elif face_covering == 'Mouthpiece':
                        mouthpiece += 1
                    else:
                        hood += 1
                        if hood_size:
                            hood_size.append(size)
            mask_size = ', '.join(mask_size)
            hood_size = ', '.join(hood_size)            

            equipment = {'hood':hood if hood else 'empty', 'hood_sizes':hood_size if hood_size else 'empty',
                        'mask': mask if mask else 'empty', 'mask_sizes':mask_size if mask_size else 'empty',
                            'mouthpiece':mouthpiece if mouthpiece else 'empty', 'xl_pipes': xl_pipes if xl_pipes else 'None'}
            return equipment
        except Exception as e:
            print('equipment finding issue', e)
            return(None)

class BookAppointment():
    def add_appointment(date_id, session_id, patient_id):
        try:
            a = Appointment(dateID = Calendar.objects.get(id = date_id), patientID = patient.objects.get(personID = patient_id), sessionTime = Time.objects.get(id = session_id), appointmentStatus = 'SCHE')
            a.save()
            return True
        except Exception as e:
            traceback.print_exc()
            raise MyException('error')
    
    def cancel_appointment(appointment_id):
        try:
            a = Appointment.objects.get(id = appointment_id)
            a.appointmentStatus = 'CANC'
            a.save()
            return True
        except Exception as e:
            traceback.print_exc()
            raise MyException('error')
        
    def change_status(appointment_id, new_status):
        try:
            if not new_status:
                new_status = 'SCHE'
            if new_status not in ['SCHE', 'CANC', 'ATTE', 'MISS', 'UNWE']:
                raise MyException('invalid status')
            a = Appointment.objects.get(id = appointment_id)
            a.appointmentStatus = new_status
            print('-------new appointment status-------\n', a.patientID)
            a.save()
            print('success')
            return True
        except Exception as e:
            traceback.print_exc()
            raise MyException('error')
        
    def change_panel(appointment_id, new_panel):
        try:
            a = Appointment.objects.get(id = appointment_id)
            a.panelPosition = new_panel
            a.save()
            return True
        except Exception as e:
            traceback.print_exc()
            raise MyException('error')
  
class Layout():
    def get_layout(date_id, session_id):
        try:
            try:
                #.first() to avoid query sets
                layout = appointmentLayout.objects.filter(dateID = date_id).filter(sessionTime = session_id).first()
                if not layout:
                    return(None)
                layout = layout.layout.image.url
            except Exception as e:
                print(e)
                raise LookupError("couldn't find layout")
            return layout
        except Exception as e:
            print('layout finding issue', e)
            return(None)

    def get_layout_and_id(date_id, session_id):
        try:
            try:
                #.first() to avoid query sets
                layout = appointmentLayout.objects.filter(dateID = date_id).filter(sessionTime = session_id).first()
                layout = {'id': layout.layout.id, 'image': layout.layout.image.url}
            except Exception as e:
                print(e)
                raise LookupError("couldn't find layout")
            return layout
        except Exception as e:
            print('layout finding issue', e)
            return(None)

    def change_layout(date_id, session_id, layout_id):
        try:
            appointment_layout = appointmentLayout.objects.filter(dateID = Calendar.objects.get(id = date_id)).filter(sessionTime = Time.objects.get(id = session_id)).first()
            print('-> found layout', appointment_layout)
            if not appointment_layout:
                new_layout = appointmentLayout(dateID = Calendar.objects.get(id = date_id), sessionTime = Time.objects.get(id = session_id), layout = Layouts.objects.get(id = layout_id))
                print('->', new_layout)
                new_layout.save()
            else:
                appointment_layout.layout = Layouts.objects.get(id = layout_id)
                appointment_layout.save()
            return True
        except Exception as e:
            traceback.print_exc()
            raise MyException('error')

    def all_layouts():
        try:
            layouts = Layouts.objects.all()
            layout_list = []
            for layout in layouts:
                layout_list.append({'id':layout.id, 'layout':layout.image.url})
            return(layout_list)
        except Exception:
            traceback.print_exc()
            return(None)
        
    def delete_layout(layout_id):
        try:
            layout = Layouts.objects.get(id=layout_id)
            layout.delete()
            return True
        except Exception:
            traceback.print_exc()
            raise MyException('error')

class FinancialInfo():
    def debt_s(id):
        try:
            debt = MoneyOwed.objects.filter(patientID = id, status='True').aggregate(Sum('amountOwed'))
            debt = debt['amountOwed__sum']
            add_zero = False
            #no debt renders as none
            if not debt:
                debt = 0
            if debt % 10 == 0:
                add_zero = True
            debt = debt / 100
            debt_s = str(debt)
            if add_zero:
                debt_s = debt_s + '0'

            return(debt_s)
        except Exception:
            traceback.print_exc()
            return(None)
    
    def credit_s(id):
        try:
            credit = MoneyPayed.objects.filter(patientID = id).aggregate(Sum('amountPayed')) 
            credit = credit['amountPayed__sum']
            add_zero = False
            if not credit:
                credit = 0
            if credit % 10 == 0:
                add_zero = True
            credit = credit / 100
            credit_s = str(credit)
            if add_zero:
                credit_s = credit_s + '0'
            return(credit_s)
        except Exception:
            traceback.print_exc()
            return(None)

    def total_s(id):
        try:
            debt = MoneyOwed.objects.filter(patientID = id, status='True').aggregate(Sum('amountOwed'))
            debt = debt['amountOwed__sum']
            credit = MoneyPayed.objects.filter(patientID = id).aggregate(Sum('amountPayed'))
            credit = credit['amountPayed__sum']
            total = (credit if credit else 0) - (debt if debt else 0)
            #zero
            add_zero = False
            if not total:
                total = 0
            if total % 10 == 0:
                add_zero = True
            total = total / 100
            total_s = str(total)
            if add_zero:
                total_s = total_s + '0'
            return(total_s)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def all_payments(id):
        try:
            payments_q = MoneyPayed.objects.filter(patientID = id).order_by('dateStamp')
            payments = []
            for pay in payments_q:
                amount = pay.amountPayed
                amount = str(amount)
                amount = amount[:-2] + '.' + amount[-2:]
                payments.append({'amount':amount, 'date':pay.dateStamp.strftime('%d/%m/%Y'), 'time':pay.dateStamp.strftime('%H:%M %p')})
            return(payments)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def all_debts(id):
        try:
            debts_q = MoneyOwed.objects.filter(patientID = id, status='True').order_by('dateStamp')
            debts = []
            for debt in debts_q:
                amount = debt.amountOwed
                amount = str(amount)
                amount = amount[:-2] + '.' + amount[-2:]
                debts.append({'amount':amount, 'date':debt.dateStamp.strftime('%d/%m/%Y'), 'time':debt.dateStamp.strftime('%H:%M %p')})
            return(debts)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

class PersonalInfo():
    def extras(id):
        try:
            extras = patient.objects.get(personID = id).extras
            extras_list = []
            if extras:
                extras = json.loads(extras)
                for ex in extras:
                    item = Extras.objects.get(id = ex)
                    extras_list.append({'item':item.item, 'id':item.id})
            if extras_list:
                 return(extras_list)
            else:
                return(None)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
    
    def extras_as_string(id):
        try:
            extras = patient.objects.get(personID = id).extras
            extras_string = ''
            if extras:
                extras = json.loads(extras)
                for ex in extras:
                    item = Extras.objects.get(id = ex)
                    extras_string = extras_string + item.item + ', '
                extras_string = extras_string[:-2]
            if extras_string:
                 return(extras_string)
            else:
                return(None)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def all_info(id):
        try:
            p = patient.objects.get(personID = id)
            cost = p.cost_pennys
            cost = str(cost)
            cost = cost[:-2] + '.' + cost[-2:]
            info = {
                'id': p.personID,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'gender': p.gender,
                'age': p.age,
                'carer': p.carer,
                'req_sess': p.req_sess,
                'phone': p.phone_number,
                'email': p.email_address,
                'cost':  cost,
                'note': p.noteID.note if p.noteID else None,
            }
            return(info)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def other_info(id):
        try:
            p = patient.objects.get(personID = id)
            info = {
                'depth': p.depth.id if p.depth else None,
                'mask': p.mask.id if p.mask else None,
                'pipe_length': p.pipe_length.id if p.pipe_length else None,
                'sizeId': p.sizeId,
                'extras': json.loads(p.extras) if p.extras else None
            }
            return(info)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
  
    def get_size(mask_type, size_id):
        try:
            size_obj = None
            if mask_type == 'Mask':
                size_obj = MaskSizes.objects.get(id = size_id).size
            elif mask_type == 'Hood':
                size_obj = HoodSizes.objects.get(id = size_id).size
            elif mask_type == 'Trachea mask':
                size_obj = TracheaSizes.objects.get(id = size_id).size
            return(size_obj)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

        
    def actually_all_info(id):
        try:
            p = patient.objects.get(personID = id)
            cost = p.cost_pennys
            cost = str(cost)
            cost = cost[:-2] + '.' + cost[-2:]
            size = p.sizeId
            try:
                size = PersonalInfo.get_size(p.mask.mask, size)
            except:
                size = None
            info = {
                'id': p.personID,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'gender': p.gender,
                'age': p.age,
                'carer': p.carer,
                'req_sess': p.req_sess,
                'phone': p.phone_number,
                'email': p.email_address,
                'cost':  cost,
                'note': p.noteID.note if p.noteID else None,
                'depth': p.depth.id if p.depth else None,
                'mask': p.mask.mask if p.mask else None,
                'pipe_length': p.pipe_length.length if p.pipe_length else None,
                'size': size,
                'extras': PersonalInfo.extras_as_string(id)
            }
            return(info)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def register(first_name, last_name, gender, age, req_sessions, phone, email, cost, depth, size, mask, pipe_length, carer, note, extras):
        try:
            print('-->', mask)
            new_patient = patient(
                first_name = first_name,
                last_name = last_name if last_name else None,
                gender = gender if gender else None,
                age = age if age else None,
                req_sess = req_sessions if req_sessions else None,
                phone_number = phone if phone else None,
                email_address = email if email else None,
                cost_pennys = cost if cost else Price.objects.first().price,
                depth = Depth.objects.get(id=depth) if depth else None,
                mask = Masks.objects.get(id=mask) if mask else None,
                pipe_length = PipeLength.objects.get(id=pipe_length) if pipe_length else None,
                sizeId = size if size else None,
                carer = carer if carer else False,
                extras = json.dumps(extras) if extras else None
            )
            if note:
                new_note = Notes(note = note)
                new_note.save()
                new_patient.noteID = new_note
            new_patient.save()
            return True

        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def edit_info(id, first_name, last_name, gender, age, req_sessions, phone, email, cost, depth, size, mask, pipe_length, carer, note, extras):
        try:
            p = patient.objects.get(personID = id)
            p.first_name = first_name
            p.last_name = last_name if last_name else None
            p.gender = gender if gender else None
            p.age = age if age else None
            p.req_sess = req_sessions if req_sessions else None
            p.phone_number = phone if phone else None
            p.email_address = email if email else None
            p.cost_pennys = cost if cost else Price.objects.first().price
            p.depth = Depth.objects.get(id=depth) if depth else None
            p.sizeId = size if size else None
            p.mask = Masks.objects.get(id=mask) if mask else None
            p.pipe_length = PipeLength.objects.get(id=pipe_length) if pipe_length else None
            p.carer = carer if carer else False
            p.extras = json.dumps(extras) if extras else None
            if note:
                if p.noteID:
                    p.noteID.note = note
                    p.noteID.save()
                else:
                    new_note = Notes(note = note)
                    new_note.save()
                    p.noteID = new_note
            p.save()
            return True
        except Exception:
            traceback.print_exc()
            raise MyException('error')


        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def scheduled_appointments(id):
        try:
            print(id)
            scheduled = Appointment.objects.filter(patientID = id, appointmentStatus = 'SCHE').order_by('dateID__the_date', 'sessionTime__time')
            carer = patient.objects.filter(personID = id)[0].carer
            #if carer all appointments are doubled so have to be grouped together in pairs
            list_apps = []
            if carer:
                loop = int(len(scheduled) / 2)
                counter = 0
                for i in range(loop):
                    app = {'date': scheduled[counter].dateID.the_date.strftime('%d/%m/%Y'), 'day':scheduled[counter].dateID.day_name, 'time':scheduled[counter].sessionTime.time.strftime('%H:%M %p'), 'app_ids':[scheduled[counter].id, scheduled[counter + 1].id]}
                    list_apps.append(app)
                    counter += 2
            else:
                for sch in scheduled:
                    app = {'date': sch.dateID.the_date.strftime('%d/%m/%Y'), 'day':sch.dateID.day_name, 'time':sch.sessionTime.time.strftime('%H:%M %p'), 'app_ids':[sch.id]}
                    list_apps.append(app)
            return(list_apps)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def all_appointments(id):
        try:
            scheduled = Appointment.objects.filter(patientID = id,appointmentStatus = 'SCHE').order_by('-dateID__the_date', '-sessionTime__time')
            canceled = Appointment.objects.filter(patientID = id, appointmentStatus = 'CANC').order_by('-dateID__the_date', '-sessionTime__time')
            attended = Appointment.objects.filter(patientID = id, appointmentStatus = 'ATTE').order_by('-dateID__the_date', '-sessionTime__time')
            missed = Appointment.objects.filter(patientID = id, appointmentStatus = 'MISS').order_by('-dateID__the_date', '-sessionTime__time')
            unwell = Appointment.objects.filter(patientID = id, appointmentStatus = 'UNWE').order_by('-dateID__the_date', '-sessionTime__time')
            dict_apps = {'scheduled':scheduled, 'canceled':canceled, 'attended':attended, 'missed':missed, 'unwell':unwell}
            return(dict_apps)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def carer(id):
        try:
            has_carer = patient.objects.get(personID = id).carer
            return(has_carer)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
    
    def notes(id):
        try:
            note = patient.objects.get(personID = id).noteID
            if note:
                note = note.note
            else:
                note = None
            return(note)
        except Exception:
            traceback.print_exc()
            raise MyException('error')


    class Update:
        def notes(id, new_note):
            try:
                pat = patient.objects.get(personID = id)
                if pat.noteID:
                    pat.noteID.note = new_note
                    pat.noteID.save()
                else:
                    new_note_obj = Notes(note = new_note)
                    new_note_obj.save()
                    pat.noteID = new_note_obj
                    pat.save()
                return(True)
            except Exception:
                traceback.print_exc()
                raise MyException('error')
        
        def extras(id, new_extras):
            try:
                pat = patient.objects.get(personID = id)
                #new_extras is list of ids
                #saved as json array
                extra_array = []
                for ex in new_extras:
                    extra_array.append(int(ex))
                pat.extras = json.dumps(extra_array)
                pat.save()
                return(True)
            except Exception:
                traceback.print_exc()
                raise MyException('error')

class CalendarInfo():
    def get_month(month, year):
        try:
            month_set = Calendar.objects.filter(the_date__month = month, the_date__year = year)
            days_of_week = {'Sunday':0, 'Monday':1, 'Tuesday':2, 'Wednesday':3, 'Thursday':4, 'Friday':5, 'Saturday':6}
            first_day = month_set.first()
            first_day = first_day.the_date.weekday()
            first_day = first_day + 1
            if first_day == 7:
                first_day = 0
            month_s = []
            #generate empty days
            for i in range(first_day):
                month_s.append({'day':None, 'id':None, 'open_status':None})
            for day in month_set:
                month_s.append({'day':day.the_date.day, 'id':day.id, 'open_status':day.open_staus, 'day_iso': day.the_date.isoformat()})
            return(month_s)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
class GeneralInfo():
    def all_active_patients():
        try:    
            all_patients = patient.objects.filter(active = True).order_by('last_name', 'first_name')
            array_of_patients = []
            for person in all_patients:
                array_of_patients.append({'name': f"{person.first_name} {person.last_name}", 'id': person.personID})
            return(array_of_patients)
        except Exception:    
            traceback.print_exc()
            raise MyException('error')
        
    def all_active_patients_name_split():
        try:    
            all_patients = patient.objects.filter(active = True).order_by('last_name', 'first_name')
            array_of_patients = []
            for person in all_patients:
                array_of_patients.append({'first_name': person.first_name, 'last_name': person.last_name, 'id': person.personID})
            return(array_of_patients)
        except Exception:    
            traceback.print_exc()
            raise MyException('error')

class Finance():
    def get_payment_by_appointment(appointment_id):
        try:
            try:
                #bug when multiple false payments exist for same appointment
                payment_id = MoneyOwed.objects.filter(appointmentID = Appointment.objects.get(id = appointment_id)).filter(status='True').first().id
                payment = MoneyOwed.objects.get(id = payment_id)
                return payment
            except:
                return False
        except Exception:
            traceback.print_exc()
            raise MyException('error')
    
    def register_payment(patient_id, amount):
        try:
            if not amount or amount <= 0:
                raise MyException('payment must be positive amount')
            p = patient.objects.get(personID = patient_id)
            pay = MoneyPayed(patientID = p, amountPayed = amount)
            pay.save()
            return(True)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
    
    def register_appointment_debt(patient_id, appointment_id):
        try:
            print('debt registration for; patient id:', patient_id, 'appointment id:', appointment_id)
            p = patient.objects.get(personID = patient_id)
            amount = p.cost_pennys
            debt = MoneyOwed(patientID = p, amountOwed = amount, appointmentID = Appointment.objects.get(id = appointment_id))
            debt.save()
            return(True)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

class GetAll():
    def face_coverings():
        try:
            all_face_coverings = Masks.objects.all()
            return(all_face_coverings)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
   
    def extras():
        try:
            all_extras = Extras.objects.all().filter(status = True)
            return(all_extras)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
   
    def depths():
        try:
            all_depths = Depth.objects.all().order_by('depth')
            all_depths_trimed = []
            for depth in all_depths:
                depth_s = ''
                #check if not float
                if (depth.depth * 10) % 10 == 0:
                    depth_s = str(int(depth.depth))
                else:
                    depth_s = str(depth.depth)
                all_depths_trimed.append({'id':depth.id, 'depth':depth_s})
            return(all_depths_trimed)
        except Exception:
            traceback.print_exc()
            raise MyException('error')

    def pipe_lengths():
        try:
            all_pipe_lengths = PipeLength.objects.all()
            return(all_pipe_lengths)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def masks():
        try:
            all_masks = Masks.objects.all()
            return(all_masks)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
    
    def mask_sizes():
        try:
            all_sizes = MaskSizes.objects.all()
            return(all_sizes)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def hood_sizes():
        try:
            all_hood_sizes = HoodSizes.objects.all()
            return(all_hood_sizes)
        except Exception:
            traceback.print_exc()
            raise MyException('error')
        
    def trachea_sizes():
        try:
            all_trachea_sizes = TracheaSizes.objects.all()
            return(all_trachea_sizes)
        except Exception:
            traceback.print_exc()
            raise MyException('error')  
