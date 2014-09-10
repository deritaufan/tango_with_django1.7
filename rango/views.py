from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.mail import send_mail, EmailMultiAlternatives #use to send html email
from django.utils import timezone
from django.template.loader import render_to_string #use to send html email
from django.utils.html import strip_tags #use to send html email
from django.contrib.auth.models import User

import hashlib, random, datetime

from rango.models import *
from rango.forms import *


def index(request):
    #context = RequestContext(request)

    category_list = get_category_list()
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list,}

    #response = render(request, 'rango/index.html', context_dict)

    #visits = int(request.COOKIES.get('visits', '0'))
    #if 'last_visit' in request.COOKIES:
    #    last_visit = request.COOKIES['last_visit']
    #    last_visit_time = datetime.datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
    #    if (datetime.datetime.now() - last_visit_time).days > 0:
    #        response.set_cookie('visits', visits+1)
    #        response.set_cookie('last_visit', datetime.datetime.now())
    #else:
    #    response.set_cookie('last_visit', datetime.datetime.now())

    #return response
    if request.session.get('last_visits'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.datetime.now() - datetime.datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.datetime.now())
    else:
        request.session['last_visit'] = str(datetime.datetime.now())
        request.session['visits'] = 1

    return render(request, 'rango/index.html', context_dict)

def about(request):
    category_list = get_category_list()
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    return render(request, 'rango/about.html', {'visits': count, 'categories': category_list})

def category(request, category_name_url):
    #context = RequestContext(request)
    category_list = get_category_list()
    category_name = category_name_url.replace('_', ' ')
    context_dict = {'category_name': category_name, 'category_name_url': category_name_url,
                    'categories': category_list}
    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages']= pages
        context_dict['category']= category
    except Category.DoesNotExist:
        pass

    return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
    #context = RequestContext(request)
    category_list = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render(request, 'rango/add_category.html', {'form': form, 'categories': category_list})

@login_required
def add_page(request, category_name_url):
    #context = RequestContext(request)
    category_list = get_category_list()
    category_name = category_name_url.replace('_', ' ')
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render(request, 'rango/add_category.html')

            page.views = 0
            page.save()

            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    return render(request, 'rango/add_page.html',
        {'category_name_url': category_name_url,
         'category_name': category_name, 'form': form,
         'categories': category_list})

def register(request):
    #context = RequestContext(request)
    category_list = get_category_list()
    args = {}
    args['categories'] = category_list
    args['registered'] = False
    args.update(csrf(request))
    if request.method == 'POST':
        form = UserForm(request.POST)
        profile = UserProfileForm(request.POST) # New line
        args['user_form'] = form
        args['profile_form'] = profile # New line
        if form.is_valid() and profile.is_valid(): # Added second conditional
            form.save()

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            website = profile.cleaned_data['website']
            picture = profile.cleaned_data['picture']

            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            activation_key = hashlib.sha1(salt+email).hexdigest()
            key_expire = datetime.datetime.today() + datetime.timedelta(2)

            user = User.objects.get(username=username)

            if 'picture' in request.FILES:
                picture = request.FILES['picture']
            new_profile = UserProfile(user=user, activation_key=activation_key,
                                      key_expire=key_expire, website=website, picture=picture)
            new_profile.save()

            args['registered'] = True

            email_subject = 'Account confirmation'
            html_content = render_to_string('rango/email_activation.html',
                                            {'username': username, 'activation_key': activation_key})
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(email_subject, text_content, 'admin@rango.com', [email])
            msg.attach(html_content, "text/html")
            msg.send()

            #email_body = "Hey %s thanks for signing up. To activate your account, click this link within 48 hours" \
            #             " http://127.0.0.1:8000/rango/confirm/%s" % (username, activation_key)
            #send_mail(email_subject, email_body, 'admin@rango.com',
            #          [email], fail_silently=False)
            args['email'] = email

            #return HttpResponseRedirect('/rango/register')
    else:
        args['user_form'] = UserForm()
        args['profile_form'] = UserProfileForm()

    return render(request, 'rango/register.html', args)

def register_confirm(request, activation_key):
    if request.user.is_authenticated():
        HttpResponseRedirect('/rango/')

    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)

    if user_profile.key_expire < timezone.now():
        return render_to_response('rango/confirm_expired.html')

    user = user_profile.user
    user.is_active = True
    user.save()

    return render(request, 'rango/confirm.html')

#def register_success(request):
#    context = RequestContext(request)
#    return render_to_response('rango/register_success.html', {}, context)

def user_login(request):
    category_list = get_category_list()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Your rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'rango/login.html', {'categories': category_list})

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')

def get_category_list():
    cat_list = Category.objects.all()

    for cat in cat_list:
        cat.url = cat.name.replace(' ', '_')

    return cat_list

@login_required
def profile(request):
    category_list = get_category_list()
    context_dict = {'categories': category_list}
    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render(request, 'rango/profile.html', context_dict)

def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)

@login_required
def like_category(request):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            category.save()

    return HttpResponse(likes)