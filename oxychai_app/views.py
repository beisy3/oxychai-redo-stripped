from django.shortcuts import render
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User
import oxychai_app.classes
from oxychai_app.classes import Finance, Layout, RetrieveApp, FinancialInfo, PersonalInfo, CalendarInfo, GeneralInfo, BookAppointment, GetAll
from oxychai_app.helper import penny_to_pounds__str
from .models import Appointment, Extras, Layouts, Time
import traceback
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required, user_passes_test

def login_page(request):
    if request.method == "GET":
        return render(request, "registration/login_operator.html")
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username, password = password)
        print(user)
        if user is not None:
            login(request, user)
            position = user.groups.first().name
            print(f'logeed in {user}, \n {position}')
            if position == 'operators':
                return HttpResponseRedirect('/operatorPage/?time=now')
            elif position == 'admins':
                return HttpResponseRedirect('/')

        print(f'login {user} unsuccessfull')
        return HttpResponse('failed')

def operator_check(user):
    return user.groups.filter(name='operators').exists()

def admin_check(user):
    return user.groups.filter(name='admins').exists()

@login_required
def log_out(request):
    logout(request)
    return HttpResponseRedirect("/signIn")

# Create your views here.
@user_passes_test(admin_check)
def index(request):
    return render(request, "oxychai/calendar_redo.html")

# Create your views here.
@user_passes_test(admin_check)
def findScheduled(request):
    try:
        if request.method == "POST":
            id = int(json.loads(request.body))
            app = PersonalInfo.scheduled_appointments(id)
            app_json = json.dumps(app)
            return HttpResponse(app_json)
    except Exception:
        traceback.print_exc()

@user_passes_test(admin_check)
def findPersonalInfo(request):
    if request.method == 'POST':
        try:
            id = json.loads(request.body)
            carer = PersonalInfo.carer(id)
            note = PersonalInfo.notes(id)
            extras = PersonalInfo.extras(id)
            form = {'extras':extras, 'note':note, 'carer':carer}
            form_j = json.dumps(form)
            return HttpResponse(form_j)
        except Exception:
            traceback.print_exc()

@user_passes_test(admin_check)
def allExtras(request):
    if request.method == 'GET':
        try:
            extras = Extras.objects.all()
            list_of_extras = []
            for extra in extras:
                dict_of_extra = {'id':extra.id, 'item':extra.item}
                list_of_extras.append(dict_of_extra)
            json_list_of_extras = json.dumps(list_of_extras)
            return HttpResponse(json_list_of_extras)
        except Exception:
            traceback.print_exc()

