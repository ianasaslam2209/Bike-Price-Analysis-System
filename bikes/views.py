import csv, io, json, os
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Min, Max, Count
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Bike, EmailVerification

def is_admin(user):
    return user.is_authenticated and user.is_staff

def _filter_bikes(request, qs=None):
    qs = qs or Bike.objects.all()
    q         = request.GET.get('q', '').strip()
    brand     = request.GET.get('brand', '').strip()
    year      = request.GET.get('year', '').strip()
    fuel      = request.GET.get('fuel', '').strip()
    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()

    if q:
        qs = qs.filter(Q(bike_name__icontains=q) | Q(brand__icontains=q))
    if brand:
        qs = qs.filter(brand=brand)
    if year:
        qs = qs.filter(year=year)
    if fuel:
        qs = qs.filter(fuel_type=fuel)
    if price_min:
        qs = qs.filter(price_usd__gte=float(price_min))
    if price_max:
        qs = qs.filter(price_usd__lte=float(price_max))
    return qs

def _sync_record_to_csv(bike, action='update'):
    """Sync a single record to the CSV file (update or delete)."""
    csv_path = settings.CSV_PATH
    if not os.path.exists(csv_path):
        return

    rows = []
    fieldnames = ['bike_name', 'brand', 'year', 'fuel_type', 'kms_driven', 'engine_capacity_cc', 'price_usd']

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    _rebuild_csv_from_db()

def _rebuild_csv_from_db():
    """Rewrite the entire CSV from the current DB state."""
    csv_path = settings.CSV_PATH
    fieldnames = ['bike_name', 'brand', 'year', 'fuel_type', 'kms_driven', 'engine_capacity_cc', 'price_usd']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for b in Bike.objects.all().order_by('id'):
            writer.writerow({
                'bike_name': b.bike_name,
                'brand': b.brand,
                'year': b.year,
                'fuel_type': b.fuel_type,
                'kms_driven': b.kms_driven,
                'engine_capacity_cc': b.engine_capacity_cc,
                'price_usd': str(b.price_usd),
            })

