from django.shortcuts import render, redirect, get_object_or_404
from .models import Staff
from myApp.models import Staff
from django.http import HttpResponse , JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import base64
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Attendance, Staff
from .forms import AttendanceForm
from datetime import datetime
from django.shortcuts import render
from django.utils import timezone
from .models import Attendance, Staff
from datetime import datetime
from datetime import datetime
from django.utils import timezone
from django.db.models import Count
from myApp.models import Attendance
from django import template
from django.db.models import Count
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# _____________________________________________LOGIN_______________________________________________________
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm
from .models import User

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                # Check if the user exists
                user = User.objects.get(username=username)
                
                # Check if the password is correct
                if user.check_password(password):
                    # Redirect to the home page on success
                    return redirect('home')
                else:
                    messages.error(request, "Incorrect password.")
            except User.DoesNotExist:
                messages.error(request, "Username not found.")
    else:
        form = LoginForm()
    return render(request, 'myApp/login.html', {'form': form})





# _____________________________________________HOME PAGE_______________________________________________________
def home(request):
    # Get today's date
    today = timezone.now().date()
    attendance_count = {}
    attendance_records = Attendance.objects.filter(attendance_date=today)

    # Process attendance records to count attendance types per employee
    for record in attendance_records:
        staff_id = record.staff.id_no  # Assuming staff.id_no uniquely identifies each employee
        attendance_type = record.attendance_type
        
        # Initialize the employee's attendance counts if not already done
        if staff_id not in attendance_count:
            attendance_count[staff_id] = {
                'name': record.staff.name,  # Store employee name
                'Onsite': 0,
                'Offsite': 0,
                'WFH': 0,
                'Leave': 0,
                'Travel': 0,
            }

        # Increment the count based on attendance type
        if attendance_type in attendance_count[staff_id]:
            attendance_count[staff_id][attendance_type] += 1

    # Aggregate the total counts for the day
    total_count = {
        'Onsite': sum(employee['Onsite'] for employee in attendance_count.values()),
        'Offsite': sum(employee['Offsite'] for employee in attendance_count.values()),
        'WFH': sum(employee['WFH'] for employee in attendance_count.values()),
        'Leave': sum(employee['Leave'] for employee in attendance_count.values()),
        'Travel': sum(employee['Travel'] for employee in attendance_count.values()),
    }

    context = {
        'total_count': total_count,  # Pass the total count to the template
    }

    return render(request, 'myApp/home.html', context)

def daily_attendance(request):
    today = timezone.now().date()
    attendance_count = {}
    attendance_records = Attendance.objects.filter(attendance_date=today)

    # Process attendance records
    for record in attendance_records:
        staff_id = record.staff.id_no
        attendance_type = record.attendance_type
        
        # Initialize the employee's attendance counts if not already done
        if staff_id not in attendance_count:
            attendance_count[staff_id] = {
                'name': record.staff.name,
                'Onsite': 0,
                'Offsite': 0,
                'WFH': 0,
                'Leave': 0,
                'Travel': 0,
            }

        # Increment the count based on attendance type
        attendance_count[staff_id][attendance_type] += 1

    # Aggregate total counts
    total_count = {
        'Onsite': sum(employee['Onsite'] for employee in attendance_count.values()),
        'Offsite': sum(employee['Offsite'] for employee in attendance_count.values()),
        'WFH': sum(employee['WFH'] for employee in attendance_count.values()),
        'Leave': sum(employee['Leave'] for employee in attendance_count.values()),
        'Travel': sum(employee['Travel'] for employee in attendance_count.values()),
    }

    context = {
        'attendance_count': attendance_count,
        'total_count': total_count,
        'attendance_records': attendance_records,
    }

    return render(request, 'myApp/home.html', context)



#------------------------------------graphs--------------------------------------------
def chart_view(request):
    return render(request, 'attendance_chart.html')

def chart_data(request):
    # Your logic for fetching attendance data and returning JSON
    attendance_data = Attendance.objects.values('attendance_type').annotate(count=Count('attendance_type'))
    labels = []
    data = []
    for entry in attendance_data:
        labels.append(entry['attendance_type'])
        data.append(entry['count'])
    return JsonResponse({'labels': labels, 'data': data})

