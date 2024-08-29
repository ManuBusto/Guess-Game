from .models import Jogos, ResultadoJogo, Aposta, Pesos, PontuacaoTime, PontuTimeProbaMarg, SomaPontosTimeCampeonato
from collections import defaultdict
from django.db.models import Count, Sum, F
from decimal import Decimal
from scipy.stats import norm
import logging
import sqlite3
import pandas as pd
from django.conf import settings

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def atualizar_apostas():
    jogos = Jogos.objects.all()

    for jogo in jogos:
        # Verificar se já existem resultados registrados para o jogo atual
        resultado_jogo = ResultadoJogo.objects.filter(jogo=jogo).first()

        if resultado_jogo:
            # Função auxiliar para criar e salvar uma aposta
            def criar_aposta(jogo, time, gols_marcados, gols_contra, vitorias, empates, derrotas, pontos, casasApostasOdds_acertos, guessGameOdds_acertos, zebra, vitorias_casa, vitorias_fora, empates_casa, empates_fora, derrotas_casa, derrotas_fora, favorito_derrota, favorito_empate):
                aposta = Aposta()
                aposta.jogo = jogo
                aposta.data = jogo.data
                aposta.hora = jogo.hora
                aposta.campeonato = jogo.campeonato
                aposta.time = time
                aposta.qtde_jogos = 1  # Sempre define qtde_jogos como 1
                aposta.gols_marcados = gols_marcados
                aposta.gols_contra = gols_contra
                aposta.gols_saldo = gols_marcados - gols_contra
                aposta.vitorias = vitorias
                aposta.empates = empates
                aposta.derrotas = derrotas
                aposta.pontos = pontos
                aposta.casasApostasOdds_acertos = casasApostasOdds_acertos
                aposta.guessGameOdds_acertos = guessGameOdds_acertos
                aposta.zebra = zebra
                aposta.vitorias_casa = vitorias_casa
                aposta.vitorias_fora = vitorias_fora
                aposta.empates_casa = empates_casa
                aposta.empates_fora = empates_fora
                aposta.derrotas_casa = derrotas_casa
                aposta.derrotas_fora = derrotas_fora
                aposta.favorito_derrota = favorito_derrota
                aposta.favorito_empate = favorito_empate
                
                # Salvar a aposta
                aposta.save()
                          
            # Calcular se a casa de apostas acertou o palpite para o time da casa 
            casasApostasOdds_acertos_casa = 1 if (
                resultado_jogo.resultado_time_casa > resultado_jogo.resultado_time_visitante and jogo.casasApostasOdds_time_casa < jogo.casasApostasOdds_time_visitante
                ) or (
                    resultado_jogo.resultado_time_casa == resultado_jogo.resultado_time_visitante and jogo.casasApostasOdds_time_casa == jogo.casasApostasOdds_time_visitante
                    ) or (
                        resultado_jogo.resultado_time_casa < resultado_jogo.resultado_time_visitante and jogo.casasApostasOdds_time_casa > jogo.casasApostasOdds_time_visitante
            ) else 0
            # Calcular se a casa de apostas acertou o palpite para o time da visitante 
            casasApostasOdds_acertos_visitante = 1 if (
                resultado_jogo.resultado_time_visitante > resultado_jogo.resultado_time_casa and jogo.casasApostasOdds_time_visitante < jogo.casasApostasOdds_time_casa
                ) or (
                    resultado_jogo.resultado_time_visitante == resultado_jogo.resultado_time_casa and jogo.casasApostasOdds_time_visitante == jogo.casasApostasOdds_time_casa
                    ) or (
                        resultado_jogo.resultado_time_visitante < resultado_jogo.resultado_time_casa and jogo.casasApostasOdds_time_visitante > jogo.casasApostasOdds_time_casa
            ) else 0                    
                    
            # Calcular se a Guess-Game acertou o palpite para time da casa 
            guessGameOdds_acertos_casa = 1 if (
                resultado_jogo.resultado_time_casa > resultado_jogo.resultado_time_visitante and jogo.pontuacaoGuessGame_time_casa > jogo.pontuacaoGuessGame_time_visitante
                ) or (
                    resultado_jogo.resultado_time_casa == resultado_jogo.resultado_time_visitante and jogo.pontuacaoGuessGame_time_casa == jogo.pontuacaoGuessGame_time_visitante
                    ) or (
                        resultado_jogo.resultado_time_casa < resultado_jogo.resultado_time_visitante and jogo.pontuacaoGuessGame_time_casa < jogo.pontuacaoGuessGame_time_visitante
            ) else 0
            # Calcular se a Guess-Game acertou o palpite para time visitante 
            guessGameOdds_acertos_visitante = 1 if (
                resultado_jogo.resultado_time_visitante > resultado_jogo.resultado_time_casa and jogo.pontuacaoGuessGame_time_visitante > jogo.pontuacaoGuessGame_time_casa
                ) or (
                    resultado_jogo.resultado_time_visitante == resultado_jogo.resultado_time_casa and jogo.pontuacaoGuessGame_time_visitante == jogo.pontuacaoGuessGame_time_casa
                    ) or (
                        resultado_jogo.resultado_time_visitante < resultado_jogo.resultado_time_casa and jogo.pontuacaoGuessGame_time_visitante < jogo.pontuacaoGuessGame_time_casa
            ) else 0
                        
            # Calcular a zebra para o time da casa
            zebra_casa = int(resultado_jogo.resultado_time_casa > resultado_jogo.resultado_time_visitante and 
                            (jogo.casasApostasOdds_time_casa / jogo.casasApostasOdds_time_visitante) > 2)

            # Calcular a zebra para o time visitante
            zebra_visitante = int(resultado_jogo.resultado_time_visitante > resultado_jogo.resultado_time_casa and 
                                (jogo.casasApostasOdds_time_visitante / jogo.casasApostasOdds_time_casa) > 2)
            
            # Calcular a favorito_perdeu para o time da casa
            favorito_derrota_casa = int(resultado_jogo.resultado_time_casa < resultado_jogo.resultado_time_visitante and 
                            (jogo.casasApostasOdds_time_casa / jogo.casasApostasOdds_time_visitante) < 0.5)

            # Calcular a favorito_perdeu para o time visitante
            favorito_derrota_visitante = int(resultado_jogo.resultado_time_visitante < resultado_jogo.resultado_time_casa and 
                                (jogo.casasApostasOdds_time_visitante / jogo.casasApostasOdds_time_casa) < 0.5)
            
            # Calcular a favorito_empatou para o time da casa
            favorito_empate_casa = int(resultado_jogo.resultado_time_casa == resultado_jogo.resultado_time_visitante and 
                            (jogo.casasApostasOdds_time_casa / jogo.casasApostasOdds_time_visitante) < 0.5)

            # Calcular a favorito_empatou para o time visitante
            favorito_empate_visitante = int(resultado_jogo.resultado_time_visitante == resultado_jogo.resultado_time_casa and 
                                (jogo.casasApostasOdds_time_visitante / jogo.casasApostasOdds_time_casa) < 0.5)

            # Criar aposta para o time da casa
            # Abaixo, gols_marcados é resultado_jogo.resultado_time_casa e gols_contra é resultado_jogo.resultado_time_visitante.
            if resultado_jogo.resultado_time_casa > resultado_jogo.resultado_time_visitante:
                # Vitória do time da casa
                criar_aposta(jogo, jogo.time_casa, resultado_jogo.resultado_time_casa, resultado_jogo.resultado_time_visitante, 1, 0, 0, 3, casasApostasOdds_acertos_casa, guessGameOdds_acertos_casa, zebra_casa, 1, 0, 0, 0, 0, 0, favorito_derrota_casa, favorito_empate_casa)

            elif resultado_jogo.resultado_time_casa == resultado_jogo.resultado_time_visitante:
                # Empate
                criar_aposta(jogo, jogo.time_casa, resultado_jogo.resultado_time_casa, resultado_jogo.resultado_time_visitante, 0, 1, 0, 1, casasApostasOdds_acertos_casa, guessGameOdds_acertos_casa, zebra_casa, 0, 0, 1, 0, 0, 0, favorito_derrota_casa, favorito_empate_casa)
            else:
                # Derrota do time da casa
                criar_aposta(jogo, jogo.time_casa, resultado_jogo.resultado_time_casa, resultado_jogo.resultado_time_visitante, 0, 0, 1, 0, casasApostasOdds_acertos_casa,  guessGameOdds_acertos_casa, zebra_casa, 0, 0, 0, 0, 1, 0, favorito_derrota_casa, favorito_empate_casa)

            # Criar aposta para o time visitante
            # Abaixo, gols_marcados é resultado_jogo.resultado_time_visitante e gols_contra é resultado_jogo.resultado_time_casa.
            if resultado_jogo.resultado_time_visitante > resultado_jogo.resultado_time_casa:
                # Vitória do time visitante
                criar_aposta(jogo, jogo.time_visitante, resultado_jogo.resultado_time_visitante, resultado_jogo.resultado_time_casa, 1, 0, 0, 3, casasApostasOdds_acertos_visitante, guessGameOdds_acertos_visitante, zebra_visitante, 0, 1, 0, 0, 0, 0, favorito_derrota_visitante, favorito_empate_visitante)
            elif resultado_jogo.resultado_time_visitante == resultado_jogo.resultado_time_casa:
                # Empate
                criar_aposta(jogo, jogo.time_visitante, resultado_jogo.resultado_time_visitante, resultado_jogo.resultado_time_casa, 0, 1, 0, 1, casasApostasOdds_acertos_visitante, guessGameOdds_acertos_visitante, zebra_visitante, 0, 0, 0, 1, 0, 0, favorito_derrota_visitante, favorito_empate_visitante)
            else:
                # Derrota do time visitante
                criar_aposta(jogo, jogo.time_visitante, resultado_jogo.resultado_time_visitante, resultado_jogo.resultado_time_casa, 0, 0, 1, 0, casasApostasOdds_acertos_visitante, guessGameOdds_acertos_visitante, zebra_visitante, 0, 0, 0, 0, 0, 1, favorito_derrota_visitante, favorito_empate_visitante)
        



            
