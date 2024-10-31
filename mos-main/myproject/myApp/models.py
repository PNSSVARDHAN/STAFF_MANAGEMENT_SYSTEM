from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from django.core.exceptions import ValidationError

class Staff(models.Model):
    # id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    dob = models.DateField()
    blood_group = models.CharField(max_length=3, blank=True, null=True)
    id_no = models.CharField(max_length=50, unique=True)
    aadhar = models.CharField(max_length=12, unique=True, blank=False)
    pan = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    emergency_contact = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    insurance_policy_no = models.CharField(max_length=50, blank=True, null=True)
    insurance_expiry = models.DateField(blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2)
    spl_allowance = models.DecimalField(max_digits=10, decimal_places=2)
    incentive = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    photo = models.ImageField(blank=True, null=True, editable=True, upload_to='staff_photos')

    def save(self, *args, **kwargs):
        if isinstance(self.photo, InMemoryUploadedFile):
            self.photo = self.photo.read()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.id_no})"
    
    def get_photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        return self.photo
    

class Attendance(models.Model):
    staff = models.ForeignKey(Staff, to_field='id_no', on_delete=models.CASCADE)
    attendance_date = models.DateField(default=timezone.now)  # Default set to current date
    attendance_type = models.CharField(
        max_length=20, 
        default='Onsite',  # Default value set for attendance_type
        choices=[
            ('Onsite', 'Onsite'),
            ('Offsite', 'Offsite'),
            ('WFH', 'Work from Home'),
            ('Leave', 'Leave'),
            ('Travel', 'Travel'),
        ]
    )
    class Meta:
        unique_together = ('staff', 'attendance_date')  # Ensure unique attendance per staff per date

    def __str__(self):
        return f"{self.staff.name} - {self.attendance_type} on {self.attendance_date}"


