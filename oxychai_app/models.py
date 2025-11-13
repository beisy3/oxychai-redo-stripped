from django.db import models
from datetime import date, timedelta
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.
class Notes(models.Model):
    note = models.CharField(max_length=250, null=True)

    def __str__(self):
        return self.note
    
class Depth(models.Model):
    depth = models.FloatField()

    def __str__(self):
        return str(self.depth)

class Time(models.Model):
    time = models.TimeField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.time.strftime('%H:%M')} id: {self.id}"
    
class PipeLength(models.Model):
    length = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.length}' 

class Extras(models.Model):
    item = models.CharField(max_length=25)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.item} status {self.status}'
    
class Price(models.Model):
    price = models.IntegerField()

    def __str__(self):
        return str(self.price)

class HoodSizes(models.Model):
    size = models.CharField(max_length=20)

    def __str__(self):
        return self.size
    
class TracheaSizes(models.Model):
    size = models.CharField(max_length=20)

    def __str__(self):
        return self.size
    
class Masks(models.Model):
    mask = models.CharField(max_length=20)

    def __str__(self):
        return self.mask
    
class MaskSizes(models.Model):
    size = models.CharField(max_length=10)
    size_full = models.CharField(max_length=25)

    def __str__(self):
        return f'{self.size} {self.size_full}'

class patient(models.Model):

    personID = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64 , blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    req_sess = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    mask = models.ForeignKey(Masks, on_delete=models.PROTECT, blank=True, null=True)
    pipe_length = models.ForeignKey(PipeLength, on_delete=models.PROTECT, blank=True, null=True)
    sizeId = models.IntegerField(null=True, blank=True)
    cost_pennys = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    depth = models.ForeignKey(Depth, on_delete=models.PROTECT, blank=True, null=True)
    active = models.BooleanField(default=True)
    noteID = models.ForeignKey(Notes, on_delete=models.PROTECT, blank=True, null=True)
    carer = models.BooleanField(default=False)
    extras = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"Name:{self.first_name} {self.last_name}, {self.gender}, {self.age}, req sess: {self.req_sess} Number:{self.phone_number} Email:{self.email_address} Mask:{self.mask} Pipe Length:{self.pipe_length} SizeId:{self.sizeId} Cost In Pennys:{self.cost_pennys} Depth:{self.depth} Date Created:{self.date}, active = {self.active}, carer = {self.carer}, extras = {self.extras}, note = {self.noteID}"

class FaceCovering(models.Model):
    type = models.CharField(max_length=20)

    def __str__(self):
        return self.type

class Calendar(models.Model):
    the_date = models.DateField(unique=True)
    day_name = models.CharField(max_length=10)
    hebrew_date = models.CharField(default=None, blank=True, null=True, max_length=30)
    holiday_name = models.CharField(blank=True, default='empty', max_length=64)
    holiday_type = models.CharField(max_length=64, default='empty', blank=True)
    open_staus = models.BooleanField(default=True)
     
    def __str__(self):
        return f"{self.the_date} ({self.day_name}) id: {self.id} holiday names: {self.holiday_name} holiday types:{self.holiday_type} open:{self.open_staus}"

    @staticmethod
    def populate_dates(start_year=2025, end_year=2099):
        """Populates the database with all dates and their corresponding day names."""
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        delta = timedelta(days=1)

        dates_to_create = []
        while start_date <= end_date:
            day_name = start_date.strftime("%A")  # Converts date to "Monday", "Tuesday", etc.
            dates_to_create.append(Calendar(the_date=start_date, day_name=day_name))
            start_date += delta
        
        Calendar.objects.bulk_create(dates_to_create, ignore_conflicts=True)

class Layouts(models.Model):
    image = models.ImageField(upload_to='layouts/')

    def __str__(self):
        return f"{self.id}"
    
    def delete(self, *args, **kwargs):
        self.image.delete()
        super(Layouts, self).delete(*args, **kwargs)
    
class appointmentLayout(models.Model):
    dateID = models.ForeignKey(Calendar, on_delete=models.PROTECT)
    sessionTime = models.ForeignKey(Time, on_delete=models.PROTECT)
    layout = models.ForeignKey(Layouts, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.dateID.the_date}, {self.sessionTime.time}, {self.layout.image}"
    

class Appointment(models.Model):
    APPOINTMENT_STATUS_OPTIONS = {
        "SCHE": "Scheduled",
        "CANC": "Canceled",
        "ATTE": "Attended",
        "MISS": "Missed",
    }
    dateID = models.ForeignKey(Calendar, on_delete=models.PROTECT)
    patientID = models.ForeignKey(patient, on_delete=models.CASCADE)
    sessionTime = models.ForeignKey(Time, on_delete=models.PROTECT)
    panelPosition = models.CharField(null=True)
    appointmentStatus = models.CharField(
        max_length=4,
        #choices=APPOINTMENT_STATUS_OPTIONS,
        default="SCHE",
    )
    

    def __str__(self):
        return f"{self.id} {self.dateID} {self.patientID} {self.sessionTime} Status:{self.appointmentStatus}" 

class MoneyOwed(models.Model):
    dateStamp = models.DateTimeField(auto_now_add=True)
    amountOwed = models.IntegerField()
    patientID = models.ForeignKey(patient, on_delete=models.SET_NULL, null=True)
    appointmentID = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"date: {self.dateStamp} amount: {self.amountOwed} patient: {self.patientID} appointment: {self.appointmentID}"
    
class MoneyPayed(models.Model):
    dateStamp = models.DateTimeField(auto_now_add=True)
    amountPayed = models.IntegerField()
    patientID = models.ForeignKey(patient, on_delete=models.SET_NULL, null=True)
    appointmentID = models.ForeignKey(Appointment, on_delete=models.PROTECT, null=True)
    noteID = models.ForeignKey(Notes, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"date: {self.dateStamp} amount: {self.amountPayed} payment method: {self.paymentMethod} patient: {self.patientID} appointment: {self.appointmentID}"