def atualizar_pesos():

    # Consulta para obter estatísticas gerais de cada time
    estatisticas_times = Aposta.objects.values('time', 'campeonato').annotate(
        total_jogos=Count('jogo_id'),
        total_pontos=Sum('pontos'), 
        total_gols_marcados=Sum('gols_marcados'),
        total_gols_contra=Sum('gols_contra'),
        total_gols_saldo=Sum('gols_saldo'), 
        total_vitorias=Sum('vitorias'),
        total_empates=Sum('empates'),
        total_derrotas=Sum('derrotas'),
    )

    for estatistica in estatisticas_times:
        print(estatistica)
        time = estatistica['time']
        campeonato = estatistica['campeonato']
        total_jogos = estatistica['total_jogos']
        total_pontos = estatistica['total_pontos'] 
        total_gols_marcados = estatistica['total_gols_marcados']
        total_gols_contra = estatistica['total_gols_contra']
        total_gols_saldo =  estatistica['total_gols_saldo']
        total_vitorias = estatistica['total_vitorias']
        total_empates = estatistica['total_empates']
        total_derrotas = estatistica['total_derrotas']
        
        # Tentar obter um registro existente com base no time e no campeonato
        try:
            pesos = Pesos.objects.get(time=time, campeonato=campeonato)
        except Pesos.DoesNotExist:
            # Se o registro não existir, criar um novo
            pesos = Pesos(time=time, campeonato=campeonato)
    
        # Atualizar as estatísticas de média de PONTOS com base nos dados da aposta
        if total_jogos > 0:
            media_pontos = total_pontos / total_jogos
            if media_pontos	> 2.16:
                pesos.pontos = 2.0
            elif media_pontos <= 2.16 and media_pontos > 2.07:
                pesos.pontos = 1.9
            elif media_pontos <= 2.07 and media_pontos > 1.96:
                pesos.pontos = 1.8
            elif media_pontos <= 1.96 and media_pontos > 1.86:
                pesos.pontos = 1.7
            elif media_pontos <= 1.86 and media_pontos > 1.78:
                pesos.pontos = 1.6
            elif media_pontos <= 1.78 and media_pontos > 1.70:
                pesos.pontos = 1.5
            elif media_pontos <= 1.70 and media_pontos > 1.62:
                pesos.pontos = 1.4
            elif media_pontos <= 1.62 and media_pontos > 1.54:
                pesos.pontos = 1.3
            elif media_pontos <= 1.54 and media_pontos > 1.46:
                pesos.pontos = 1.2
            elif media_pontos <= 1.46 and media_pontos > 1.38:
                pesos.pontos = 1.1
            elif media_pontos <= 1.38 and media_pontos > 1.31:
                pesos.pontos = 1.0
            elif media_pontos <= 1.31 and media_pontos > 1.23:
                pesos.pontos = 0.9
            elif media_pontos <= 1.23 and media_pontos > 1.15:
                pesos.pontos = 0.8
            elif media_pontos <= 1.15 and media_pontos > 1.07:
                pesos.pontos = 0.7
            elif media_pontos <= 1.07 and media_pontos > 0.99:
                pesos.pontos = 0.6
            elif media_pontos <= 0.99 and media_pontos > 0.91:
                pesos.pontos = 0.5
            elif media_pontos <= 0.91 and media_pontos > 0.83:
                pesos.pontos = 0.4
            elif media_pontos <= 0.83 and media_pontos > 0.75:
                pesos.pontos = 0.3
            elif media_pontos <= 0.75 and media_pontos > 0.65:
                pesos.pontos = 0.2
            elif media_pontos <= 0.65 and media_pontos > 0.54:
                pesos.pontos = 0.1
            else:		
                pesos.pontos = 0.0

        # Atualizar as estatísticas de média de GOLS MARCADOS com base nos dados da aposta      
        if total_jogos > 0:
            media_gols_marcados = total_gols_marcados / total_jogos    
            if media_gols_marcados	> 2.16:
                pesos.gols_marcados = 2.0
            elif media_gols_marcados <= 2.16 and media_gols_marcados > 2.07:
                pesos.gols_marcados = 1.9
            elif media_gols_marcados <= 2.07 and media_gols_marcados > 1.96:
                pesos.gols_marcados = 1.8
            elif media_gols_marcados <= 1.96 and media_gols_marcados > 1.86:
                pesos.gols_marcados = 1.7
            elif media_gols_marcados <= 1.86 and media_gols_marcados > 1.78:
                pesos.gols_marcados = 1.6
            elif media_gols_marcados <= 1.78 and media_gols_marcados > 1.70:
                pesos.gols_marcados = 1.5
            elif media_gols_marcados <= 1.70 and media_gols_marcados > 1.62:
                pesos.gols_marcados = 1.4
            elif media_gols_marcados <= 1.62 and media_gols_marcados > 1.54:
                pesos.gols_marcados = 1.3
            elif media_gols_marcados <= 1.54 and media_gols_marcados > 1.46:
                pesos.gols_marcados = 1.2
            elif media_gols_marcados <= 1.46 and media_gols_marcados > 1.38:
                pesos.gols_marcados = 1.1
            elif media_gols_marcados <= 1.38 and media_gols_marcados > 1.31:
                pesos.gols_marcados = 1.0
            elif media_gols_marcados <= 1.31 and media_gols_marcados > 1.23:
                pesos.gols_marcados = 0.9
            elif media_gols_marcados <= 1.23 and media_gols_marcados > 1.15:
                pesos.gols_marcados = 0.8
            elif media_gols_marcados <= 1.15 and media_gols_marcados > 1.07:
                pesos.gols_marcados = 0.7
            elif media_gols_marcados <= 1.07 and media_gols_marcados > 0.99:
                pesos.gols_marcados = 0.6
            elif media_gols_marcados <= 0.99 and media_gols_marcados > 0.91:
                pesos.gols_marcados = 0.5
            elif media_gols_marcados <= 0.91 and media_gols_marcados > 0.83:
                pesos.gols_marcados = 0.4
            elif media_gols_marcados <= 0.83 and media_gols_marcados > 0.75:
                pesos.gols_marcados = 0.3
            elif media_gols_marcados <= 0.75 and media_gols_marcados > 0.65:
                pesos.gols_marcados = 0.2
            elif media_gols_marcados <= 0.65 and media_gols_marcados > 0.54:
                pesos.gols_marcados = 0.1
            else:		
                pesos.gols_marcados = 0.0

        # Atualizar as estatísticas de média de GOLS CONTRA com base nos dados da aposta      
        if total_jogos > 0:
            media_gols_contra=total_gols_contra/total_jogos
            if media_gols_contra < 0.66:
                pesos.gols_contra = 2.0
            elif media_gols_contra >= 0.66 and media_gols_contra < 0.74:
                pesos.gols_contra = 1.9
            elif media_gols_contra >= 0.74 and media_gols_contra < 0.82:
                pesos.gols_contra = 1.8
            elif media_gols_contra >= 0.82 and media_gols_contra < 0.89:
                pesos.gols_contra = 1.7
            elif media_gols_contra >= 0.89 and media_gols_contra < 0.97:
                pesos.gols_contra = 1.6
            elif media_gols_contra >= 0.97 and media_gols_contra < 1.05:
                pesos.gols_contra = 1.5						
            elif media_gols_contra >= 1.05 and media_gols_contra < 1.13:
                pesos.gols_contra = 1.4
            elif media_gols_contra >= 1.13 and media_gols_contra < 1.21:
                pesos.gols_contra = 1.3
            elif media_gols_contra >= 1.21 and media_gols_contra < 1.29:
                pesos.gols_contra = 1.2
            elif media_gols_contra >= 1.29 and media_gols_contra < 1.37:
                pesos.gols_contra = 1.1
            elif media_gols_contra >= 1.37 and media_gols_contra < 1.45:
                pesos.gols_contra = 1.0
            elif media_gols_contra >= 1.45 and media_gols_contra < 1.53:
                pesos.gols_contra = 0.9
            elif media_gols_contra >= 1.53 and media_gols_contra < 1.61:
                pesos.gols_contra = 0.8
            elif media_gols_contra >= 1.61 and media_gols_contra < 1.68:
                pesos.gols_contra = 0.7
            elif media_gols_contra >= 1.68 and media_gols_contra < 1.76:
                pesos.gols_contra = 0.6
            elif media_gols_contra >= 1.76 and media_gols_contra < 1.84:
                pesos.gols_contra = 0.5
            elif media_gols_contra >= 1.84 and media_gols_contra < 1.92:
                pesos.gols_contra = 0.4
            elif media_gols_contra >= 1.92 and media_gols_contra < 2.00:
                pesos.gols_contra = 0.3
            elif media_gols_contra >= 2.00 and media_gols_contra < 2.08:
                pesos.gols_contra = 0.2
            elif media_gols_contra >= 2.08 and media_gols_contra < 2.16:
                pesos.gols_contra = 0.1
            else:
                pesos.gols_contra = 0.0

        # Atualizar as estatísticas de média de GOLS SALDO com base nos dados da aposta      
        if total_jogos > 0:
            media_gols_saldo = total_gols_saldo / total_jogos                    
            if media_gols_saldo > 1.95:
                pesos.gols_saldo = 2.0						
            elif media_gols_saldo <= 1.95 and media_gols_saldo > 1.79:
                pesos.gols_saldo = 1.9						
            elif media_gols_saldo <= 1.79 and media_gols_saldo > 1.63:
                pesos.gols_saldo = 1.8						
            elif media_gols_saldo <= 1.63 and media_gols_saldo > 1.47:
                pesos.gols_saldo = 1.7						
            elif media_gols_saldo <= 1.47 and media_gols_saldo > 1.32:
                pesos.gols_saldo = 1.6						
            elif media_gols_saldo <= 1.32 and media_gols_saldo > 1.16:
                pesos.gols_saldo = 1.5						
            elif media_gols_saldo <= 1.16 and media_gols_saldo > 1.00 :
                pesos.gols_saldo = 1.4						
            elif media_gols_saldo <= 1.00 and media_gols_saldo > 0.84:
                pesos.gols_saldo = 1.3						
            elif media_gols_saldo <= 0.84 and media_gols_saldo > 0.68:
                pesos.gols_saldo = 1.2						
            elif media_gols_saldo <= 0.68 and media_gols_saldo > 0.53:
                pesos.gols_saldo = 1.1						
            elif media_gols_saldo <= 0.53 and media_gols_saldo > 0.37:
                pesos.gols_saldo = 1.0						
            elif media_gols_saldo <= 0.37 and media_gols_saldo > 0.21:
                pesos.gols_saldo = 0.9						
            elif media_gols_saldo <= 0.21 and media_gols_saldo > 0.05:
                pesos.gols_saldo = 0.8						
            elif media_gols_saldo <= 0.05 and media_gols_saldo > -0.11:
                pesos.gols_saldo = 0.7						
            elif media_gols_saldo <= -0.11 and media_gols_saldo > -0.26:
                pesos.gols_saldo = 0.6						
            elif media_gols_saldo <= -0.26 and media_gols_saldo > -0.42:
                pesos.gols_saldo = 0.5						
            elif media_gols_saldo <= -0.42 and media_gols_saldo > -0.58:
                pesos.gols_saldo = 0.4						
            elif media_gols_saldo <= -0.58 and media_gols_saldo > -0.74:
                pesos.gols_saldo = 0.3						
            elif media_gols_saldo <= -0.74 and media_gols_saldo > -0.89:
                pesos.gols_saldo = 0.2						
            elif media_gols_saldo <= -0.89 and media_gols_saldo > -1.05:
                pesos.gols_saldo = 0.1
            else:	
                pesos.gols_saldo = 0.0

        # Atualizar as estatísticas de média de VITORIAS com base nos dados da aposta
        if total_jogos > 0:
            media_vitorias = total_vitorias / total_jogos						         
            if media_vitorias > 0.66:
                pesos.vitorias = 2.0
            elif media_vitorias	<=	0.66 and media_vitorias	> 0.63:
                pesos.vitorias = 1.9						
            elif media_vitorias	<=	0.63 and media_vitorias	> 0.61:
                pesos.vitorias = 1.8						
            elif media_vitorias	<=	0.61 and media_vitorias	> 0.58:
                pesos.vitorias = 1.7						
            elif media_vitorias	<=	0.58 and media_vitorias	> 0.55:
                pesos.vitorias = 1.6						
            elif media_vitorias	<=	0.55 and media_vitorias	> 0.53:
                pesos.vitorias = 1.5						
            elif media_vitorias	<=	0.53 and media_vitorias	> 0.50:
                pesos.vitorias = 1.4						
            elif media_vitorias	<=	0.50 and media_vitorias	> 0.47:
                pesos.vitorias = 1.3						
            elif media_vitorias	<=	0.47 and media_vitorias	> 0.45:
                pesos.vitorias = 1.2						
            elif media_vitorias	<=	0.45 and media_vitorias	> 0.42:
                pesos.vitorias = 1.1						
            elif media_vitorias	<=	0.42 and media_vitorias	> 0.39:
                pesos.vitorias = 1.0						
            elif media_vitorias	<=	0.39 and media_vitorias	> 0.37:
                pesos.vitorias = 0.9						
            elif media_vitorias	<=	0.37 and media_vitorias	> 0.34:
                pesos.vitorias = 0.8						
            elif media_vitorias	<= 0.34	and media_vitorias	> 0.32:
                pesos.vitorias = 0.7						
            elif media_vitorias	<=	0.32 and media_vitorias	> 0.29:
                pesos.vitorias = 0.6						
            elif media_vitorias	<=	0.29 and media_vitorias	> 0.26:
                pesos.vitorias = 0.5						
            elif media_vitorias	<=	0.26 and media_vitorias	> 0.24:
                pesos.vitorias = 0.4						
            elif media_vitorias	<=	0.24 and media_vitorias	> 0.21:
                pesos.vitorias = 0.3						
            elif media_vitorias	<=	0.21 and media_vitorias	> 0.18:
                pesos.vitorias = 0.2						
            elif media_vitorias	<=	0.18 and media_vitorias	> 0.16:
                pesos.vitorias = 0.1						
            else:						
                pesos.vitorias = 0.0						

        # Atualizar as estatísticas de média de EMPATES com base nos dados da aposta (MESMO CRITÉRIO PARA TODOS OS CAMPEONATOS)     
        if total_jogos > 0:						
            media_empates = total_empates / total_jogos
            if media_empates > 0.58:
                pesos.empates = 2.0
            elif media_empates	<= 0.58	and media_empates > 0.55:
                pesos.empates = 1.9						
            elif media_empates	<= 0.55	and media_empates > 0.53:
                pesos.empates = 1.8						
            elif media_empates	<= 0.53	and media_empates > 0.50:
                pesos.empates = 1.7						
            elif media_empates	<= 0.50	and media_empates > 0.47:
                pesos.empates = 1.6						
            elif media_empates	<= 0.47	and media_empates > 0.45:
                pesos.empates = 1.5						
            elif media_empates	<= 0.45	and media_empates > 0.42:
                pesos.empates = 1.4						
            elif media_empates	<= 0.42	and media_empates > 0.39:
                pesos.empates = 1.3						
            elif media_empates	<= 0.39	and media_empates > 0.37:
                pesos.empates = 1.2						
            elif media_empates	<= 0.37	and media_empates > 0.34:
                pesos.empates = 1.1						
            elif media_empates	<= 0.34	and media_empates > 0.32:
                pesos.empates = 1.0						
            elif media_empates	<= 0.32	and media_empates > 0.29:
                pesos.empates = 0.9						
            elif media_empates	<= 0.29	and media_empates > 0.26:
                pesos.empates = 0.8						
            elif media_empates	<= 0.26	and media_empates > 0.24:
                pesos.empates = 0.7						
            elif media_empates	<= 0.24	and media_empates > 0.21:
                pesos.empates = 0.6						
            elif media_empates	<= 0.21	and media_empates > 0.18:
                pesos.empates = 0.5						
            elif media_empates	<= 0.18	and media_empates > 0.16:
                pesos.empates = 0.4						
            elif media_empates	<= 0.16	and media_empates > 0.13:
                pesos.empates = 0.3						
            elif media_empates	<= 0.13	and media_empates > 0.11:
                pesos.empates = 0.2						
            elif media_empates	<= 0.11	and media_empates > 0.08:
                pesos.empates = 0.1						
            else:						
                pesos.empates = 0.0						

        # Atualizar as estatísticas de média de DERROTAS com base nos dados da aposta      
        if total_jogos > 0:						
            media_derrotas = total_derrotas / total_jogos						
            if media_derrotas < 0.11:
                pesos.derrotas = 2.0						
            elif media_derrotas	>= 0.11	and media_derrotas < 0.13:
                pesos.derrotas = 1.9						
            elif media_derrotas	>= 0.13	and media_derrotas < 0.16:
                pesos.derrotas = 1.8						
            elif media_derrotas	>= 0.16	and media_derrotas < 0.18:
                pesos.derrotas = 1.7						
            elif media_derrotas	>= 0.18	and media_derrotas < 0.21:
                pesos.derrotas = 1.6					
            elif media_derrotas	>= 0.21	and media_derrotas < 0.24:
                pesos.derrotas = 1.5						
            elif media_derrotas	>= 0.24	and media_derrotas < 0.26:
                pesos.derrotas = 1.4						
            elif media_derrotas	>= 0.26	and media_derrotas < 0.29:
                pesos.derrotas = 1.3						
            elif media_derrotas	>= 0.29	and media_derrotas < 0.32:
                pesos.derrotas = 1.2						
            elif media_derrotas	>= 0.32	and media_derrotas < 0.34:
                pesos.derrotas = 1.1						
            elif media_derrotas	>= 0.34	and media_derrotas < 0.37:
                pesos.derrotas = 1.0						
            elif media_derrotas	>= 0.37	and media_derrotas < 0.39:
                pesos.derrotas = 0.9						
            elif media_derrotas	>= 0.39	and media_derrotas < 0.42:
                pesos.derrotas = 0.8						
            elif media_derrotas	>= 0.42	and media_derrotas < 0.45:
                pesos.derrotas = 0.7						
            elif media_derrotas	>= 0.45	and media_derrotas < 0.47:
                pesos.derrotas = 0.6						
            elif media_derrotas	>= 0.47	and media_derrotas < 0.50:
                pesos.derrotas = 0.5						
            elif media_derrotas	>= 0.50	and media_derrotas < 0.53:
                pesos.derrotas = 0.4						
            elif media_derrotas	>= 0.53	and media_derrotas < 0.55:
                pesos.derrotas = 0.3						
            elif media_derrotas	>= 0.55	and media_derrotas < 0.58:
                pesos.derrotas = 0.2						
            elif media_derrotas	>= 0.58	and media_derrotas < 0.61:
                pesos.derrotas = 0.1						
            else:						
                pesos.derrotas = 0.0						
            
            
            pesos.save()