@user_passes_test(admin_check)
def updateExtraDetails(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print(form)
            id = form['id']
            extras = form['extras']
            note = form['note']
            PersonalInfo.Update.extras(id, extras)
            PersonalInfo.Update.notes(id, note)
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()

def resetPassword(request):
    if request.method == 'GET':
        try:
            return render(request, "registration/set_password.html")
        except Exception:
            traceback.print_exc()

    if request.method == 'POST':
        try:
            form = request.body
            print('password sent')
            new_password = request.POST.get('password1')
            confirm_password = request.POST.get('password2')
            if new_password == confirm_password and len(new_password) > 5:
                u = User.objects.get(username__exact='--mrsDafner')
                u.set_password(new_password)
                u.save()
                return HttpResponse('successfully changed password')
            elif len(new_password) < 6:
                print('too short')
                return HttpResponse('too short')
            else:
                return HttpResponse('failiure', status=400)
        
        except Exception:
            return HttpResponse('not allowed')
            traceback.print_exc()

#@login_required
def newCalendar(request):
    if request.method == 'GET':
        try:
            all_sessions = Time.objects.all().filter(status = True).order_by('time')
            form = []
            for sess in all_sessions:
                dict_of_sess = {'id':sess.id, 'time':sess.time.strftime("%I:%M %p")}
                form.append(dict_of_sess)
            form = json.dumps(form)
            print(form)
            return render(request, "oxychai/calendar_redo.html", {'sessions':form})
        except Exception:
            traceback.print_exc()

#@user_passes_test(admin_check)
def monthGenerator(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print(form)
            month = int(form['month'])
            year = int(form['year'])
            month_gen = json.dumps(CalendarInfo.get_month(month, year))
            return HttpResponse(month_gen)
        except Exception:
            traceback.print_exc()
            return HttpResponse('failiure', status=400)

#@login_required
def appointmentsPatientInfo(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print(form)
            day_id = form['day_id']
            session_id = form['session_id']
            patients = []
            apps = RetrieveApp.get_patients(day_id, session_id)
            for app in apps:
                extras = PersonalInfo.extras_as_string(app.patientID.personID)
                total = FinancialInfo.total_s(app.patientID.personID)
                size = PersonalInfo.get_size(app.patientID.mask.mask, app.patientID.sizeId) if app.patientID.mask and app.patientID.sizeId else ''
                attended_group = Appointment.objects.filter(patientID = app.patientID.personID, appointmentStatus = 'ATTE').order_by('dateID__the_date', 'sessionTime__time')
                print('------------attended amount------------------\n', attended_group)
                s_app = {
                    'id':app.id,
                    'name':f"{app.patientID.first_name} {app.patientID.last_name}",
                    'patient_id':app.patientID.personID,
                    'position':app.panelPosition if app.panelPosition else '',
                    'depth':app.patientID.depth.depth if app.patientID.depth else '',
                    'mask': app.patientID.mask.mask if app.patientID.mask else '',
                    'size': size if size else '',
                    'pipe_length': app.patientID.pipe_length.length if app.patientID.pipe_length else '',
                    'carer': app.patientID.carer,
                    'status':app.appointmentStatus,
                    'price': penny_to_pounds__str(app.patientID.cost_pennys),
                    'notes':app.patientID.noteID.note if app.patientID.noteID else '',
                    'extras': extras,
                    'phone_number': app.patientID.phone_number,
                    'num_sess':len(attended_group),
                    'balance': total,
                    'appointment_id': app.id
                    }
                patients.append(s_app)
            print(patients)
            patients_j = json.dumps(patients)
            return HttpResponse(patients_j)
        except Exception as e:
            traceback.print_exc()
            return HttpResponse('failed', status=400)

#@login_required
def allPatientsSearch(request):
    try:
        if request.method == 'GET':
            day_id = request.GET.get('day_id')
            session_id = request.GET.get('session_id')
            print(day_id, session_id)
            ppl_booked = RetrieveApp.get_patients(day_id, session_id)
            list_of_ppl_booked = []
            for p in ppl_booked:
                list_of_ppl_booked.append(p.patientID.personID)
            #ppl_not_booked = RetrieveApp.patients_not_booked(day_id, session_id)
            other_ppl = GeneralInfo.all_active_patients_name_split()
            info = {'day_id':day_id, 'session_id':session_id, 'all_ppl':other_ppl, 'ppl_booked':list_of_ppl_booked}
            info_j = json.dumps(info)
            return HttpResponse(info_j)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse('failed', status=400)

#@login_required
def layoutFind(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print(form)
            day_id = form['day_id']
            session_id = form['session_id']
            layout = Layout.get_layout_and_id(day_id, session_id)
            all_layouts = Layout.all_layouts()
            json.dumps(all_layouts)
            layout_dict = {'layout':layout, 'all_layouts':all_layouts}
            print(layout_dict)
            layout_j = json.dumps(layout_dict)
            return HttpResponse(layout_j)
        except Exception:
            traceback.print_exc()
            return HttpResponse('failiure', status=400)
        
def todayLayout(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print(form)
            day_id = form['day_id']
            session_id = form['session_id']
            layout = Layout.get_layout(day_id, session_id)
            response = {'layout':layout}
            response_j = json.dumps(response)
            return HttpResponse(response_j)
        except Exception:
            traceback.print_exc()
            return HttpResponse('failiure', status=400)
    

#@login_required
def bookAppointmentInd(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print('\n \n \n', '------------------------------------------------------------', form)
            day_id = form['day_id']
            session_id = form['session_id']
            patient_id = form['patient_id']
            existing = RetrieveApp.find_existing(day_id, session_id, patient_id)
            print('existing appointment:', existing)
            if existing:
                existing.appointmentStatus = 'SCHE'
                existing.save()
                print('existing appointment found:', existing)
            else:
                x = BookAppointment.add_appointment(day_id, session_id, patient_id)
                if not x:
                    print('failed to book', day_id, session_id, patient_id)
                    return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()
            return HttpResponse('failiure', status=400)

#@login_required
def changeLayout(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            day_id = form['day_id']
            session_id = form['session_id']
            layout_id = form['layout_id']
            print(session_id, day_id, layout_id)
            x = Layout.change_layout(day_id, session_id, layout_id)
            if not x:
                print('failed to change layout', day_id, session_id, layout_id)
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()
            return HttpResponse('failiure', status=400)

#@login_required
def addPayment(request):
    try:
        if request.method == 'POST':
            form = json.loads(request.body)
            print('add payment', form)
            id = form['person_id']
            amount = int(form['amount'])
            pay = Finance.register_payment(id, amount)
            if not pay:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
    except Exception:
        traceback.print_exc()
        return HttpResponse('failure', status=400)
    
#@login_required
def getBalance(request):
    try:
        if request.method == 'POST':
            print('get balance', request.body)
            id = json.loads(request.body)
            total = FinancialInfo.total_s(id)
            total_j = json.dumps(total)
            return HttpResponse(total_j)
    except Exception:
        traceback.print_exc()
        return HttpResponse('failure', status=400)
    
#@login_required
def cancelAppointment(request):
    try:
        if request.method == 'POST':
            appointment_id = json.loads(request.body)
            print('cancel appointment', appointment_id)
            x = BookAppointment.cancel_appointment(appointment_id)
            if not x:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
    except Exception:
        traceback.print_exc()
        return HttpResponse('failure', status=400)
    
#@login_required
def changeAppStatus(request):
    try:
        if request.method == 'POST':
            form = json.loads(request.body)
            print('---------------change status--------------------\n', form)
            appointment_id = form['appointment_id']
            patient_id = form['patient_id']
            new_status = form['new_status']
            old_status = RetrieveApp.get_appointment(appointment_id).appointmentStatus
            try:
                BookAppointment.change_status(appointment_id, new_status)
            except:
                print('responded negative')
                return HttpResponse('failed', status=400)

            #sort out old debt if previously saved debt
            old_payment = Finance.get_payment_by_appointment(appointment_id)
            if old_status != 'SCHE':
                try:
                    if old_payment:
                        old_payment.status = False
                except:
                    BookAppointment.change_status(appointment_id, old_status)
                    print('failed to register debt, reverted status')
                    return HttpResponse('failed', status=400)

            #register new debt if attended or missed
            if new_status == 'ATTE' or new_status == 'MISS':
                try:
                    Finance.register_appointment_debt(patient_id, appointment_id)
                except:
                    BookAppointment.change_status(appointment_id, old_status)
                    print('failed to register debt, reverted status')
                    return HttpResponse('failed', status=400)
            
            #if all goes ok save old payment as false
            if old_payment:
                old_payment.save()
            
            return HttpResponse('success')
    except Exception:
        traceback.print_exc()
        return HttpResponse('failed', status=400)
    
def RegisterNew(request):

    if request.method == 'GET':
        try:
            all_extras = GetAll.extras()
            all_depths = GetAll.depths()
            all_masks = GetAll.masks()
            all_mask_sizes = GetAll.mask_sizes()
            all_hood_sizes = GetAll.hood_sizes()
            all_trachea_sizes = GetAll.trachea_sizes()
            all_pipe_lengths = GetAll.pipe_lengths()
            return render(request, "oxychai/register_new.html", {"extras": all_extras, "depths": all_depths, "masks": all_masks, "trachea_sizes": all_trachea_sizes, "hood_sizes": all_hood_sizes, "mask_sizes": all_mask_sizes, "pipe_lengths": all_pipe_lengths})
        except Exception:
            traceback.print_exc()

    else:
        try:
            form = json.loads(request.body)
            print('\n', '\n', '\n')
            print('register-----------------------------------', form)
            first_name = form['first_name']
            last_name = form['last_name']
            gender = form['gender']
            age = form['age']
            req_sessions = form['req_sessions']
            email = form['email']
            phone = form['phone']
            cost = form['cost']
            depth = form['depth']
            mask = form['mask']
            pipe_length = form['pipe_length']
            size = form['size']
            note = form['note']
            carer = form['carer']
            extras = form['extras']
            registration = PersonalInfo.register(first_name, last_name, gender, age, req_sessions, phone, email, cost, depth, size, mask, pipe_length, carer, note, extras)
            if not registration:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            print('----------------------------')
            traceback.print_exc()
            return HttpResponse('failure', status=400)
     
"""def UploadLayout(request):
    if request.method == 'POST':
        try:
            form = request.POST
            layout_image = request.FILES['layout_image']
            x = Layouts(image = layout_image)
            x.save()
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)"""
        
def changePanelPosition(request):
    if request.method == 'POST':
        try:
            form = json.loads(request.body)
            print('change panel position', form)
            appointment_id = form['appointment_id']
            position = form['position']
            x = BookAppointment.change_panel(appointment_id, position)
            if not x:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)
        
def searchPatients(request):
    if request.method == 'GET':
        try:
            all_patients = GeneralInfo.all_active_patients()
            return render(request, "oxychai/search_patients_redo.html", {'all_patients': all_patients})
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)
        
def editDetails(request):
    if request.method == 'GET':
        try:
            id = request.GET.get('id')
            all_extras = GetAll.extras()
            all_depths = GetAll.depths()
            all_masks = GetAll.masks()
            all_mask_sizes = GetAll.mask_sizes()
            all_hood_sizes = GetAll.hood_sizes()
            all_trachea_sizes = GetAll.trachea_sizes()
            all_pipe_lengths = GetAll.pipe_lengths()
            all_renderable_info = PersonalInfo.all_info(id)
            all_other_info = json.dumps(PersonalInfo.other_info(id))
            return render(request, "oxychai/edit_patient_details_redo.html", {'details': all_renderable_info, "other_info": all_other_info, "extras": all_extras, "depths": all_depths, "masks": all_masks, "trachea_sizes": all_trachea_sizes, "hood_sizes": all_hood_sizes, "mask_sizes": all_mask_sizes, "pipe_lengths": all_pipe_lengths})
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)
    else:
        try:
            form = json.loads(request.body)
            print('\n', '\n', '\n')
            print('edit details-----------------------------------', form)
            id = form['id']
            first_name = form['first_name']
            last_name = form['last_name']
            gender = form['gender']
            age = form['age']
            req_sessions = form['req_sessions']
            email = form['email']
            phone = form['phone']
            cost = form['cost']
            depth = form['depth']
            mask = form['mask']
            pipe_length = form['pipe_length']
            size = form['size']
            note = form['note']
            carer = form['carer']
            extras = form['extras']
            edit = PersonalInfo.edit_info(id, first_name, last_name, gender, age, req_sessions, phone, email, cost, depth, size, mask, pipe_length, carer, note, extras)
            if not edit:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            print('----------------------------')
            traceback.print_exc()
            return HttpResponse('failure', status=400)

def saveLayout(request):
    if request.method == 'POST':
        try:
            from io import BytesIO
            print(request.FILES)
            layout_image = request.FILES['layout_image']
            size = layout_image.seek(0, 2)
            if size > 8000000:
                return HttpResponse('File too large, please try again with images less than 8mb', status=400)
            x = Layouts(image = layout_image)
            x.save()
            return HttpResponse('Successfully uploaded image')
        except Exception:
            traceback.print_exc()
            return HttpResponse('Image upload failed', status=400)
        
    else:
        return render(request, "oxychai/upload_layout.html")

def layoutDelete(request):
    return None

        
def patientProfile(request):
    #send appointment info, financial info, personal info
    if request.method == 'GET':
        try:
            id = request.GET.get('id')
            patient_info = PersonalInfo.actually_all_info(id)
            print('--------patient info-----------\n', patient_info)
            appointments = PersonalInfo.all_appointments(id)
            financial_info = {'total':FinancialInfo.total_s(id), 'debt':FinancialInfo.all_debts(id), 'payments':FinancialInfo.all_payments(id)}
            return render(request, "oxychai/patient_profile_redo.html", {'patient_info': patient_info, 'financial_info': financial_info, 'appointments': appointments})
        except Exception:
            traceback.print_exc()

def deleteLayout(request):
    if request.method == 'GET':
        layouts = Layout.all_layouts()
        return render(request, "oxychai/delete_layout.html", {'layouts': layouts})
    
    elif request.method == 'POST':
        import time

        time.sleep(5)
        try:
            form = json.loads(request.body)
            layout_id = form['layout_id']
            x = Layout.delete_layout(layout_id)
            if not x:
                return HttpResponse('failed', status=400)
            return HttpResponse('success')
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)
        
def allPatients(request):
    if request.method == 'GET':
        try:
            all_patients = GeneralInfo.all_active_patients_name_split()
            print('all patients:', all_patients)
            j_all_patients = json.dumps(all_patients)
            print('--------------------------')
            return HttpResponse(j_all_patients)
        except Exception:
            traceback.print_exc()
            return HttpResponse('failure', status=400)