def work_mode_chart_data(request):
    # Get today's date and the date 30 days ago
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # Query the attendance for the last 30 days, grouped by attendance_type
    attendance_data = Attendance.objects.filter(attendance_date__gte=last_30_days).values('attendance_type').annotate(
        count=Count('staff', distinct=True)
    )

    # Prepare data for Chart.js
    labels = []  # Work modes like 'Onsite', 'Offsite', etc.
    data = []    # Corresponding counts of employees

    for entry in attendance_data:
        labels.append(entry['attendance_type'])
        data.append(entry['count'])

    return JsonResponse({'labels': labels, 'data': data})

def individual_work_mode_data(request, work_mode):
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # Filter attendance for the last 30 days for the specific work mode
    attendance_data = Attendance.objects.filter(
        attendance_type=work_mode, attendance_date__gte=last_30_days
    ).values('staff__name').annotate(count=Count('staff')).order_by('staff__name')

    labels = []
    data = []

    for entry in attendance_data:
        labels.append(entry['staff__name'])  # Staff names
        data.append(entry['count'])          # Count of how many times they were in the specific work mode

    return JsonResponse({'labels': labels, 'data': data})

def staff_workmode_data(request):
    last_30_days = timezone.now() - timedelta(days=30)
    staff_data = []

    # Fetch all staff members
    staff_members = Staff.objects.all()
    
    for staff in staff_members:
        work_modes = Attendance.objects.filter(staff=staff, attendance_date__gte=last_30_days)
        
        work_mode_counts = {
            'Onsite': work_modes.filter(attendance_type='Onsite').count(),
            'Offsite': work_modes.filter(attendance_type='Offsite').count(),
            'WFH': work_modes.filter(attendance_type='WFH').count(),
            'Leave': work_modes.filter(attendance_type='Leave').count(),
            'Travel': work_modes.filter(attendance_type='Travel').count(),
        }

        staff_data.append({
            'staff_name': staff.name,
            'work_modes': work_mode_counts
        })

    return JsonResponse(staff_data, safe=False)



# _____________________________________________MANAGE_STAFF_______________________________________________________

# View for managing staff
def manage_staff(request):
    staff_list = Staff.objects.all()
    return render(request, 'myApp/managestaff.html', {'staff_list': staff_list})

# View for adding new staff
def add_staff(request):
    if request.method == 'POST':
        staff = Staff(
            name=request.POST['name'],
            designation=request.POST['designation'],
            qualification=request.POST.get('qualification', ''),
            joining_date=request.POST.get('joining_date', None),
            dob=request.POST['dob'],
            blood_group=request.POST.get('blood_group', ''),
            id_no=request.POST['id_no'],
            aadhar=request.POST['aadhar'],
            pan=request.POST.get('pan', ''),
            email=request.POST['email'],
            mobile=request.POST['mobile'],
            emergency_contact=request.POST.get('emergency_contact', ''),
            address=request.POST.get('address', ''),
            insurance_policy_no=request.POST.get('insurance_policy_no', ''),
            insurance_expiry=request.POST.get('insurance_expiry', None),
            basic_salary=request.POST['basic_salary'],
            hra=request.POST['hra'],
            conveyance=request.POST['conveyance'],
            spl_allowance=request.POST['spl_allowance'],
            photo=request.FILES.get('photo', None),
        )
        staff.save()
        messages.success(request, 'Staff member added successfully!')
        return redirect('myApp:staff_success')
    return render(request, 'myApp/add_staff.html')

