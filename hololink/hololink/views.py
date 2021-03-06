from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from accounts.forms import SignUpWithEmailForm
from .forms import UserSettingsFormForPublicProfile
from django.core.mail import send_mail
from django.conf import settings
from project.models import Project
from accounts.models import Profile, Recommendation
from article.models import Keyword, Article, Domain
from django.contrib.auth.models import User
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Sum
from django.http import HttpResponseRedirect
import os
from .settings import BASE_DIR
from django.db.models import Count


def now():
    return timezone.localtime(timezone.now())

def d3demo(request):
    return render(request, 'd3demo.html')


# a email-sending script, not a view
def send_password_email(subject, message, recipient):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


def index(request):
    if request.method == 'POST':
        form = SignUpWithEmailForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data.get('email')
            username = email[0:email.index('@')]
            user.username = username
            random_uuid_password = uuid.uuid4().hex[0:6]
            user.set_password(random_uuid_password)
            user.save()
            # send a random uuid password email
            recipient = f'{email}'
            subject = "[Hololink] You have created an account."
            try:
                if '_' in username:
                    username_readable = ' '.join([word[0].upper() + word[1:] for word in username.split('_')])
                else:
                    username_readable = username
            except Exception:
                username_readable = username
            message = f'Hi {username_readable},'
            message += '\n\nYou have created a new account on Hololink. Login and learn more!'
            message += f'\n\nYour account: {username}'
            message += f'\nYour password: {random_uuid_password}'
            message += '\n\nSincerely,'
            message += '\nHololink'
            send_password_email(
                subject=subject,
                message=message,
                recipient=recipient,
            )
            return redirect('/accounts/password_reset/done/')
    else:
        form = SignUpWithEmailForm()
    context = {
        'form': form,
    }
    if request.user.is_authenticated:
        return redirect(reverse('user_dashboard', kwargs={'slug':request.user}))
    else:
        return render(request, 'landing_page_ver3.html', context)
    
    

def user_dashboard(request, slug):
    if not request.user.is_authenticated:
        return redirect(reverse('login'))
    
    profile = get_object_or_404(Profile, user=request.user)
    user = get_object_or_404(User, username=request.user)

    count_articles = []
    projects = Project.objects.filter(created_by=request.user).order_by('-last_edited_time') #use -created_at to desc()
    
    projects = projects[:4]
    for project in projects:
        count_articles.append(project.articles_project_owned.all().count())

    count_projects = projects.count()
    count_followings = profile.followings.count()
    count_followers = user.followers.count()
    count_likes = projects.aggregate(Sum('project_likes')).get('project_likes__sum', 0)
    count_basestone = Keyword.objects.filter(owned_by_user=profile, keyword_type='basestone').count()
    count_stellar = Keyword.objects.filter(owned_by_user=profile, keyword_type='stellar').count()
    count_recommendation = Recommendation.objects.filter(user=user).count()
    count_source = profile.source.count()
    count_user_owned_article = Article.objects.filter(owned_by=user).count()


    data_for_insights = [
        {'title':'Articles', 'count':count_user_owned_article},
        {'title':'Galaxies', 'count':count_projects},
        {'title':'Basestones', 'count':count_basestone},
        {'title':'Stellars', 'count':count_stellar},
        {'title':'Sources', 'count':count_source},
        {'title':'Recommendation', 'count':count_recommendation}
    ]

    print(count_basestone)

    context = {
        'profile' : profile,
        'projects' : projects,
        'countArticles' : count_articles,
        'countFollowings' : count_followings,
        'countFollowers' : count_followers,
        'countlikes' : count_likes,
        'data_for_insights' : data_for_insights,
        'active_nav':'overview'
    }

    return render(request, 'user_dashboard_ver2.html', context) 

def user_public_profile(request, slug):
    
    '''
        BE CAREFUL!! This section is user public area, can't let any not alowed info leak out.
    '''
    countArticles = []
    
    projects = Project.objects.filter(created_by=request.user).filter(project_visibility='Public').order_by('-last_edited_time') #use -created_at to desc()
    projects = projects[:4]
    for project in projects:
        countArticles.append(project.articles.count())

    profile = get_object_or_404(Profile, user=request.user)

    context = {
        'profile':profile,
        'projects': projects,
        'countArticles' : countArticles
    }

    return render(request, 'user_dashboard_ver2_public.html', context) 


def explore(request):
    projects = Project.objects.filter(project_visibility='Public')
    project_sortby_likes = projects.order_by('-project_likes')
    


    context = {
        'project_sortby_likes':project_sortby_likes,
        'projects':projects
    }

    return render(request, 'explore.html', context) 

