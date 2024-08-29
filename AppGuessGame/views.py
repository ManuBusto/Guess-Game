from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from datetime import date
from .forms import VisitorLogForm, CustomUserForm, ProfileForm, UserRegistrationForm, ContatoForm
import json
from .models import PontuacaoTime, SomaPontosTimeCampeonato, PontuacaoTime, Proximos_jogos, ResultadoJogo, Jogos, Aposta, VisitorLog, Profile



# views de retorno do resiter ou alterar para views desejada alterando o caminho no 
def home(request):
    return render(request, 'home.html')

def politicaPrivacidade(request):
    return render(request, 'politicaPrivacidade.html')

def sobreNos(request):
    return render(request, 'sobreNos.html')

def readme(request):
    return render(request, 'readme.html')




def proximos_jogos_graficos(request, jogo_id):
    jogo = get_object_or_404(Proximos_jogos, game_id=jogo_id)
    
    #contexto para o gráfico 
    context = {
        'jogo': jogo,
        'time_casa': jogo.time_casa,
        'time_visitante': jogo.time_visitante,
        'data': jogo.data,
        'hora': jogo.hora,
        'casasApostasOdds_time_casa': jogo.casasApostasOdds_time_casa,
        'casasApostasOdds_empate': jogo.casasApostasOdds_empate,
        'casasApostasOdds_time_visitante': jogo.casasApostasOdds_time_visitante,
    }

    try:
        # Consultar informações de pontuação média ponderada para os times selecionados
        pontuacao_media_time1 = PontuacaoTime.objects.filter(time=jogo.time_casa, campeonato=jogo.campeonato).first()
        pontuacao_media_time2 = PontuacaoTime.objects.filter(time=jogo.time_visitante, campeonato=jogo.campeonato).first()
        # Verificar se os objetos não são None antes de acessar o atributo
        pontuacao_time1 = pontuacao_media_time1.pontuacao_media_ponderada if pontuacao_media_time1 else 0
        pontuacao_time2 = pontuacao_media_time2.pontuacao_media_ponderada if pontuacao_media_time2 else 0
       
        time1 = SomaPontosTimeCampeonato.objects.get(time=jogo.time_casa, campeonato=jogo.campeonato)
        time2 = SomaPontosTimeCampeonato.objects.get(time=jogo.time_visitante, campeonato=jogo.campeonato)
        total_jogos_time1 = time1.soma_qtde_jogos
        total_jogos_time2 = time2.soma_qtde_jogos        
        total_pontos_time1 = time1.soma_pontos
        total_pontos_time2 = time2.soma_pontos
        total_zebra_time1 = time1.soma_zebra
        total_zebra_time2 = time2.soma_zebra
        total_favorito_derrota_time1 = time1.soma_favorito_derrota
        total_favorito_derrota_time2 = time2.soma_favorito_derrota
        total_favorito_empate_time1 = time1.soma_favorito_empate
        total_favorito_empate_time2 = time2.soma_favorito_empate
        
        # Obter todos os times ordenados por pontos
        all_teams = SomaPontosTimeCampeonato.objects.filter(campeonato=jogo.campeonato).order_by('-soma_pontos')

        # Inicializar colocações como None
        colocacao_time1 = None
        colocacao_time2 = None

        # Iterar sobre os times e encontrar a colocação
        for idx, team in enumerate(all_teams, start=1):
            if team.time == time1.time:
                colocacao_time1 = idx
            if team.time == time2.time:
                colocacao_time2 = idx

        # Calcular porcentagens de acertos GuessGameOdds
        time1_guessGameOdds_porcentagem = (time1.soma_guessGameOdds_acertos / total_jogos_time1) * 100
        time2_guessGameOdds_porcentagem = (time2.soma_guessGameOdds_acertos / total_jogos_time2) * 100
        # Calcular porcentagens de acertos Casas de Apostas
        time1_casasApostasOdds_porcentagem = (time1.soma_casasApostasOdds_acertos / total_jogos_time1) * 100
        time2_casasApostasOdds_porcentagem = (time2.soma_casasApostasOdds_acertos / total_jogos_time2) * 100
        # Dados para os gráficos de rosca
        time1_rosca_data = [time1_guessGameOdds_porcentagem, time1_casasApostasOdds_porcentagem]
        time2_rosca_data = [time2_guessGameOdds_porcentagem, time2_casasApostasOdds_porcentagem]
        
        # Dados para o gráfico de barras - Desempenho Jogos
        time1_vitorias_data = [time1.soma_vitorias, time1.soma_vitorias_casa, time1.soma_vitorias_fora]
        time2_vitorias_data = [time2.soma_vitorias, time2.soma_vitorias_casa, time2.soma_vitorias_fora]
        
        time1_empates_data = [time1.soma_empates, time1.soma_empates_casa, time1.soma_empates_fora]
        time2_empates_data = [time2.soma_empates, time2.soma_empates_casa, time2.soma_empates_fora]
        
        time1_derrotas_data = [time1.soma_derrotas, time1.soma_derrotas_casa, time1.soma_derrotas_fora]
        time2_derrotas_data = [time2.soma_derrotas, time2.soma_derrotas_casa, time2.soma_derrotas_fora]
        
        # Dados para o gráfico de barras - Desempenho em gols
        time1_bar_data2 = [time1.soma_gols_marcados, time1.soma_gols_contra, time1.soma_gols_saldo]
        time2_bar_data2 = [time2.soma_gols_marcados, time2.soma_gols_contra, time2.soma_gols_saldo]

        context.update({
            'time1_name': time1.time,
            'time2_name': time2.time,
            'total_jogos_time1': total_jogos_time1,
            'total_jogos_time2': total_jogos_time2,
            'total_pontos_time1': total_pontos_time1,
            'total_pontos_time2': total_pontos_time2,
            'time1_rosca_data': time1_rosca_data,
            'time2_rosca_data': time2_rosca_data,
            'total_favorito_derrota_time1': total_favorito_derrota_time1,
            'total_favorito_derrota_time2': total_favorito_derrota_time2,
            'total_favorito_empate_time1': total_favorito_empate_time1,
            'total_favorito_empate_time2': total_favorito_empate_time2,
            'total_zebra_time1': total_zebra_time1,
            'total_zebra_time2': total_zebra_time2,
            'time1_vitorias_data': time1_vitorias_data,
            'time2_vitorias_data': time2_vitorias_data,
            'time1_empates_data': time1_empates_data,
            'time2_empates_data': time2_empates_data,
            'time1_derrotas_data': time1_derrotas_data,
            'time2_derrotas_data': time2_derrotas_data,
            'time1_bar_data2': time1_bar_data2,
            'time2_bar_data2': time2_bar_data2,
            'pontuacao_time1': pontuacao_time1,
            'pontuacao_time2': pontuacao_time2,
            'colocacao_time1': colocacao_time1,
            'colocacao_time2': colocacao_time2,
        })

        # Busca as últimas 7 apostas de vitória, empate ou derrota para o time casa e visitante
        ultimas_7_apostas_time_casa = Aposta.objects.filter(
            Q(time=jogo.time_casa, vitorias__gt=0) | Q(time=jogo.time_casa, empates__gt=0) | Q(time=jogo.time_casa, derrotas__gt=0)
        ).order_by('-data')[:7]

        ultimas_7_apostas_time_visitante = Aposta.objects.filter(
            Q(time=jogo.time_visitante, vitorias__gt=0) | Q(time=jogo.time_visitante, empates__gt=0) | Q(time=jogo.time_visitante, derrotas__gt=0)
        ).order_by('-data')[:7]

        context['ultimas_7_apostas_time_casa'] = ultimas_7_apostas_time_casa
        context['ultimas_7_apostas_time_visitante'] = ultimas_7_apostas_time_visitante
        
        # Busca o jogo anterior em que o time 1 jogou em casa ou fora
        jogo_anterior_time1 = Jogos.objects.filter(Q(time_casa=jogo.time_casa) | Q(time_visitante=jogo.time_casa), data__lt=jogo.data).order_by('-data').first()

        # Busca os resultados do jogo anterior do time 1 (se houver)
        resultado_jogo_anterior_time1 = None
        if jogo_anterior_time1:
            resultado_jogo_anterior_time1 = ResultadoJogo.objects.filter(jogo=jogo_anterior_time1).first()

        context['jogo_anterior_time1'] = jogo_anterior_time1
        context['resultado_jogo_anterior_time1'] = resultado_jogo_anterior_time1

        # Busca o jogo anterior em que o time 2 jogou em casa ou fora
        jogo_anterior_time2 = Jogos.objects.filter(Q(time_casa=jogo.time_visitante) | Q(time_visitante=jogo.time_visitante), data__lt=jogo.data).order_by('-data').first()

        # Busca os resultados do jogo anterior do time 2 (se houver)
        resultado_jogo_anterior_time2 = None
        if jogo_anterior_time2:
            resultado_jogo_anterior_time2 = ResultadoJogo.objects.filter(jogo=jogo_anterior_time2).first()

        context['jogo_anterior_time2'] = jogo_anterior_time2
        context['resultado_jogo_anterior_time2'] = resultado_jogo_anterior_time2     
        
        # Busca o próximo jogo em que o time 1 jogará em casa ou fora
        proximo_jogo_time1 = Proximos_jogos.objects.filter(Q(time_casa=jogo.time_casa) | Q(time_visitante=jogo.time_casa), data__gt=jogo.data).order_by('data').first()

        # Define o resultado do próximo jogo do time 1 como None
        resultado_proximo_jogo_time1 = None

        context['proximo_jogo_time1'] = proximo_jogo_time1
        context['resultado_proximo_jogo_time1'] = resultado_proximo_jogo_time1

        # Busca o próximo jogo em que o time 2 jogará em casa ou fora
        proximo_jogo_time2 = Proximos_jogos.objects.filter(Q(time_casa=jogo.time_visitante) | Q(time_visitante=jogo.time_visitante), data__gt=jogo.data).order_by('data').first()

        # Define o resultado do próximo jogo do time 2 como None
        resultado_proximo_jogo_time2 = None

        context['proximo_jogo_time2'] = proximo_jogo_time2
        context['resultado_proximo_jogo_time2'] = resultado_proximo_jogo_time2

        # Busca os times com melhor ataque/defesa e pior ataque/defesa
        times = SomaPontosTimeCampeonato.objects.filter(campeonato=jogo.campeonato)
        if times.exists():
            melhor_ataque = times.order_by('-soma_gols_marcados').first()
            pior_ataque = times.order_by('soma_gols_marcados').first()
            melhor_defesa = times.order_by('soma_gols_contra').first()
            pior_defesa = times.order_by('-soma_gols_contra').first()
            
            context.update({
                'melhor_ataque': melhor_ataque.time if melhor_ataque else 'Nenhum',
                'melhor_ataque_gols': melhor_ataque.soma_gols_marcados if melhor_ataque else 0,
                'pior_ataque': pior_ataque.time if pior_ataque else 'Nenhum',
                'pior_ataque_gols': pior_ataque.soma_gols_marcados if pior_ataque else 0,
                'melhor_defesa': melhor_defesa.time if melhor_defesa else 'Nenhum',
                'melhor_defesa_gols': melhor_defesa.soma_gols_contra if melhor_defesa else 0,
                'pior_defesa': pior_defesa.time if pior_defesa else 'Nenhum',
                'pior_defesa_gols': pior_defesa.soma_gols_contra if pior_defesa else 0,
            })
        else:
            context.update({
                'melhor_ataque': 'Nenhum',
                'melhor_ataque_gols': 0,
                'pior_ataque': 'Nenhum',
                'pior_ataque_gols': 0,
                'melhor_defesa': 'Nenhum',
                'melhor_defesa_gols': 0,
                'pior_defesa': 'Nenhum',
                'pior_defesa_gols': 0,
            })
                    
    except SomaPontosTimeCampeonato.DoesNotExist:
        context['error'] = "Times não encontrados no campeonato selecionado."

    return render(request, 'proximos_jogos_graficos.html', context)
    