# View for editing staff
def edit_staff(request, id_no):
    staff = get_object_or_404(Staff, id_no=id_no)
    if request.method == 'POST':
        staff.name = request.POST['name']
        staff.designation = request.POST['designation']
        staff.qualification = request.POST.get('qualification', '')
        staff.joining_date = request.POST.get('joining_date', None)
        staff.dob = request.POST['dob']
        staff.blood_group = request.POST.get('blood_group', '')
        staff.aadhar = request.POST['aadhar']
        staff.pan = request.POST.get('pan', '')
        staff.email = request.POST['email']
        staff.mobile = request.POST['mobile']
        staff.emergency_contact = request.POST.get('emergency_contact', '')
        staff.address = request.POST.get('address', '')
        staff.insurance_policy_no = request.POST.get('insurance_policy_no', '')
        staff.insurance_expiry = request.POST.get('insurance_expiry', None)
        staff.basic_salary = request.POST['basic_salary']
        staff.hra = request.POST['hra']
        staff.conveyance = request.POST['conveyance']
        staff.spl_allowance = request.POST['spl_allowance']
        if request.FILES.get('photo'):
            staff.photo = request.FILES['photo']
        staff.save()
        messages.success(request, 'Staff member updated successfully!')
        return redirect('myApp:manage_staff')
    return render(request, 'myApp/edit_staff.html', {'staff': staff})

from datetime import datetime