def signup_view(request):
    """Step 1: collect email+username+password, send verification code."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        step = request.POST.get('step', '1')

        if step == '1':
            username = request.POST.get('username', '').strip()
            email    = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            password2 = request.POST.get('password2', '').strip()

            if not username or not email or not password:
                messages.error(request, 'All fields are required.')
            elif password != password2:
                messages.error(request, 'Passwords do not match.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
            else:
                code = EmailVerification.generate_code()
                EmailVerification.objects.filter(email=email, used=False).delete()
                EmailVerification.objects.create(email=email, code=code)

                send_mail(
                    subject='Your BikeAnalysis Verification Code',
                    message=f'Your verification code is: {code}\n\nIt expires in 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )

                request.session['pending_signup'] = {
                    'username': username,
                    'email': email,
                    'password': password,
                }
                messages.success(request, f'Verification code sent to {email}. Check your email (or console in dev mode).')
                return render(request, 'bikes/signup.html', {'step': '2', 'email': email})

        elif step == '2':
            code  = request.POST.get('code', '').strip()
            email = request.POST.get('email', '').strip()
            pending = request.session.get('pending_signup')

            if not pending or pending['email'] != email:
                messages.error(request, 'Session expired. Please start again.')
                return render(request, 'bikes/signup.html', {'step': '1'})

            try:
                ev = EmailVerification.objects.filter(email=email, code=code, used=False).latest('created_at')
            except EmailVerification.DoesNotExist:
                messages.error(request, 'Invalid verification code.')
                return render(request, 'bikes/signup.html', {'step': '2', 'email': email})

            if ev.is_expired():
                messages.error(request, 'Code expired. Please sign up again.')
                return render(request, 'bikes/signup.html', {'step': '1'})

            ev.used = True
            ev.save()

            user = User.objects.create_user(
                username=pending['username'],
                email=pending['email'],
                password=pending['password'],
            )
            del request.session['pending_signup']
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account is verified.')
            return redirect('home')

    return render(request, 'bikes/signup.html', {'step': '1'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'bikes/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    all_bikes = Bike.objects.all()
    stats = all_bikes.aggregate(
        avg_price=Avg('price_usd'),
        min_price=Min('price_usd'),
        max_price=Max('price_usd'),
    )
    featured_bikes = all_bikes.order_by('-price_usd')[:6]
    brand_count = all_bikes.values('brand').distinct().count()
    year_count  = all_bikes.values('year').distinct().count()

    context = {
        'db_total'      : all_bikes.count(),
        'stats'         : stats,
        'featured_bikes': featured_bikes,
        'brand_count'   : brand_count,
        'year_count'    : year_count,
    }
    return render(request, 'bikes/home.html', context)

@login_required
def search(request):
    bikes = _filter_bikes(request)
    total = bikes.count()
    all_bikes = Bike.objects.all()
    brands = all_bikes.values_list('brand', flat=True).distinct().order_by('brand')
    years  = all_bikes.values_list('year', flat=True).distinct().order_by('-year')
    stats  = bikes.aggregate(avg_price=Avg('price_usd'), min_price=Min('price_usd'), max_price=Max('price_usd'))

    context = {
        'bikes'        : bikes,
        'total'        : total,
        'brands'       : brands,
        'years'        : years,
        'stats'        : stats,
        'q'            : request.GET.get('q',''),
        'sel_brand'    : request.GET.get('brand',''),
        'sel_year'     : request.GET.get('year',''),
        'sel_fuel'     : request.GET.get('fuel',''),
        'sel_price_min': request.GET.get('price_min',''),
        'sel_price_max': request.GET.get('price_max',''),
        'db_total'     : all_bikes.count(),
    }
    return render(request, 'bikes/search.html', context)

@login_required
def bike_detail(request, pk):
    bike      = get_object_or_404(Bike, pk=pk)
    similar   = Bike.objects.filter(brand=bike.brand).exclude(pk=pk).order_by('?')[:4]
    brand_avg = Bike.objects.filter(brand=bike.brand).aggregate(avg=Avg('price_usd'))['avg'] or 0
    context   = {'bike': bike, 'similar': similar, 'brand_avg': round(float(brand_avg), 2)}
    return render(request, 'bikes/detail.html', context)

@login_required
def analytics(request):
    all_bikes = Bike.objects.all()
    total     = all_bikes.count() or 1
    fuel_qs   = all_bikes.values('fuel_type').annotate(cnt=Count('id'))
    fuel_map  = {r['fuel_type']: r['cnt'] for r in fuel_qs}
    petrol_n  = fuel_map.get('Petrol', 0)
    electric_n= fuel_map.get('Electric', 0)

    import statistics
    prices   = list(all_bikes.values_list('price_usd', flat=True))
    prices_f = [float(p) for p in prices]
    p_min, p_max = min(prices_f), max(prices_f)
    bucket = (p_max - p_min) / 10
    hist_labels, hist_counts = [], []
    for i in range(10):
        lo = p_min + i * bucket
        hi = lo + bucket
        cnt = sum(1 for p in prices_f if lo <= p < hi)
        hist_labels.append(f"${int(lo/1000)}k" if lo >= 1000 else f"${int(lo)}")
        hist_counts.append(cnt)

    brand_stats = all_bikes.values('brand').annotate(
        avg_price=Avg('price_usd'), cnt=Count('id'),
        min_price=Min('price_usd'), max_price=Max('price_usd'),
    ).order_by('-avg_price')

    year_trend = all_bikes.values('year').annotate(avg_price=Avg('price_usd')).order_by('year')
    scatter    = list(
        all_bikes.filter(fuel_type='Petrol', engine_capacity_cc__gt=0)
        .values('bike_name','brand','engine_capacity_cc','price_usd','kms_driven')[:200]
    )
    top10 = all_bikes.order_by('-price_usd')[:10]

    context = {
        'total'       : total,
        'petrol_n'    : petrol_n,
        'electric_n'  : electric_n,
        'petrol_pct'  : round(petrol_n / total * 100, 1),
        'electric_pct': round(electric_n / total * 100, 1),
        'hist_labels' : json.dumps(hist_labels),
        'hist_counts' : json.dumps(hist_counts),
        'brand_stats' : brand_stats,
        'year_trend'  : json.dumps([{'year': r['year'], 'avg': round(float(r['avg_price']),2)} for r in year_trend]),
        'scatter_data': json.dumps([{'name':r['bike_name'],'brand':r['brand'],'cc':r['engine_capacity_cc'],'price':float(r['price_usd']),'kms':r['kms_driven']} for r in scatter]),
        'top10'       : top10,
        'avg_price'   : round(sum(prices_f)/len(prices_f), 2),
        'median_price': round(statistics.median(prices_f), 2),
    }
    return render(request, 'bikes/analytics.html', context)

@login_required
def compare(request):
    all_bikes    = Bike.objects.all().order_by('brand','bike_name')
    selected_ids = request.GET.getlist('ids')
    selected     = Bike.objects.filter(id__in=selected_ids) if selected_ids else []
    return render(request, 'bikes/compare.html', {
        'all_bikes'   : all_bikes,
        'selected'    : selected,
        'selected_ids': [str(i) for i in selected_ids],
    })

@user_passes_test(is_admin, login_url='/login/')
def import_csv(request):
    result = None
    if request.method == 'POST' and request.FILES.get('csv_file'):
        f       = request.FILES['csv_file']
        decoded = f.read().decode('utf-8')
        reader  = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors  = []
        for i, row in enumerate(reader, 1):
            try:
                Bike.objects.create(
                    bike_name          = row['bike_name'].strip(),
                    brand              = row['brand'].strip(),
                    year               = int(row['year']),
                    fuel_type          = row['fuel_type'].strip(),
                    kms_driven         = int(row['kms_driven']),
                    engine_capacity_cc = int(row['engine_capacity_cc']),
                    price_usd          = float(row['price_usd']),
                )
                created += 1
            except Exception as e:
                errors.append(f"Row {i}: {e}")
        _rebuild_csv_from_db()
        result = {'created': created, 'errors': errors[:10]}
    return render(request, 'bikes/import_csv.html', {
        'result'  : result,
        'db_total': Bike.objects.count(),
    })

@user_passes_test(is_admin, login_url='/login/')
def admin_records(request):
    """Admin dashboard: view, search all records with update/delete."""
    bikes = _filter_bikes(request)
    all_bikes = Bike.objects.all()
    brands = all_bikes.values_list('brand', flat=True).distinct().order_by('brand')
    years  = all_bikes.values_list('year', flat=True).distinct().order_by('-year')

    context = {
        'bikes'        : bikes,
        'total'        : bikes.count(),
        'db_total'     : all_bikes.count(),
        'brands'       : brands,
        'years'        : years,
        'q'            : request.GET.get('q',''),
        'sel_brand'    : request.GET.get('brand',''),
        'sel_year'     : request.GET.get('year',''),
        'sel_fuel'     : request.GET.get('fuel',''),
        'sel_price_min': request.GET.get('price_min',''),
        'sel_price_max': request.GET.get('price_max',''),
    }
    return render(request, 'bikes/admin_records.html', context)

@user_passes_test(is_admin, login_url='/login/')
def bike_edit(request, pk):
    bike = get_object_or_404(Bike, pk=pk)

    if request.method == 'POST':
        try:
            bike.bike_name          = request.POST['bike_name'].strip()
            bike.brand              = request.POST['brand'].strip()
            bike.year               = int(request.POST['year'])
            bike.fuel_type          = request.POST['fuel_type'].strip()
            bike.kms_driven         = int(request.POST['kms_driven'])
            bike.engine_capacity_cc = int(request.POST['engine_capacity_cc'])
            bike.price_usd          = float(request.POST['price_usd'])
            bike.save()
            _rebuild_csv_from_db()
            messages.success(request, f'"{bike.bike_name}" updated successfully and CSV synced.')
            return redirect('admin_records')
        except Exception as e:
            messages.error(request, f'Error updating record: {e}')

    return render(request, 'bikes/bike_edit.html', {'bike': bike})

@user_passes_test(is_admin, login_url='/login/')
def bike_delete(request, pk):
    bike = get_object_or_404(Bike, pk=pk)

    if request.method == 'POST':
        name = bike.bike_name
        bike.delete()
        _rebuild_csv_from_db()
        messages.success(request, f'"{name}" deleted from DB and CSV.')
        return redirect('admin_records')

    return render(request, 'bikes/bike_confirm_delete.html', {'bike': bike})

@user_passes_test(is_admin, login_url='/login/')
def bike_add(request):
    if request.method == 'POST':
        try:
            bike = Bike.objects.create(
                bike_name          = request.POST['bike_name'].strip(),
                brand              = request.POST['brand'].strip(),
                year               = int(request.POST['year']),
                fuel_type          = request.POST['fuel_type'].strip(),
                kms_driven         = int(request.POST['kms_driven']),
                engine_capacity_cc = int(request.POST['engine_capacity_cc']),
                price_usd          = float(request.POST['price_usd']),
            )
            _rebuild_csv_from_db()
            messages.success(request, f'"{bike.bike_name}" added and CSV synced.')
            return redirect('admin_records')
        except Exception as e:
            messages.error(request, f'Error adding record: {e}')

    return render(request, 'bikes/bike_add.html')