def proximos_jogos_lista(request):
    # Obtendo a lista de campeonatos distintos e ordenando alfabeticamente
    campeonatos = Proximos_jogos.objects.values_list('campeonato', flat=True).distinct().order_by('campeonato')
    selected_campeonato = request.GET.get('campeonato', '')
    context = {
        'campeonatos': campeonatos,
        'selected_campeonato': selected_campeonato,
    }

    if selected_campeonato:
        jogos = Proximos_jogos.objects.filter(campeonato__icontains=selected_campeonato)
    else:
        jogos = Proximos_jogos.objects.all()
    
    context['jogos'] = jogos
    
    return render(request, 'proximos_jogos_lista.html', context)



def guess_game_times(request):
    
    campeonatos = SomaPontosTimeCampeonato.objects.values_list('campeonato', flat=True).distinct().order_by('campeonato')
    
    selected_campeonato1 = request.GET.get('campeonato1')
    selected_campeonato2 = request.GET.get('campeonato2')
    selected_times1 = request.GET.getlist('times1')
    selected_times2 = request.GET.getlist('times2')

    context = {
        'campeonatos': campeonatos,
        'selected_campeonato1': selected_campeonato1,
        'selected_campeonato2': selected_campeonato2,
        'selected_times1': selected_times1,
        'selected_times2': selected_times2,
    }

    if selected_campeonato1:
        times1 = SomaPontosTimeCampeonato.objects.filter(campeonato=selected_campeonato1).order_by('time')
        context['times1'] = times1

    if selected_campeonato2:
        times2 = SomaPontosTimeCampeonato.objects.filter(campeonato=selected_campeonato2).order_by('time')
        context['times2'] = times2

    # Verificar se ambos os campeonatos e times foram selecionados
    if selected_campeonato1 and selected_campeonato2 and selected_times1 and selected_times2:
        try:
            # Obter os dados dos dois times selecionados
            time1 = SomaPontosTimeCampeonato.objects.get(time=selected_times1[0], campeonato=selected_campeonato1)
            time2 = SomaPontosTimeCampeonato.objects.get(time=selected_times2[0], campeonato=selected_campeonato2)

            # Obter as pontuações médias ponderadas dos times selecionados
            pontuacao_time1 = PontuacaoTime.objects.get(campeonato=selected_campeonato1, time=selected_times1[0])
            pontuacao_time2 = PontuacaoTime.objects.get(campeonato=selected_campeonato2, time=selected_times2[0])

            # Obter os dados dos dois times selecionados
            time1 = SomaPontosTimeCampeonato.objects.get(time=selected_times1[0], campeonato=selected_campeonato1)
            time2 = SomaPontosTimeCampeonato.objects.get(time=selected_times2[0], campeonato=selected_campeonato2)
            
            # Obter as pontuações médias ponderadas dos times selecionados
            pontuacao_time1 = PontuacaoTime.objects.get(campeonato=selected_campeonato1, time=selected_times1[0])
            pontuacao_time2 = PontuacaoTime.objects.get(campeonato=selected_campeonato2, time=selected_times2[0])
            total_jogos_time1 = time1.soma_qtde_jogos
            total_jogos_time2 = time2.soma_qtde_jogos        
            total_pontos_time1 = time1.soma_pontos
            total_pontos_time2 = time2.soma_pontos
            total_zebra_time1 = time1.soma_zebra
            total_zebra_time2 = time2.soma_zebra
            total_favorito_derrota_time1 = time1.soma_favorito_derrota
            total_favorito_derrota_time2 = time2.soma_favorito_derrota
            total_favorito_empate_time1 = time1.soma_favorito_empate
            total_favorito_empate_time2 = time2.soma_favorito_empate
            

            # Obter todos os times ordenados por pontos para determinar a colocação
            all_teams1 = SomaPontosTimeCampeonato.objects.filter(campeonato=selected_campeonato1).order_by('-soma_pontos')
            all_teams2 = SomaPontosTimeCampeonato.objects.filter(campeonato=selected_campeonato2).order_by('-soma_pontos')

            colocacao_time1 = None
            colocacao_time2 = None

            # Iterar sobre os times e encontrar a colocação
            for idx, team in enumerate(all_teams1, start=1):
                if team.time == selected_times1[0]:
                    colocacao_time1 = idx
                    break

            for idx, team in enumerate(all_teams2, start=1):
                if team.time == selected_times2[0]:
                    colocacao_time2 = idx
                    break
            
            # Calcular porcentagens de acertos GuessGameOdds
            time1_guessGameOdds_porcentagem = (time1.soma_guessGameOdds_acertos / time1.soma_qtde_jogos) * 100 if time1.soma_qtde_jogos != 0 else 0
            time2_guessGameOdds_porcentagem = (time2.soma_guessGameOdds_acertos / time2.soma_qtde_jogos) * 100 if time2.soma_qtde_jogos != 0 else 0

            # Calcular porcentagens de acertos Casas de Apostas
            time1_casasApostasOdds_porcentagem = (time1.soma_casasApostasOdds_acertos / time1.soma_qtde_jogos) * 100 if time1.soma_qtde_jogos != 0 else 0
            time2_casasApostasOdds_porcentagem = (time2.soma_casasApostasOdds_acertos / time2.soma_qtde_jogos) * 100 if time2.soma_qtde_jogos != 0 else 0

            # Dados para os gráficos de rosca
            time1_rosca_data = [time1_guessGameOdds_porcentagem, time1_casasApostasOdds_porcentagem]
            time2_rosca_data = [time2_guessGameOdds_porcentagem, time2_casasApostasOdds_porcentagem]

            # Dados para o gráfico de barras - Desempenho Jogos
            time1_vitorias_data = [time1.soma_vitorias, time1.soma_vitorias_casa, time1.soma_vitorias_fora]
            time2_vitorias_data = [time2.soma_vitorias, time2.soma_vitorias_casa, time2.soma_vitorias_fora]

            time1_empates_data = [time1.soma_empates, time1.soma_empates_casa, time1.soma_empates_fora]
            time2_empates_data = [time2.soma_empates, time2.soma_empates_casa, time2.soma_empates_fora]

            time1_derrotas_data = [time1.soma_derrotas, time1.soma_derrotas_casa, time1.soma_derrotas_fora]
            time2_derrotas_data = [time2.soma_derrotas, time2.soma_derrotas_casa, time2.soma_derrotas_fora]

            # Dados para o gráfico de barras - Desempenho em gols
            time1_bar_data2 = [time1.soma_gols_marcados, time1.soma_gols_contra, time1.soma_gols_saldo]
            time2_bar_data2 = [time2.soma_gols_marcados, time2.soma_gols_contra, time2.soma_gols_saldo]

            context.update({
                'time1_name': time1.time,
                'time2_name': time2.time,
                'colocacao_time1': colocacao_time1,
                'colocacao_time2': colocacao_time2,
                'time1_rosca_data': time1_rosca_data,
                'time2_rosca_data': time2_rosca_data,
                'time1_vitorias_data': time1_vitorias_data,
                'time2_vitorias_data': time2_vitorias_data,
                'time1_empates_data': time1_empates_data,
                'time2_empates_data': time2_empates_data,
                'time1_derrotas_data': time1_derrotas_data,
                'time2_derrotas_data': time2_derrotas_data,
                'time1_bar_data2': time1_bar_data2,
                'time2_bar_data2': time2_bar_data2,
                'pontuacao_media_time1': pontuacao_time1.pontuacao_media_ponderada,
                'pontuacao_media_time2': pontuacao_time2.pontuacao_media_ponderada,
                'total_jogos_time1': total_jogos_time1,
                'total_jogos_time2': total_jogos_time2,
                'total_pontos_time1': total_pontos_time1,
                'total_pontos_time2': total_pontos_time2,
                'total_favorito_derrota_time1': total_favorito_derrota_time1,
                'total_favorito_derrota_time2': total_favorito_derrota_time2,
                'total_favorito_empate_time1': total_favorito_empate_time1,
                'total_favorito_empate_time2': total_favorito_empate_time2,
                'total_zebra_time1': total_zebra_time1,
                'total_zebra_time2': total_zebra_time2,
            })

            # Busca as últimas 7 apostas de vitória, empate ou derrota para o time casa e visitante
            ultimas_7_apostas_time_casa = Aposta.objects.filter(
                Q(time=time1.time, vitorias__gt=0) | Q(time=time1.time, empates__gt=0) | Q(time=time1.time, derrotas__gt=0)
            ).order_by('-data')[:7]

            ultimas_7_apostas_time_visitante = Aposta.objects.filter(
                Q(time=time2.time, vitorias__gt=0) | Q(time=time2.time, empates__gt=0) | Q(time=time2.time, derrotas__gt=0)
            ).order_by('-data')[:7]

            context['ultimas_7_apostas_time_casa'] = ultimas_7_apostas_time_casa
            context['ultimas_7_apostas_time_visitante'] = ultimas_7_apostas_time_visitante

            # Busca o jogo anterior em que o time 1 jogou em casa ou fora
            jogo_anterior_time1 = Jogos.objects.filter(Q(time_casa=time1.time) | Q(time_visitante=time1.time), data__lt=date.today()).order_by('-data').first()

            # Busca os resultados do jogo anterior do time 1 (se houver)
            resultado_jogo_anterior_time1 = None
            if jogo_anterior_time1:
                resultado_jogo_anterior_time1 = ResultadoJogo.objects.filter(jogo=jogo_anterior_time1).first()

            context['jogo_anterior_time1'] = jogo_anterior_time1
            context['resultado_jogo_anterior_time1'] = resultado_jogo_anterior_time1

            # Busca o jogo anterior em que o time 2 jogou em casa ou fora
            jogo_anterior_time2 = Jogos.objects.filter(Q(time_casa=time2.time) | Q(time_visitante=time2.time), data__lt=date.today()).order_by('-data').first()

            # Busca os resultados do jogo anterior do time 2 (se houver)
            resultado_jogo_anterior_time2 = None
            if jogo_anterior_time2:
                resultado_jogo_anterior_time2 = ResultadoJogo.objects.filter(jogo=jogo_anterior_time2).first()

            context['jogo_anterior_time2'] = jogo_anterior_time2
            context['resultado_jogo_anterior_time2'] = resultado_jogo_anterior_time2     

            # Busca o próximo jogo em que o time 1 jogará em casa ou fora
            proximo_jogo_time1 = Proximos_jogos.objects.filter(Q(time_casa=time1.time) | Q(time_visitante=time1.time), data__gt=date.today()).order_by('data').first()

            # Define o próximo jogo do time 1 e verifica se o time é visitante ou casa
            if proximo_jogo_time1:
                context['proximo_jogo_time1'] = proximo_jogo_time1
                if proximo_jogo_time1.time_casa == time1.time:
                    context['time1_proximo_jogo_local'] = 'Casa'
                else:
                    context['time1_proximo_jogo_local'] = 'Fora'
            else:
                context['proximo_jogo_time1'] = None
                context['time1_proximo_jogo_local'] = None

            # Busca o próximo jogo em que o time 2 jogará em casa ou fora
            proximo_jogo_time2 = Proximos_jogos.objects.filter(Q(time_casa=time2.time) | Q(time_visitante=time2.time), data__gt=date.today()).order_by('data').first()

            # Define o próximo jogo do time 2 e verifica se o time é visitante ou casa
            if proximo_jogo_time2:
                context['proximo_jogo_time2'] = proximo_jogo_time2
                if proximo_jogo_time2.time_casa == time2.time:
                    context['time2_proximo_jogo_local'] = 'Casa'
                else:
                    context['time2_proximo_jogo_local'] = 'Fora'
            else:
                context['proximo_jogo_time2'] = None
                context['time2_proximo_jogo_local'] = None

            # Busca os melhores ataques e defesas do campeonato
            times = SomaPontosTimeCampeonato.objects.filter(campeonato__in=[selected_campeonato1, selected_campeonato2]).order_by('-soma_pontos')

            if times.exists():
                melhor_ataque = times.order_by('-soma_gols_marcados').first()
                pior_ataque = times.order_by('soma_gols_marcados').first()
                melhor_defesa = times.order_by('soma_gols_contra').first()
                pior_defesa = times.order_by('-soma_gols_contra').first()
                
                context.update({
                    'melhor_ataque': melhor_ataque.time if melhor_ataque else 'Nenhum',
                    'melhor_ataque_gols': melhor_ataque.soma_gols_marcados if melhor_ataque else 0,
                    'pior_ataque': pior_ataque.time if pior_ataque else 'Nenhum',
                    'pior_ataque_gols': pior_ataque.soma_gols_marcados if pior_ataque else 0,
                    'melhor_defesa': melhor_defesa.time if melhor_defesa else 'Nenhum',
                    'melhor_defesa_gols': melhor_defesa.soma_gols_contra if melhor_defesa else 0,
                    'pior_defesa': pior_defesa.time if pior_defesa else 'Nenhum',
                    'pior_defesa_gols': pior_defesa.soma_gols_contra if pior_defesa else 0,
                })
            else:
                context.update({
                    'melhor_ataque': 'Nenhum',
                    'melhor_ataque_gols': 0,
                    'pior_ataque': 'Nenhum',
                    'pior_ataque_gols': 0,
                    'melhor_defesa': 'Nenhum',
                    'melhor_defesa_gols': 0,
                    'pior_defesa': 'Nenhum',
                    'pior_defesa_gols': 0,
                })
        except SomaPontosTimeCampeonato.DoesNotExist:
            context['error'] = "Times não encontrados no campeonato selecionado."

    return render(request, 'guess_game_times.html', context)