def user_source(request, usernameslug):
    
    count_article_list = []

    profile = get_object_or_404(Profile, user=request.user)
    domains = Domain.objects.filter(owned_by_user=profile).annotate(num_source=Count('owned_by_articles')).order_by('-num_source')
    for domain in domains:
        count_article = Article.objects.filter(owned_by=request.user, domain=domain).count()
        count_article_list.append(count_article)

    context = {
        'domains':domains,
        'profile':profile,
        'count_article_list':count_article_list,
        'active_nav':'sources',

    }

    return render(request, 'user_source.html', context)
    

def explore_users(request):
    '''
        BE CAREFUL! This will demo some user public info.
    '''
    #profiles = Profile.objects.all()

    profile = Profile.objects.all().order_by('-followers')

    context = {
        'profile':profile,
    }
    
    return render(request, 'explore_users.html', context)

@csrf_exempt
def user_settings(request, slug):
    profile = get_object_or_404(Profile, user=request.user)
    user = get_object_or_404(User, username=request.user)

    context = {
        'form': None,
        'tips': [],
        'profile':profile,
        'active_nav':'public_profile',
    }

    if request.method == 'POST':
        form = UserSettingsFormForPublicProfile(request.POST)
        changedFieldforMessage = []
        # make sure we don't update the username and cause error because
        # cleaned_data.get('username') is '' right now
        if 'username' not in form.changed_data:
            if form.is_valid():
                # make sure user had changed the bio not the initial value we put in 
                if form.cleaned_data.get('bio') != profile.bio:
                    setattr(profile, 'bio', form.cleaned_data.get('bio'))
                    changedFieldforMessage.append('Bio')
                    if request.FILES.get('avatar', None) != None:
                        try:
                            os.remove(BASE_DIR + user.profile.user_avatar.url)
                        except Exception as e:
                            print('Exception in removing old profile image: ', e)
                        profile.user_avatar = request.FILES['avatar']
                        changedFieldforMessage.append('Avatar')

                    profile.save()
                    changedFieldforMessage_str = '、'.join(changedFieldforMessage)
                    messages.success(request, _(f'Profile updated successfully: {changedFieldforMessage_str}'))
                    return HttpResponseRedirect(reverse('user_settings', args=(slug,)))
                else:
                    if request.FILES.get('avatar', None) != None:
                        try:
                            os.remove(BASE_DIR + user.profile.user_avatar.url)
                        except Exception as e:
                            print('Exception in removing old profile image: ', e)
                        profile.user_avatar = request.FILES['avatar']
                        changedFieldforMessage.append('Avatar')
                        profile.save()
                        changedFieldforMessage_str = '、'.join(changedFieldforMessage)
                        messages.success(request, _(f'Profile updated successfully: {changedFieldforMessage_str}'))

                    form = UserSettingsFormForPublicProfile()                 
                    context['form'] = form
                    form.fields['username'].widget.attrs['placeholder'] = profile.user 
                    form.fields['bio'].initial = profile.bio
                    return render(request, 'user_settings_publicprofile.html', context)
            else:
                form = UserSettingsFormForPublicProfile(request.POST)
                context['form'] = form
                return render(request, 'user_settings_publicprofile.html', context)          
        else:
            if form.is_valid():
                setattr(profile, 'bio', form.cleaned_data.get('bio'))
                setattr(user, 'username', form.cleaned_data.get('username'))
                changedFieldforMessage.append('Username')
                changedFieldforMessage.append('Bio')
                if request.FILES.get('avatar', None) != None:
                    try:
                        os.remove(BASE_DIR + user.profile.user_avatar.url)
                    except Exception as e:
                        print('Exception in removing old profile image: ', e)
                    profile.user_avatar = request.FILES['avatar']
                    changedFieldforMessage.append('Avatar')

                profile.save()
                user.save()
                changedFieldforMessage_str = '、'.join(changedFieldforMessage)
                messages.success(request, _(f'Profile updated successfully: {changedFieldforMessage_str}'))
                return HttpResponseRedirect(reverse('user_settings', args=(slug,)))
            else:
                form = UserSettingsFormForPublicProfile(request.POST)
                context['form'] = form
                return render(request, 'user_settings_publicprofile.html', context)

    else:
        form = UserSettingsFormForPublicProfile()
        context['form'] = form
        form.fields['username'].widget.attrs['placeholder'] = profile.user 
        form.fields['bio'].initial = profile.bio
        return render(request, 'user_settings_publicprofile.html', context)


def user_settings_account(request,slug):
    profile = get_object_or_404(Profile, user=request.user)
    user = get_object_or_404(User, username=request.user)

    context = {
        'form': None,
        'tips': [],
        'profile':profile,
        'active_nav':'account',
    }

    return render(request, 'user_settings_account.html', context)