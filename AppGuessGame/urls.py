from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import (
    politicaPrivacidade,
    sobreNos,
    oferecemos,
    readme,
    guess_game_times,
    proximos_jogos_graficos,
    proximos_jogos_lista,
    faleConosco,
    contato_sucesso,
    cookie_policy,
    accept_cookies,
    visitor_log_list,
    visitor_log_detail,
    add_visitor_log,
    user_list,
    user_detail,
    update_user,
    profile_detail,
    edit_profile,
    register,
    home,
    log_ip,
)
 
urlpatterns = [
    path('politicaPrivacidade/', politicaPrivacidade, name='politicaPrivacidade'),
    path('sobreNos/', sobreNos, name='sobreNos'),
    path('oferecemos/', oferecemos, name='oferecemos'),
    path('readme/', readme, name='readme'),
    path('guess_game_times/', guess_game_times, name='guess_game_times'),
    path('proximos_jogos_lista/', proximos_jogos_lista, name='proximos_jogos_lista'),
    path('graficos/<int:jogo_id>/', proximos_jogos_graficos, name='proximos_jogos_graficos'),
    path('faleConosco/', faleConosco, name='faleConosco'),
    path('contato/sucesso/', contato_sucesso, name='contato_sucesso'),
    path('cookie_policy/', cookie_policy, name='cookie_policy'),
    path('accept_cookies/', accept_cookies, name='accept_cookies'),


    path('visitor_logs/', visitor_log_list, name='visitor_log_list'),
    path('visitor_logs/<int:pk>/', visitor_log_detail, name='visitor_log_detail'),
    path('visitor_logs/add/', add_visitor_log, name='add_visitor_log'),
    # URLs para CustomUser
    path('users/', user_list, name='user_list'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', update_user, name='update_user'),
    # URLs para Profile
    path('profile/', profile_detail, name='profile_detail'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    # urls para cadastro de usuários
    path('register/', register, name='register'),
    # Certifique-se de ter uma URL para a página inicial ou de destino após o registro
    path('home/', home, name='home'),
    # urls autenticação e login 
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('update-user/<int:pk>/', update_user, name='update_user'),
    path('log_ip/', log_ip, name='log_ip'),
]