def atualizar_pontos():
    pesos = Pesos.objects.all()
    # Dicionário para armazenar a média ponderada dos pesos por time e campeonato
    media_ponderada_por_time_campeonato = defaultdict(Decimal)
    total_pesos_por_time_campeonato = defaultdict(int)

    # Iterar sobre cada objeto Pesos e calcular a média ponderada dos pesos
    for peso_objeto in pesos:
        time = peso_objeto.time
        campeonato = peso_objeto.campeonato
        pesos_individuais = [peso_objeto.pontos, peso_objeto.gols_marcados, peso_objeto.gols_contra, peso_objeto.gols_saldo, peso_objeto.vitorias, peso_objeto.empates, peso_objeto.derrotas]
        media_ponderada_por_time_campeonato[(time, campeonato)] += sum(Decimal(peso) * peso_valor for peso, peso_valor in zip(pesos_individuais, [Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1')]))
        total_pesos_por_time_campeonato[(time, campeonato)] += 1

    # Calcular a média ponderada final e atribuir a pontuação para cada time
    pontuacoes_por_time_campeonato = {}
    for (time, campeonato), media_ponderada in media_ponderada_por_time_campeonato.items():
        total_pesos = total_pesos_por_time_campeonato[(time, campeonato)]
        pontuacao = media_ponderada / total_pesos / len(pesos_individuais)  # Dividir pela quantidade total de pesos
        pontuacoes_por_time_campeonato[(time, campeonato)] = pontuacao
        
    # Exibir as pontuações
    for (time, campeonato), pontuacao in pontuacoes_por_time_campeonato.items():
        print(f"{time} - {campeonato}: {pontuacao}")
        
    # Salvando os resultados no modelo PontuacaoTime
    for (time, campeonato), pontuacao in pontuacoes_por_time_campeonato.items():
        PontuacaoTime.objects.create(campeonato=campeonato, time=time, pontuacao_media_ponderada=pontuacao)


#def calcular_probabilidade_vitoria(time1, time2):
def calcular_probabilidade_vitoria(time1, time2):
    pesos_time1 = Pesos.objects.filter(time=time1)
    pesos_time2 = Pesos.objects.filter(time=time2)

    # Dicionários para armazenar a média ponderada dos pesos para cada time
    media_ponderada_time1 = defaultdict(Decimal)
    media_ponderada_time2 = defaultdict(Decimal)

    # Iterar sobre cada objeto de peso e calcular a média ponderada
    for peso in pesos_time1:
        pesos = [peso.gols_marcados, peso.gols_contra, peso.vitorias, peso.empates, peso.derrotas]
        media_ponderada_time1[time1] += sum(Decimal(peso) * peso_valor for peso, peso_valor in zip(pesos, [Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1')]))

    for peso in pesos_time2:
        pesos = [peso.gols_marcados, peso.gols_contra, peso.vitorias, peso.empates, peso.derrotas]
        media_ponderada_time2[time2] += sum(Decimal(peso) * peso_valor for peso, peso_valor in zip(pesos, [Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1'), Decimal('1')]))

    # Calcular a média ponderada final para cada time
    media_ponderada_final_time1 = sum(media_ponderada_time1.values()) / len(pesos_time1)
    media_ponderada_final_time2 = sum(media_ponderada_time2.values()) / len(pesos_time2)

    # Calcular a diferença de pontuação entre os times
    diferenca_pontuacao = float(media_ponderada_final_time1 - media_ponderada_final_time2)

    # Calcular a probabilidade de vitória e a margem de vitória esperada
    probabilidade_vitoria_time1 = norm.cdf(diferenca_pontuacao)
    margem_vitoria_esperada_time1 = norm.mean() * diferenca_pontuacao

    probabilidade_vitoria_time2 = 1 - probabilidade_vitoria_time1
    margem_vitoria_esperada_time2 = -margem_vitoria_esperada_time1

    # Salvar os resultados no modelo PontuTimeProbaMarg
    PontuTimeProbaMarg.objects.create(
        campeonato=pesos_time1.first().campeonato,
        time1=time1,
        probabilidade_vitoria_time1=probabilidade_vitoria_time1,
        margem_vitoria_esperada_time1=margem_vitoria_esperada_time1,
        time2=time2,
        probabilidade_vitoria_time2=probabilidade_vitoria_time2,
        margem_vitoria_esperada_time2=margem_vitoria_esperada_time2
    )

    # Adicionar log do resultado
    logger.info(f"Resultado calculado para {time1} vs {time2}: "
                f"Diferença de pontuação: {diferenca_pontuacao}, "
                f"Probabilidade de vitória ({time1}): {probabilidade_vitoria_time1}, "
                f"Margem de vitória esperada ({time1}): {margem_vitoria_esperada_time1}, "                
                f"Probabilidade de vitória ({time2}): {probabilidade_vitoria_time2}, "
                f"Margem de vitória esperada ({time2}): {margem_vitoria_esperada_time2}")


def Atualizar_SomaPontosTimeCampeonato():
    # Obtendo todas as apostas
    apostas = Aposta.objects.all()

    # Dicionário para armazenar as somas por time e campeonato
    somas_por_time_campeonato = {}

    # Calculando as somas para cada time e campeonato
    for aposta in apostas:
        chave = (aposta.time, aposta.campeonato)

        # Adicionando as somas ao dicionário ou criando novas entradas se necessário
        if chave in somas_por_time_campeonato:
            soma = somas_por_time_campeonato[chave]
            soma['soma_qtde_jogos'] += aposta.qtde_jogos
            soma['soma_pontos'] += aposta.pontos
            soma['soma_vitorias'] += aposta.vitorias
            soma['soma_empates'] += aposta.empates
            soma['soma_derrotas'] += aposta.derrotas
            soma['soma_gols_marcados'] += aposta.gols_marcados
            soma['soma_gols_contra'] += aposta.gols_contra
            soma['soma_gols_saldo'] += aposta.gols_saldo
            soma['soma_casasApostasOdds_acertos'] += aposta.casasApostasOdds_acertos
            soma['soma_guessGameOdds_acertos'] += aposta.guessGameOdds_acertos
            soma['soma_zebra'] +=  aposta.zebra
            soma['soma_vitorias_casa'] +=  aposta.vitorias_casa
            soma['soma_vitorias_fora'] +=  aposta.vitorias_fora
            soma['soma_empates_casa'] +=  aposta.empates_casa
            soma['soma_empates_fora'] +=  aposta.empates_fora
            soma['soma_derrotas_casa'] +=  aposta.derrotas_casa
            soma['soma_derrotas_fora'] +=  aposta.derrotas_fora
            soma['soma_favorito_derrota'] +=  aposta.favorito_derrota
            soma['soma_favorito_empate'] +=  aposta.favorito_empate
        else:
            somas_por_time_campeonato[chave] = {
                'soma_qtde_jogos': aposta.qtde_jogos,
                'soma_pontos': aposta.pontos,
                'soma_vitorias': aposta.vitorias,
                'soma_empates': aposta.empates,
                'soma_derrotas': aposta.derrotas,
                'soma_gols_marcados': aposta.gols_marcados,
                'soma_gols_contra': aposta.gols_contra,
                'soma_gols_saldo': aposta.gols_saldo,
                'soma_casasApostasOdds_acertos': aposta.casasApostasOdds_acertos,
                'soma_guessGameOdds_acertos': aposta.guessGameOdds_acertos,
                'soma_zebra' : aposta.zebra,
                'soma_vitorias_casa' : aposta.vitorias_casa,
                'soma_vitorias_fora' : aposta.vitorias_fora,
                'soma_empates_casa' : aposta.empates_casa,
                'soma_empates_fora' : aposta.empates_fora,
                'soma_derrotas_casa' : aposta.derrotas_casa,
                'soma_derrotas_fora' : aposta.derrotas_fora,
                'soma_favorito_derrota': aposta.favorito_derrota,
                'soma_favorito_empate': aposta.favorito_empate
            }

    # Atualizando a tabela SomaPontosTimeCampeonato
    for chave, soma in somas_por_time_campeonato.items():
        time, campeonato = chave
        soma_instance, created = SomaPontosTimeCampeonato.objects.get_or_create(
            time=time,
            campeonato=campeonato,
        )
        soma_instance.soma_qtde_jogos = soma['soma_qtde_jogos']
        soma_instance.soma_pontos = soma['soma_pontos']
        soma_instance.soma_vitorias = soma['soma_vitorias']
        soma_instance.soma_empates = soma['soma_empates']
        soma_instance.soma_derrotas = soma['soma_derrotas']
        soma_instance.soma_gols_marcados = soma['soma_gols_marcados']
        soma_instance.soma_gols_contra = soma['soma_gols_contra']
        soma_instance.soma_gols_saldo = soma['soma_gols_saldo']
        soma_instance.soma_casasApostasOdds_acertos = soma['soma_casasApostasOdds_acertos']
        soma_instance.soma_guessGameOdds_acertos = soma['soma_guessGameOdds_acertos']
        soma_instance.soma_zebra = soma['soma_zebra']
        soma_instance.soma_vitorias_casa = soma['soma_vitorias_casa']
        soma_instance.soma_vitorias_fora = soma['soma_vitorias_fora']
        soma_instance.soma_empates_casa = soma['soma_empates_casa']
        soma_instance.soma_empates_fora = soma['soma_empates_fora']
        soma_instance.soma_derrotas_casa = soma['soma_derrotas_casa']
        soma_instance.soma_derrotas_fora = soma['soma_derrotas_fora']
        soma_instance.soma_favorito_derrota = soma['soma_favorito_derrota']
        soma_instance.soma_favorito_empate = soma['soma_favorito_empate']
        soma_instance.save()


# Exporta do DB a tabela AppGuessGame_pontuacaotime para o arquivo pontuacaoTimes.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_pontuacaoTime():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_pontuacaotime"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'pontuacaoTimes.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel


# Exporta do DB a tabela AppGuessGame_aposta para o arquivo aposta_performanceTimes.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_aposta():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_aposta"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'aposta_performanceTimes.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel


# Exporta do DB a tabela AppGuessGame_pesos para o arquivo aposta_pesos.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_pesos():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_pesos"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'aposta_pesos.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel


# Exporta do DB a tabela AppGuessGame_SomaPontosTimeCampeonato para o arquivo pontuacaoTimes.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_SomaPontosTimeCampeonato():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_SomaPontosTimeCampeonato"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'SomaPontosTimeCampeonato.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel


# Exporta do DB a tabela AppGuessGame_Jogos para o arquivo jogos.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_Jogos():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_jogos"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'jogos.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel


# Exporta do DB a tabela AppGuessGame_resultadojogo para o arquivo resultadojogo.xlsx na pasta raiz do projeto GuessGame
def exportar_xlsx_resultadojogo():
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

    # Consulta SQL para selecionar todos os dados da tabela
    query = "SELECT * FROM AppGuessGame_resultadojogo"

    # Ler os dados da consulta para um DataFrame
    df = pd.read_sql_query(query, conn)

    # Nome do arquivo Excel de saída
    nome_do_arquivo_excel = 'resultadojogo.xlsx'

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_do_arquivo_excel, index=False)

    # Fechar a conexão com o banco de dados
    conn.close()

    return nome_do_arquivo_excel
