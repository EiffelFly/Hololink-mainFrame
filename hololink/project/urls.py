from django.urls import path
from .views import projects_list, project_detail, create_newproject, project_dashboard, project_articles, project_hologram, galaxy_setting, deliver_D3, galaxy_telescope, add_telescope_configuration

app_name = 'project'

urlpatterns = [
     path('', projects_list, name='projects_list'),
     path('create/', create_newproject, name='create_newproject'),
     path('ajax/add_telescope_configuration/', add_telescope_configuration, name='add_telescope_configuration'),
     path('<slug:projectnameslug>/', project_dashboard, name='project_dashboard'),
     path('<slug:projectnameslug>/articles', project_articles, name='project_articles'),
     path('<slug:projectnameslug>/hologram', project_hologram, name='project_hologram'),
     path('<slug:projectnameslug>/settings', galaxy_setting, name='galaxy_setting'),
     path('<slug:projectnameslug>/telescope', galaxy_telescope, name='galaxy_telescope'),
     path('<slug:projectnameslug>/deliverd3', deliver_D3, name='deliver_D3')
]