def contato(request):
    if request.method == 'POST':
        form = ContatoForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome']
            email = form.cleaned_data['email']
            assunto = form.cleaned_data['assunto']
            mensagem = form.cleaned_data['mensagem']
            
            # Enviar e-mail
            send_mail(
                assunto,
                mensagem,
                email,
                ['seu-email@exemplo.com'],  # Substitua pelo e-mail de destino
                fail_silently=False,
            )
            
            # Redirecionar para a página de sucesso
            return redirect('contato_sucesso')
    else:
        form = ContatoForm()
    
    return render(request, 'contato.html', {'form': form})

# Renderiza a página de sucesso após o envio do formulário de contato.
def contato_sucesso(request):
    return render(request, 'contato_sucesso.html')



# Função que lida com aceitação de cookies
def accept_cookies(request):
    response = redirect(request.META.get('HTTP_REFERER', '/'))
    if request.user.is_authenticated:
        request.user.cookies_accepted = True
        request.user.save()
    else:
        response.set_cookie('cookies_accepted', 'true', max_age=365*24*60*60)  # 1 ano
    return response

# Esta função renderiza a página que detalha a política de cookies, os usuários obtem mais informações sobre como os cookies
#  são usados no site.
def cookie_policy(request):
    return render(request, 'cookie_policy.html')