def edit_staff_view(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    
    # Format the dates
    staff.joining_date = staff.joining_date.strftime('%Y-%m-%d') if staff.joining_date else ''
    staff.dob = staff.dob.strftime('%Y-%m-%d') if staff.dob else ''
    staff.insurance_expiry = staff.insurance_expiry.strftime('%Y-%m-%d') if staff.insurance_expiry else ''
    
    if request.method == 'POST':
        # Handle form submission
        pass
    
    return render(request, 'myApp/edit_staff.html', {'staff': staff})


register = template.Library()

@register.filter(name='b64encode')

def b64encode(value):

    return base64.b64encode(value).decode('utf-8')


# View for deleting staff
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Staff, Attendance

def delete_staff(request):
    if request.method == 'POST':
        try:
            # Retrieve id_no from query parameters
            id_no = request.GET.get('id_no')
            print(f"Received id_no exactly as passed: '{id_no}'")  # Debug log
            staff_member = get_object_or_404(Staff, id_no=id_no)

            # Delete all related attendance records
            deleted_count = Attendance.objects.filter(staff=staff_member).delete()
            print(f"Deleted {deleted_count} related attendance records")

            # Delete the staff member
            staff_member.delete()
            print(f"Deleted staff member with id_no: {id_no}")

            messages.success(request, 'Staff member and related data deleted successfully!')
            return redirect('myApp:manage_staff')
        except Staff.DoesNotExist:
            messages.error(request, 'Staff member not found.')
            return redirect('myApp:manage_staff')
        except Exception as e:
            print(f"Error occurred: {e}")
            messages.error(request, f'Error: {str(e)}')
            return redirect('myApp:manage_staff')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('myApp:manage_staff')



def manage_staff_view(request):
    Staff_list = Staff.objects.all()
    Staff_list = Staff.objects.values('id_no', 'name', 'designation', 'mobile')
    return render(request,'myApp/manage_staff.html',{'Staff_list':Staff_list})


def staff_detail(request, staff_id):
    staff = Staff.objects.get(id=staff_id)  # Fetch the staff member by ID
    return render(request, 'myApp/staff_detail.html', {'staff': staff})

def staff_success(request):
    return render(request, 'myApp/staff_success.html')

# _____________________________________________ATTENDANCE_______________________________________________________
# View for taking attendance page 

def attendance(request):
    staff_list = Staff.objects.all()
    return render(request, 'myApp/attendance.html', {'staff_list': staff_list})

def error(request):
    return render(request, 'myApp/error.html')

def view_attendance(request):
     if request.method == 'GET':
        attendance_date = request.GET.get('view_attendance_date')
        attendance_records = Attendance.objects.filter(attendance_date=attendance_date)
        return render(request, 'myApp/view_attendance.html', {'attendance_records': attendance_records, 'attendance_date': attendance_date})
     return render(request, 'myApp/view_attendance.html')

def attendance_staff_detail(request, staff_id):
    staff = get_object_or_404(Staff, id_no=staff_id)
    return render(request, 'myApp/attendance_staff_detail.html', {'staff': staff})

def attendance_success(request):
    return render(request, 'myApp/attendance_success.html')

def attendance_view(request):
    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date', timezone.now().date())
        today = timezone.now().date()
        # Convert attendance_date to a date object
        attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()

        # Prevent updating future attendance
        if attendance_date_obj > today:
            messages.error(request, 'Cannot record attendance for future dates.')
            return redirect('myApp:error')

        # Loop through the staff members in the POST data
        staff_list = Staff.objects.all()  # Fetch all staff members
        for staff in staff_list:
            attendance_type = request.POST.get(f'attendance_type_{staff.id_no}')
            if attendance_type:
                # Check if attendance already exists for the staff and date
                attendance, created = Attendance.objects.get_or_create(
                    staff=staff,  # Reference the staff instance
                    attendance_date=attendance_date,
                    defaults={'attendance_type': attendance_type}
                )

                if not created:
                    attendance.attendance_type = attendance_type
                    attendance.save()

        messages.success(request, 'Attendance recorded successfully!')
        return redirect('myApp:attendance_success')  # Redirect to the success page
    else:
        form = AttendanceForm()

    # Fetch today's attendance records to display
    attendance_records = Attendance.objects.filter(attendance_date=timezone.now().date())
    return render(request, 'myApp/attendance.html', {'form': form, 'attendance_records': attendance_records})

def attendance_menu(request):
    return render(request, 'myApp/attendance_menu.html')

def weekly_attendance(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendance_records = Attendance.objects.filter(attendance_date__range=[start_date, end_date])
    
    # Initialize a dictionary to hold attendance counts for each employee
    attendance_count = {}

    for record in attendance_records:
        staff_id = record.staff.id_no  # Assuming staff.id_no uniquely identifies each employee
        if staff_id not in attendance_count:
            attendance_count[staff_id] = {
                'name': record.staff.name,  # Store employee name
                'Onsite': 0,
                'Offsite': 0,
                'WFH': 0,
                'Leave': 0,
                'Travel': 0,
            }
        
        # Increment the count based on attendance type
        attendance_count[staff_id][record.attendance_type] += 1

    context = {
        'attendance_records': attendance_records,
        'attendance_count': attendance_count,
    }
    
    return render(request, 'myApp/weekly_attendance.html', context)


def monthly_attendance(request):
    month = request.GET.get('month')
    attendance_count = {}
    attendance_records = []  # Initialize attendance_records as an empty list

    if month and month.isdigit() and 1 <= int(month) <= 12:
        # Determine the year from the current date
        year = timezone.now().year

        # Get the start and end date for the specified month
        start_date = datetime(year, int(month), 1)
        end_date = datetime(year, int(month) + 1, 1) if month != '12' else datetime(year + 1, 1, 1)

        # Fetch attendance records for the specified month
        attendance_records = Attendance.objects.filter(attendance_date__range=[start_date, end_date])

        # Process attendance records to count attendance types per employee
        for record in attendance_records:
            staff_id = record.staff.id_no  # Assuming staff.id_no uniquely identifies each employee
            attendance_type = record.attendance_type
            
            # Initialize the employee's attendance counts if not already done
            if staff_id not in attendance_count:
                attendance_count[staff_id] = {
                    'name': record.staff.name,  # Store employee name
                    'Onsite': 0,
                    'Offsite': 0,
                    'WFH': 0,
                    'Leave': 0,
                    'Travel': 0,
                }

            # Increment the count based on attendance type
            if attendance_type in attendance_count[staff_id]:
                attendance_count[staff_id][attendance_type] += 1

    context = {
        'attendance_count': attendance_count,
        'attendance_records': attendance_records,  # Optional: if you want to use it in the template
    }
    
    return render(request, 'myApp/month.html', context)  # Updated template name





# _____________________________________________STAFF_PROFILES_______________________________________________________

def staff_profiles(request):
    staff_members = Staff.objects.all()
    context = {'staff_members': staff_members}
    return render(request, 'myApp/staff_profiles.html', context)

def view_bio(request, id_no):
    staff = get_object_or_404(Staff, id_no=id_no)
    return render(request, 'view_bio.html', {'staff': staff})

# _____________________________________________PAY_SLIP_______________________________________________________

def pay_slip(request):
    return render(request, 'myApp/pay_slip.html')

def pay_slip(request):
    staff_members = Staff.objects.all()  # Fetch all staff members
    context = {
        'staff_members': staff_members
    }
    return render(request, 'myApp/pay_slip.html', context)


# views.py

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Staff

def generate_pay_slip(request, id_no):
    # Fetch the staff member based on the id_no
    staff_member = Staff.objects.get(id_no=id_no)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    current_month = date.today().strftime('%B_%Y')
    response['Content-Disposition'] = f'attachment; filename="pay_slip_{staff_member.name}_{current_month}.pdf"'

    # Create the PDF using ReportLab
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Add the company logo
    logo_path = finders.find('myproject/images/logopdf.jpg')  # Ensure the logo is in the 'static/images' folder
    if logo_path:  # Check if logo is found
        p.drawImage(logo_path, 50, height - 100, width=120, height=50)

    # Title and Company Information
    p.setFont("Helvetica", 12)
    p.drawString(450, height - 60, "Pay Slip For the Month")
    
    # Fetch the present month
    p.setFont("Helvetica-Bold", 14)
    current_month = date.today().strftime('%B %Y')
    p.drawString(465, height - 80, f"{current_month}")

    # Employee Summary Section
    p.setFont("Helvetica-Bold", 9)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 160, "EMPLOYEE SUMMARY")
    p.setFillColor(colors.black)  # Reset to black for subsequent text


    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 180, "Employee Name     :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 180, f"{staff_member.name}")


    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 200, f"Employee ID           :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 200, f"{staff_member.id_no}")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 220, f"Pay Period              :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 220, f"{current_month}")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 240, f"Pay Date                 :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 240, f"{date.today().strftime('%d/%m/%Y')}")

    # Salary Information
    total_salary = staff_member.basic_salary + staff_member.hra + staff_member.conveyance + staff_member.spl_allowance + staff_member.incentive

    # Draw a dotted box around the salary information
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.setFillColor(colors.lightgreen)
    p.setFillAlpha(0.5)  # Set opacity to 50%
    p.roundRect(340, height - 210, 220, 75, 10, stroke=1, fill=1)
    p.setFillAlpha(0.5)  # Reset opacity to 100%
    p.setFillColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(340, height - 260, 220, 125, 10) #black border
    p.setFont("Helvetica-Bold", 25)
    p.drawString(350, height - 175, f"{total_salary:,.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(350, height - 190, "Employee Net Pay")
    
    # Calculate the number of leave days in the current month for the staff member
    year = date.today().year
    month = date.today().month
    leave_days = Attendance.objects.filter(
        staff=staff_member,
        attendance_type='Leave',
        attendance_date__year=year,
        attendance_date__month=month
    ).count()
    p.drawString(350, height - 250, f"LOP Days: {leave_days}")

    # Calculate the number of days in the current month
    num_days_in_month = monthrange(year, month)[1]
    paid_days = num_days_in_month - leave_days
    p.drawString(350, height - 230, f"Paid Days: {paid_days}")

    # Earnings and Deductions Table Headers
    # Draw a box around the Earnings and Deductions headers
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(50, height - 460, 500, 150, 10)

    p.setFont("Times-Roman", 12)
    p.drawString(60, height - 330, "EARNINGS")
    p.drawString(210, height - 330, "AMOUNT")
    p.drawString(310, height - 330, "DEDUCTIONS")
    p.drawString(460, height - 330, "AMOUNT")

    # Draw a dotted line between the earning amount and basic
    p.setDash(1, 2)  # Set the dash pattern: 1 point on, 2 points off
    p.line(60, height - 340, 260, height - 340)  # Draw the line
    p.setDash()  # Reset to solid line

    p.setDash(1, 2)  # Set the dash pattern: 1 point on, 2 points off
    p.line(310, height - 340, 510, height - 340)  # Draw the line
    p.setDash()  # Reset to solid line

    # Earnings Details
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 360, "Basic  ")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 360, f"{staff_member.basic_salary:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 380, "House Rent Allowance ")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 380, f"{staff_member.hra:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 400, "Conveyance")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 400, f"{staff_member.conveyance:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 420, "Special Allowance")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 420, f"{staff_member.spl_allowance:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 440, "Incentives")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 440, f"{staff_member.incentive:.2f}")


    p.drawString(60,height-470, "Gross Earnings")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 470, f"{total_salary:.2f}")

    # Deductions Details
    p.setFont("Helvetica", 10)
    p.drawString(310, height - 360, "Income Tax")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(460, height - 360, "0.00")
    p.setFont("Helvetica", 10)
    p.drawString(310, height - 380, "Provident Fund")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(460, height - 380, "0.00")

    
    p.drawString(310, height - 470  , "Total Deductions")
    total_deductions = 0.00  # Assuming no deductions for now
    p.drawString(460, height - 470, f"{total_deductions:.2f}")
        

    # Net Payable
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, height - 540, "TOTAL NET PAYABLE")
    p.setFont("Helvetica", 9)
    p.drawString(60, height - 550, "Gross Earnings - Total Deductions")
    p.setFont("Helvetica-Bold", 14)
    
    # Set background color for the amount only
    amount_x = 460
    amount_y = height - 560
    amount_width = 90
    amount_height = 35
    
    p.setFillColor(colors.lightgreen)
    p.setFillAlpha(0.5)  # Set opacity to 50%
    p.roundRect(amount_x, amount_y, amount_width, amount_height, 10, stroke=0, fill=1)
    
    # Reset fill color to black for text
    p.setFillAlpha(1)  # Reset opacity to 100%
    p.setFillColor(colors.black)
    p.drawString(470, height - 548, f"{total_salary:,.2f}")

    # Draw a box around the Net Payable section
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(50, height - 560, 500, 35, 10)

    p.showPage()
    p.save()

    return response