# log_ip: Registra o IP do visitante, geralmente usado para monitoramento ou análise.
def log_ip(request):
    if request.method == 'POST':
        ip_address = request.META.get('REMOTE_ADDR')
        # Aqui você pode adicionar código para registrar o IP ou qualquer outra lógica necessária
        return JsonResponse({'message': 'IP logged', 'ip': ip_address})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)



# Visitor_log_list e visitor_log_detail: Lidam com a exibição de logs de visitantes.
@login_required # Garante que apenas usuários autenticados possam acessar
def visitor_log_list(request):
    logs = VisitorLog.objects.all().order_by('-timestamp')
    return render(request, 'visitor_log_list.html', {'logs': logs})

def visitor_log_detail(request, pk):
    log = get_object_or_404(VisitorLog, pk=pk)
    return render(request, 'visitor_log_detail.html', {'log': log})

def add_visitor_log(request):
    if request.method == 'POST':
        form = VisitorLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('visitor_log_list')
    else:
        form = VisitorLogForm()
    return render(request, 'add_visitor_log.html', {'form': form})



# user_list, user_detail, update_user: Gerenciam a visualização e atualização de informações do usuário.
User = get_user_model()
@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'user_detail.html', {'user': user})

@login_required
def update_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_detail', pk=user.pk)
    else:
        form = CustomUserForm(instance=user)
    return render(request, 'update_user.html', {'form': form})



# profile_detail e edit_profile: Lidam com a visualização e edição do perfil do usuário.
@login_required
def profile_detail(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'profile_detail.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})



# register: Gerencia o registro de novos usuários.
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Faz login automático após o registro
            return redirect('home')  # Redireciona para uma página inicial ou outra página
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})



# Permissões e Grupos: Se você precisa de um controle mais granular, use permissões e grupos para definir quem pode acessar certas
#  partes do site. Isso pode ser configurado usando o sistema de permissões do Django e grupos no painel de administração.
def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def add_visitor_log(request):
    if request.method == 'POST':
        form = VisitorLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('visitor_log_list')
    else:
        form = VisitorLogForm()
    return render(request, 'add_visitor_log.html', {'form': form})