# views.py

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import date
from calendar import monthrange
from .models import Staff, Attendance  # Adjust as needed based on your models
from django.contrib.staticfiles import finders

def view_pay_slip(request, id_no):
    # Fetch the staff member based on the id_no
    try:
        staff_member = Staff.objects.get(id_no=id_no)
    except Staff.DoesNotExist:
        return HttpResponse("Staff member not found", status=404)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="pay_slip_{staff_member.name}.pdf"'

    # Create the PDF using ReportLab
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Add the company logo
    logo_path = finders.find('myproject/images/logopdf.jpg')  # Ensure the logo is in the 'static/images' folder
    if logo_path:  # Check if logo is found
        p.drawImage(logo_path, 50, height - 100, width=120, height=50)

    # Title and Company Information
    p.setFont("Helvetica", 12)
    p.drawString(450, height - 60, "Pay Slip For the Month")
    
    # Fetch the present month
    p.setFont("Helvetica-Bold", 14)
    current_month = date.today().strftime('%B %Y')
    p.drawString(465, height - 80, f"{current_month}")

    # Employee Summary Section
    p.setFont("Helvetica-Bold", 9)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 160, "EMPLOYEE SUMMARY")
    p.setFillColor(colors.black)  # Reset to black for subsequent text


    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 180, "Employee Name     :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 180, f"{staff_member.name}")


    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 200, f"Employee ID           :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 200, f"{staff_member.id_no}")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 220, f"Pay Period              :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 220, f"{current_month}")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(65, height - 240, f"Pay Date                 :")
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 240, f"{date.today().strftime('%d/%m/%Y')}")

    # Salary Information
    total_salary = staff_member.basic_salary + staff_member.hra + staff_member.conveyance + staff_member.spl_allowance + staff_member.incentive

    # Draw a dotted box around the salary information
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.setFillColor(colors.lightgreen)
    p.setFillAlpha(0.5)  # Set opacity to 50%
    p.roundRect(340, height - 210, 220, 75, 10, stroke=1, fill=1)
    p.setFillAlpha(0.5)  # Reset opacity to 100%
    p.setFillColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(340, height - 260, 220, 125, 10) #black border
    p.setFont("Helvetica-Bold", 25)
    p.drawString(350, height - 175, f"{total_salary:,.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(350, height - 190, "Employee Net Pay")
    
    # Calculate the number of leave days in the current month for the staff member
    year = date.today().year
    month = date.today().month
    leave_days = Attendance.objects.filter(
        staff=staff_member,
        attendance_type='Leave',
        attendance_date__year=year,
        attendance_date__month=month
    ).count()
    p.drawString(350, height - 250, f"LOP Days: {leave_days}")

    # Calculate the number of days in the current month
    num_days_in_month = monthrange(year, month)[1]
    paid_days = num_days_in_month - leave_days
    p.drawString(350, height - 230, f"Paid Days: {paid_days}")

    # Earnings and Deductions Table Headers
    # Draw a box around the Earnings and Deductions headers
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(50, height - 460, 500, 150, 10)

    p.setFont("Times-Roman", 12)
    p.drawString(60, height - 330, "EARNINGS")
    p.drawString(210, height - 330, "AMOUNT")
    p.drawString(310, height - 330, "DEDUCTIONS")
    p.drawString(460, height - 330, "AMOUNT")

    # Draw a dotted line between the earning amount and basic
    p.setDash(1, 2)  # Set the dash pattern: 1 point on, 2 points off
    p.line(60, height - 340, 260, height - 340)  # Draw the line
    p.setDash()  # Reset to solid line

    p.setDash(1, 2)  # Set the dash pattern: 1 point on, 2 points off
    p.line(310, height - 340, 510, height - 340)  # Draw the line
    p.setDash()  # Reset to solid line

    # Earnings Details
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 360, "Basic  ")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 360, f"{staff_member.basic_salary:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 380, "House Rent Allowance ")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 380, f"{staff_member.hra:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 400, "Conveyance")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 400, f"{staff_member.conveyance:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 420, "Special Allowance")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 420, f"{staff_member.spl_allowance:.2f}")
    p.setFont("Helvetica", 10)
    p.drawString(60, height - 440, "Incentives")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 440, f"{staff_member.incentive:.2f}")


    p.drawString(60,height-470, "Gross Earnings")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(210, height - 470, f"{total_salary:.2f}")

    # Deductions Details
    p.setFont("Helvetica", 10)
    p.drawString(310, height - 360, "Income Tax")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(460, height - 360, "0.00")
    p.setFont("Helvetica", 10)
    p.drawString(310, height - 380, "Provident Fund")
    p.setFont("Helvetica-Bold", 10)
    p.drawString(460, height - 380, "0.00")

    
    p.drawString(310, height - 470  , "Total Deductions")
    total_deductions = 0.00  # Assuming no deductions for now
    p.drawString(460, height - 470, f"{total_deductions:.2f}")
        

    # Net Payable
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, height - 540, "TOTAL NET PAYABLE")
    p.setFont("Helvetica", 9)
    p.drawString(60, height - 550, "Gross Earnings - Total Deductions")
    p.setFont("Helvetica-Bold", 14)
    
    # Set background color for the amount only
    amount_x = 460
    amount_y = height - 560
    amount_width = 90
    amount_height = 35
    
    p.setFillColor(colors.lightgreen)
    p.setFillAlpha(0.5)  # Set opacity to 50%
    p.roundRect(amount_x, amount_y, amount_width, amount_height, 10, stroke=0, fill=1)
    
    # Reset fill color to black for text
    p.setFillAlpha(1)  # Reset opacity to 100%
    p.setFillColor(colors.black)
    p.drawString(470, height - 548, f"{total_salary:,.2f}")

    # Draw a box around the Net Payable section
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.roundRect(50, height - 560, 500, 35, 10)

    p.showPage()
    p.save()

    return response

def edit_earnings(request, id_no):
    staff = get_object_or_404(Staff, id_no=id_no)
        
    if request.method == 'POST':
        staff.basic_salary = request.POST['basic_salary']
        staff.hra = request.POST['hra']
        staff.conveyance = request.POST['conveyance']
        staff.spl_allowance = request.POST['spl_allowance']
        staff.incentive = request.POST['incentive']
        staff.save()
        messages.success(request, 'Earnings updated successfully!')
        return redirect('myApp:pay_slip')
        
    return render(request, 'myApp/edit_earnings.html', {'staff': staff})







# _____________________________________________settings_______________________________________________________
def settings(request):
    return render(request, 'myApp/settings.html')

#___________________________________________-Backup_______________________________________________________



